// -----------------------------------------------------------------------------
// Guardrail Policy (generated) — edit app/policies/main.yaml
// -----------------------------------------------------------------------------
// Signal Contract (policy-visible context):
//   - override_detected: bool
//   - pii_detected: bool
//   - toxicity_detected: bool
//   - toxicity_enforce_block: bool
//   - financial_advice_detected: bool
//   - low_confidence: bool
//   - intent: string
//
// Template: strict
// Low confidence threshold: 0.5
// Low confidence clamp tier: P2_Medium

// Rule 1 — Critical Override Block (P0_Critical)
forbid (
    principal,
    action,
    resource
)
when {
    context.override_detected == true
};

// Rule 2 — PII Protection Block (P1_High)
forbid (
    principal,
    action,
    resource
)
when {
    context.pii_detected == true
};

// Rule 3 — Toxicity Guard Block (P2_Medium)
forbid (
    principal,
    action,
    resource
)
when {
    context.toxicity_detected == true &&
    context.toxicity_enforce_block == true
};

// Rule 4 — Financial Advice Block (P3_Low)
forbid (
    principal,
    action,
    resource
)
when {
    context.financial_advice_detected == true
};

// Rule 5 — Low Confidence Clamp
forbid (
    principal,
    action,
    resource
)
when {
    context.low_confidence == true
};

// Baseline allow when no deny rules matched.
permit (
    principal,
    action,
    resource
);
