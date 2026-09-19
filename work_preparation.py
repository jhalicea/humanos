"""Human-facing preparation layer for the HumanOS Work Loop.

The normal surface is deliberately small. Full contracts remain available as
details, while the preparation path compiles and validates them underneath.
Nothing in this module dispatches or executes work.
"""
from __future__ import annotations

import copy
from dataclasses import dataclass

from friend_packet_compiler import compile_friend_packet
from friend_privacy import sanitize_friend_packet
from work_order_compiler import compile_work_order


@dataclass(frozen=True)
class PreparedWork:
    work_order: dict
    friend_packet: dict
    prepared_packet: dict
    privacy_findings: tuple
    destination: str

    @property
    def status(self):
        return "READY"

    @property
    def changed_for_privacy(self):
        return self.prepared_packet != self.friend_packet

    def details(self):
        """Return full deterministic artifacts for audit/debug views."""
        return {
            "status": self.status,
            "destination": self.destination,
            "work_order": copy.deepcopy(self.work_order),
            "friend_packet": copy.deepcopy(self.friend_packet),
            "prepared_packet": copy.deepcopy(self.prepared_packet),
            "privacy_findings": [
                {
                    "category": item.category,
                    "field": item.field,
                    "count": item.count,
                    "action": item.action,
                }
                for item in self.privacy_findings
            ],
        }

    def review_card(self):
        """Return the concise default human view.

        IDs, hashes, schema names, and raw findings are intentionally omitted.
        They remain available from details().
        """
        objective = self.work_order["objective"].strip()
        role = self.prepared_packet["worker_role"].strip()
        path_count = len(self.prepared_packet["allowed_scope"])
        check_count = len(self.prepared_packet["acceptance_criteria"])
        ownership = self.prepared_packet["ownership"]["mode"]
        privacy = self.prepared_packet["privacy_classification"]
        location = "On this Mac" if self.destination == "LOCAL" else "External, privacy-filtered"
        privacy_changes = sum(item.count for item in self.privacy_findings)

        scope_label = f"{path_count} item" + ("" if path_count == 1 else "s")
        check_label = f"{check_count} check" + ("" if check_count == 1 else "s")
        lines = [
            "Ready",
            objective,
            f"Scope: {scope_label} · {ownership.replace('_', ' ').title()}",
            f"Worker: {role}",
            f"Privacy: {privacy.title()} · {location}",
            f"Verification: {check_label}",
        ]
        if self.destination == "EXTERNAL" and privacy_changes:
            lines.append(
                f"Privacy protection: {privacy_changes} sensitive value"
                + ("" if privacy_changes == 1 else "s")
                + " removed"
            )
        lines.append("Nothing has run yet.")
        return "\n".join(lines)


def prepare_work(
    decision,
    assignment,
    *,
    repository,
    ref,
    baseline_commit_sha,
    destination="LOCAL",
):
    """Compile and privacy-prepare work without dispatching it."""
    work_order = compile_work_order(
        decision,
        repository=repository,
        ref=ref,
        baseline_commit_sha=baseline_commit_sha,
    )
    friend_packet = compile_friend_packet(work_order, assignment)
    protected = sanitize_friend_packet(
        friend_packet,
        destination=destination,
        work_order=work_order,
    )
    return PreparedWork(
        work_order=work_order,
        friend_packet=friend_packet,
        prepared_packet=protected.packet,
        privacy_findings=protected.findings,
        destination=protected.destination,
    )
