# Documentation Index 📚

Complete guide to Intent Analyzer Guardrail documentation.

---

## 🚀 Getting Started

**New to the project? Start here:**

1. **[README.md](../README.md)** - Project overview and quick start
2. **[CHEATSHEET.md](CHEATSHEET.md)** - Quick reference for common commands
3. **[CLI_GUIDE.md](CLI_GUIDE.md)** - Detailed command-line documentation

---

## 📖 Documentation by Topic

### Command-Line Interface

| Document | Description | Audience |
|----------|-------------|----------|
| [CLI_GUIDE.md](CLI_GUIDE.md) | Complete CLI reference with all commands and examples | All users |
| [CHEATSHEET.md](CHEATSHEET.md) | One-page quick reference | All users |

### Workflows & Patterns

| Document | Description | Audience |
|----------|-------------|----------|
| [WORKFLOWS.md](WORKFLOWS.md) | Visual guides for common usage patterns | All users |

### Architecture & Design

| Document | Description | Audience |
|----------|-------------|----------|
| [tutorial.md](tutorial.md) | Step-by-step architecture guide | Developers |
| [architecture_demo.md](architecture_demo.md) | Detailed request processing trace | Developers |

---

## 🎯 Documentation by Use Case

### I want to...

**...get started quickly**
→ [README.md](../README.md) → Quick Start section

**...understand all available commands**
→ [CLI_GUIDE.md](CLI_GUIDE.md)

**...look up a specific command**
→ [CHEATSHEET.md](CHEATSHEET.md)

**...set up a new environment**
→ [WORKFLOWS.md](WORKFLOWS.md) → Initial Setup Workflow

**...modify policy configuration**
→ [WORKFLOWS.md](WORKFLOWS.md) → Policy Development Workflow  
→ [CLI_GUIDE.md](CLI_GUIDE.md) → Policy Management section

**...integrate the API into my application**
→ [CLI_GUIDE.md](CLI_GUIDE.md) → Integration Examples  
→ [WORKFLOWS.md](WORKFLOWS.md) → API Integration Workflow

**...deploy to production**
→ [WORKFLOWS.md](WORKFLOWS.md) → Deployment Workflow  
→ [CLI_GUIDE.md](CLI_GUIDE.md) → Environment Configuration

**...troubleshoot issues**
→ [WORKFLOWS.md](WORKFLOWS.md) → Troubleshooting Workflow  
→ [CLI_GUIDE.md](CLI_GUIDE.md) → Troubleshooting section

**...understand the architecture**
→ [tutorial.md](tutorial.md)  
→ [architecture_demo.md](architecture_demo.md)

**...test my changes**
→ [WORKFLOWS.md](WORKFLOWS.md) → Testing Workflow  
→ [CLI_GUIDE.md](CLI_GUIDE.md) → Testing & Validation

**...manage role overrides**
→ [WORKFLOWS.md](WORKFLOWS.md) → Role Override Workflow  
→ [CLI_GUIDE.md](CLI_GUIDE.md) → Policy Configuration

---

## 📋 Quick Reference Tables

### All Commands

| Command | Purpose | Doc Reference |
|---------|---------|---------------|
| `./guardrail init` | Initialize policy files | [CLI_GUIDE.md](CLI_GUIDE.md#initialize-policy) |
| `./guardrail policy edit` | Interactive policy editor | [CLI_GUIDE.md](CLI_GUIDE.md#policy-editor-interactive-tui) |
| `./guardrail policy validate` | Validate policy | [CLI_GUIDE.md](CLI_GUIDE.md#validate-policy) |
| `./guardrail policy simulate` | Test policy decision | [CLI_GUIDE.md](CLI_GUIDE.md#simulate-decision) |
| `./guardrail policy show` | Display policy summary | [CLI_GUIDE.md](CLI_GUIDE.md#show-policy-summary) |
| `./guardrail policy export` | Export Cedar policy | [CLI_GUIDE.md](CLI_GUIDE.md#export-cedar-policy) |
| `python main.py` | Start API server | [CLI_GUIDE.md](CLI_GUIDE.md#start-api-server) |

### Risk Tiers

| Tier | Risk Level | Doc Reference |
|------|-----------|---------------|
| P0_Critical | 🔴 Critical | [README.md](../README.md#-critical-block-immediately) |
| P1_High | 🟠 High | [README.md](../README.md#-high-reviewblock) |
| P2_Medium | 🟡 Medium | [README.md](../README.md#-medium-flag) |
| P3_Low | 🔵 Low | [README.md](../README.md#-low-allow) |
| P4_Info | ⚪ Info | [README.md](../README.md#-low-allow) |

### Policy Templates

| Template | Blocked Tiers | Doc Reference |
|----------|--------------|---------------|
| strict | P0, P1, P2, P3 | [CLI_GUIDE.md](CLI_GUIDE.md#templates) |
| balanced | P0, P1 | [CLI_GUIDE.md](CLI_GUIDE.md#templates) |
| permissive | P0 | [CLI_GUIDE.md](CLI_GUIDE.md#templates) |

---

## 🔍 Search by Keyword

### API
- [CLI_GUIDE.md](CLI_GUIDE.md) → API Endpoints
- [CLI_GUIDE.md](CLI_GUIDE.md) → Integration Examples
- [WORKFLOWS.md](WORKFLOWS.md) → API Integration Workflow

### Cedar
- [CLI_GUIDE.md](CLI_GUIDE.md) → Export Cedar Policy
- [README.md](../README.md) → System Architecture

### Docker
- [CLI_GUIDE.md](CLI_GUIDE.md) → Server Commands → Docker
- [WORKFLOWS.md](WORKFLOWS.md) → Deployment Workflow

### Environment Variables
- [CLI_GUIDE.md](CLI_GUIDE.md) → Environment Configuration
- [CHEATSHEET.md](CHEATSHEET.md) → Environment

### Policy
- [CLI_GUIDE.md](CLI_GUIDE.md) → Policy Management
- [WORKFLOWS.md](WORKFLOWS.md) → Policy Development Workflow
- [WORKFLOWS.md](WORKFLOWS.md) → Policy Update Workflow

### Python SDK
- [CLI_GUIDE.md](CLI_GUIDE.md) → Integration Examples → Python SDK
- [README.md](../README.md) → Integration (Python SDK)

### Role Overrides
- [CLI_GUIDE.md](CLI_GUIDE.md) → Policy Configuration
- [WORKFLOWS.md](WORKFLOWS.md) → Role Override Workflow

### Simulation
- [CLI_GUIDE.md](CLI_GUIDE.md) → Simulate Decision
- [WORKFLOWS.md](WORKFLOWS.md) → Testing Workflow

### Testing
- [CLI_GUIDE.md](CLI_GUIDE.md) → Testing & Validation
- [WORKFLOWS.md](WORKFLOWS.md) → Testing Workflow

### TUI (Terminal UI)
- [CLI_GUIDE.md](CLI_GUIDE.md) → Policy Editor
- [WORKFLOWS.md](WORKFLOWS.md) → Policy Development Workflow
- [CHEATSHEET.md](CHEATSHEET.md) → CLI Editor Commands

### Troubleshooting
- [CLI_GUIDE.md](CLI_GUIDE.md) → Troubleshooting
- [WORKFLOWS.md](WORKFLOWS.md) → Troubleshooting Workflow

---

## 📊 Documentation Hierarchy

```
IntentAnalyser-AIGuardrail/
│
├── README.md                    # Project overview
│
└── docs/
    ├── INDEX.md                 # This file
    │
    ├── Quick Reference
    │   ├── CHEATSHEET.md        # One-page reference
    │   └── CLI_GUIDE.md         # Complete CLI docs
    │
    ├── Guides
    │   └── WORKFLOWS.md         # Visual workflow guides
    │
    └── Architecture
        ├── tutorial.md          # Architecture guide
        └── architecture_demo.md # Request processing trace
```

---

## 🎓 Learning Paths

### Path 1: Quick Start User
```
1. README.md (Quick Start)
2. CHEATSHEET.md
3. CLI_GUIDE.md (as needed)
```

### Path 2: Policy Administrator
```
1. README.md (System Architecture)
2. CLI_GUIDE.md (Policy Management)
3. WORKFLOWS.md (Policy Development)
4. WORKFLOWS.md (Policy Update)
```

### Path 3: Application Developer
```
1. README.md (Integration)
2. CLI_GUIDE.md (Integration Examples)
3. WORKFLOWS.md (API Integration)
4. tutorial.md (Architecture)
```

### Path 4: System Architect
```
1. README.md (System Architecture)
2. tutorial.md
3. architecture_demo.md
4. CLI_GUIDE.md (complete)
```

---

## 📝 Document Summaries

### README.md
**Length:** ~500 lines  
**Topics:** Overview, architecture, quick start, deployment  
**Best for:** First-time users, project overview

### CLI_GUIDE.md
**Length:** ~800 lines  
**Topics:** All commands, configuration, integration, troubleshooting  
**Best for:** Complete reference, detailed examples

### CHEATSHEET.md
**Length:** ~200 lines  
**Topics:** Quick command reference, common patterns  
**Best for:** Quick lookups, daily use

### WORKFLOWS.md
**Length:** ~600 lines  
**Topics:** Visual workflows, step-by-step guides  
**Best for:** Understanding processes, troubleshooting

### tutorial.md
**Length:** Variable  
**Topics:** Architecture deep-dive, design decisions  
**Best for:** Understanding internals

### architecture_demo.md
**Length:** Variable  
**Topics:** Request processing, execution flow  
**Best for:** Debugging, optimization

---

## 🔄 Document Maintenance

### When to Update

| Trigger | Update These Docs |
|---------|------------------|
| New command added | CLI_GUIDE.md, CHEATSHEET.md |
| New workflow | WORKFLOWS.md |
| Architecture change | tutorial.md, architecture_demo.md, README.md |
| New tier/policy | CLI_GUIDE.md, README.md |
| API change | CLI_GUIDE.md, README.md |
| Deployment change | CLI_GUIDE.md, WORKFLOWS.md |

---

## 📞 Getting Help

**Can't find what you need?**

1. Check this index for the right document
2. Use Ctrl+F to search within documents
3. Check the [Troubleshooting section](CLI_GUIDE.md#troubleshooting)
4. Review [Workflows](WORKFLOWS.md) for visual guides
5. Open a GitHub issue

---

## 🎯 Most Common Questions

**Q: How do I start the server?**  
A: [CLI_GUIDE.md → Server Commands](CLI_GUIDE.md#server-commands)

**Q: How do I edit policy?**  
A: [CLI_GUIDE.md → Policy Editor](CLI_GUIDE.md#policy-editor-interactive-tui)

**Q: What do the tiers mean?**  
A: [README.md → Taxonomy](../README.md#-taxonomy--capabilities)

**Q: How do I integrate the API?**  
A: [CLI_GUIDE.md → Integration Examples](CLI_GUIDE.md#integration-examples)

**Q: How do I test my policy?**  
A: [CLI_GUIDE.md → Simulate Decision](CLI_GUIDE.md#simulate-decision)

**Q: Server won't start, what do I do?**  
A: [WORKFLOWS.md → Troubleshooting](WORKFLOWS.md#7-troubleshooting-workflow)

**Q: How do role overrides work?**  
A: [WORKFLOWS.md → Role Override Workflow](WORKFLOWS.md#8-role-override-workflow)

**Q: How do I deploy to production?**  
A: [WORKFLOWS.md → Deployment Workflow](WORKFLOWS.md#5-deployment-workflow)

---

**Last Updated:** 2024  
**Version:** 4.0.0
