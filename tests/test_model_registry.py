import unittest

from model_registry import (
    ModelIdentity,
    ModelRegistry,
    QualificationRef,
    RuntimeProfile,
    model_id_from_ollama,
    profile_id_from_name,
)


class ModelRegistryTests(unittest.TestCase):
    def setUp(self):
        self.registry = ModelRegistry()
        self.model_id = model_id_from_ollama(
            family="qwen3-coder",
            weights_digest="sha256:1194192cf2a187eb02722edcc3f77b11",
            quantization="Q4_K_M",
        )
        self.registry.register_model(ModelIdentity(
            model_id=self.model_id,
            provider="local",
            family="qwen3-coder",
            architecture="qwen3moe",
            parameter_count="30.5B",
            quantization="Q4_K_M",
            weights_digest="sha256:1194192cf2a187eb02722edcc3f77b11",
            capabilities=("completion", "tools"),
        ))

    def test_aliases_share_model_identity_but_keep_profiles(self):
        for name, context in (("qwen3-coder:30b", 4096), ("qwen3-coder-local:16k", 16384), ("qwen3-coder:16k", 16384)):
            self.registry.register_profile(RuntimeProfile(
                profile_id=profile_id_from_name(name),
                model_id=self.model_id,
                runtime="ollama",
                configured_name=name,
                context_window=context,
            ))
        self.assertEqual(3, len(self.registry.profiles_for_model(self.model_id)))
        self.assertEqual(1, len(self.registry.models))

    def test_qualification_attaches_to_exact_profile(self):
        profile = RuntimeProfile(
            profile_id=profile_id_from_name("qwen3-coder-local:16k"),
            model_id=self.model_id,
            runtime="ollama",
            configured_name="qwen3-coder-local:16k",
            context_window=16384,
        )
        self.registry.register_profile(profile)
        self.registry.attach_qualification(QualificationRef(
            qualification_id="HOS-AMR-001-LOCAL-02",
            model_id=self.model_id,
            profile_id=profile.profile_id,
            framework="adaptive-mastery-review",
            framework_version="v2",
            status="PROPOSAL",
        ))
        self.assertEqual("HOS-AMR-001-LOCAL-02", self.registry.qualifications_for_profile(profile.profile_id)[0].qualification_id)

    def test_rejects_cross_model_qualification(self):
        profile = RuntimeProfile("p1", self.model_id, "ollama", "qwen")
        self.registry.register_profile(profile)
        other = ModelIdentity("other", "local", "llama3")
        self.registry.register_model(other)
        with self.assertRaises(ValueError):
            self.registry.attach_qualification(QualificationRef("q1", "other", "p1", "HINE", "1.1", "PASS"))

    def test_registry_does_not_authorize_or_route(self):
        snap = self.registry.snapshot()
        self.assertTrue(snap["policy"]["descriptive_only"])
        self.assertFalse(snap["policy"]["automatic_naturalization"])
        self.assertFalse(snap["policy"]["automatic_routing"])
        self.assertTrue(snap["policy"]["human_promotion_required"])

    def test_unknown_weights_do_not_claim_identity_equivalence(self):
        a = model_id_from_ollama(family="llama3", weights_digest=None, quantization=None)
        b = model_id_from_ollama(family="llama3.2", weights_digest=None, quantization=None)
        self.assertNotEqual(a, b)


if __name__ == "__main__":
    unittest.main()
