# Role System Architecture Principle

## The Core Problem

**Hardcoded roles in infrastructure = business logic leakage**

When a governance system ships with:
```yaml
role_overrides:
  admin: ALL
  analyst: P3_Low
```

It makes dangerous assumptions:
- You have an "admin" role
- You have an "analyst" role  
- "admin" should bypass security
- Your org structure matches this hierarchy

**This is wrong.**

---

## What Roles Actually Are

Roles are **not** governance primitives.

**Tiers** are governance primitives.

Roles are **modifiers** on tier enforcement.

```
Tier System (Core):
  P0_Critical → Block
  P1_High → Block
  
Role System (Optional Layer):
  IF role == "trusted_analyst"
  THEN allow P1_High
```

Roles are metadata from the caller, not policy.

---

## The Correct Default State

### Minimal Config (No Roles)
```yaml
version: 1
template: balanced
blocked_tiers:
  - P0_Critical
  - P1_High
role_overrides: {}  # Empty by default
low_confidence:
  threshold: 0.4
  clamp_tier: P3_Low
```

**Why this is correct:**
- No business assumptions
- Pure tier enforcement
- Role system is opt-in
- Infrastructure stays neutral

---

## Role System as Optional Capability

Roles should be **explicitly enabled**, not assumed.

### Proposed Flow

**Default behavior:**
```bash
$ ./guardrail init
# Creates policy with role_overrides: {}
```

**Enabling roles:**
```bash
$ ./guardrail roles enable
Role system enabled. Add roles with:
  ./guardrail roles add <name> <tier|ALL>
```

**Adding roles:**
```bash
$ ./guardrail roles add analyst P3_Low
$ ./guardrail roles add admin ALL
```

This makes role usage **explicit and intentional**.

---

## Why "admin: ALL" is Dangerous

```yaml
role_overrides:
  admin: ALL
```

This line implies:
- Some users can bypass all security
- The system trusts the "admin" attribute
- No validation of role claims

**In enterprise:** Fine (internal identity system)
**In public API:** Liability (anyone can claim role="admin")

**Solution:** Don't ship with bypass accounts.

If users need bypass, they add it explicitly:
```bash
$ ./guardrail roles add admin ALL
⚠ Warning: This role bypasses all security checks.
Continue? [y/N]
```

---

## Role Validation (Future)

Right now roles are just strings.

Better architecture:
```
Role = caller attribute enforced by host system
```

Guardrail should **validate** roles, not **define** them.

### Possible Enhancement
```yaml
role_validation:
  enabled: true
  method: jwt  # or header_signature, or external_service
  jwt_secret: <secret>
```

Then:
```python
# Caller must provide signed JWT
headers = {"Authorization": "Bearer <jwt_with_role_claim>"}
```

This separates:
- **Identity** (external system)
- **Policy** (guardrail)

---

## The Identity Question

**Is Guardrail:**
1. A policy engine? (tier enforcement only)
2. An identity-aware governance system? (role validation + tier enforcement)

**Current state:** Half-committed to #2 without full infrastructure.

**Recommendation:** 
- Core = #1 (policy engine)
- Roles = optional metadata (no validation)
- Future = #2 (with proper identity validation)

---

## Clean Layered Architecture

### Layer 1: Tier Enforcement (Core)
```
Input → Detect tier → Check blocked_tiers → Allow/Block
```

No roles. Pure tier logic.

### Layer 2: Role Modifiers (Optional)
```
Input + Role → Detect tier → Check role_overrides → Check blocked_tiers → Allow/Block
```

Roles modify tier enforcement.

### Layer 3: Identity Validation (Future)
```
Input + Signed Role → Validate signature → Detect tier → Check role_overrides → Allow/Block
```

Roles are cryptographically verified.

---

## Implementation Changes

### ✅ Completed
- Removed hardcoded roles from presets
- `role_overrides: {}` by default
- YAML shows `{}  # No role overrides (tier enforcement only)`
- Removed "admin has full access" warnings
- Policy summary shows "Role system: disabled" when empty

### 🚧 Future Enhancements
- `./guardrail roles enable` command
- `./guardrail roles add <name> <tier>` command
- `./guardrail roles list` command
- Warning prompt when adding `ALL` bypass
- Optional JWT validation for role claims

---

## The Psychological Effect

**Before (with hardcoded roles):**
```yaml
role_overrides:
  admin: ALL
  analyst: P3_Low
```
Developer thinks: *"This assumes too much about my system."*

**After (empty by default):**
```yaml
role_overrides: {}  # No role overrides (tier enforcement only)
```
Developer thinks: *"Okay, it's neutral. I can add roles if I need them."*

**Trust increases.**

---

## Key Principles

1. **Infrastructure must assume nothing** about business logic
2. **Roles are not governance primitives** (tiers are)
3. **Role system is optional**, not required
4. **Bypass accounts should never be implicit**
5. **Identity validation is separate** from policy enforcement

---

## Bottom Line

**Governance that hardcodes business logic loses trust.**

**Governance that stays neutral gets adopted.**

Roles are now opt-in, not assumed.

That's cleaner engineering.
