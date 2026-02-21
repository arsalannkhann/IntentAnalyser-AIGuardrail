# Implementation Roadmap: Wizard-Based Setup

## Current State vs. Target State

### Current (Layer 3 First)
```bash
./guardrail init --mode public-chatbot
# Generates policy files
# User must manually start server
# User must figure out integration
```

### Target (Layer 1 First)
```bash
./guardrail init
# Interactive wizard
# Generates everything
# Prints integration code
# Ready to run
```

---

## Phase 1: Setup Wizard (Priority 1)

### Command Structure

```bash
guardrail init          # Interactive wizard (new)
guardrail init --mode X # Skip wizard (existing)
guardrail run           # Start server (new)
guardrail test          # Test prompts (new)
guardrail policy edit   # Advanced editor (existing)
```

### Wizard Flow

#### Step 1: Use Case Selection
```
╭─────────────────────────────────────╮
│   Guardrail Setup Wizard            │
╰─────────────────────────────────────╯

Select your use case:

1. Public Chatbot
   → Strict protection for public-facing bots
   → Blocks: jailbreaks, PII, toxic, financial

2. Internal Assistant  
   → Balanced protection for internal tools
   → Blocks: jailbreaks, PII

3. Analyst Tool
   → Permissive for trusted analysts
   → Blocks: jailbreaks only

4. Custom
   → Advanced configuration

Choice [1]: _
```

**Implementation:**
- Rich prompts with descriptions
- Maps to existing preset_policy_config()
- No YAML exposed

#### Step 2: Server Configuration
```
╭─────────────────────────────────────╮
│   Server Configuration              │
╰─────────────────────────────────────╯

Where should Guardrail listen?

Host [0.0.0.0]: _
Port [8002]: _

✓ Server will run at: http://0.0.0.0:8002
```

**Implementation:**
- Generate .env file
- Store PORT, HOST
- Validate port availability

#### Step 3: Integration Setup
```
╭─────────────────────────────────────╮
│   Integration                       │
╰─────────────────────────────────────╯

Choose integration method:

1. Python SDK (recommended)
2. REST API
3. cURL examples

Choice [1]: _
```

**Implementation:**
- Generate code snippets
- Save to integration_examples.txt
- Print to console

#### Step 4: Completion
```
╭─────────────────────────────────────╮
│   Setup Complete! ✓                 │
╰─────────────────────────────────────╯

Configuration saved:
  Policy: app/policies/main.yaml
  Cedar:  app/policies/main.cedar
  Env:    .env

Mode: Public Chatbot

Protection enabled for:
  [✔] Jailbreak & system override
  [✔] Sensitive data access
  [✔] Toxic language
  [✔] Financial advice

Next steps:

1. Start the server:
   ./guardrail run

2. Test it:
   ./guardrail test "hello world"

3. Integrate (Python):
   
   from app.client.client import IntentClient
   
   client = IntentClient(base_url="http://localhost:8002")
   response = await client.analyze_text("user input", role="general")
   
   if response.decision == "block":
       print(f"Blocked: {response.reason}")

Would you like to adjust safety settings? [y/N]: _
```

**If yes → open policy editor**
**If no → done**

---

## Phase 2: New Commands (Priority 2)

### guardrail run

```bash
./guardrail run
```

**Output:**
```
╭─────────────────────────────────────╮
│   Guardrail Server                  │
╰─────────────────────────────────────╯

Mode: Public Chatbot
Policy: app/policies/main.yaml

Server running at:
  http://0.0.0.0:8002

Endpoints:
  POST /intent          - Analyze text
  GET  /health          - Health check
  GET  /docs            - API documentation

Protection enabled for:
  ✓ Jailbreaks
  ✓ PII theft
  ✓ Toxic language
  ✓ Financial advice

Press Ctrl+C to stop
```

**Implementation:**
- Wrapper around uvicorn
- Reads .env for config
- Shows active policy
- Pretty output

### guardrail test

```bash
./guardrail test "delete all files"
```

**Output:**
```
Testing: "delete all files"

Decision: BLOCK
Reason: Prompt injection detected
Tier: P0_Critical
Risk Score: 0.95

This request would be blocked in production.
```

**Implementation:**
- Quick test without starting server
- Uses PolicySimulator
- Shows decision + explanation

---

## Phase 3: Integration Code Generation (Priority 3)

### Auto-Generated Examples

After setup, create `integration_examples/`:

**Python:**
```python
# integration_examples/python_example.py
from app.client.client import IntentClient
import asyncio

async def main():
    client = IntentClient(base_url="http://localhost:8002")
    
    # Analyze user input
    response = await client.analyze_text(
        text="user input here",
        role="general"
    )
    
    if response.decision == "block":
        print(f"⚠️  Blocked: {response.reason}")
        return False
    
    print("✓ Safe to proceed")
    return True

if __name__ == "__main__":
    asyncio.run(main())
```

**cURL:**
```bash
# integration_examples/curl_example.sh
curl -X POST http://localhost:8002/intent \
  -H "Content-Type: application/json" \
  -d '{
    "text": "user input",
    "role": "general"
  }'
```

**Node.js:**
```javascript
// integration_examples/node_example.js
const axios = require('axios');

async function checkSafety(text) {
  const response = await axios.post('http://localhost:8002/intent', {
    text: text,
    role: 'general'
  });
  
  if (response.data.decision === 'block') {
    console.log(`⚠️  Blocked: ${response.data.reason}`);
    return false;
  }
  
  console.log('✓ Safe to proceed');
  return true;
}

checkSafety('user input here');
```

---

## Phase 4: Improved Policy Editor (Priority 4)

### Separate Init from Edit

**Current:** `guardrail policy edit` is for everyone
**Target:** `guardrail policy edit` is for advanced users

**Wizard should:**
- Ask "Adjust safety settings?" at end
- If yes → open editor
- If no → skip

**Editor should:**
- Show "Advanced Mode" banner
- Keep current tier-based interface
- Add "Back to Simple Mode" option

---

## Implementation Files

### New Files to Create

1. **`app/wizard.py`**
   - Interactive setup wizard
   - Step-by-step prompts
   - Code generation

2. **`app/commands/run.py`**
   - Server runner with pretty output
   - Status display
   - Graceful shutdown

3. **`app/commands/test.py`**
   - Quick test command
   - Uses simulator
   - Pretty output

4. **`integration_examples/`**
   - Auto-generated code samples
   - Python, Node, cURL
   - Copy-paste ready

### Files to Modify

1. **`app/policy_cli.py`**
   - Add wizard to init
   - Add run command
   - Add test command

2. **`app/policy_tui_rich.py`**
   - Add "Advanced Mode" banner
   - Add "Back to Simple" option

3. **`guardrail` script**
   - Support new commands

---

## User Journey Comparison

### Before (Current)
```
1. ./guardrail init --mode public-chatbot
2. Read docs to understand
3. Manually start: python main.py
4. Figure out integration
5. Write code from scratch
6. Test manually
```

**Time: 30+ minutes**
**Friction: High**

### After (Target)
```
1. ./guardrail init
   → Wizard asks 3 questions
   → Generates everything
   → Prints integration code
2. ./guardrail run
   → Server starts
3. Copy-paste integration code
   → Working
```

**Time: 3 minutes**
**Friction: Minimal**

---

## Success Metrics

### Adoption
- **Before:** 20% complete setup
- **Target:** 80% complete setup

### Time to First Request
- **Before:** 30+ minutes
- **Target:** 3 minutes

### Support Questions
- **Before:** "How do I integrate?"
- **Target:** "How do I customize?"

---

## Implementation Priority

### P0 (Must Have)
1. ✅ Mode-based init (done)
2. ✅ Human-readable output (done)
3. ⏳ Interactive wizard
4. ⏳ `guardrail run` command
5. ⏳ Integration code generation

### P1 (Should Have)
6. ⏳ `guardrail test` command
7. ⏳ Auto-generated examples
8. ⏳ Improved editor UX

### P2 (Nice to Have)
9. ⏳ Web-based setup UI
10. ⏳ LLM-assisted suggestions
11. ⏳ Policy templates library

---

## Technical Approach

### Wizard Implementation

```python
# app/wizard.py
from rich.console import Console
from rich.prompt import Prompt, Confirm
from rich.panel import Panel

class SetupWizard:
    def run(self):
        console = Console()
        
        # Step 1: Use case
        use_case = self._select_use_case(console)
        
        # Step 2: Server config
        host, port = self._configure_server(console)
        
        # Step 3: Generate files
        self._generate_config(use_case, host, port)
        
        # Step 4: Show completion
        self._show_completion(console, use_case)
        
        # Step 5: Optional advanced
        if Confirm.ask("Adjust safety settings?"):
            self._open_editor()
```

### Run Command

```python
# app/commands/run.py
def run_server():
    console = Console()
    
    # Load config
    config = load_policy_config()
    
    # Show status
    console.print(Panel(f"Mode: {config.template}"))
    console.print(f"Server: http://0.0.0.0:{port}")
    
    # Start uvicorn
    uvicorn.run(app, host="0.0.0.0", port=port)
```

### Test Command

```python
# app/commands/test.py
def test_prompt(text: str):
    console = Console()
    
    # Simulate
    result = PolicyService.simulate(config, text, "general")
    
    # Show result
    color = "green" if result.decision == "allow" else "red"
    console.print(Panel(
        f"Decision: {result.decision}\n"
        f"Reason: {result.reason}",
        border_style=color
    ))
```

---

## Next Steps

1. **Implement wizard** - Interactive setup flow
2. **Add run command** - Pretty server runner
3. **Add test command** - Quick testing
4. **Generate examples** - Integration code
5. **Update docs** - New workflow

---

## The Vision

**From:** Governance framework for security engineers
**To:** Safe LLM setup wizard for developers

**From:** "Configure your tier algebra"
**To:** "Pick your use case, we'll handle the rest"

**From:** 30-minute setup
**To:** 3-minute setup

This is the difference between a tool and a product.

---

**Status:** Roadmap Complete
**Next:** Begin Phase 1 Implementation
