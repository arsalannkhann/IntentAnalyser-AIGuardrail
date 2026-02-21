from __future__ import annotations

from pathlib import Path
from typing import Dict, List

from app.services.policy_config import PolicyConfig, normalize_policy_config

TIER_SIGNAL_EXPRESSIONS: Dict[str, str] = {
    "P0_Critical": "context.override_detected == true",
    "P1_High": "context.pii_detected == true",
    "P2_Medium": "context.toxicity_detected == true &&\n    context.toxicity_enforce_block == true",
    "P3_Low": "context.financial_advice_detected == true",
    "P4_Info": (
        "context.intent == \"info.query\" ||\n"
        "    context.intent == \"info.summarize\" ||\n"
        "    context.intent == \"tool.safe\" ||\n"
        "    context.intent == \"conv.greeting\""
    ),
}

TIER_RULE_LABELS = {
    "P0_Critical": "Critical Override Block",
    "P1_High": "PII Protection Block",
    "P2_Medium": "Toxicity Guard Block",
    "P3_Low": "Financial Advice Block",
    "P4_Info": "Informational Clamp Block",
}


def compile_cedar_policy(config: PolicyConfig) -> str:
    normalized = normalize_policy_config(config)

    lines: List[str] = [
        "// -----------------------------------------------------------------------------",
        "// Guardrail Policy (generated) — edit app/policies/main.yaml",
        "// -----------------------------------------------------------------------------",
        "// Signal Contract (policy-visible context):",
        "//   - override_detected: bool",
        "//   - pii_detected: bool",
        "//   - toxicity_detected: bool",
        "//   - toxicity_enforce_block: bool",
        "//   - financial_advice_detected: bool",
        "//   - low_confidence: bool",
        "//   - intent: string",
        "//",
        f"// Template: {normalized.template}",
        f"// Low confidence threshold: {normalized.low_confidence_threshold}",
        f"// Low confidence clamp tier: {normalized.low_confidence_clamp_tier}",
        "",
    ]

    rule_counter = 1
    for tier in normalized.blocked_tiers:
        signal_expression = TIER_SIGNAL_EXPRESSIONS[tier]
        role_clause = _role_restriction_clause(normalized.exempt_roles_for_tier(tier))
        full_expression = signal_expression + role_clause
        lines.extend(
            [
                f"// Rule {rule_counter} — {TIER_RULE_LABELS[tier]} ({tier})",
                "forbid (",
                "    principal,",
                "    action,",
                "    resource",
                ")",
                "when {",
                f"    {full_expression}",
                "};",
                "",
            ]
        )
        rule_counter += 1

    clamp_role_clause = _role_restriction_clause(
        normalized.exempt_roles_for_tier(normalized.low_confidence_clamp_tier)
    )
    clamp_expression = "context.low_confidence == true" + clamp_role_clause
    lines.extend(
        [
            f"// Rule {rule_counter} — Low Confidence Clamp",
            "forbid (",
            "    principal,",
            "    action,",
            "    resource",
            ")",
            "when {",
            f"    {clamp_expression}",
            "};",
            "",
            "// Baseline allow when no deny rules matched.",
            "permit (",
            "    principal,",
            "    action,",
            "    resource",
            ");",
            "",
        ]
    )

    return "\n".join(lines)


def validate_cedar_policy(policy_text: str, source: str = "<generated>") -> str:
    try:
        import cedarpy
    except ImportError as exc:
        raise RuntimeError(
            "cedarpy is required to validate Cedar policy text. "
            "Activate the project venv before running policy commands."
        ) from exc

    try:
        return cedarpy.format_policies(policy_text)
    except Exception as exc:  # pragma: no cover - behavior depends on cedarpy internals
        raise ValueError(f"Failed to compile Cedar policy '{source}': {exc}") from exc


def write_cedar_policy(config: PolicyConfig, path: str | Path) -> Path:
    policy_path = Path(path)
    policy_path.parent.mkdir(parents=True, exist_ok=True)
    policy_text = compile_cedar_policy(config)
    validate_cedar_policy(policy_text, source=str(policy_path))
    policy_path.write_text(policy_text, encoding="utf-8")
    return policy_path


def _role_restriction_clause(exempt_roles: List[str]) -> str:
    if not exempt_roles:
        return ""
    restrictions = " &&\n    ".join(
        [f'principal.user_role != "{role}"' for role in sorted(exempt_roles)]
    )
    return " &&\n    " + restrictions
