"""Approval workflow tests for supervisor events."""

from __future__ import annotations

import pathlib
from typing import Any, Dict, List


class _FakeCtx:
    def __init__(self, tmp_path: pathlib.Path):
        self._state: Dict[str, Any] = {
            "owner_chat_id": 123,
            "pending_approvals": {},
            "evolution_mode_enabled": False,
        }
        self.sent: List[str] = []
        self.saved_states: List[Dict[str, Any]] = []
        self.PENDING: List[Dict[str, Any]] = []
        self.DRIVE_ROOT = tmp_path

    def load_state(self) -> Dict[str, Any]:
        return dict(self._state)

    def save_state(self, st: Dict[str, Any]) -> None:
        self._state = dict(st)
        self.saved_states.append(dict(st))

    def send_with_budget(self, _chat_id: int, text: str, **_kwargs: Any) -> None:
        self.sent.append(text)

    def sort_pending(self) -> None:
        return

    def persist_queue_snapshot(self, reason: str = "") -> None:
        return


def test_toggle_evolution_requires_approval(tmp_path: pathlib.Path):
    from supervisor.events import _handle_toggle_evolution

    ctx = _FakeCtx(tmp_path)
    _handle_toggle_evolution({"type": "toggle_evolution", "enabled": True}, ctx)

    pending = ctx._state.get("pending_approvals") or {}
    assert pending, "approval request must be persisted"
    rec = next(iter(pending.values()))
    assert rec.get("status") == "pending"
    assert rec.get("action") == "toggle_evolution"
    assert ctx._state.get("evolution_mode_enabled") is False


def test_toggle_evolution_executes_when_approved(tmp_path: pathlib.Path):
    from supervisor.events import _handle_toggle_evolution

    ctx = _FakeCtx(tmp_path)
    _handle_toggle_evolution(
        {"type": "toggle_evolution", "enabled": True, "approved": True, "approval_id": "abc123"},
        ctx,
    )

    assert ctx._state.get("evolution_mode_enabled") is True
    assert any("Evolution: ON" in msg for msg in ctx.sent)
