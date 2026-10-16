# Decisions and assumptions

- Hardware prototype baseline is an ESP32, FC-28 or capacitive soil-moisture sensor, DHT11, breadboard, jumper wires and USB data cable. Sensor ingestion software now exists; root-zone water balance remains an estimate and physical wiring/calibration is still unverified. The optional LED is not implemented.
- Crop coefficients, root growth, readily available water, effective rain, observation resets and irrigation efficiencies use the approximate values in `JalRakshak_AI_Master_Prompt.md`.
- When root depth increases, existing depletion is scaled proportionally to new root-zone capacity; newly accessed soil is treated as having the same fractional depletion as the existing zone.
- Simulation begins at field capacity on the first available weather date in the absence of a farmer observation.
- Forecast effective rain is weighted by daily rain probability; pessimistic mode credits no forecast rain.
- Gemini is optional and its key is intentionally unset. Deterministic explanatory fallback keeps the core usable without credentials.
- No trustworthy labeled training set was supplied. We do not download or train on unrelated/invented data, and we report no ML score.
- Weather sample is synthetic demonstration data, clearly labelled, not for model training.
- Costly or paid APIs are not required. The app uses the public Open-Meteo endpoints with timeout and local fallback.
- ESP32 data uses the existing SQLite database through a separate local FastAPI process. The API defaults to loopback; non-loopback access requires a bearer token and uses a small request-body limit and a per-device one-second rate limit.
- Soil-probe values are calibrated relative percentages, not volumetric water content. Firmware ships with calibration disabled; the simple 30% threshold is configurable and not field-validated. Sensor and water-balance disagreement yields `INSUFFICIENT DATA` for inspection.
- Demo sensor values are generated only in the Streamlit session, visibly labelled, never persisted, and barred from producing an irrigation recommendation.
- The optional Random Forest training utility requires measured or expert-provided labels, uses an earlier/later chronological split, and compares with a threshold baseline. No model is bundled; only trusted local model artifacts should be loaded.
- Git initialization/phase commits depend on repository status; currently this folder may not have Git metadata. See `PROJECT_HANDOFF.md`.
