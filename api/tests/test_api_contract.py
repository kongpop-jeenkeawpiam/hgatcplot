import unittest

from fastapi.testclient import TestClient

from app.main import app
from app.r_engine import check_r_engine
from app.registry import get_module, list_modules


class ApiContractTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        self.module = get_module("volcano")
        self.session_id = "api-contract-session"

    def test_module_precheck_job_artifact_and_history_flow(self):
        health = self.client.get("/api/health")
        self.assertEqual(health.status_code, 200)
        self.assertEqual(health.json()["templateCount"], 125)

        modules = self.client.get("/api/modules")
        self.assertEqual(modules.status_code, 200)
        self.assertIn("Transcriptome", modules.json()["groups"])
        self.assertEqual(sum(len(items) for items in modules.json()["groups"].values()), 125)

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

    def test_module_detail_includes_engine_source_and_aliases(self):
        detail = self.client.get("/api/modules/motif-logo")

        self.assertEqual(detail.status_code, 200)
        payload = detail.json()
        self.assertEqual(payload["engine"], "r")
        self.assertIn("sourceUrl", payload)
        self.assertIn("motif-logo", payload["aliases"])

    def test_precheck_reports_missing_columns_and_r_engine_status(self):
        response = self.client.post(
            "/api/modules/motif-logo/precheck",
            json={"data": "wrong\tcolumns\nA\t1\n", "source": "paste"},
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["engine"], "r")
        self.assertIn("engineStatus", payload)
        self.assertTrue(any("Missing required column" in error for error in payload["errors"]))

    def test_unknown_module_and_failed_render_errors_are_clear(self):
        missing = self.client.get("/api/modules/not-a-module")
        self.assertEqual(missing.status_code, 404)

        failed_job = self.client.post(
            "/api/jobs",
            json={
                "moduleSlug": "volcano",
                "data": "gene\twrong\nA\t1\n",
                "options": {},
                "sessionId": self.session_id,
            },
        )
        self.assertEqual(failed_job.status_code, 200)
        self.assertEqual(failed_job.json()["status"], "failed")
        self.assertTrue(any("Missing required column" in error for error in failed_job.json()["errors"]))

    def test_r_job_artifact_flow_when_r_is_available(self):
        if not check_r_engine().available:
            self.skipTest("R is unavailable in this environment.")

        module = get_module("motif-logo")
        job = self.client.post(
            "/api/jobs",
            json={
                "moduleSlug": module.slug,
                "data": module.demo_data,
                "options": module.default_options,
                "sessionId": self.session_id,
            },
        )
        self.assertEqual(job.status_code, 200)
        payload = job.json()
        self.assertEqual(payload["status"], "succeeded", payload["errors"])
        for export_format in module.export_formats:
            artifact = self.client.get(payload["artifacts"][export_format])
            self.assertEqual(artifact.status_code, 200)

    def test_every_registered_module_has_api_detail(self):
        for module in list_modules():
            with self.subTest(module=module.slug):
                response = self.client.get(f"/api/modules/{module.slug}")
                self.assertEqual(response.status_code, 200)


if __name__ == "__main__":
    unittest.main()
