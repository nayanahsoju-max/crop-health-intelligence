"""End-to-end integration verification tests for Stage 35."""
import requests

BASE_URL = "http://127.0.0.1:8000"


def test_history_persistence_and_retrieval():
    resp = requests.get(f"{BASE_URL}/predictions?limit=10")
    assert resp.status_code == 200, resp.text
    history = resp.json()
    assert isinstance(history, list)
    assert len(history) >= 3, f"Expected at least 3 records, got {len(history)}"

    # Check newest record
    record = history[0]
    assert "id" in record
    assert "predicted_class_id" in record
    assert "confidence" in record

    # Retrieve record detail
    detail_resp = requests.get(f"{BASE_URL}/predictions/{record['id']}")
    assert detail_resp.status_code == 200
    detail = detail_resp.json()
    assert detail["id"] == record["id"]
    assert detail["predicted_class_id"] == record["predicted_class_id"]
    assert "recommendation_result" in detail
    assert "result_metadata" in detail


def test_error_handling_cases():
    img_path = "data/PlantVillage/Tomato_Early_blight/0012b9d2-2130-4a06-a834-b1f3af34f57e___RS_Erly.B 8389.JPG"

    # 1. Missing crop
    with open(img_path, "rb") as f:
        resp = requests.post(f"{BASE_URL}/predict", files={"image": ("tomato.jpg", f, "image/jpeg")})
    assert resp.status_code == 422, resp.text
    err = resp.json()
    assert err.get("detail", {}).get("code") == "invalid_crop"

    # 2. Invalid crop (e.g. banana)
    with open(img_path, "rb") as f:
        resp = requests.post(f"{BASE_URL}/predict", files={"image": ("tomato.jpg", f, "image/jpeg")}, data={"crop": "banana"})
    assert resp.status_code == 422, resp.text
    err = resp.json()
    assert err.get("detail", {}).get("code") == "invalid_crop"

    # 3. Missing image
    resp = requests.post(f"{BASE_URL}/predict", data={"crop": "tomato"})
    assert resp.status_code == 422

    # 4. Unsupported image format (e.g. GIF)
    gif_bytes = b"GIF89a\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00\xff\xff\xff!\xf9\x04\x01\x00\x00\x00\x00,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;"
    resp = requests.post(f"{BASE_URL}/predict", files={"image": ("test.gif", gif_bytes, "image/gif")}, data={"crop": "tomato"})
    assert resp.status_code == 415, resp.text
    assert resp.json().get("detail", {}).get("code") == "unsupported_image_type"

    # 5. Corrupted image bytes
    corrupt_bytes = b"NOT_AN_IMAGE_AT_ALL_CORRUPT"
    resp = requests.post(f"{BASE_URL}/predict", files={"image": ("test.jpg", corrupt_bytes, "image/jpeg")}, data={"crop": "tomato"})
    assert resp.status_code == 400, resp.text
    assert resp.json().get("detail", {}).get("code") == "invalid_image"

    # 6. Oversized image (>10MB)
    huge_bytes = b"\x00" * (11 * 1024 * 1024)
    resp = requests.post(f"{BASE_URL}/predict", files={"image": ("huge.jpg", huge_bytes, "image/jpeg")}, data={"crop": "tomato"})
    assert resp.status_code == 413, resp.text
    assert resp.json().get("detail", {}).get("code") == "upload_too_large"

    # 7. Missing optional location (should succeed with weather_context.status == not_requested)
    with open(img_path, "rb") as f:
        resp = requests.post(f"{BASE_URL}/predict", files={"image": ("tomato.jpg", f, "image/jpeg")}, data={"crop": "tomato"})
    assert resp.status_code == 200
    res = resp.json()
    assert res["weather_context"]["status"] == "not_requested"
    assert res["prediction"]["class_id"] == "tomato_early_blight"
    assert res["explainability"]["status"] == "available"


def test_weather_fallback():
    img_path = "data/PlantVillage/Tomato_Early_blight/0012b9d2-2130-4a06-a834-b1f3af34f57e___RS_Erly.B 8389.JPG"
    # Nonexistent location
    with open(img_path, "rb") as f:
        resp = requests.post(f"{BASE_URL}/predict", files={"image": ("tomato.jpg", f, "image/jpeg")}, data={"crop": "tomato", "location": "NonExistentPlaceXYZ123456789"})
    assert resp.status_code == 200
    res = resp.json()
    assert res["weather_context"]["status"] in ("unavailable", "available")
    assert res["prediction_status"] == "accepted"


if __name__ == "__main__":
    test_history_persistence_and_retrieval()
    print("History test passed!")
    test_error_handling_cases()
    print("Error handling tests passed!")
    test_weather_fallback()
    print("Weather fallback test passed!")
    print("ALL E2E AUTOMATED TESTS PASSED!")
