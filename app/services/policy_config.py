from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
from typing import Any, Dict, List

DEFAULT_POLICY_CONFIG_PATH = Path("app/policies/main.yaml")
DEFAULT_CEDAR_POLICY_PATH = Path("app/policies/main.cedar")

ALLOW_ALL = "ALL"
SUPPORTED_TEMPLATES = {"strict", "balanced", "permissive", "custom"}

TIER_ORDER = [
    "P0_Critical",
    "P1_High",
    "P2_Medium",
    "P3_Low",
    "P4_Info",
]
TIER_RANK = {tier: index for index, tier in enumerate(TIER_ORDER)}

ROLE_PATTERN = re.compile(r"^[A-Za-z][A-Za-z0-9_-]{0,31}$")


class PolicyConfigError(ValueError):
    """Raised when policy config schema validation fails."""


@dataclass
class PolicyConfig:
    version: int
    template: str
    blocked_tiers: List[str]
    role_overrides: Dict[str, str]
    low_confidence_threshold: float
    low_confidence_clamp_tier: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "version": self.version,
            "template": self.template,
            "blocked_tiers": list(self.blocked_tiers),
            "role_overrides": dict(self.role_overrides),
            "low_confidence": {
                "threshold": self.low_confidence_threshold,
                "clamp_tier": self.low_confidence_clamp_tier,
            },
        }

    def exempt_roles_for_tier(self, tier: str) -> List[str]:
        if tier not in TIER_RANK:
            raise PolicyConfigError(f"Unknown tier: {tier}")
        tier_rank = TIER_RANK[tier]
        exempt_roles: List[str] = []
        for role, allowance in self.role_overrides.items():
            if allowance == ALLOW_ALL:
                exempt_roles.append(role)
                continue
            if tier_rank >= TIER_RANK[allowance]:
                exempt_roles.append(role)
        return sorted(set(exempt_roles))


def preset_policy_config(template: str = "balanced") -> PolicyConfig:
    normalized = template.strip().lower()
    presets = {
        "strict": {
            "version": 1,
            "template": "strict",
            "blocked_tiers": ["P0_Critical", "P1_High", "P2_Medium", "P3_Low"],
            "role_overrides": {},
            "low_confidence": {"threshold": 0.5, "clamp_tier": "P2_Medium"},
        },
        "balanced": {
            "version": 1,
            "template": "balanced",
            "blocked_tiers": ["P0_Critical", "P1_High"],
            "role_overrides": {},
            "low_confidence": {"threshold": 0.4, "clamp_tier": "P3_Low"},
        },
        "permissive": {
            "version": 1,
            "template": "permissive",
            "blocked_tiers": ["P0_Critical"],
            "role_overrides": {},
            "low_confidence": {"threshold": 0.3, "clamp_tier": "P4_Info"},
        },
    }
    if normalized not in presets:
        raise PolicyConfigError(
            f"Unknown template '{template}'. Choose one of: strict, balanced, permissive."
        )
    return policy_config_from_data(presets[normalized], source=f"template:{normalized}")


def parse_policy_yaml(content: str, source: str = "<memory>") -> Dict[str, Any]:
    data: Dict[str, Any] = {
        "blocked_tiers": [],
        "role_overrides": {},
        "low_confidence": {},
    }
    active_section: str | None = None

    for line_no, raw_line in enumerate(content.splitlines(), start=1):
        if "\t" in raw_line:
            raise PolicyConfigError(f"{source}:{line_no}: tabs are not supported in YAML config")

        line = raw_line.split("#", 1)[0].rstrip()
        if not line.strip():
            continue

        indent = len(line) - len(line.lstrip(" "))
        stripped = line.lstrip(" ")

        if indent == 0:
            if ":" not in stripped:
                raise PolicyConfigError(f"{source}:{line_no}: expected '<key>: <value>'")
            key, raw_value = stripped.split(":", 1)
            key = key.strip()
            value = raw_value.strip()
            if key in {"blocked_tiers", "role_overrides", "low_confidence"}:
                if value:
                    raise PolicyConfigError(
                        f"{source}:{line_no}: section '{key}' cannot use inline values"
                    )
                active_section = key
                continue

            active_section = None
            data[key] = _parse_scalar(value)
            continue

        if indent != 2:
            raise PolicyConfigError(
                f"{source}:{line_no}: unsupported indentation level {indent}; use 2 spaces"
            )

        if active_section == "blocked_tiers":
            if not stripped.startswith("- "):
                raise PolicyConfigError(f"{source}:{line_no}: blocked tier entries must use '- '")
            tier = stripped[2:].strip()
            if not tier:
                raise PolicyConfigError(f"{source}:{line_no}: blocked tier cannot be empty")
            data["blocked_tiers"].append(tier)
            continue

        if active_section == "role_overrides":
            if ":" not in stripped:
                raise PolicyConfigError(f"{source}:{line_no}: expected '<role>: <tier|ALL>'")
            role, raw_allowance = stripped.split(":", 1)
            role = role.strip()
            allowance = raw_allowance.strip()
            if not role or not allowance:
                raise PolicyConfigError(f"{source}:{line_no}: invalid role override entry")
            data["role_overrides"][role] = allowance
            continue

        if active_section == "low_confidence":
            if ":" not in stripped:
                raise PolicyConfigError(f"{source}:{line_no}: expected '<field>: <value>'")
            key, raw_value = stripped.split(":", 1)
            key = key.strip()
            value = raw_value.strip()
            if not key or value == "":
                raise PolicyConfigError(f"{source}:{line_no}: invalid low_confidence entry")
            data["low_confidence"][key] = _parse_scalar(value)
            continue

        raise PolicyConfigError(f"{source}:{line_no}: unexpected indentation")

    return data


def policy_config_from_data(data: Dict[str, Any], source: str = "<memory>") -> PolicyConfig:
    if not isinstance(data, dict):
        raise PolicyConfigError(f"{source}: policy config must be a mapping")

    version = data.get("version", 1)
    if not isinstance(version, int):
        raise PolicyConfigError(f"{source}: 'version' must be an integer")

    template = str(data.get("template", "custom")).strip().lower()
    if template not in SUPPORTED_TEMPLATES:
        raise PolicyConfigError(
            f"{source}: invalid 'template' ({template}). Expected one of: "
            "strict, balanced, permissive, custom."
        )

    blocked_raw = data.get("blocked_tiers", [])
    if not isinstance(blocked_raw, list):
        raise PolicyConfigError(f"{source}: 'blocked_tiers' must be a list")
    blocked_tiers: List[str] = []
    for tier in blocked_raw:
        tier_name = str(tier).strip()
        if tier_name not in TIER_RANK:
            raise PolicyConfigError(f"{source}: unsupported blocked tier '{tier_name}'")
        if tier_name not in blocked_tiers:
            blocked_tiers.append(tier_name)
    blocked_tiers.sort(key=lambda tier_name: TIER_RANK[tier_name])

    role_raw = data.get("role_overrides", {})
    if not isinstance(role_raw, dict):
        raise PolicyConfigError(f"{source}: 'role_overrides' must be a mapping")
    role_overrides: Dict[str, str] = {}
    for role_name, allowance_value in role_raw.items():
        role = str(role_name).strip()
        allowance = str(allowance_value).strip()
        if not ROLE_PATTERN.match(role):
            raise PolicyConfigError(
                f"{source}: invalid role '{role}'. Role must match {ROLE_PATTERN.pattern}"
            )
        if allowance.upper() == ALLOW_ALL:
            role_overrides[role] = ALLOW_ALL
            continue
        if allowance not in TIER_RANK:
            raise PolicyConfigError(
                f"{source}: invalid override tier '{allowance}' for role '{role}'"
            )
        role_overrides[role] = allowance

    low_conf_raw = data.get("low_confidence", {})
    if not isinstance(low_conf_raw, dict):
        raise PolicyConfigError(f"{source}: 'low_confidence' must be a mapping")

    threshold_value = low_conf_raw.get("threshold", 0.4)
    try:
        low_confidence_threshold = float(threshold_value)
    except (TypeError, ValueError) as exc:
        raise PolicyConfigError(f"{source}: low_confidence.threshold must be numeric") from exc
    if low_confidence_threshold < 0.0 or low_confidence_threshold > 1.0:
        raise PolicyConfigError(
            f"{source}: low_confidence.threshold must be within [0, 1]"
        )

    clamp_tier = str(low_conf_raw.get("clamp_tier", "P3_Low")).strip()
    if clamp_tier not in TIER_RANK:
        raise PolicyConfigError(
            f"{source}: low_confidence.clamp_tier must be one of {', '.join(TIER_ORDER)}"
        )

    return PolicyConfig(
        version=version,
        template=template,
        blocked_tiers=blocked_tiers,
        role_overrides=role_overrides,
        low_confidence_threshold=low_confidence_threshold,
        low_confidence_clamp_tier=clamp_tier,
    )


def normalize_policy_config(config: PolicyConfig) -> PolicyConfig:
    return policy_config_from_data(config.to_dict(), source="normalized_config")


def load_policy_config(path: str | Path = DEFAULT_POLICY_CONFIG_PATH) -> PolicyConfig:
    policy_path = Path(path)
    if not policy_path.exists():
        raise PolicyConfigError(f"Policy config not found: {policy_path}")
    data = parse_policy_yaml(policy_path.read_text(encoding="utf-8"), source=str(policy_path))
    return policy_config_from_data(data, source=str(policy_path))


def dump_policy_yaml(config: PolicyConfig) -> str:
    normalized = normalize_policy_config(config)
    threshold = f"{normalized.low_confidence_threshold:.3f}".rstrip("0").rstrip(".")
    if not threshold:
        threshold = "0"

    lines = [
        f"version: {normalized.version}",
        f"template: {normalized.template}",
        "blocked_tiers:",
    ]

    for tier in normalized.blocked_tiers:
        lines.append(f"  - {tier}")

    lines.append("role_overrides:")
    if normalized.role_overrides:
        for role in sorted(normalized.role_overrides):
            lines.append(f"  {role}: {normalized.role_overrides[role]}")
    else:
        lines.append("  {}  # No role overrides (tier enforcement only)")

    lines.extend(
        [
            "low_confidence:",
            f"  threshold: {threshold}",
            f"  clamp_tier: {normalized.low_confidence_clamp_tier}",
        ]
    )
    return "\n".join(lines) + "\n"


def save_policy_config(config: PolicyConfig, path: str | Path) -> Path:
    policy_path = Path(path)
    policy_path.parent.mkdir(parents=True, exist_ok=True)
    policy_path.write_text(dump_policy_yaml(config), encoding="utf-8")
    return policy_path


def _parse_scalar(raw_value: str) -> Any:
    if re.fullmatch(r"-?\d+", raw_value):
        return int(raw_value)
    if re.fullmatch(r"-?\d+\.\d+", raw_value):
        return float(raw_value)
    return raw_value
