import unittest

from model_router import TaskProfile, route_task


class ModelRouterTests(unittest.TestCase):
    def test_green_bounded_work_routes_to_luna(self):
        result = route_task(TaskProfile(task_id="T1", well_defined=True))
        self.assertEqual("BUILD", result["task_class"])
        self.assertEqual("GREEN", result["risk_lane"])
        self.assertEqual("luna", result["primary_model"])
        self.assertIsNone(result["reviewer_model"])
        self.assertFalse(result["authority_granted"])

    def test_methodical_state_work_routes_to_terra(self):
        result = route_task(TaskProfile(
            task_id="T2", well_defined=True, operational_state_dominant=True
        ))
        self.assertEqual("ENGINEER", result["task_class"])
        self.assertEqual("terra", result["primary_model"])
        self.assertEqual("METHODICAL_ENGINEER", result["behavior_overlay"])

    def test_ambiguous_work_defaults_to_sol(self):
        result = route_task(TaskProfile(task_id="T3", well_defined=False))
        self.assertEqual("DECIDE", result["task_class"])
        self.assertEqual("AMBER", result["risk_lane"])
        self.assertEqual("sol", result["primary_model"])
        self.assertIn("JUDGMENT_REQUIRED", result["reason_codes"])

    def test_red_security_work_uses_sol_with_astra_review(self):
        result = route_task(TaskProfile(
            task_id="T4", well_defined=False, security_privacy_authority=True
        ))
        self.assertEqual("RED", result["risk_lane"])
        self.assertEqual("sol", result["primary_model"])
        self.assertEqual("astra", result["reviewer_model"])

    def test_broad_red_work_escalates_to_astra(self):
        result = route_task(TaskProfile(
            task_id="T5",
            well_defined=False,
            high_consequence=True,
            broad_parallel_work=True,
            cross_system=True,
        ))
        self.assertEqual("ESCALATE", result["task_class"])
        self.assertEqual("astra", result["primary_model"])
        self.assertEqual("sol", result["reviewer_model"])
        self.assertIn("PARALLEL_BREADTH", result["reason_codes"])

    def test_amber_bounded_work_gets_sol_review(self):
        result = route_task(TaskProfile(
            task_id="T6", well_defined=True, important_artifact=True
        ))
        self.assertEqual("BUILD", result["task_class"])
        self.assertEqual("AMBER", result["risk_lane"])
        self.assertEqual("luna", result["primary_model"])
        self.assertEqual("sol", result["reviewer_model"])

    def test_owner_override_is_recorded_without_erasing_risk(self):
        result = route_task(TaskProfile(
            task_id="T7",
            well_defined=False,
            security_privacy_authority=True,
            owner_override="terra",
        ))
        self.assertEqual("RED", result["risk_lane"])
        self.assertEqual("terra", result["primary_model"])
        self.assertEqual("owner_override", result["route_source"])
        self.assertEqual("astra", result["reviewer_model"])
        self.assertIn("OWNER_OVERRIDE", result["reason_codes"])

    def test_invalid_owner_override_is_rejected(self):
        with self.assertRaises(ValueError):
            route_task(TaskProfile(
                task_id="T8", well_defined=True, owner_override="gpt-5.5"
            ))


if __name__ == "__main__":
    unittest.main()
