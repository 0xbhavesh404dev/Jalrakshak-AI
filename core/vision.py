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
