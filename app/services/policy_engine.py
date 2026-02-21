import logging
import cedarpy
from typing import Dict, Any, List
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class EvaluationResult:
    decision: str
    reason: str
    diagnostics: List[str]

class PolicyEngine:
    def __init__(self, policy_path: str = "app/policies/main.cedar"):
        self.policy_path = policy_path
        self.policy_content = self._load_policy(policy_path)
        self.compiled_policy = self._compile_policy(self.policy_content, policy_path)
        logger.info("Loaded and compiled Cedar policies from %s", policy_path)

    @staticmethod
    def _load_policy(policy_path: str) -> str:
        try:
            with open(policy_path, "r", encoding="utf-8") as policy_file:
                return policy_file.read()
        except FileNotFoundError as exc:
            raise RuntimeError(f"Policy file not found: {policy_path}") from exc

    @staticmethod
    def _compile_policy(policy_content: str, policy_path: str) -> str:
        """
        Parse and normalize Cedar policies once at startup.
        This validates syntax up front so policy failures are fail-fast.
        """
        try:
            return cedarpy.format_policies(policy_content)
        except Exception as exc:
            raise RuntimeError(
                f"Failed to compile Cedar policy '{policy_path}': {exc}"
            ) from exc

    def evaluate(
        self,
        principal: str,
        action: str,
        resource: str,
        context: Dict[str, Any]
    ) -> EvaluationResult:
        """
        Evaluate a request against the Cedar policies.
        """
        request = {
            "principal": principal,
            "action": action,
            "resource": resource,
            "context": context
        }
        
        # We assume empty entities list for now as our policies are self-contained
        # or rely on context. If we need hierarchical role checking that isn't
        # pure string matching, we'd populate entities here.
        # Construct principal entity to ensure Cedar recognizes it
        # Principal format: Role::"name" -> type=Role, id=name
        p_type, p_id = principal.split("::")
        p_id = p_id.strip('"') # Remove quotes
        
        principal_entity = {
            "uid": {"type": p_type, "id": p_id},
            "attrs": {
                "user_role": p_id
            },
            "parents": []
        }
        entities = [principal_entity]
        logger.info("CEDAR REQUEST: %s", request)

        try:
            result: cedarpy.AuthzResult = cedarpy.is_authorized(
                request,
                self.compiled_policy,
                entities,
            )
            
            decision_str = "allow" if result.decision == cedarpy.Decision.Allow else "block"
            
            # Extract diagnostics (reasons for denial) if available
            reasons = []
            if hasattr(result, "diagnostics") and result.diagnostics:
                # Diagnostics object usually contains errors or reasons
                reasons = [str(d) for d in result.diagnostics.errors] if hasattr(result.diagnostics, "errors") else []

            # Add reason for blocking
            reason_msg = "Policy Check Passed"
            if decision_str == "block":
                reason_msg = f"Policy Denied: {', '.join(reasons) if reasons else 'Implicit Deny or Rule Block'}"

            return EvaluationResult(
                decision=decision_str,
                reason=reason_msg,
                diagnostics=reasons
            )

        except Exception as e:
            logger.error(f"Cedar Evaluation Error: {e}")
            return EvaluationResult(
                decision="block",
                reason=f"Evaluation Error: {str(e)}",
                diagnostics=[str(e)]
            )
