import unittest

from fastapi.testclient import TestClient

from app.main import app
from app.registry import get_module


class ApiContractTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        self.module = get_module("volcano")
        self.session_id = "api-contract-session"

    def test_module_precheck_job_artifact_and_history_flow(self):
        modules = self.client.get("/api/modules")
        self.assertEqual(modules.status_code, 200)
        self.assertIn("Transcriptome", modules.json()["groups"])

        precheck = self.client.post(
            "/api/modules/volcano/precheck",
            json={"data": self.module.demo_data, "source": "paste"},
        )
        self.assertEqual(precheck.status_code, 200)
        self.assertEqual(precheck.json()["errors"], [])
        self.assertGreater(precheck.json()["rowCount"], 0)

        job = self.client.post(
            "/api/jobs",
            json={
                "moduleSlug": "volcano",
                "data": self.module.demo_data,
                "options": self.module.default_options,
                "sessionId": self.session_id,
            },
        )
        self.assertEqual(job.status_code, 200)
        payload = job.json()
        self.assertEqual(payload["status"], "succeeded")
        self.assertIn("svg", payload["artifacts"])

        artifact = self.client.get(payload["artifacts"]["svg"])
        self.assertEqual(artifact.status_code, 200)
        self.assertIn("<svg", artifact.text)

        history = self.client.get(f"/api/history?sessionId={self.session_id}")
        self.assertEqual(history.status_code, 200)
        self.assertTrue(any(item["id"] == payload["id"] for item in history.json()["jobs"]))


if __name__ == "__main__":
    unittest.main()
