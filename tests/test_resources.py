"""Check the actual distributed offline assets, without fetching the internet."""
import hashlib
import json
from pathlib import Path
import unittest

WEB = Path(__file__).resolve().parents[1] / 'TD/web'


class OfflineResourcesTests(unittest.TestCase):
    def test_distributed_runtime_and_model_match_manifest(self):
        resources = json.loads((WEB / 'resources.sha256.json').read_text(encoding='utf-8'))
        self.assertIn('models/hand_landmarker.task', resources)
        self.assertIn('vendor/vision_bundle.mjs', resources)
        for relative, digest in resources.items():
            with self.subTest(resource=relative):
                path = (WEB / relative).resolve()
                self.assertTrue(path.is_relative_to(WEB.resolve()))
                self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), digest)

    def test_custom_camera_page_uses_local_model_and_runtime(self):
        source = (WEB / 'hand_tracking.js').read_text(encoding='utf-8')
        self.assertIn("'./hand_worker.js'", source)
        worker = (WEB / 'hand_worker.js').read_text(encoding='utf-8')
        self.assertIn("'./vendor/vision_bundle.mjs'", worker)
        self.assertIn("'./vendor/wasm'", worker)
        self.assertIn("'./models/hand_landmarker.task'", worker)
        self.assertNotRegex(worker, r'https?://')
        self.assertNotRegex(source, r'https?://')
        self.assertNotRegex((WEB / 'index.html').read_text(encoding='utf-8'), r'https?://')


if __name__ == '__main__':
    unittest.main()
