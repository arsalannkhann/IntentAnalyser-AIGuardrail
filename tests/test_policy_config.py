import unittest

from app.services.policy_compiler import compile_cedar_policy, validate_cedar_policy
from app.services.policy_config import (
    PolicyConfigError,
    dump_policy_yaml,
    parse_policy_yaml,
    policy_config_from_data,
    preset_policy_config,
)


class PolicyConfigTests(unittest.TestCase):
    def test_preset_roundtrip_parses(self) -> None:
        preset = preset_policy_config("balanced")
        dumped = dump_policy_yaml(preset)
        parsed = parse_policy_yaml(dumped, source="roundtrip")
        rebuilt = policy_config_from_data(parsed, source="roundtrip")
        self.assertEqual(rebuilt.template, "balanced")
        self.assertEqual(rebuilt.blocked_tiers, ["P0_Critical", "P1_High"])
        self.assertEqual(rebuilt.role_overrides["analyst"], "P3_Low")
        self.assertAlmostEqual(rebuilt.low_confidence_threshold, 0.4)

    def test_invalid_override_tier_raises(self) -> None:
        data = preset_policy_config("balanced").to_dict()
        data["role_overrides"]["analyst"] = "P9_Imaginary"
        with self.assertRaises(PolicyConfigError):
            policy_config_from_data(data, source="bad_override")

    def test_generated_cedar_compiles(self) -> None:
        config = preset_policy_config("strict")
        cedar_text = compile_cedar_policy(config)
        compiled = validate_cedar_policy(cedar_text, source="generated")
        self.assertTrue(compiled)


if __name__ == "__main__":
    unittest.main()
