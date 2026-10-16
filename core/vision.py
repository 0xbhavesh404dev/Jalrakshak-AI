"""Optional Gemini vision estimate from an in-memory field photo."""
import base64
import json

import requests

from .config import GEMINI_API_KEY, GEMINI_MODEL


def inspect_soil_photo(image_bytes, mime_type, soil_type, weather_summary):
    if not GEMINI_API_KEY:
        return None, "Add GEMINI_API_KEY in your local .env and restart the app to enable photo analysis."

    prompt = (
        "Assess only visible surface wetness cues in this close-up farm soil photo. Ignore soil colour completely. "
        "Do not infer moisture from colour, location, crop, or weather; weather and mapped soil are context only. "
        "Use visible sheen, water film, clumping, stickiness evidence, cracks, crust, and loose dry texture. "
        "If the photo does not clearly show soil or cues are insufficient, return Unknown. "
        "Do not claim a photo can measure subsurface moisture. "
        "Return only JSON with keys condition (one of Likely wet, Moist, Slightly dry, Likely dry, Unknown) "
        "and note (one short sentence). "
        f"Mapped/manual soil type: {soil_type}. Weather context: {weather_summary}."
    )
    payload = {
        "contents": [{"parts": [
            {"inline_data": {"mime_type": mime_type, "data": base64.b64encode(image_bytes).decode("ascii")}},
            {"text": prompt},
        ]}],
        "generationConfig": {"responseMimeType": "application/json"},
    }
    models = [GEMINI_MODEL]
    fallback_model = "gemini-3.6-flash"
    if GEMINI_MODEL != fallback_model:
        models.append(fallback_model)

    try:
        response = None
        for model in models:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
            response = requests.post(
                url,
                headers={"x-goog-api-key": GEMINI_API_KEY},
                json=payload,
                timeout=20,
            )
            if response.status_code == 503 and model != models[-1]:
                continue
            break

        response.raise_for_status()
        text = response.json()["candidates"][0]["content"]["parts"][0]["text"]
        data = json.loads(text)
        allowed = {"Likely wet", "Moist", "Slightly dry", "Likely dry", "Unknown"}
        if data.get("condition") not in allowed or not isinstance(data.get("note"), str):
            raise ValueError("Unexpected vision response")
        return data, None
    except requests.HTTPError as exc:
        status = exc.response.status_code if exc.response is not None else None
        if status == 503:
            return None, "Gemini is temporarily busy. Please try the photo estimate again in a little while."
        if status in (401, 403):
            return None, "Gemini rejected the API key or its permissions. Check that the key is valid and enabled for the Gemini API."
        if status == 429:
            return None, "Gemini API quota or rate limit reached. Check your Google AI Studio usage and try again later."
        return None, f"Gemini photo analysis failed (HTTP {status or 'error'}). Check the model setting and network."
    except (requests.RequestException, ValueError, KeyError, IndexError, TypeError):
        return None, "Photo analysis could not be completed. Check the API key and network, or use the weather estimate and a direct field check."


def photo_water_guidance(visual, water_balance_action, active_crop=True, crop_stage=None):
    """Combine visible surface cues with the crop water-balance recommendation."""
    if not active_crop or water_balance_action == "NO_CROP":
        return {
            "status": "NO ACTIVE CROP",
            "title": "No watering needed",
            "detail": "There is no active crop saved for this field.",
        }

    condition = visual.get("condition") if isinstance(visual, dict) else None
    if condition not in {"Likely wet", "Moist", "Slightly dry", "Likely dry"}:
        return {
            "status": "INSUFFICIENT PHOTO DETAIL",
            "title": "AI could not judge this photo",
            "detail": "Take a close, well-lit photo of bare soil so the AI can see surface moisture cues.",
        }

    balance_needs_water = water_balance_action in {"IRRIGATE_NOW", "IRRIGATE_SOON"}
    photo_looks_dry = condition in {"Slightly dry", "Likely dry"}

    if crop_stage == "late_stage" and balance_needs_water:
        return {
            "status": "CROP-STAGE CAUTION",
            "title": "Possible water need near harvest",
            "detail": "The photo and crop estimate suggest dryness, but this crop is near its harvest window. Avoid a large irrigation based only on a photo estimate.",
        }

    if photo_looks_dry and balance_needs_water:
        return {
            "status": "IRRIGATION LIKELY NEEDED",
            "title": "Photo suggests watering is needed",
            "detail": "The photo shows dry surface cues and the crop water-balance estimate also shows a root-zone deficit. This is a visual estimate, not a direct moisture measurement.",
        }
    if photo_looks_dry:
        return {
            "status": "NO IRRIGATION NEEDED NOW",
            "title": "No watering needed right now",
            "detail": "The surface looks dry, but the crop water-balance estimate does not show an immediate root-zone deficit.",
        }
    if balance_needs_water:
        return {
            "status": "CONFLICTING SIGNALS",
            "title": "Photo and crop estimate disagree",
            "detail": "The surface looks moist, but the crop water-balance estimate shows a root-zone deficit. A surface photo cannot confirm moisture deeper in the soil, so this estimate is uncertain.",
        }
    return {
        "status": "NO IRRIGATION NEEDED NOW",
        "title": "No watering needed right now",
        "detail": "The photo shows surface moisture and the crop water-balance estimate does not show an immediate root-zone deficit.",
    }
