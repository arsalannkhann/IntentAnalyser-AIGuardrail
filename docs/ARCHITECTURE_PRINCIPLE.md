# Architecture Principle: Hardened Modes as Foundation

## The Core Principle

**Predefined modes are product.**  
**LLM assistance is UX sugar.**

Never flip this order.

---

## Why Predefined Modes Win

### 1. Governance Must Be Boring

Would you let an LLM configure:
- AWS IAM policies?
- Firewall rules?
- Database write permissions?

**No.**

You might let it **draft**.  
But you **review and compile**.

Same principle here.

### 2. The Stability Hierarchy

```
┌─────────────────────────────────┐
│   Hardened Predefined Modes     │  ← Source of Truth
│   (strict, balanced, permissive)│  ← Audited, tested, stable
└─────────────────────────────────┘
              ↑
              │ generates
              │
┌─────────────────────────────────┐
│   Structured Config Model       │  ← Type-safe, validated
│   (PolicyConfig dataclass)      │  ← Deterministic
└─────────────────────────────────┘
              ↑
              │ compiles to
              │
┌─────────────────────────────────┐
│   Cedar Policy Language         │  ← Formal verification
│   (main.cedar)                  │  ← Runtime enforcement
└─────────────────────────────────┘
```

**LLM sits ABOVE this stack, not in it.**

---

## The Correct Architecture (Hybrid)

### Flow

```
User describes intent
    ↓
LLM maps to closest preset + suggested modifications
    ↓
User confirms
    ↓
System generates deterministic YAML from structured config model
```

**The LLM suggests.**  
**Your engine decides.**

That's safe.

---

## What We Built

### Layer 1: Hardened Modes (Foundation)

```bash
./guardrail init --mode public-chatbot
./guardrail init --mode internal-assistant
./guardrail init --mode analyst-tool
```

**These are:**
- Audited
- Tested
- Documented
- Stable
- Predictable

**Not:**
- LLM-generated
- User-invented
- Randomly configured

### Layer 2: Structured Modifications

```python
config = preset_policy_config("balanced")
config.blocked_tiers.append("P2_Medium")  # Structured
config.role_overrides["admin"] = "ALL"    # Type-safe
```

**Not:**
```yaml
# Raw YAML editing
blocked_tiers:
  - P0_Critcal  # Typo!
  - P1_Hihg     # Typo!
```

### Layer 3: Deterministic Compilation

```python
PolicyService.save(config, yaml_path, cedar_path)
```

**Guarantees:**
- Valid YAML
- Valid Cedar
- Consistent semantics
- No drift

---

## Why LLM-Generated YAML Fails

### Problem 1: Inconsistency

```yaml
# LLM might generate:
blocked_tiers:
  - critical
  - high
  - medium

# Or:
blocked_tiers:
  - P0
  - P1
  - P2

# Or:
blocked_tiers:
  - jailbreak
  - pii
  - toxic
```

**No standardization.**

### Problem 2: Hidden Drift

```yaml
# Week 1
low_confidence:
  threshold: 0.4

# Week 2 (LLM regenerates)
low_confidence:
  threshold: 0.45

# Week 3
low_confidence:
  threshold: 0.38
```

**Policy changes without intent.**

### Problem 3: No Audit Trail

```
Who changed the policy?
Why was it changed?
What was the old value?
```

**LLM-generated configs have no provenance.**

### Problem 4: Enterprise Distrust

```
"Our security policy is AI-generated."
```

**No enterprise will accept this.**

---

## Long-Term Scalability

### Predefined Modes Give You

✅ **Standardization** - Everyone speaks same language  
✅ **Shared vocabulary** - "balanced" means same thing everywhere  
✅ **Easier onboarding** - New devs pick a mode, done  
✅ **Enterprise confidence** - Audited, tested, stable  
✅ **Compliance** - Can certify specific modes  
✅ **Support** - Can debug "balanced mode" issues  

### LLM-Generated YAML Gives You

❌ **Chaos** - Every config is unique  
❌ **Inconsistency** - No two configs match  
❌ **Hidden drift** - Policies change unexpectedly  
❌ **No audit trail** - Can't track changes  
❌ **Support nightmare** - Can't debug unique configs  
❌ **Compliance risk** - Can't certify AI-generated policies  

---

## What Investors Trust

### Option A: Predefined Modes
```
"We have 4 hardened security modes:
- Public-facing (strict)
- Internal (balanced)
- Analyst (permissive)
- Custom (advanced)

Each mode is audited, tested, and certified."
```

**Investor reaction:** ✅ Confident

### Option B: LLM-Generated
```
"Our AI generates custom security policies
based on natural language descriptions."
```

**Investor reaction:** ❌ Concerned

---

## The Right Hybrid Approach

### What We Ship

**Core Product:**
- 4 hardened modes
- Structured config model
- Deterministic compilation
- Type-safe modifications

**UX Sugar (Future):**
- LLM assistant that suggests changes
- Natural language policy explanation
- Tradeoff analysis
- Impact prediction

**The LLM never writes raw YAML directly.**

---

## Future: LLM Assistant (Safe)

### User Flow

```
User: "I need to block toxic language but allow financial advice"

LLM: "I recommend starting with 'balanced' mode and:
      - Enable P2_Medium (toxic language)
      - Keep P3_Low disabled (financial advice)
      
      This will block:
      ✓ Jailbreaks
      ✓ PII theft
      ✓ Toxic language
      
      But allow:
      ✓ Financial advice
      ✓ General queries
      
      Tradeoff: May miss some edge cases in toxicity.
      
      Apply this configuration?"

User: "Yes"

System: Generates structured PolicyConfig
        Validates
        Compiles to Cedar
        Saves deterministically
```

**LLM suggests. Engine decides. User confirms.**

---

## Implementation Status

### ✅ Built (Foundation)

1. **Hardened modes** - public-chatbot, internal-assistant, analyst-tool
2. **Structured config** - PolicyConfig dataclass
3. **Deterministic compilation** - PolicyService
4. **Type-safe modifications** - Python API
5. **Validation** - Schema enforcement
6. **Cedar compilation** - Formal policy language

### 🔮 Future (UX Sugar)

1. **LLM assistant** - Suggests configurations
2. **Natural language** - Explains policies
3. **Impact analysis** - Predicts changes
4. **Tradeoff explanation** - Shows pros/cons

**Foundation is solid. Sugar can be added safely.**

---

## Key Architectural Decisions

### Decision 1: Modes Are Immutable

```python
# Good: Start from preset
config = preset_policy_config("balanced")
config.blocked_tiers.append("P2_Medium")

# Bad: Invent from scratch
config = PolicyConfig(
    blocked_tiers=["something", "random"],
    ...
)
```

### Decision 2: Modifications Are Structured

```python
# Good: Type-safe API
config.blocked_tiers.append("P2_Medium")

# Bad: String manipulation
yaml_str += "\n  - P2_Medium"
```

### Decision 3: Compilation Is Deterministic

```python
# Always produces same output for same input
PolicyService.save(config, yaml_path, cedar_path)
```

### Decision 4: LLM Is Advisory Only

```python
# LLM suggests
suggestion = llm.suggest_config(user_intent)

# User confirms
if user.confirms(suggestion):
    # Engine decides
    config = build_config_from_suggestion(suggestion)
    PolicyService.save(config, ...)
```

---

## Why This Matters

### For Security

**Predefined modes:**
- Can be audited
- Can be certified
- Can be tested
- Have known properties

**LLM-generated configs:**
- Cannot be audited (infinite variations)
- Cannot be certified (non-deterministic)
- Cannot be tested (too many combinations)
- Have unknown properties

### For Operations

**Predefined modes:**
- Easy to debug ("balanced mode issue")
- Easy to support (known configurations)
- Easy to document (finite set)

**LLM-generated configs:**
- Hard to debug (unique snowflakes)
- Hard to support (infinite variations)
- Hard to document (can't enumerate)

### For Adoption

**Predefined modes:**
- Easy to understand ("public-chatbot")
- Easy to choose (3-4 options)
- Easy to trust (audited)

**LLM-generated configs:**
- Hard to understand (what did it generate?)
- Hard to choose (infinite options)
- Hard to trust (AI-generated security?)

---

## The Bottom Line

**Governance must be boring and predictable at its core.**

**Innovation can sit on top. Not underneath.**

---

## Comparison: Other Systems

### AWS IAM

**Foundation:** Predefined policies (ReadOnly, PowerUser, Admin)  
**Customization:** Structured JSON with validation  
**LLM:** Can suggest, never generates directly  

### Kubernetes RBAC

**Foundation:** Predefined roles (view, edit, admin)  
**Customization:** Structured YAML with schema  
**LLM:** Not in the loop  

### Firewall Rules

**Foundation:** Predefined profiles (strict, moderate, permissive)  
**Customization:** Structured rule language  
**LLM:** Advisory only  

**Same pattern everywhere.**

---

## Our Implementation

### Foundation (Solid)

```bash
./guardrail init --mode public-chatbot
```

Generates:
- Validated YAML
- Compiled Cedar
- Deterministic output
- Auditable config

### Customization (Structured)

```bash
./guardrail policy edit
```

Modifies:
- Through type-safe API
- With validation
- With warnings
- With simulation

### Future: LLM (Advisory)

```bash
./guardrail suggest "block toxic but allow finance"
```

Would:
- Map to closest mode
- Suggest modifications
- Explain tradeoffs
- Wait for confirmation
- Generate deterministically

**Never writes YAML directly.**

---

## Strategic Positioning

**We are not:**
- "AI-generated security policies"
- "Natural language firewall"
- "LLM-configured guardrails"

**We are:**
- "Hardened security modes with AI assistance"
- "Predefined policies with smart suggestions"
- "Deterministic governance with LLM UX"

**The difference matters for enterprise sales.**

---

## Summary

✅ **Ship:** Hardened modes as foundation  
✅ **Allow:** Structured modifications  
✅ **Provide:** Advanced editor  
🔮 **Add:** LLM assistant that suggests (never generates)  

**Governance is product.**  
**LLM is UX sugar.**  

**Never flip this order.**

---

**Architecture Date:** 2024  
**Status:** Foundation Complete  
**Next:** LLM advisory layer (optional)
