from __future__ import annotations

from pathlib import Path

from app.services.policy_compiler import write_cedar_policy
from app.services.policy_config import (
    PolicyConfig,
    load_policy_config,
    normalize_policy_config,
    preset_policy_config,
    save_policy_config,
)
from app.services.policy_simulator import PolicySimulator


class PolicyService:
    """Domain service for policy operations. UI should only call this."""

    @staticmethod
    def load(config_path: Path, template: str) -> PolicyConfig:
        if config_path.exists():
            return load_policy_config(config_path)
        return preset_policy_config(template)

    @staticmethod
    def normalize(config: PolicyConfig) -> PolicyConfig:
        return normalize_policy_config(config)

    @staticmethod
    def save(config: PolicyConfig, config_path: Path, cedar_path: Path) -> None:
        normalized = normalize_policy_config(config)
        save_policy_config(normalized, config_path)
        write_cedar_policy(normalized, cedar_path)

    @staticmethod
    def simulate(config: PolicyConfig, text: str, role: str):
        normalized = normalize_policy_config(config)
        simulator = PolicySimulator(normalized)
        return simulator.simulate(text=text, role=role)

    @staticmethod
    def explain_decision(result, config: PolicyConfig) -> dict[str, str]:
        """Derive human-readable explanation from simulation result."""
        matched_signals = [
            key
            for key, value in result.signal_contract.items()
            if key.endswith("_detected") and isinstance(value, bool) and value
        ]
        if result.signal_contract.get("low_confidence"):
            matched_signals.append("low_confidence")

        policy_matches = PolicyService._derive_policy_matches(result.signal_contract, config)

        return {
            "decision": result.decision.upper(),
            "tier": result.tier,
            "signals": ", ".join(matched_signals) if matched_signals else "none",
            "policy_matches": ", ".join(policy_matches) if policy_matches else "none",
        }

    @staticmethod
    def _derive_policy_matches(signal_contract: dict[str, object], config: PolicyConfig) -> list[str]:
        """Core logic for matching signals to policy rules. Single source of truth."""
        matches: list[str] = []

        if signal_contract.get("override_detected") and "P0_Critical" in config.blocked_tiers:
            matches.append("blocked_tiers:P0_Critical")
        if signal_contract.get("pii_detected") and "P1_High" in config.blocked_tiers:
            matches.append("blocked_tiers:P1_High")
        if (
            signal_contract.get("toxicity_detected")
            and signal_contract.get("toxicity_enforce_block")
            and "P2_Medium" in config.blocked_tiers
        ):
            matches.append("blocked_tiers:P2_Medium")
        if signal_contract.get("financial_advice_detected") and "P3_Low" in config.blocked_tiers:
            matches.append("blocked_tiers:P3_Low")

        intent = signal_contract.get("intent")
        info_intents = {"info.query", "info.summarize", "tool.safe", "conv.greeting"}
        if intent in info_intents and "P4_Info" in config.blocked_tiers:
            matches.append("blocked_tiers:P4_Info")

        if signal_contract.get("low_confidence"):
            matches.append(f"low_confidence_clamp:{config.low_confidence_clamp_tier}")

        return matches
