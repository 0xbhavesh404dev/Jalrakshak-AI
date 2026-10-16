# MASTER PROMPT — Build JalRakshak AI
## Sensor-Ready Smart Irrigation Advisory Web Platform

**Give this entire file to your coding agent together with `DOCUMENTATION.md`. Tell the agent to read `DOCUMENTATION.md` first, then follow this master prompt.**

---

## 1. Your role and goal

Act as a senior full-stack Python engineer, embedded-integration engineer, applied ML engineer, tester, and UI designer. Build **JalRakshak AI**, a sensor-ready irrigation advisory web platform for the AI BOTS-2026 hackathon.

**Tagline:** *Predict the Need. Save Every Drop.*

The app must answer one practical question:

> **“Does this field probably need irrigation today, or can the farmer safely wait and check again?”**

The hardware prototype uses an ESP32, FC-28 or capacitive soil-moisture sensor, DHT11 temperature/humidity sensor, breadboard, male-to-male jumper wires, USB data cable, and an LED with a 220-ohm resistor. The current app does not yet ingest ESP32 readings, so it estimates field water conditions from weather data, crop and soil information, irrigation history, and optional farmer observations until the integration is implemented. It must never describe estimates as measurements or uncalibrated raw readings as percentages.

The finished app should:
- Run locally on a normal laptop.
- Look like a polished, modern web portal, not a plain notebook.
- Be understandable to a farmer or judge.
- Work with live weather when internet is available.
- Have an offline demo mode that uses clearly labelled sample data.
- Be demonstrable in about 3 minutes.
- Prefer a small, correct, tested product over many incomplete features.

Do not promise that this prototype guarantees crop health or real-world water savings. Clearly show its assumptions and limitations.

---

## 2. Mandatory working method

For every phase, follow:

**BUILD → RUN → VERIFY → FIX → LOG → COMMIT → NEXT**

1. Build only the current phase.
2. Run the stated commands and tests. Read the actual output.
3. Fix errors and rerun the checks. Never claim a test passed unless you ran it.
4. If the same issue fails five times, simplify the feature, record why in `DECISIONS.md`, and continue.
5. Update `PROGRESS.md` with date/time, files changed, checks run, results, and remaining issues.
6. Commit each completed phase with a message such as `phase 2: add weather fallback`.
7. Keep the application runnable after every phase.
8. Do not ask questions. Make a sensible, conservative assumption and document it in `DECISIONS.md`.
9. Finish all **P0** requirements before working on P1 or P2.
10. Never claim the project is finished while required tests are failing.

### Priority labels
- **P0 — Essential:** required for the minimum working demo.
- **P1 — Important:** add only after all P0 features work.
- **P2 — Optional:** omit if time is short.

---

## 3. Non-negotiable honesty and safety rules

1. **Sensor boundary:** root-zone water, depletion, crop stress, irrigation quantities, and recommendations remain estimates unless explicitly supported by validated sensor inputs. Keep hardware measurements separate from modelled estimates and identify their source.
2. **Keep two water quantities separate:**
   - The app's **estimated root-zone water balance**, reported in millimetres and based on crop/soil assumptions.
   - Open-Meteo's **modelled surface soil moisture**, if available, reported separately in its own units and chart.
   Never combine them as if they were the same measurement.
3. Never train a model on random or invented data and present its output as a real ML result. Synthetic data may be used for unit tests only and must be labelled.
4. Do not invent model-accuracy numbers. Show actual validation results or say validation could not be completed.
5. “Data quality: High/Medium/Low” describes the quality and completeness of inputs; it is **not** the probability that a recommendation is correct.
6. Label all simulated water savings as **“simulated compared with the stated baseline”**, never as proven field savings.
7. Every irrigation recommendation page must show:
   > “This is an estimate based on weather data and standard crop parameters. Check the soil in the field before irrigating and follow local agricultural advice.”
8. Do not make unsupported claims such as “guarantees water savings”, “prevents crop failure”, or “knows the actual soil moisture”.
9. No API keys in source code. Use `.env` and include `.env.example`. Never log or display secrets.
10. Every external request needs a timeout, error handling, and a fallback. Never show raw stack traces to users.
11. Use simple language and clear units. Explain assumptions in an expandable “How this is calculated” section.
12. The system is an advisory prototype, not a replacement for a local agricultural officer or a field soil check.

---

## 4. Product scope and user journey

A farmer or judge should be able to:

1. Open the landing page and understand the problem in 10 seconds.
2. Create a farm in under one minute.
3. Choose location, crop, soil, field area, irrigation method, and sowing date.
4. See weather and the source/freshness of that weather.
5. See one clear action: `IRRIGATE NOW`, `IRRIGATE SOON`, `WAIT`, `RAIN EXPECTED — RECHECK`, or `NO ACTIVE CROP`.
6. See the reasons, estimated amount in mm and litres, best suggested time, and data-quality level.
7. Change a weather scenario (for example, heatwave or no rain) and see how the estimate changes.
8. Ask a basic question in English, Telugu, or Hindi and get an explanation based on the displayed results.
9. Run the demo without internet using an obvious “OFFLINE DEMO DATA” banner.

### Core user interface
Build a polished Streamlit multi-page web app with:
- A landing page with a strong hero section, concise description, and “Get Started” button.
- A clean sidebar with icons and clear page names.
- Consistent typography, spacing, green agricultural colour accents, accessible contrast, and responsive layouts.
- Cards for the recommendation and important metrics.
- Interactive Plotly charts with titles, axes, units, legends, and readable tooltips.
- Text and icons in addition to colour; colour alone must not communicate status.
- Clear loading, empty, warning, and error states.
- Avoid unsafe or brittle HTML. If custom CSS is used, keep it in one reusable file.

---

## 5. Fixed technology stack

Use these technologies unless a documented technical blocker requires a change:

- **Language:** Python 3.10+
- **Web UI:** Streamlit multipage app + small, centralized custom CSS
- **Charts:** Plotly
- **Data:** pandas and NumPy
- **Weather/geocoding:** Open-Meteo public APIs (no key expected for the selected endpoints; check current documentation before coding)
- **Database:** SQLite through Python's standard `sqlite3`
- **ML:** scikit-learn
- **Optional LLM:** Gemini REST API using `requests`; never required for the core app
- **Map (P1):** Folium + `streamlit-folium`, only if it works reliably and does not delay P0
- **Tests:** pytest + Streamlit `AppTest`
- **Configuration:** python-dotenv
- **Model persistence (if used):** joblib

Do not introduce React, Flask, TensorFlow, a paid database, or extra infrastructure. Do not add dependencies without a clear reason.

Before implementing an API call, check the provider's current official documentation and use the currently supported variable names and endpoint parameters.

---

## 6. Folder structure — create this structure

```text
jalrakshak-ai/
├── app.py
├── pages/
│   ├── 1_Farm_Setup.py
│   ├── 2_Dashboard.py
│   ├── 3_Weather_Intelligence.py
│   ├── 4_Digital_Twin.py
│   ├── 5_AI_Agronomist.py
│   └── 6_Water_Usage.py
├── core/
│   ├── __init__.py
│   ├── config.py
│   ├── crops.py
│   ├── soils.py
│   ├── weather.py
│   ├── waterbalance.py
│   ├── decision.py
│   ├── ml.py
│   ├── simulator.py
│   ├── optimizer.py
│   ├── agronomist.py
│   ├── i18n.py
│   ├── db.py
│   ├── advisory.py
│   └── ui.py
├── assets/
│   ├── styles.css
│   └── logo.svg                 # optional; simple local asset
├── data/
│   ├── sample_weather_hyderabad.json
│   └── cache/                   # generated at runtime; gitignored
├── models/                      # trained model cache; gitignored
├── tests/
│   ├── conftest.py
│   ├── test_config.py
│   ├── test_crops.py
│   ├── test_soils.py
│   ├── test_weather.py
│   ├── test_waterbalance.py
│   ├── test_decision.py
│   ├── test_db.py
│   ├── test_simulator.py
│   ├── test_optimizer.py
│   ├── test_ml.py
│   ├── test_i18n.py
│   └── test_pages.py
├── .streamlit/
│   └── config.toml
├── .env.example
├── .gitignore
├── requirements.txt
├── DOCUMENTATION.md
├── README.md
├── PROGRESS.md
├── DECISIONS.md
├── DEMO_SCRIPT.md
└── JUDGE_QA.md
```

Rules:
- Keep calculations and business rules in `core/`, not inside page files.
- `core/` modules must not import Streamlit.
- Pages call functions in `core/` and focus on presentation.
- Keep constants and thresholds in `core/config.py` or the relevant domain module.
- Use parameterized SQL queries.
- Use a new/short-lived SQLite connection per operation.
- Do not commit `.env`, database files, cache files, model files, or virtual environments.

---

## 7. Data model and farm inputs

### Farm profile
Store:
- `id`
- `name`
- `place`
- `latitude`, `longitude`
- `crop`
- `soil`
- `irrigation_method`
- `area_acres`
- `sowing_date`
- optional `harvest_date`
- `created_at`

### Irrigation log
Store:
- `id`, `farm_id`, `date`
- `gross_mm`
- `method`
- optional `note`

### Farmer observation
Store:
- `id`, `farm_id`, `date`
- `state`: `dry`, `moist`, or `wet`

### Recommendation history
Store:
- `id`, `farm_id`, `date`
- `action`, `net_mm`, `gross_mm`, `litres`
- `data_quality`
- JSON containing the structured reasons and important inputs

Add appropriate foreign keys and cascading deletion where supported. Validate user inputs. Do not allow negative area or invalid dates.

---

## 8. Crop, soil, and irrigation assumptions

Treat these as approximate standard values, not universal truth. Put source notes in code comments and explain that local varieties, weather, and farming practices can change them. Use the FAO-56 approach as a simplified reference and do not claim this prototype is a certified agronomic tool.

### Crop table

Use these initial crop values, with stage lengths in days `(initial, development, mid, late)`, crop coefficient values `(Kc_initial, Kc_mid, Kc_end)`, maximum effective root depth in metres, and depletion fraction `p`.

| Crop | Stage days | Kc values | Maximum root depth (m) | p |
|---|---:|---:|---:|---:|
| Tomato | 30 / 40 / 40 / 25 | 0.60 / 1.15 / 0.80 | 0.8 | 0.40 |
| Chilli | 30 / 35 / 40 / 20 | 0.60 / 1.05 / 0.90 | 0.6 | 0.30 |
| Cotton | 30 / 50 / 55 / 45 | 0.35 / 1.15 / 0.70 | 1.0 | 0.65 |
| Maize | 20 / 35 / 40 / 30 | 0.30 / 1.20 / 0.60 | 0.8 | 0.55 |
| Groundnut | 25 / 35 / 45 / 25 | 0.40 / 1.15 / 0.60 | 0.6 | 0.50 |
| Rice (paddy) | 30 / 30 / 60 / 30 | 1.05 / 1.20 / 0.90 | 0.5 | 0.20 |

Implement:
- `kc_for(crop, age_days)`: constant during initial stage, linear rise during development, constant at mid-stage, linear decline during late stage, then Kc_end.
- `root_depth(crop, age_days)`: starts at 25% of maximum and grows linearly to maximum by the end of development, then remains constant.
- `p_adjusted(p, etc) = clip(p + 0.04 * (5 - etc), 0.10, 0.80)`.
- `crop_status`: not yet sown, growing, late stage (seven or fewer days to harvest), or fallow/harvested.
- If harvest date is omitted, estimate it from the crop's listed stage lengths and clearly label it as estimated.

For rice, show a note that paddy normally uses standing water and this simplified model is less reliable for rice.

### Soil table

Approximate plant-available water capacity (`awc`) in mm per metre:
- Sandy: 80
- Sandy loam: 110
- Loamy: 140
- Clay loam: 160
- Clay: 180

Show a short plain-English note for each soil type. Irrigation application efficiencies:
- Drip: 0.90
- Sprinkler: 0.75
- Flood/furrow: 0.60

### Unit conversions
- Water depth is in mm.
- `1 mm over 1 acre = approximately 4,047 litres`.
- `litres = gross_mm × 4,047 × area_acres`.
- Use consistent units throughout. Add unit tests for conversions.

---

## 9. Weather data service

Implement `core/weather.py` with:
- `search_places(name)` using the current Open-Meteo geocoding endpoint, plus a small built-in preset list if geocoding fails.
- `get_weather(latitude, longitude, past_days=60, forecast_days=7)` returning a documented data object or dictionary containing daily:
  `date, tmax, tmin, rain, rain_prob, et0, humidity, wind, sm_model, is_forecast`.
- Current weather may be displayed if available, but recommendations must use clearly defined daily data.
- Cache successful responses locally.
- Fallback order: **live API → cached response → bundled sample data**.
- `JALRAKSHAK_OFFLINE=1` must go directly to bundled sample data.
- Display source and age: `Live weather`, `Cached weather`, or `OFFLINE DEMO DATA — sample weather`.
- Add request timeouts, input validation, schema checks, and graceful error messages.
- Handle missing values and dates carefully. Do not silently fill large missing sections with fabricated values.
- Bundle a sample dataset with dates relative to the demo date or rebase dates safely when loading it.
- Use sample data only for demo/fallback and clearly label it.
- Add a test for every fallback path. Mock network calls in unit tests; do not require internet for the normal test suite.

---

## 10. Water-balance engine

Implement `core/waterbalance.py` as pure, testable Python. Suggested interface:

`run_balance(weather_df, farm, irrigation_events, observations, pessimistic=False) -> pandas.DataFrame`

Use root-zone depletion `Dr` in mm:
- `Dr = 0` means root zone is at field capacity.
- `TAW` is total available water, in mm.
- `storage = TAW - Dr`.
- `ETc = Kc × ET0`.
- `TAW = awc × effective_root_depth`.
- `RAW = p_adjusted × TAW`.
- Effective rain: 0 mm when daily rain is under 2 mm; otherwise `0.8 × rain` as a documented simplification.
- Irrigation net input: `gross_mm × efficiency(method)`.
- Stress indicator: `Dr > RAW`.
- Water-stress coefficient:
  - `Ks = 1` when `Dr <= RAW`.
  - Otherwise `Ks = max(0, (TAW - Dr) / (TAW - RAW))`.
- `ETa = Ks × ETc`.
- Update depletion using effective rain, net irrigation, and actual crop use, then clamp it to `[0, TAW]`.
- Track drainage when the balance implies water above field capacity.
- If root depth increases, do not arbitrarily reset existing depletion; document how newly accessed soil is treated.
- Observation reset: on a farmer observation date, set depletion to a configurable fraction of TAW:
  - Wet: `0.10 × TAW`
  - Moist: `0.45 × TAW`
  - Dry: `0.80 × TAW`
  These are rough assumptions and must be explained in the UI.
- Forecast rain can be weighted using documented probability bands; also provide a pessimistic projection that gives no credit to forecast rain.
- Return columns such as:
  `is_forecast, tmax, tmin, rain, rain_prob, et0, kc, etc, eta, ks, root, taw, raw, peff, irrigation_net, drainage, storage, depletion, stress`.

Important:
- Define the start date and initial condition clearly. If there is no farmer observation, state that the simulation assumes the root zone started wet/at field capacity at the chosen start date.
- Check water-balance arithmetic using hand-calculated examples and a mass-balance test.
- Do not claim exact field water content. This is a simplified estimate.

---

## 11. Irrigation decision engine

Implement `core/decision.py` with structured reason codes, not only hard-coded paragraphs.

Possible actions:
- `NO_CROP`
- `IRRIGATE_NOW`
- `IRRIGATE_SOON`
- `WAIT`
- `SKIP_RAIN_EXPECTED`

Use this decision order:
1. Check crop status. If not sown or fallow, return `NO_CROP`.
2. Check whether estimated storage is below the crop's readily available water threshold.
3. If stressed and meaningful rain is expected soon with sufficiently high rain probability, recommend rechecking after rain rather than automatically watering.
4. If stressed and meaningful rain is not expected, recommend `IRRIGATE_NOW`.
5. If not yet stressed, find the first forecast date when storage is projected to cross the threshold:
   - within 24 hours: `IRRIGATE_SOON`
   - within the next 7 days: `WAIT` with a planned reassessment/irrigation date
   - no crossing within 7 days: `WAIT`
6. Near harvest, avoid blindly recommending large irrigation amounts; show a caution and advise following crop-specific local guidance.

Make thresholds configurable and explain them. For each recommendation, show:
- Action and plain-language meaning
- 1–3 main reasons
- Estimated water depth in mm
- Estimated gross quantity in litres for the farm area, when applicable
- Suggested time (early morning may be suggested as a general guideline, not a guarantee)
- When to reassess
- Data-quality level and why
- The disclaimer from Section 3

Do not show a water amount when the engine cannot calculate it responsibly. Handle missing weather or missing farm data gracefully.

---

## 12. Machine learning: implement honestly and in the right order

### Critical design rule
Do not compare unlike quantities as though they were equal. The root-zone balance estimates water available to crop roots in mm. Open-Meteo's modelled surface moisture is a separate surface-layer quantity, often in volumetric fraction. A residual model that subtracts one directly from the other is invalid unless a defensible, validated conversion is established.

### P0
- Build the app and the physics/decision engine first.
- Include an ML page structure and a clear fallback state.
- If reliable historical training data is unavailable, show “ML forecast unavailable — the weather-based water-balance projection is still available.” Do not invent metrics or results.

### P1: ML forecast when real historical data is available
Prefer a clearly defined target that is consistently available from historical data. One feasible option is to forecast Open-Meteo's **modelled 0–7 cm surface soil moisture** using its own past values plus weather features. Label it as modelled surface moisture and keep it separate from root-zone storage.

Use scikit-learn quantile Gradient Boosting models (`loss="quantile"`, alpha 0.1, 0.5, 0.9) for each forecast horizon from 1 to 7 days if time and data permit. Features may include:
- Recent surface moisture and its changes
- Rain sums over recent days
- Recent ET0 and temperature
- Forecast rain and ET0, if available at inference
- Day-of-year sine/cosine features

Validation:
- Use a time-ordered split; never shuffle time-series rows randomly.
- Compare the median forecast with a persistence baseline (`future moisture = latest observed moisture`).
- Report actual MAE and 10–90% interval coverage for each horizon.
- State when the model does not beat persistence.
- Enforce `q10 <= q50 <= q90` and clip only to valid documented target bounds.
- Cache trained models and do not retrain on every Streamlit rerun.
- If API/history/model training fails, keep the main irrigation app working.

### P2: Residual correction
Only attempt a hybrid residual correction if a valid target and matched training pairs are available. Never compute a residual by subtracting root-zone millimetres from surface-moisture fractions. Do not claim the hybrid model beats the physics baseline unless real time-ordered validation proves it.

---

## 13. Digital Twin and schedule optimizer

Implement `core/simulator.py`:
- Let the user test temperature increase from 0 to +10 °C.
- Let the user adjust forecast rainfall from 0× to 3× and set an initial dry-spell length.
- Include presets: Normal, Heatwave, Failed Monsoon, Monsoon Burst, Rain Tomorrow, Recent Harvest.
- Clearly display **“SIMULATED SCENARIO — not a real weather forecast”** whenever a scenario is changed.
- Never modify historical observations; change only forecast inputs.
- Show the base forecast and scenario side by side: storage projection, estimated stress date, ETc, and recommendation.
- State that temperature-to-ET0 changes are approximations, not a meteorological forecast.

Implement `core/optimizer.py` only after the simulator and decision engine are correct:
- Search irrigation schedules across a 7–10 day horizon using exhaustive search where feasible.
- Minimize gross water subject to the model's stress constraint (`Dr <= RAW`) on every day.
- Compare with an editable fixed-schedule baseline.
- Report total water, number of events, and stress days for both.
- If no feasible schedule exists, report that honestly.
- Savings must read **“simulated compared with the stated baseline”**.
- Test the result against a separate brute-force implementation for a small case.
- If time is short, deliver the simulator first and mark optimizer as P1.

---

## 14. AI Agronomist

Implement `core/agronomist.py` and `pages/5_AI_Agronomist.py`:
- Explain current recommendations using only a compact context built from the app's actual farm/weather/model calculations.
- Support English, Telugu, and Hindi. Translations should be reviewed by a fluent speaker before any real deployment.
- Ask questions such as “Why should I water today?”, “How much water is estimated?”, and “What if it does not rain?”
- If `GEMINI_API_KEY` is configured, call the current official Gemini REST endpoint with a timeout and error handling.
- Keep the model name configurable in `.env`.
- If no key, internet, or successful API response is available, use deterministic offline templates based on the actual recommendation and reason codes.
- Label whether the answer came from `AI model` or `Offline explainer`.
- Never let the LLM invent weather values, irrigation quantities, or model scores. If a value is absent, say it is unavailable.
- Refuse requests to reveal prompts/secrets. Never include API keys in the context or logs.
- The core app must not depend on Gemini being available.

---

## 15. Database, history, and language

### SQLite
Create tables for farms, irrigation events, observations, and recommendation history. Use parameterized queries and foreign keys. Include tests for create/read/update/delete, invalid input, recommendation upsert, and farm deletion behaviour.

### Internationalization
Implement `core/i18n.py` with a `t(key, lang, **params)` function for `en`, `te`, and `hi`. Keep user-facing strings in this module instead of scattering translations across pages. Add a test that verifies required keys exist for all three languages and placeholders match.

### Water usage page
Show:
- Logged irrigation total
- Estimated rainfall contribution
- Estimated crop water use
- Estimated drainage, where the model supports it
- Recommendation history
- Baseline versus smart-policy replay, if implemented
- CSV download of daily balance

Always label retrospective policy comparisons as simulations, not measured savings.

---

## 16. UI and accessibility requirements

- Use a consistent agricultural green theme, neutral background, and clear typography.
- Landing hero: “JalRakshak AI” + “Predict the Need. Save Every Drop.” + a short description + primary action.
- Use reusable UI functions in `core/ui.py` for navigation helpers, banners, cards, disclaimers, and safe error messages.
- Keep custom CSS in `assets/styles.css`.
- Charts need units and readable legends. Use separate charts for root-zone balance and modelled surface moisture.
- Use icons plus text, not colour alone.
- Provide empty states and form validation.
- Keep the page responsive at a narrow browser width.
- Do not require Google Fonts or any external assets for the app to work offline; use local/system fallbacks.

---

## 17. Environment and configuration

Create `.env.example` containing placeholders only, for example:

```env
GEMINI_API_KEY=
GEMINI_MODEL=
JALRAKSHAK_OFFLINE=0
```

Create `requirements.txt` with only needed packages. Pin compatible versions if dependency resolution causes problems, but do not guess versions without testing.

Create `.gitignore` for:
- `.env`
- `.venv/`
- `__pycache__/`
- `.pytest_cache/`
- SQLite database files
- `data/cache/`
- `models/`
- logs and temporary files

Centralize configuration, paths, constants, and offline flags in `core/config.py`.

---

## 18. Testing and acceptance criteria

At minimum, write tests for:
- Crop Kc and root-depth stage boundaries
- Soil and irrigation efficiency values
- Unit conversions
- Weather parsing, missing values, and live/cache/sample fallback
- Water-balance no-rain, light-rain, heavy-rain, irrigation, stress, observation reset, and mass balance
- Every decision action and important boundary
- Database CRUD and validation
- Scenario invariants (normal scenario unchanged; historical rows unchanged)
- Optimizer feasibility and brute-force check if optimizer exists
- ML quantile order, time-ordered validation, and fallback if ML exists
- Missing translation keys
- Streamlit page smoke tests in offline mode

Required checks:
```bash
python -m compileall .
pytest -q
```

Run the app:
```bash
streamlit run app.py
```

If Streamlit AppTest is supported for a page, run it. Do not claim a browser visual check unless you actually performed it. Network-dependent tests must be mocked or marked as optional smoke tests.

### Final acceptance criteria
- The app launches without an exception.
- A farm can be created and remains saved after restart.
- The dashboard shows a recommendation with reasons, units, data source, data-quality explanation, and disclaimer.
- Offline demo mode works without internet and is clearly labelled.
- Heatwave/no-rain simulation changes the forecast projection in a sensible way.
- The app does not confuse root-zone estimates with modelled surface moisture.
- All required tests pass, or remaining failures are clearly documented.
- The 3-minute demo script can be completed from a fresh local start.
- No fake ML performance claims are displayed.

---

## 19. Development phases

### Phase 0 — Scaffold and run `[P0]`
Create the structure, requirements, configuration, `.env.example`, `.gitignore`, landing page, stub pages, `PROGRESS.md`, and `DECISIONS.md`. Initialize Git. Confirm the app launches.

### Phase 1 — Weather service and offline fallback `[P0]`
Implement Open-Meteo parsing, caching, sample data, and offline mode. Test every fallback without depending on internet.

### Phase 2 — Crop/soil tables and calculations `[P0]`
Implement crop coefficients, root depth, soil capacities, efficiencies, crop status, and unit conversions. Add unit tests.

### Phase 3 — Water balance and decision engine `[P0]`
Implement the water-balance engine and recommendation logic. Hand-check calculations and add mass-balance tests.

### Phase 4 — Database and farm setup `[P0]`
Build farm forms, validation, farm selection, irrigation logs, and dry/moist/wet observations. Verify data survives restart.

### Phase 5 — Dashboard and weather intelligence `[P0]`
Build the main recommendation card, metrics, reason list, weather-source banner, and charts.

### Phase 6 — Digital Twin simulator `[P0]`
Add heatwave and failed-monsoon scenarios first; add other presets if time permits. Verify scenarios do not modify historical weather.

### Phase 7 — Finalize offline UX and core tests `[P0]`
Test all core pages in offline mode. Fix layout and error handling. Do not move on while core demo is unstable.

### Phase 8 — ML forecast `[P1]`
Only when real historical target data can be downloaded and validated. Implement a separate surface-moisture forecast and honest baseline comparison. If unavailable, show a clean fallback.

### Phase 9 — Optimizer and Water Usage `[P1]`
Add schedule optimization, history, CSV download, and simulated comparison with a stated baseline.

### Phase 10 — AI Agronomist `[P1]`
Add offline templates first. Add Gemini only if time and API access permit.

### Phase 11 — UI polish and optional map `[P1/P2]`
Improve visuals, responsive layout, map, and advisory copy without breaking offline use.

### Phase 12 — Final QA and demo kit `[P0]`
Run tests, fresh-start check, offline test, update documentation, and prepare the demo script and judge Q&A.

**Important:** If hackathon time is running out, stop adding features and make the P0 flow reliable.

---

## 20. Required project documentation

Maintain these files:
- `DOCUMENTATION.md`: what the project does, how it works, architecture, formulas, ML limitations, and how to use it, in simple English.
- `README.md`: installation, run commands, environment setup, offline demo, tests, and limitations.
- `PROGRESS.md`: phase checklist and actual test results.
- `DECISIONS.md`: assumptions, simplifications, and deviations.
- `DEMO_SCRIPT.md`: timed 3-minute demo.
- `JUDGE_QA.md`: likely judge questions and honest answers.

Do not leave placeholder documentation after implementation. Update docs to match the code that actually exists.

---

## 21. Three-minute demo

1. **0:00–0:20 — Problem and home page:** “Farmers often decide when to irrigate using experience and guesswork. JalRakshak AI combines weather and crop information to give an explainable irrigation estimate.”
2. **0:20–0:50 — Farm setup:** select a prepared demo farm or create one.
3. **0:50–1:20 — Dashboard:** show the recommendation, estimated quantity, reasons, weather source, and disclaimer.
4. **1:20–2:00 — Digital Twin:** activate Heatwave or Failed Monsoon and show how the projection changes.
5. **2:00–2:30 — ML or fallback:** if a validated model is available, show its real validation table. Otherwise explain that the core water-balance model works and ML is unavailable in offline mode.
6. **2:30–3:00 — Close:** “No physical sensors are needed for this prototype. It gives explainable estimates, lets farmers explore weather scenarios, and reminds them to verify the soil before irrigating.”

---

## 22. Start instruction

Read `DOCUMENTATION.md` first. Then begin **Phase 0 only**. Build it, run the checks, fix failures, update `PROGRESS.md`, record assumptions in `DECISIONS.md`, and commit. Continue phase by phase. Do not attempt all features in one giant unverified code dump.
