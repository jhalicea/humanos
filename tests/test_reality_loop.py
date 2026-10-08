import unittest

from reality_loop import (
    Authority,
    COMPLETE,
    RealityLoop,
    STOP_AUTHORITY,
    STOP_EVIDENCE_MISMATCH,
    STOP_HORIZON,
    STOP_NO_PATH,
    Verification,
)


class RealityLoopTests(unittest.TestCase):
    def make_loop(self, *, plan=None, authority=None, verify=None, max_blocks=16):
        calls = {"execute": [], "authority": [], "checkpoint": [], "reconsider": []}

        def default_plan(goal, history):
            return {"step": len(history) + 1}

        def default_authority(goal, block, history):
            calls["authority"].append(block["step"])
            return Authority(True, snapshot={"epoch": len(history) + 1})

        def execute(goal, block, auth):
            calls["execute"].append(block["step"])
            return {"did": block["step"]}

        def observe(goal, block, effect):
            return {"observed": effect["did"]}

        def default_verify(goal, block, observation, auth):
            return Verification(True, goal_complete=False, evidence=observation)

        def checkpoint(event):
            calls["checkpoint"].append(event["block"])

        def reconsider(goal, block, verdict, history):
            calls["reconsider"].append(block["step"])

        loop = RealityLoop(
            plan=plan or default_plan,
            authority=authority or default_authority,
            execute=execute,
            observe=observe,
            verify=verify or default_verify,
            checkpoint=checkpoint,
            reconsider=reconsider,
            max_blocks=max_blocks,
        )
        return loop, calls

    def test_complete_after_verified_checkpoint(self):
        def verify(goal, block, observation, auth):
            return Verification(True, goal_complete=block["step"] == 3, evidence=observation)

        loop, calls = self.make_loop(verify=verify)
        result = loop.run("complete three verified blocks")
        self.assertEqual(COMPLETE, result.status)
        self.assertEqual([1, 2, 3], calls["execute"])
        self.assertEqual([1, 2, 3], calls["checkpoint"])
        self.assertEqual(3, result.verifications)

    def test_reality_mismatch_hard_stops_momentum_before_next_block(self):
        def verify(goal, block, observation, auth):
            if block["step"] == 2:
                return Verification(False, note="environment contradicts simulation assumption")
            return Verification(True)

        loop, calls = self.make_loop(verify=verify, max_blocks=8)
        result = loop.run("keep going unless reality disagrees")
        self.assertEqual(STOP_EVIDENCE_MISMATCH, result.status)
        self.assertEqual([1, 2], calls["execute"])
        self.assertEqual([1], calls["checkpoint"])
        self.assertEqual([1], calls["reconsider"])
        self.assertEqual(2, result.blocks_attempted)
        self.assertEqual(1, result.blocks_completed)

    def test_authority_is_refreshed_before_every_block_and_revocation_prevents_effect(self):
        seen = []

        def authority(goal, block, history):
            seen.append(block["step"])
            if block["step"] == 2:
                return Authority(False, snapshot={"epoch": 2}, reason="owner revoked permission")
            return Authority(True, snapshot={"epoch": 1})

        loop, calls = self.make_loop(authority=authority, max_blocks=5)
        result = loop.run("bounded task")
        self.assertEqual(STOP_AUTHORITY, result.status)
        self.assertEqual([1, 2], seen)
        self.assertEqual([1], calls["execute"])
        self.assertEqual("owner revoked permission", result.stop_reason)

    def test_impossible_task_stops_when_no_legitimate_plan_exists(self):
        def plan(goal, history):
            return None

        loop, calls = self.make_loop(plan=plan)
        result = loop.run("impossible task")
        self.assertEqual(STOP_NO_PATH, result.status)
        self.assertEqual([], calls["execute"])
        self.assertEqual([], calls["authority"])

    def test_horizon_limit_is_measured_not_silently_extended(self):
        loop, calls = self.make_loop(max_blocks=32)
        result = loop.run("long horizon evaluation")
        self.assertEqual(STOP_HORIZON, result.status)
        self.assertEqual(32, result.blocks_completed)
        self.assertEqual(32, result.verifications)
        self.assertEqual(list(range(1, 33)), calls["execute"])
        self.assertEqual(list(range(1, 33)), calls["checkpoint"])

    def test_verifier_interface_has_no_worker_reasoning_parameter(self):
        received = []

        def verify(goal, block, observation, auth):
            received.append((goal, block, observation, auth))
            return Verification(True, goal_complete=True)

        loop, _ = self.make_loop(verify=verify)
        result = loop.run("behavior-only monitoring")
        self.assertEqual(COMPLETE, result.status)
        self.assertEqual(1, len(received))
        self.assertEqual(4, len(received[0]))


if __name__ == "__main__":
    unittest.main()
