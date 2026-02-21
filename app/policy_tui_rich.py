from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt, Confirm
from rich.layout import Layout
from rich.live import Live
from rich.text import Text

from app.services.policy_config import TIER_ORDER, PolicyConfig, preset_policy_config
from app.services.policy_service import PolicyService


class PolicyEditorTUI:
    def __init__(self, config: PolicyConfig, config_path: Path, cedar_path: Path):
        self.config = config
        self.config_path = config_path
        self.cedar_path = cedar_path
        self.dirty = False
        self.console = Console()

    def run(self):
        while True:
            self.console.clear()
            self.render()
            
            cmd = Prompt.ask("\n[bold cyan]Command[/]", default="help").strip().lower()
            
            if cmd in ["q", "quit", "exit"]:
                if self.dirty and not Confirm.ask("[yellow]Unsaved changes. Quit anyway?[/]"):
                    continue
                break
            elif cmd in ["h", "help", "?"]:
                self.show_help()
            elif cmd in ["t", "template"]:
                self.edit_template()
            elif cmd in ["b", "blocked"]:
                self.edit_blocked()
            elif cmd in ["o", "override"]:
                self.add_override()
            elif cmd in ["x", "remove"]:
                self.remove_override()
            elif cmd in ["l", "lowconf"]:
                self.edit_lowconf()
            elif cmd in ["m", "simulate"]:
                self.simulate()
            elif cmd in ["s", "save"]:
                self.save()
            else:
                self.console.print(f"[red]Unknown command: {cmd}[/]")
                self.console.input("\nPress Enter to continue...")

    def render(self):
        # Header
        self.console.print(Panel.fit(
            "[bold cyan]Guardrail Policy Editor[/]",
            border_style="cyan"
        ))
        
        # Status with warnings
        state = "[green]saved[/]" if not self.dirty else "[yellow]unsaved[/]"
        effective_mode = self._get_effective_mode()
        self.console.print(f"Policy: [cyan]{self.config.template}[/] v{self.config.version} | State: {state} | Mode: {effective_mode}")
        self.console.print(f"File: [dim]{self.config_path}[/]")
        
        # Policy warnings
        warnings = self._get_policy_warnings()
        if warnings:
            for warning in warnings:
                self.console.print(f"[yellow]⚠ {warning}[/]")
        
        self.console.print()
        
        # Blocked Tiers
        blocked_table = Table(title="Blocked Tiers", show_header=False, box=None)
        tier_descriptions = {
            "P0_Critical": "Prompt injection, system override",
            "P1_High": "PII theft, credential access",
            "P2_Medium": "Toxicity, harassment",
            "P3_Low": "Financial advice, off-topic",
            "P4_Info": "General queries, greetings"
        }
        for tier in TIER_ORDER:
            status = "[green]✓[/]" if tier in self.config.blocked_tiers else "[dim]○[/]"
            color = {"P0_Critical": "red", "P1_High": "yellow", "P2_Medium": "magenta", 
                    "P3_Low": "blue", "P4_Info": "dim"}[tier]
            blocked_table.add_row(status, f"[{color}]{tier}[/]", f"[dim]{tier_descriptions[tier]}[/]")
        self.console.print(blocked_table)
        
        # Role Overrides
        self.console.print("\n[bold]Role Overrides:[/]")
        if self.config.role_overrides:
            for role, allowance in sorted(self.config.role_overrides.items()):
                self.console.print(f"  [cyan]{role}[/] → [green]{allowance}[/]")
        else:
            self.console.print("  [dim](none)[/]")
        
        # Low Confidence
        self.console.print(f"\n[bold]Low Confidence:[/] threshold={self.config.low_confidence_threshold} clamp={self.config.low_confidence_clamp_tier}")
        
        # Commands
        self.console.print("\n[dim]Commands: t=template b=blocked o=override x=remove l=lowconf m=simulate s=save q=quit h=help[/]")

    def show_help(self):
        self.console.print(Panel("""
[bold cyan]Commands:[/]

[bold]t[/] template  - Switch policy template
[bold]b[/] blocked   - Toggle blocked tiers
[bold]o[/] override  - Add/update role override
[bold]x[/] remove    - Remove role override
[bold]l[/] lowconf   - Set low-confidence settings
[bold]m[/] simulate  - Test policy decision
[bold]s[/] save      - Save policy
[bold]q[/] quit      - Exit editor
[bold]h[/] help      - Show this help
        """, title="Help", border_style="cyan"))
        self.console.input("\nPress Enter to continue...")

    def edit_template(self):
        self.console.print("\n[bold]Templates:[/]")
        self.console.print("1. [red]strict[/] - Block P0,P1,P2,P3")
        self.console.print("2. [yellow]balanced[/] - Block P0,P1")
        self.console.print("3. [green]permissive[/] - Block P0 only")
        self.console.print("4. [cyan]custom[/] - Keep current settings")
        
        choice = Prompt.ask("Select", choices=["1", "2", "3", "4", "strict", "balanced", "permissive", "custom"], default="2")
        
        template_map = {"1": "strict", "2": "balanced", "3": "permissive", "4": "custom"}
        template = template_map.get(choice, choice)
        
        if template in ["strict", "balanced", "permissive"]:
            self.config = preset_policy_config(template)
        else:
            self.config.template = "custom"
        
        self.dirty = True

    def edit_blocked(self):
        self.console.print("\n[bold]Toggle Blocked Tiers:[/]")
        for i, tier in enumerate(TIER_ORDER, 1):
            status = "✓" if tier in self.config.blocked_tiers else " "
            self.console.print(f"{i}. [{status}] {tier}")
        
        choice = Prompt.ask("Enter tier numbers to toggle (comma-separated)", default="")
        if not choice:
            return
        
        for token in choice.split(","):
            token = token.strip()
            if token.isdigit() and 1 <= int(token) <= len(TIER_ORDER):
                tier = TIER_ORDER[int(token) - 1]
                if tier in self.config.blocked_tiers:
                    self.config.blocked_tiers.remove(tier)
                else:
                    self.config.blocked_tiers.append(tier)
        
        self.config.template = "custom"
        self.dirty = True

    def add_override(self):
        role = Prompt.ask("\n[bold]Role name[/]")
        if not role:
            return
        
        self.console.print("\nAllowance:")
        self.console.print("0. ALL (bypass all blocks)")
        for i, tier in enumerate(TIER_ORDER, 1):
            self.console.print(f"{i}. {tier}")
        
        choice = Prompt.ask("Select", default="0")
        
        if choice == "0":
            allowance = "ALL"
        elif choice.isdigit() and 1 <= int(choice) <= len(TIER_ORDER):
            allowance = TIER_ORDER[int(choice) - 1]
        else:
            self.console.print("[red]Invalid choice[/]")
            self.console.input("Press Enter...")
            return
        
        self.config.role_overrides[role] = allowance
        self.config.template = "custom"
        self.dirty = True

    def remove_override(self):
        if not self.config.role_overrides:
            self.console.print("\n[yellow]No overrides to remove[/]")
            self.console.input("Press Enter...")
            return
        
        self.console.print("\n[bold]Current Overrides:[/]")
        roles = list(self.config.role_overrides.keys())
        for i, role in enumerate(roles, 1):
            self.console.print(f"{i}. {role} → {self.config.role_overrides[role]}")
        
        choice = Prompt.ask("Select number to remove", default="")
        if choice.isdigit() and 1 <= int(choice) <= len(roles):
            role = roles[int(choice) - 1]
            del self.config.role_overrides[role]
            self.config.template = "custom"
            self.dirty = True

    def edit_lowconf(self):
        threshold = Prompt.ask("\n[bold]Threshold (0-1)[/]", default=str(self.config.low_confidence_threshold))
        try:
            threshold = float(threshold)
            if 0 <= threshold <= 1:
                self.config.low_confidence_threshold = threshold
            else:
                raise ValueError()
        except ValueError:
            self.console.print("[red]Invalid threshold[/]")
            self.console.input("Press Enter...")
            return
        
        self.console.print("\nClamp tier:")
        for i, tier in enumerate(TIER_ORDER, 1):
            self.console.print(f"{i}. {tier}")
        
        choice = Prompt.ask("Select", default="3")
        if choice.isdigit() and 1 <= int(choice) <= len(TIER_ORDER):
            self.config.low_confidence_clamp_tier = TIER_ORDER[int(choice) - 1]
        
        self.config.template = "custom"
        self.dirty = True

    def simulate(self):
        text = Prompt.ask("\n[bold]Input text[/]")
        if not text:
            return
        
        role = Prompt.ask("[bold]Role[/]", default="general")
        
        try:
            result = PolicyService.simulate(self.config, text, role)
            explanation = PolicyService.explain_decision(result, self.config)
            
            decision_color = "green" if result.decision == "allow" else "red"
            
            # Only show signals that influenced the decision
            influencing_signals = self._get_influencing_signals(result.signal_contract, explanation['policy_matches'])
            
            self.console.print(Panel(f"""
[bold]Decision:[/] [{decision_color}]{explanation['decision']}[/]
[bold]Tier:[/] {explanation['tier']}
[bold]Rule Applied:[/] {explanation['policy_matches']}
[bold]Influencing Signals:[/] {influencing_signals}
            """, title="Simulation Result", border_style=decision_color))
        except Exception as e:
            self.console.print(f"[red]Error: {e}[/]")
        
        self.console.input("\nPress Enter...")

    def save(self):
        try:
            PolicyService.save(self.config, self.config_path, self.cedar_path)
            self.config = PolicyService.normalize(self.config)
            self.dirty = False
            self.console.print("[green]✓ Saved successfully[/]")
        except Exception as e:
            self.console.print(f"[red]Save failed: {e}[/]")
        
        self.console.input("Press Enter...")

    def _get_effective_mode(self) -> str:
        blocked_count = len(self.config.blocked_tiers)
        if blocked_count == 0:
            return "[green]allow-all[/]"
        elif blocked_count == len(TIER_ORDER):
            return "[red]deny-all[/]"
        elif blocked_count >= 4:
            return "[yellow]strict[/]"
        elif blocked_count >= 2:
            return "[cyan]balanced[/]"
        else:
            return "[green]permissive[/]"

    def _get_policy_warnings(self) -> list[str]:
        warnings = []
        
        # All tiers blocked
        if len(self.config.blocked_tiers) == len(TIER_ORDER):
            warnings.append("All tiers blocked. System will deny all requests.")
        
        # No tiers blocked
        if len(self.config.blocked_tiers) == 0:
            warnings.append("No tiers blocked. System will allow all requests.")
        
        # P4 blocked (informational queries)
        if "P4_Info" in self.config.blocked_tiers:
            warnings.append("P4_Info blocked. Benign informational queries will be denied.")
        
        return warnings

    def _get_influencing_signals(self, signal_contract: dict, policy_matches: str) -> str:
        """Only show signals that actually influenced the decision"""
        if policy_matches == "none":
            return "none"
        
        influencing = []
        
        # Map policy matches to their signals
        if "blocked_tiers:P0_Critical" in policy_matches and signal_contract.get("override_detected"):
            influencing.append("override_detected")
        if "blocked_tiers:P1_High" in policy_matches and signal_contract.get("pii_detected"):
            influencing.append("pii_detected")
        if "blocked_tiers:P2_Medium" in policy_matches and signal_contract.get("toxicity_detected"):
            influencing.append("toxicity_detected")
        if "blocked_tiers:P3_Low" in policy_matches and signal_contract.get("financial_advice_detected"):
            influencing.append("financial_advice_detected")
        if "blocked_tiers:P4_Info" in policy_matches:
            influencing.append("info_query")
        if "low_confidence_clamp" in policy_matches:
            influencing.append("low_confidence")
        
        return ", ".join(influencing) if influencing else "none"


def run_policy_editor_rich(config_path: Path, cedar_path: Path, template: str) -> int:
    config = PolicyService.load(config_path, template)
    editor = PolicyEditorTUI(config, config_path, cedar_path)
    editor.run()
    return 0
