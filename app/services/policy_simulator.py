from __future__ import annotations

import asyncio
from dataclasses import dataclass
import re
from typing import Any, Dict, List, Tuple

from app.core.taxonomy import IntentCategory
from app.services.detectors.regex import RegexDetector
from app.services.policy_compiler import compile_cedar_policy, validate_cedar_policy
from app.services.policy_config import PolicyConfig, TIER_ORDER, TIER_RANK
from app.services.priority_engine import PriorityEngine

OVERRIDE_INTENTS = {
    IntentCategory.PROMPT_INJECTION,
    IntentCategory.JAILBREAK,
    IntentCategory.SYSTEM_OVERRIDE,
}

BENIGN_INTENT_HINTS = {
    IntentCategory.INFO_QUERY,
    IntentCategory.INFO_SUMMARIZE,
    IntentCategory.TOOL_AUTHORIZED,
    IntentCategory.GREETING,
}

SENSITIVE_INTENTS = {
    IntentCategory.PROMPT_INJECTION,
    IntentCategory.JAILBREAK,
    IntentCategory.SYSTEM_OVERRIDE,
    IntentCategory.PII_EXFILTRATION,
    IntentCategory.TOOL_MISUSE,
    IntentCategory.TOXICITY,
    IntentCategory.FINANCIAL_ADVICE,
}

RISK_SCORE_BY_TIER: Dict[str, float] = {
    "P0_Critical": 1.0,
    "P1_High": 0.85,
    "P2_Medium": 0.65,
    "P3_Low": 0.45,
    "P4_Info": 0.0,
}
RANK_TO_TIER = {index: tier for index, tier in enumerate(TIER_ORDER)}

PII_PATTERN_DEFINITIONS = [
    re.compile(r"\bsocial\s+security\s+number\b", re.IGNORECASE),
    re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
    re.compile(r"\bcredit\s*card\b", re.IGNORECASE),
    re.compile(r"\b(api[_\s-]?keys?|secret\s+keys?)\b", re.IGNORECASE),
    re.compile(r"\b(passwords?|passwd|credentials?)\b", re.IGNORECASE),
    re.compile(r"\bprivate\s+keys?\b", re.IGNORECASE),
    re.compile(r"\bdump\s+(the\s+)?(database|db)\b", re.IGNORECASE),
    re.compile(r"\b(show|list|dump).{0,20}\buser\s+emails?\b", re.IGNORECASE),
]

TOXICITY_PATTERNS = [
    re.compile(r"\buseless\b", re.IGNORECASE),
    re.compile(r"\bstupid\b", re.IGNORECASE),
    re.compile(r"\bshut\s+up\b", re.IGNORECASE),
    re.compile(r"\bidiot\b", re.IGNORECASE),
    re.compile(r"\bmoron\b", re.IGNORECASE),
    re.compile(r"\bworthless\b", re.IGNORECASE),
]

FINANCIAL_PATTERNS = [
    re.compile(r"\bstocks?\b", re.IGNORECASE),
    re.compile(r"\bcrypto(currency)?\b", re.IGNORECASE),
    re.compile(r"\binvest(ment|ing)?\b", re.IGNORECASE),
    re.compile(r"\btrading?\b", re.IGNORECASE),
    re.compile(r"\bmarket\s+(prediction|forecast|trend)\b", re.IGNORECASE),
]


@dataclass
class PolicySimulationResult:
    decision: str
    reason: str
    intent: str
    confidence: float
    tier: str
    risk_score: float
    signal_contract: Dict[str, Any]


class PolicySimulator:
    def __init__(self, config: PolicyConfig):
        self.config = config
        self.priority_engine = PriorityEngine()
        self.regex_detector = RegexDetector()
        self._load_regex_patterns()
        generated_policy = compile_cedar_policy(config)
        self.compiled_policy = validate_cedar_policy(generated_policy, source="<simulator-policy>")

    def simulate(self, text: str, role: str = "general") -> PolicySimulationResult:
        text_value = text.strip()
        if not text_value:
            raise ValueError("Simulation text must not be empty")

        regex_result = self.regex_detector.detect(text_value)
        pii_detected = self._detect_pii(text_value)
        toxicity_detected = self._detect_toxicity(text_value)
        financial_detected = self._detect_financial(text_value)

        candidates = []
        if regex_result.get("detected"):
            candidates.append(
                {
                    "intent": regex_result["intent"],
                    "score": float(regex_result.get("score", 1.0)),
                    "source": "regex",
                }
            )
        if pii_detected:
            candidates.append(
                {
                    "intent": IntentCategory.PII_EXFILTRATION,
                    "score": 1.0,
                    "source": "pii-patterns",
                }
            )
        if toxicity_detected:
            candidates.append(
                {
                    "intent": IntentCategory.TOXICITY,
                    "score": 0.75,
                    "source": "toxicity-lexicon",
                }
            )
        if financial_detected:
            candidates.append(
                {
                    "intent": IntentCategory.FINANCIAL_ADVICE,
                    "score": 0.8,
                    "source": "financial-keywords",
                }
            )

        deterministic_safe_signal = (
            not regex_result.get("detected")
            and not pii_detected
            and not toxicity_detected
            and not financial_detected
            and _looks_like_safe_question(text_value)
        )

        if deterministic_safe_signal:
            candidates.append(
                {
                    "intent": IntentCategory.INFO_QUERY,
                    "score": 0.6,
                    "source": "safe-path",
                }
            )

        if not candidates:
            candidates.append(
                {
                    "intent": IntentCategory.UNKNOWN,
                    "score": 0.25,
                    "source": "fallback",
                }
            )

        primary_intent, primary_score, _ = self.priority_engine.resolve(candidates)

        signal_contract = self._build_signal_contract(
            regex_result=regex_result,
            pii_detected=pii_detected,
            toxicity_detected=toxicity_detected,
            financial_detected=financial_detected,
            primary_intent=primary_intent,
            primary_score=float(primary_score),
            deterministic_safe_signal=deterministic_safe_signal,
        )
        context = {
            "override_detected": signal_contract["override_detected"],
            "pii_detected": signal_contract["pii_detected"],
            "toxicity_detected": signal_contract["toxicity_detected"],
            "toxicity_enforce_block": signal_contract["toxicity_enforce_block"],
            "financial_advice_detected": signal_contract["financial_advice_detected"],
            "low_confidence": signal_contract["low_confidence"],
            "intent": signal_contract["intent"],
        }

        decision, reason = self._evaluate_policy(role=role, context=context)
        tier, risk_score = self._derive_tier_and_score(
            role=role,
            signal_contract=signal_contract,
        )

        return PolicySimulationResult(
            decision=decision,
            reason=reason,
            intent=primary_intent.value,
            confidence=float(primary_score),
            tier=tier,
            risk_score=risk_score,
            signal_contract=signal_contract,
        )

    def simulate_signals(
        self,
        role: str,
        signal_contract: Dict[str, Any],
    ) -> PolicySimulationResult:
        required_fields = [
            "override_detected",
            "pii_detected",
            "toxicity_detected",
            "toxicity_enforce_block",
            "financial_advice_detected",
            "low_confidence",
            "intent",
            "confidence",
        ]
        for field in required_fields:
            if field not in signal_contract:
                raise ValueError(f"signal_contract missing required field: {field}")

        context = {
            "override_detected": bool(signal_contract["override_detected"]),
            "pii_detected": bool(signal_contract["pii_detected"]),
            "toxicity_detected": bool(signal_contract["toxicity_detected"]),
            "toxicity_enforce_block": bool(signal_contract["toxicity_enforce_block"]),
            "financial_advice_detected": bool(signal_contract["financial_advice_detected"]),
            "low_confidence": bool(signal_contract["low_confidence"]),
            "intent": str(signal_contract["intent"]),
        }

        decision, reason = self._evaluate_policy(role=role, context=context)
        tier, risk_score = self._derive_tier_and_score(role=role, signal_contract=signal_contract)

        return PolicySimulationResult(
            decision=decision,
            reason=reason,
            intent=str(signal_contract["intent"]),
            confidence=float(signal_contract["confidence"]),
            tier=tier,
            risk_score=risk_score,
            signal_contract=dict(signal_contract),
        )

    def _build_signal_contract(
        self,
        regex_result: Dict[str, Any],
        pii_detected: bool,
        toxicity_detected: bool,
        financial_detected: bool,
        primary_intent: IntentCategory,
        primary_score: float,
        deterministic_safe_signal: bool,
    ) -> Dict[str, Any]:
        override_detected = bool(
            regex_result.get("detected") and regex_result.get("intent") in OVERRIDE_INTENTS
        )
        pii_flag = bool(
            pii_detected
            or (
                regex_result.get("detected")
                and regex_result.get("intent") == IntentCategory.PII_EXFILTRATION
            )
        )

        raw_low_confidence = primary_score < self.config.low_confidence_threshold
        benign_hint_detected = primary_intent in BENIGN_INTENT_HINTS
        sensitive_hint_detected = primary_intent in SENSITIVE_INTENTS
        risk_aware_low_confidence = bool(
            raw_low_confidence
            and not deterministic_safe_signal
            and not benign_hint_detected
            and sensitive_hint_detected
        )

        return {
            "override_detected": override_detected,
            "pii_detected": pii_flag,
            "toxicity_detected": bool(toxicity_detected),
            "toxicity_enforce_block": True,
            "financial_advice_detected": bool(financial_detected),
            "low_confidence": risk_aware_low_confidence,
            "low_confidence_raw": raw_low_confidence,
            "deterministic_safe_signal": bool(deterministic_safe_signal),
            "benign_hint_detected": bool(benign_hint_detected),
            "sensitive_model_hint": bool(sensitive_hint_detected),
            "toxicity_score": 0.7 if toxicity_detected else 0.0,
            "financial_advice_score": 0.8 if financial_detected else 0.0,
            "confidence": max(0.0, min(1.0, primary_score)),
            "intent": primary_intent.value,
        }

    def _evaluate_policy(self, role: str, context: Dict[str, Any]) -> Tuple[str, str]:
        try:
            import cedarpy
        except ImportError as exc:
            raise RuntimeError(
                "cedarpy is required to simulate policies. Activate the project venv first."
            ) from exc

        principal = f"Role::\"{role}\""
        request = {
            "principal": principal,
            "action": "Action::\"query\"",
            "resource": "App::\"IntentAnalyzer\"",
            "context": context,
        }
        principal_entity = {
            "uid": {"type": "Role", "id": role},
            "attrs": {"user_role": role},
            "parents": [],
        }
        result: cedarpy.AuthzResult = cedarpy.is_authorized(
            request,
            self.compiled_policy,
            [principal_entity],
        )
        decision = "allow" if result.decision == cedarpy.Decision.Allow else "block"
        diagnostics: List[str] = []
        if hasattr(result, "diagnostics") and result.diagnostics:
            diagnostics = (
                [str(err) for err in result.diagnostics.errors]
                if hasattr(result.diagnostics, "errors")
                else []
            )
        reason = "Policy Check Passed"
        if decision == "block":
            reason = (
                f"Policy Denied: {', '.join(diagnostics)}"
                if diagnostics
                else "Policy Denied: Implicit Deny or Rule Block"
            )
        return decision, reason

    def _derive_tier_and_score(
        self,
        role: str,
        signal_contract: Dict[str, Any],
    ) -> Tuple[str, float]:
        tier_rank = 4
        if signal_contract["override_detected"]:
            tier_rank = min(tier_rank, 0)
        if signal_contract["pii_detected"]:
            tier_rank = min(tier_rank, 1)
        if signal_contract["toxicity_detected"]:
            tier_rank = min(tier_rank, 2)
        if signal_contract["financial_advice_detected"]:
            tier_rank = min(tier_rank, 3)

        clamp_tier = self.config.low_confidence_clamp_tier
        clamp_rank = TIER_RANK[clamp_tier]
        clamp_exempt_roles = set(self.config.exempt_roles_for_tier(clamp_tier))
        if signal_contract["low_confidence"] and role not in clamp_exempt_roles:
            tier_rank = min(tier_rank, clamp_rank)

        tier = RANK_TO_TIER[tier_rank]
        return tier, RISK_SCORE_BY_TIER[tier]

    def _detect_pii(self, text: str) -> bool:
        return any(pattern.search(text) for pattern in PII_PATTERN_DEFINITIONS)

    def _detect_toxicity(self, text: str) -> bool:
        return any(pattern.search(text) for pattern in TOXICITY_PATTERNS)

    def _detect_financial(self, text: str) -> bool:
        return any(pattern.search(text) for pattern in FINANCIAL_PATTERNS)

    def _load_regex_patterns(self) -> None:
        try:
            asyncio.run(self.regex_detector.load())
        except RuntimeError:
            loop = asyncio.new_event_loop()
            try:
                loop.run_until_complete(self.regex_detector.load())
            finally:
                loop.close()


def _looks_like_safe_question(text: str) -> bool:
    return bool(
        re.match(r"^\s*(who|what|when|where|why|how|define)\b.{1,180}\??\s*$", text, re.IGNORECASE)
    )
