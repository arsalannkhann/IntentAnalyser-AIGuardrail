from __future__ import annotations

from pathlib import Path

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.widgets import Checkbox, Input, Select, Static

from app.services.policy_config import (
    ALLOW_ALL,
    ROLE_PATTERN,
    PolicyConfig,
    PolicyConfigError,
    TIER_ORDER,
    TIER_RANK,
)
from app.services.policy_service import PolicyService

BLOCKED_CHECKBOX_IDS = {tier: f"blocked-tier-{index}" for index, tier in enumerate(TIER_ORDER)}
CHECKBOX_ID_TO_TIER = {checkbox_id: tier for tier, checkbox_id in BLOCKED_CHECKBOX_IDS.items()}
TIER_STYLE_CLASS = {
    "P0_Critical": "tier-p0",
    "P1_High": "tier-p1",
    "P2_Medium": "tier-p2",
    "P3_Low": "tier-p3",
    "P4_Info": "tier-p4",
}


def run_policy_editor_textual(config_path: Path, cedar_path: Path, template: str) -> int:
    config = PolicyService.load(config_path, template)
    app = PolicyEditorTextualApp(config=config, config_path=config_path, cedar_path=cedar_path)
    app.run()
    return 0


class PolicyEditorTextualApp(App[None]):
    CSS = """
    Screen {
        background: #111418;
        color: #d0d4d8;
    }

    #root {
        layout: vertical;
        padding: 1 2;
        height: 1fr;
    }

    #title {
        color: #4c78a8;
        text-style: bold;
        margin-bottom: 1;
    }

    .section {
        border: solid #2a2f36;
        padding: 0 1;
        margin-bottom: 1;
    }

    .section-title {
        color: #7c8792;
        text-style: bold;
    }

    .meta-row {
        height: auto;
        layout: horizontal;
    }

    .meta-label {
        color: #7c8792;
        width: 10;
    }

    .meta-value {
        color: #d0d4d8;
    }

    #meta-state.state-saved {
        color: #4c8c6b;
    }

    #meta-state.state-unsaved {
        color: #c7a64a;
    }

    #blocked-section .tier-row {
        height: auto;
        layout: horizontal;
    }

    #blocked-section Checkbox {
        width: 4;
        min-width: 4;
        margin-right: 1;
    }

    .tier-label {
        color: #d0d4d8;
    }

    .tier-p0 {
        color: #c24b4b;
    }

    .tier-p1 {
        color: #b86a4d;
    }

    .tier-p2 {
        color: #c7a64a;
    }

    .tier-p3 {
        color: #4c78a8;
    }

    .tier-p4 {
        color: #7c8792;
    }

    #layout-row {
        layout: horizontal;
        height: 17;
    }

    #left-column {
        width: 1fr;
        margin-right: 1;
    }

    #right-column {
        width: 1fr;
    }

    #overrides-view {
        height: 6;
        color: #d0d4d8;
    }

    .row {
        height: auto;
        layout: horizontal;
        margin-top: 1;
    }

    Input {
        background: #111418;
        color: #d0d4d8;
        border: solid #2a2f36;
        margin-right: 1;
        width: 1fr;
    }

    Select {
        background: #111418;
        color: #d0d4d8;
        border: solid #2a2f36;
        width: 24;
        margin-right: 1;
    }

    #preview-result {
        margin-top: 1;
        color: #d0d4d8;
        border: solid #2a2f36;
        padding: 0 1;
        height: 6;
    }

    #preview-result.decision-allow {
        color: #4c8c6b;
    }

    #preview-result.decision-block {
        color: #c24b4b;
    }

    #status {
        border: solid #2a2f36;
        color: #7c8792;
        padding: 0 1;
        height: 3;
    }

    #status.status-success {
        color: #4c8c6b;
    }

    #status.status-warning {
        color: #c7a64a;
    }

    #status.status-danger {
        color: #c24b4b;
    }

    #actions {
        height: 3;
        color: #7c8792;
        border: solid #2a2f36;
        padding: 0 1;
    }
    """

    BINDINGS = [
        Binding("ctrl+s", "save", "Save"),
        Binding("ctrl+r", "simulate", "Simulate"),
        Binding("ctrl+o", "override_upsert", "Upsert Override"),
        Binding("ctrl+x", "override_remove", "Remove Override"),
        Binding("ctrl+q", "quit_requested", "Quit"),
    ]

    def __init__(self, config: PolicyConfig, config_path: Path, cedar_path: Path):
        super().__init__()
        self.config = config
        self.config_path = config_path
        self.cedar_path = cedar_path
        self.dirty = False
        self._confirm_quit = False
        self._suspend_events = False

    def compose(self) -> ComposeResult:
        with Vertical(id="root"):
            yield Static("Guardrail Policy Editor", id="title")

            with Vertical(classes="section"):
                with Horizontal(classes="meta-row"):
                    yield Static("policy", classes="meta-label")
                    yield Static("", id="meta-policy", classes="meta-value")
                with Horizontal(classes="meta-row"):
                    yield Static("file", classes="meta-label")
                    yield Static(str(self.config_path), id="meta-file", classes="meta-value")
                with Horizontal(classes="meta-row"):
                    yield Static("state", classes="meta-label")
                    yield Static("", id="meta-state", classes="meta-value")

            with Horizontal(id="layout-row"):
                with Vertical(id="left-column"):
                    with Vertical(id="blocked-section", classes="section"):
                        yield Static("BLOCKED TIERS", classes="section-title")
                        for tier in TIER_ORDER:
                            with Horizontal(classes="tier-row"):
                                yield Checkbox(value=tier in self.config.blocked_tiers, id=BLOCKED_CHECKBOX_IDS[tier])
                                yield Static(tier, classes=f"tier-label {TIER_STYLE_CLASS[tier]}")

                    with Vertical(id="lowconf-section", classes="section"):
                        yield Static("LOW CONFIDENCE", classes="section-title")
                        yield Input(
                            value=self._threshold_text(),
                            placeholder="threshold (0..1), press Enter to apply",
                            id="lowconf-threshold",
                        )
                        yield Select(
                            options=[(tier, tier) for tier in TIER_ORDER],
                            value=self.config.low_confidence_clamp_tier,
                            id="lowconf-clamp-tier",
                        )

                with Vertical(id="right-column"):
                    with Vertical(id="overrides-section", classes="section"):
                        yield Static("ROLE OVERRIDES", classes="section-title")
                        yield Static("", id="overrides-view")
                        with Horizontal(classes="row"):
                            yield Input(placeholder="role", id="override-role")
                            yield Select(
                                options=[("ALL", ALLOW_ALL)] + [(tier, tier) for tier in TIER_ORDER],
                                value=ALLOW_ALL,
                                id="override-allowance",
                            )
                            yield Static("Ctrl+O upsert")
                        with Horizontal(classes="row"):
                            yield Input(placeholder="role to remove", id="override-remove-role")
                            yield Static("Ctrl+X remove")

                    with Vertical(id="template-section", classes="section"):
                        yield Static("TEMPLATE", classes="section-title")
                        yield Select(
                            options=[
                                ("strict", "strict"),
                                ("balanced", "balanced"),
                                ("permissive", "permissive"),
                                ("custom", "custom"),
                            ],
                            value=self.config.template,
                            id="template-select",
                        )
                        yield Static("Structured model editing only. YAML text is never edited directly.")

            with Vertical(classes="section"):
                yield Static("DECISION PREVIEW", classes="section-title")
                with Horizontal(classes="row"):
                    yield Input(placeholder="input text to simulate", id="preview-input")
                    yield Input(value="general", placeholder="role", id="preview-role")
                yield Static("Run simulation to see decision result.", id="preview-result")

            with Vertical(id="actions"):
                yield Static(
                    "keyboard only: Ctrl+S save | Ctrl+R simulate | Ctrl+O upsert override | "
                    "Ctrl+X remove override | Ctrl+Q quit"
                )

            yield Static("", id="status")

    def on_mount(self) -> None:
        self._sync_widgets_from_config()
        self._set_status("Ready.", level="info")

    def on_checkbox_changed(self, event: Checkbox.Changed) -> None:
        if self._suspend_events:
            return
        checkbox_id = event.checkbox.id or ""
        tier = CHECKBOX_ID_TO_TIER.get(checkbox_id)
        if tier is None:
            return

        if event.value and tier not in self.config.blocked_tiers:
            self.config.blocked_tiers.append(tier)
        elif not event.value and tier in self.config.blocked_tiers:
            self.config.blocked_tiers.remove(tier)
        else:
            return

        self.config.blocked_tiers.sort(key=lambda name: TIER_RANK[name])
        self.config.template = "custom"
        self._mark_dirty(f"Blocked tiers updated: {', '.join(self.config.blocked_tiers)}")
        self._sync_widgets_from_config()

    def on_select_changed(self, event: Select.Changed) -> None:
        if self._suspend_events:
            return

        select_id = event.select.id or ""
        value = event.value
        if not isinstance(value, str):
            return

        if select_id == "template-select":
            if value in {"strict", "balanced", "permissive"}:
                from app.services.policy_config import preset_policy_config
                self.config = preset_policy_config(value)
                self._mark_dirty(f"Template set to '{value}'.")
            elif value == "custom":
                self.config.template = "custom"
                self._mark_dirty("Template set to custom.")
            self._sync_widgets_from_config()
            return

        if select_id == "lowconf-clamp-tier":
            self.config.low_confidence_clamp_tier = value
            self.config.template = "custom"
            self._mark_dirty(f"Clamp tier set to {value}.")
            self._sync_widgets_from_config()
            return

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if self._suspend_events:
            return

        input_id = event.input.id or ""
        if input_id != "lowconf-threshold":
            return

        raw_value = event.value.strip()
        if not raw_value:
            return

        try:
            threshold = float(raw_value)
        except ValueError:
            self._set_status("Threshold must be numeric in [0,1].", level="warning")
            return
        if threshold < 0.0 or threshold > 1.0:
            self._set_status("Threshold must be within 0 to 1.", level="warning")
            return

        self.config.low_confidence_threshold = threshold
        self.config.template = "custom"
        self._mark_dirty(f"Threshold set to {threshold}.")
        self._sync_widgets_from_config()

    def action_save(self) -> None:
        try:
            PolicyService.save(self.config, self.config_path, self.cedar_path)
            self.config = PolicyService.normalize(self.config)
        except (PolicyConfigError, ValueError, RuntimeError) as exc:
            self._set_status(f"Save failed: {exc}", level="danger")
            return

        self.dirty = False
        self._confirm_quit = False
        self._sync_widgets_from_config()
        self._set_status("Saved policy YAML and Cedar.", level="success")

    def action_simulate(self) -> None:
        self._simulate_preview()

    def action_override_upsert(self) -> None:
        self._upsert_override()

    def action_override_remove(self) -> None:
        self._remove_override_by_input()

    def action_quit_requested(self) -> None:
        if self.dirty and not self._confirm_quit:
            self._confirm_quit = True
            self._set_status("Unsaved changes. Press Ctrl+Q again to quit without saving.", level="warning")
            return
        self.exit()

    def on_mouse_down(self, event) -> None:
        event.stop()

    def on_mouse_up(self, event) -> None:
        event.stop()

    def on_click(self, event) -> None:
        event.stop()

    def on_mouse_move(self, event) -> None:
        event.stop()

    def on_mouse_scroll_up(self, event) -> None:
        event.stop()

    def on_mouse_scroll_down(self, event) -> None:
        event.stop()

    def _upsert_override(self) -> None:
        role_input = self.query_one("#override-role", Input)
        allowance_select = self.query_one("#override-allowance", Select)
        role = role_input.value.strip()
        allowance = allowance_select.value

        if not role:
            self._set_status("Role is required.", level="warning")
            return
        if not ROLE_PATTERN.match(role):
            self._set_status("Role format is invalid.", level="warning")
            return
        if not isinstance(allowance, str):
            self._set_status("Allowance selection is invalid.", level="warning")
            return

        self.config.role_overrides[role] = allowance
        self.config.template = "custom"
        role_input.value = ""
        self._mark_dirty(f"Override set: {role} -> {allowance}")
        self._sync_widgets_from_config()

    def _remove_override_by_input(self) -> None:
        role_input = self.query_one("#override-remove-role", Input)
        role = role_input.value.strip()
        if not role:
            self._set_status("Role to remove is required.", level="warning")
            return
        if role not in self.config.role_overrides:
            self._set_status(f"Override not found: {role}", level="warning")
            return

        del self.config.role_overrides[role]
        self.config.template = "custom"
        role_input.value = ""
        self._mark_dirty(f"Removed override: {role}")
        self._sync_widgets_from_config()

    def _simulate_preview(self) -> None:
        preview_input = self.query_one("#preview-input", Input).value.strip()
        preview_role = self.query_one("#preview-role", Input).value.strip() or "general"
        if not preview_input:
            self._set_status("Simulation input is required.", level="warning")
            return

        try:
            result = PolicyService.simulate(self.config, preview_input, preview_role)
            explanation = PolicyService.explain_decision(result, self.config)
        except (PolicyConfigError, ValueError, RuntimeError) as exc:
            self._set_status(f"Simulation failed: {exc}", level="danger")
            return

        preview_text = (
            f"input   : {preview_input}\n"
            f"role    : {preview_role}\n"
            f"result  : {explanation['decision']} ({explanation['tier']})\n"
            f"matched : {explanation['policy_matches']}\n"
            f"signals : {explanation['signals']}"
        )
        preview_widget = self.query_one("#preview-result", Static)
        preview_widget.update(preview_text)
        self._set_preview_decision_style(result.decision)
        self._set_status("Simulation completed.", level="info")

    def _sync_widgets_from_config(self) -> None:
        self._suspend_events = True
        try:
            for tier in TIER_ORDER:
                checkbox = self.query_one(f"#{BLOCKED_CHECKBOX_IDS[tier]}", Checkbox)
                checkbox.value = tier in self.config.blocked_tiers

            template_select = self.query_one("#template-select", Select)
            template_select.value = self.config.template

            threshold_input = self.query_one("#lowconf-threshold", Input)
            threshold_input.value = self._threshold_text()

            clamp_select = self.query_one("#lowconf-clamp-tier", Select)
            clamp_select.value = self.config.low_confidence_clamp_tier

            self.query_one("#meta-policy", Static).update(
                f"{self.config.template} v{self.config.version}"
            )
            self.query_one("#meta-file", Static).update(str(self.config_path))
            self._refresh_overrides_view()
            self._refresh_state_indicator()
        finally:
            self._suspend_events = False

    def _refresh_overrides_view(self) -> None:
        if not self.config.role_overrides:
            text = "(none)"
        else:
            lines = []
            for role, allowance in sorted(self.config.role_overrides.items()):
                lines.append(f"{role:<14} : {allowance}")
            text = "\n".join(lines)
        self.query_one("#overrides-view", Static).update(text)

    def _refresh_state_indicator(self) -> None:
        state_widget = self.query_one("#meta-state", Static)
        state_widget.remove_class("state-saved")
        state_widget.remove_class("state-unsaved")
        if self.dirty:
            state_widget.update("unsaved")
            state_widget.add_class("state-unsaved")
        else:
            state_widget.update("saved")
            state_widget.add_class("state-saved")

    def _set_preview_decision_style(self, decision: str) -> None:
        preview_widget = self.query_one("#preview-result", Static)
        preview_widget.remove_class("decision-allow")
        preview_widget.remove_class("decision-block")
        if decision == "allow":
            preview_widget.add_class("decision-allow")
        elif decision == "block":
            preview_widget.add_class("decision-block")

    def _mark_dirty(self, message: str) -> None:
        self.dirty = True
        self._confirm_quit = False
        self._refresh_state_indicator()
        self._set_status(message, level="warning")

    def _set_status(self, message: str, level: str = "info") -> None:
        status_widget = self.query_one("#status", Static)
        status_widget.remove_class("status-success")
        status_widget.remove_class("status-warning")
        status_widget.remove_class("status-danger")
        if level == "success":
            status_widget.add_class("status-success")
        elif level == "warning":
            status_widget.add_class("status-warning")
        elif level == "danger":
            status_widget.add_class("status-danger")
        status_widget.update(message)

    def _threshold_text(self) -> str:
        value = f"{self.config.low_confidence_threshold:.3f}".rstrip("0").rstrip(".")
        return value or "0"
