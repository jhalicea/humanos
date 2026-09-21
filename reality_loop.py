"""Evidence-driven execution cycle for long-horizon HumanOS work.

The loop deliberately separates task execution from authority and verification.
A worker can propose and execute only after the trusted host refreshes authority.
The verifier receives observable behavior/evidence, not the worker's private rationale.
"""
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional


STOP_EVIDENCE_MISMATCH = "evidence_no_longer_matches_assumptions"
STOP_AUTHORITY = "authority_not_granted"
STOP_NO_PATH = "no_legitimate_path"
STOP_HORIZON = "horizon_limit"
COMPLETE = "complete"


@dataclass(frozen=True)
class Verification:
    matches_assumptions: bool
    goal_complete: bool = False
    evidence: Any = None
    note: str = ""


@dataclass(frozen=True)
class Authority:
    granted: bool
    snapshot: Any = None
    reason: str = ""


@dataclass
class RealityResult:
    status: str
    goal: str
    blocks_attempted: int = 0
    blocks_completed: int = 0
    verifications: int = 0
    checkpoints: int = 0
    history: List[Dict[str, Any]] = field(default_factory=list)
    stop_reason: Optional[str] = None


class RealityLoop:
    """Run bounded work as plan -> authority -> execute -> observe -> verify -> checkpoint -> reconsider.

    `verify` intentionally receives only the goal, current block, observable result,
    and current authority snapshot. The worker's hidden/private rationale is not part
    of the verifier interface, reducing narrative contamination between actor and monitor.
    """

    def __init__(
        self,
        *,
        plan: Callable[[str, List[Dict[str, Any]]], Any],
        authority: Callable[[str, Any, List[Dict[str, Any]]], Authority],
        execute: Callable[[str, Any, Authority], Any],
        observe: Callable[[str, Any, Any], Any],
        verify: Callable[[str, Any, Any, Authority], Verification],
        checkpoint: Callable[[Dict[str, Any]], None],
        reconsider: Callable[[str, Any, Verification, List[Dict[str, Any]]], None],
        max_blocks: int = 16,
    ):
        if type(max_blocks) is not int or max_blocks < 1:
            raise ValueError("max_blocks must be a positive integer")
        self.plan = plan
        self.authority = authority
        self.execute = execute
        self.observe = observe
        self.verify = verify
        self.checkpoint = checkpoint
        self.reconsider = reconsider
        self.max_blocks = max_blocks

    def run(self, goal: str) -> RealityResult:
        if not isinstance(goal, str) or not goal.strip():
            raise ValueError("goal must be non-empty text")
        result = RealityResult(status=STOP_HORIZON, goal=goal, stop_reason=STOP_HORIZON)

        for block_no in range(1, self.max_blocks + 1):
            block = self.plan(goal, list(result.history))
            if block is None:
                result.status = STOP_NO_PATH
                result.stop_reason = STOP_NO_PATH
                return result

            result.blocks_attempted += 1

            # Authority is refreshed immediately before every consequential block.
            auth = self.authority(goal, block, list(result.history))
            if not isinstance(auth, Authority):
                raise TypeError("authority must return Authority")
            if not auth.granted:
                result.status = STOP_AUTHORITY
                result.stop_reason = auth.reason or STOP_AUTHORITY
                result.history.append({
                    "block": block_no,
                    "plan": block,
                    "authority": auth,
                    "status": STOP_AUTHORITY,
                })
                return result

            effect = self.execute(goal, block, auth)
            observation = self.observe(goal, block, effect)
            verdict = self.verify(goal, block, observation, auth)
            if not isinstance(verdict, Verification):
                raise TypeError("verify must return Verification")
            result.verifications += 1

            event = {
                "block": block_no,
                "plan": block,
                "authority": auth,
                "observation": observation,
                "verification": verdict,
            }
            result.history.append(event)

            # A reality mismatch is a first-class hard stop, not a suggestion.
            if not verdict.matches_assumptions:
                event["status"] = STOP_EVIDENCE_MISMATCH
                result.status = STOP_EVIDENCE_MISMATCH
                result.stop_reason = verdict.note or STOP_EVIDENCE_MISMATCH
                return result

            self.checkpoint(dict(event))
            result.checkpoints += 1
            result.blocks_completed += 1

            if verdict.goal_complete:
                event["status"] = COMPLETE
                result.status = COMPLETE
                result.stop_reason = None
                return result

            # Reconsideration occurs only after evidence has been independently verified.
            self.reconsider(goal, block, verdict, list(result.history))

        return result
