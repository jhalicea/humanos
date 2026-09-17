import hashlib
import io
import json
import tempfile
import unittest
from pathlib import Path

from model_artifacts import ArtifactStore, DownloadPolicyError, IntegrityError, ManifestError, RegistryError, load_registry

REV = "0123456789abcdef0123456789abcdef01234567"
HOST = "models.example"


class Response(io.BytesIO):
    def __init__(self, data: bytes, url: str):
        super().__init__(data); self._url = url
    def geturl(self): return self._url


class ModelArtifactStoreTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.root = Path(self.temp.name); self.calls = []
        self.payloads = {
            f"https://{HOST}/repo/{REV}/weights/params_shard_0.bin": b"shard-zero",
            f"https://{HOST}/repo/{REV}/weights/params_shard_1.bin": b"shard-one",
            f"https://{HOST}/repo/{REV}/tokenizer.json": b'{"type":"fixture"}',
            f"https://{HOST}/repo/{REV}/runtime/test.wasm": b"not-executable-fixture",
        }
        artifacts = []
        for url, data in self.payloads.items():
            name = url.split(f"/{REV}/", 1)[1]
            kind = "weights" if name.startswith("weights/") else "runtime" if name.startswith("runtime/") else "tokenizer"
            artifacts.append({"name": name, "kind": kind, "url": url, "size": len(data), "sha256": hashlib.sha256(data).hexdigest()})
        self.manifest = {"schema_version": 1, "model_id": "fixture-360m", "source_revision": REV, "runtime_family": "fixture-only", "artifacts": artifacts}
        self.manifest_bytes = json.dumps(self.manifest, sort_keys=True).encode()
        self.manifest_url = f"https://{HOST}/repo/{REV}/manifest.json"
        self.payloads[self.manifest_url] = self.manifest_bytes
        self.registry_path = self.root / "registry.json"; self._write_registry()

    def tearDown(self): self.temp.cleanup()

    def _write_registry(self, **changes):
        entry = {"model_id": "fixture-360m", "status": "candidate", "source_revision": REV,
                 "manifest_url": self.manifest_url, "manifest_size": len(self.manifest_bytes),
                 "manifest_sha256": hashlib.sha256(self.manifest_bytes).hexdigest(), "allowed_hosts": [HOST]}
        entry.update(changes)
        self.registry_path.write_text(json.dumps({"schema_version": 1, "models": [entry]}), encoding="utf-8")

    def opener(self, url, timeout):
        self.calls.append(url)
        if url not in self.payloads: raise OSError("unexpected URL")
        return Response(self.payloads[url], url)

    def store(self): return ArtifactStore(self.root / "store", opener=self.opener, chunk_bytes=4096)

    def test_downloads_shards_and_writes_verified_receipt(self):
        result = self.store().fetch_model(self.registry_path, "fixture-360m")
        self.assertFalse(result.reused_cache); self.assertEqual(result.artifact_count, 4)
        self.assertTrue((result.model_dir / "weights/params_shard_0.bin").is_file())
        self.assertTrue((result.model_dir / "weights/params_shard_1.bin").is_file())
        receipt = json.loads((result.model_dir / "VERIFIED.json").read_text())
        self.assertEqual(receipt["source_revision"], REV); self.assertEqual(len(receipt["artifacts"]), 4)

    def test_verified_cache_is_reused_without_redownloading_artifacts(self):
        store = self.store(); store.fetch_model(self.registry_path, "fixture-360m"); call_count = len(self.calls)
        second = store.fetch_model(self.registry_path, "fixture-360m")
        self.assertTrue(second.reused_cache); self.assertEqual(self.calls[call_count:], [self.manifest_url])

    def test_bad_artifact_hash_fails_closed_without_final_model(self):
        url = f"https://{HOST}/repo/{REV}/weights/params_shard_1.bin"; self.payloads[url] = b"tampered"
        with self.assertRaises(IntegrityError): self.store().fetch_model(self.registry_path, "fixture-360m")
        self.assertFalse((self.root / "store/models/fixture-360m" / REV).exists())
        self.assertFalse(any((self.root / "store").rglob("*.partial")))

    def test_bad_manifest_hash_fails_before_artifact_downloads(self):
        self._write_registry(manifest_sha256="0" * 64)
        with self.assertRaises(IntegrityError): self.store().fetch_model(self.registry_path, "fixture-360m")
        self.assertEqual(self.calls, [self.manifest_url])

    def test_mutable_main_ref_is_rejected(self):
        self._write_registry(manifest_url=f"https://{HOST}/repo/main/manifest.json")
        with self.assertRaises(RegistryError): load_registry(self.registry_path)

    def test_registry_requires_immutable_revision_in_url(self):
        self._write_registry(manifest_url=f"https://{HOST}/repo/manifest.json")
        with self.assertRaises(RegistryError): load_registry(self.registry_path)

    def test_cross_host_redirect_is_rejected(self):
        def redirected(url, timeout): return Response(self.payloads[url], "https://evil.example/payload")
        with self.assertRaises(DownloadPolicyError):
            ArtifactStore(self.root / "redirect", opener=redirected).fetch_model(self.registry_path, "fixture-360m")

    def test_path_traversal_in_manifest_is_rejected(self):
        self.manifest["artifacts"][0]["name"] = "../escape.bin"
        data = json.dumps(self.manifest, sort_keys=True).encode(); self.payloads[self.manifest_url] = data
        self._write_registry(manifest_size=len(data), manifest_sha256=hashlib.sha256(data).hexdigest())
        with self.assertRaises(ManifestError): self.store().fetch_model(self.registry_path, "fixture-360m")

    def test_size_limit_blocks_resource_exhaustion_manifest(self):
        with self.assertRaises(ManifestError):
            ArtifactStore(self.root / "tiny", opener=self.opener, max_total_bytes=1).fetch_model(self.registry_path, "fixture-360m")

    def test_existing_corrupt_verified_cache_is_not_overwritten(self):
        store = self.store(); result = store.fetch_model(self.registry_path, "fixture-360m")
        target = result.model_dir / "weights/params_shard_0.bin"; target.write_bytes(b"corrupt"); before = len(self.calls)
        with self.assertRaises(IntegrityError): store.fetch_model(self.registry_path, "fixture-360m")
        self.assertEqual(self.calls[before:], [self.manifest_url]); self.assertEqual(target.read_bytes(), b"corrupt")


if __name__ == "__main__": unittest.main()
