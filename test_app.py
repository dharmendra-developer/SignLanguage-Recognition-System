import tempfile
import unittest
from pathlib import Path

from app import create_app


class SignVoiceApiTestCase(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        base = Path(self.temp_dir.name)
        self.app = create_app({
            "TESTING": True,
            "DATABASE": str(base / "test.db"),
            "MODEL_PATH": str(base / "artifacts" / "gesture_model.joblib"),
        })
        self.client = self.app.test_client()

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_health_and_not_found(self):
        response = self.client.get("/api/health")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.get_json()["ok"])
        self.assertEqual(response.get_json()["samples"], 0)

        response = self.client.get("/api/does-not-exist")
        self.assertEqual(response.status_code, 404)
        self.assertIn("error", response.get_json())

    def test_add_validate_predict_and_reset_samples(self):
        features = [0.0] * 63
        response = self.client.post("/api/samples", json={
            "label": "HELLO",
            "hindi_label": "नमस्ते",
            "samples": [features],
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["saved"], 1)

        response = self.client.post("/api/predict", json={"features": features})
        self.assertEqual(response.status_code, 409)
        self.assertIn("not trained", response.get_json()["error"].lower())

        response = self.client.delete("/api/samples/hello")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["deleted"], 1)

        response = self.client.post("/api/samples", json={
            "label": "HELLO",
            "hindi_label": "नमस्ते",
            "samples": [[1.0] * 62],
        })
        self.assertEqual(response.status_code, 400)

    def test_accept_dual_hand_samples(self):
        features = [0.0] * 126
        response = self.client.post("/api/samples", json={
            "label": "HELLO",
            "hindi_label": "नमस्ते",
            "samples": [features],
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["saved"], 1)


if __name__ == "__main__":
    unittest.main()
