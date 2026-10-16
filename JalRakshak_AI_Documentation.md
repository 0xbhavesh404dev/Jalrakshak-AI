# JalRakshak AI — Project Documentation
## Simple-English guide: what we are building and how it works

**Tagline:** *Predict the Need. Save Every Drop.*

## Current implementation snapshot (2026-10-16)

The project currently has a runnable Streamlit multi-page implementation. Core calculations and data handling are in `core/`; each page in `pages/` presents those functions. SQLite persists farms, irrigation events, farmer observations and one recommendation per farm per date. The Dashboard uses the latest historical balance row as the current estimate and forecasts only from future rows.

The offline sample is generated demonstration data and is not suitable for training or judging real forecast accuracy. The ML interface intentionally returns an unavailable message until suitable historical surface-moisture data and time-ordered validation are available. The schedule helper is an early bounded search and is not yet exposed as an optimizer workflow in the UI. The optional Gemini request is implemented but requires the owner to supply a key in local `.env`; the deterministic explanation is the default. See `PROJECT_HANDOFF.md` for verification and remaining work.

---

## 1. What is JalRakshak AI?

JalRakshak AI is a software application that helps a farmer decide whether a field may need irrigation today or whether the farmer can wait and check again.

Farmers need to think about several things before watering a crop:
- Has it rained recently?
- Is rain expected soon?
- How hot is the weather?
- Which crop is growing?
- How old is the crop?
- What type of soil is in the field?
- When was the field last irrigated?

JalRakshak AI brings these details together and gives the farmer a simple recommendation with reasons.

The software now includes an optional ESP32 ingestion path: firmware in `hardware/esp32_sensor.ino`, a local FastAPI service in `sensor_api.py`, a `sensor_readings` table in the existing SQLite database, and live sensor/history/prediction sections in the Streamlit dashboard. The owner still needs to wire and calibrate physical hardware; this code change did not test a physical board. Weather-based root-zone values remain estimates, while sensor predictions use a separately labelled calibrated relative percentage. The farmer should check the actual soil before following a recommendation.

### Hardware prototype contract

The ESP32 reads a moisture probe and DHT11, then posts a timestamped payload to the local API. Validation, stale status, calibration display, and a rule-based threshold baseline are implemented. The firmware's calibration flag defaults to false. The 30% dry threshold is a configurable demonstration rule, not a scientifically validated irrigation policy. Hardware readings and weather-model estimates are visibly distinct. The optional LED is not implemented, and there is no pump, relay, valve, or automatic watering control.

## 2. What problem are we solving?

A farmer may water a field too early, use more water than needed, or wait too long during hot, dry weather. Weather alone does not answer whether a particular crop in a particular field needs water.

Our project tries to give a more useful answer by combining:
1. Weather data
2. Crop type and growth stage
3. Soil type
4. Field area and irrigation method
5. Previous irrigation records
6. A simple crop-water calculation
7. Optional machine learning and scenario simulation

The goal is to support a farmer's decision, not replace the farmer's experience or local agricultural advice.

## 3. Who can use it?

- Small and medium-sized farmers
- Students and agricultural project teams
- Demonstrators who want to understand irrigation planning
- Agricultural educators who want to explain the effect of weather on crop water needs

The first version is a prototype. It must be tested with real farms and local agricultural experts before being relied on for actual irrigation decisions.

## 4. What will the application do?

### A. Farm Setup
The user enters:
- Farm name and location
- Crop
- Soil type
- Field area
- Irrigation method, such as drip, sprinkler, or flood/furrow
- Sowing date and optional harvest date

The app stores the farm details locally in an SQLite database.

### B. Weather Intelligence
The app tries to get weather information from Open-Meteo, such as:
- Maximum and minimum temperature
- Rainfall and rain probability
- Reference evapotranspiration (ET0)
- Humidity and wind, when available

The app shows whether the information is live, cached, or sample data. If the internet is unavailable, the app can use bundled sample weather for a demonstration. It must clearly display an **OFFLINE DEMO DATA** warning.

### C. Irrigation Dashboard
The dashboard gives one main recommendation:
- **IRRIGATE NOW:** the model estimates that the crop may already be short of available water.
- **IRRIGATE SOON:** the model estimates that the water threshold may be crossed soon.
- **WAIT:** the model estimates that irrigation may not be needed immediately.
- **RAIN EXPECTED — RECHECK:** rain may provide water soon, so the farmer should reassess after the rain.
- **NO ACTIVE CROP:** the crop has not been planted yet or the recorded crop season has ended.

The dashboard also shows the reasons, estimated water quantity when it can be calculated, forecast summary, data-quality level, and a disclaimer.

### D. Digital Twin
A digital twin is a computer model that lets us test “what if?” situations.

For example:
- What if the next week is hotter?
- What if no rain falls?
- What if heavy rain arrives?
- What if the crop season has ended?

The user changes a slider or chooses a scenario. The app recalculates the estimated soil-water balance and recommendation.

A scenario is a simulation, not a real weather forecast.

### E. Machine-Learning Forecast (optional, after the core works)
If enough suitable historical data is available, the app can train a model to forecast Open-Meteo's **modelled surface soil moisture** for the next seven days.

This surface-moisture forecast is not the same as the app's estimated root-zone water balance. They must be displayed separately.

The model must be tested on later dates that were not used for training. It must be compared with a simple baseline, and the app must show the real test results. If training data or internet is unavailable, the app should explain that the ML forecast is unavailable rather than inventing results.

### F. AI Agronomist (optional)
The user can ask questions such as:
- Why does the app recommend watering?
- How much water is estimated?
- What could happen if there is no rain?

If a configured AI service is available, it can explain the app's existing results in English, Telugu, or Hindi. If not, prepared offline explanations should still work.

The chatbot must use the numbers calculated by the app. It must not invent weather, quantities, or accuracy figures.

### G. Water Usage and History (optional)
The app can show logged irrigation, estimated rainfall contribution, crop-water use, previous recommendations, and a comparison between an irrigation schedule and a baseline.

Any calculated saving must be called a **simulated saving compared with the stated baseline**. It is not proof of savings on a real farm.

---

## 5. How does it work? The full flow

```text
Farmer enters farm details
          |
          v
Weather data + crop + soil + irrigation history
          |
          v
Validate inputs and show data source
          |
          v
Crop-water balance calculation
          |
          v
Estimated root-zone water and stress threshold
          |
          v
Decision rules
          |
          v
Recommendation + reasons + estimated quantity
          |
          +------------------------------+
          |                              |
          v                              v
Digital Twin scenarios          Optional ML forecast
          |                              |
          +---------------+--------------+
                          |
                          v
                Dashboard and explanation
```

The main irrigation recommendation can work without the optional ML model or chatbot.

## 6. What is the water-balance calculation?

The app uses a simplified crop-water balance inspired by the FAO-56 approach. The values are approximate, and the result depends on the starting assumption and the quality of the input data.

Important terms:

- **ET0:** Reference evapotranspiration. It estimates the effect of weather on water loss from a reference surface.
- **Kc:** Crop coefficient. It adjusts ET0 to approximate the water use of a particular crop at a particular growth stage.
- **ETc:** Estimated crop water use. The simplified calculation is `ETc = Kc × ET0`.
- **TAW:** Total available water in the crop's effective root zone.
- **RAW:** Readily available water. It is an estimated threshold used to indicate when the crop may begin to experience water stress.
- **Depletion (`Dr`):** Estimated amount of available root-zone water that has been used up. In this model, zero depletion means the root zone is at field capacity.
- **Effective rainfall:** The part of rainfall that the simplified model counts as entering the root zone.
- **Irrigation efficiency:** The share of applied water estimated to reach the useful root zone.

The model updates its estimate using crop water use, effective rainfall, and logged irrigation. It limits the calculated depletion to physically reasonable model bounds.

### Weather inputs and modelled soil moisture

The live service calls Open-Meteo's free `/v1/forecast` endpoint with the saved field coordinates; no API key is required. Current air temperature, relative humidity, precipitation, rain and wind are requested as current/hourly values. Daily precipitation and FAO reference evapotranspiration (ET₀) supply the water-balance series. Open-Meteo's hourly soil-water layers use depths of 0–1, 1–3, 3–9, 9–27 and 27–81 cm. The dashboard's 0–7 cm and 7–28 cm figures are depth-weighted averages of those layers, retained as volumetric content (m³/m³) and shown as a percentage. They are weather-model estimates, not sensor measurements. The API provides the requested units and available layers; some model/location combinations can omit soil moisture.

When a complete API profile covers the crop's current modeled root depth (at most 81 cm), the app estimates profile depletion as the difference between texture-specific field capacity and modelled volumetric water content, integrated across the root depth. Field capacity is approximated as the app's soil available-water value plus a texture-specific permanent-wilting-point assumption: Sandy 0.05, Sandy loam 0.08, Loamy 0.12, Clay loam 0.18 and Clay 0.27 m³/m³. These are coarse prototype assumptions, not lab-measured soil constants. That API-derived estimate updates today's crop-specific water-stress check; the existing water-balance forecast projects changes using crop ETc, rainfall and irrigation. If any required soil layer is missing or the crop root depth exceeds 81 cm, the recommendation falls back to the weather/crop/soil water-balance estimate without fabricating an API reading.

The water-balance fallback begins at field capacity at the oldest day in its fetched history, counts 80% of rainfall of at least 2 mm as effective, and scales forecast rain by its probability. Crop coefficient, root depth and readily-available-water threshold vary by crop; available-water capacity varies by selected soil. Logged irrigation and field observations update the estimate. These simplified assumptions need field validation and can be wrong locally. The dashboard uses a recent per-location cache; if no live or cached forecast is available, it displays an unavailable message instead of giving advice based on another location's sample data. Bundled sample weather is used only when demo mode is explicitly enabled.

### Important limitation
The water-balance estimate does not directly measure root-zone water. A calibrated probe can provide a relative soil-moisture reading, but this is not volumetric water content or a lab measurement. The model can be wrong if its initial condition, local soil, crop variety, rainfall, irrigation log, or probe calibration differs from assumptions. A farmer can enter a Dry, Moist, or Wet observation to adjust the estimate.

## 7. How do we estimate the water quantity?

The app estimates a water depth in millimetres. If it has enough information, it converts the gross irrigation depth into litres:

`Estimated litres = gross irrigation depth (mm) × 4,047 × field area (acres)`

This conversion is approximate. The gross amount accounts for the selected irrigation method's assumed efficiency.

The app should not display a precise water quantity if the necessary inputs are missing or invalid.

## 8. How is machine learning used?

Machine learning is not the same as the water-balance calculation.

- The **water-balance engine** uses documented formulas and assumptions.
- The **decision engine** applies clear rules to the water-balance result.
- The optional **ML model** learns patterns from historical data to forecast modelled surface soil moisture.
- The optional **AI Agronomist** explains existing results in natural language.

For a fair ML test, the data must be split by time: older records for training and later records for testing. The model should be compared with a simple persistence baseline, which assumes tomorrow's moisture will be the same as the latest observed value.

If the ML model performs worse than the baseline, the application must say so. It must not claim that AI is more accurate without evidence.

## 9. What is the Digital Twin?

The Digital Twin is a simulation of how the estimated field water balance might change under different weather assumptions.

Example:
1. Open the current weather scenario.
2. Select **Heatwave**.
3. The app raises the forecast temperature using a documented approximation.
4. The app recalculates crop-water use and estimated depletion.
5. The app shows whether the projected irrigation date changes.

This helps users understand why hotter or drier conditions may change an irrigation plan. It does not predict the actual weather and must always show a simulation warning.

## 10. Technology used

| Technology | Purpose |
|---|---|
| Python | Main programming language |
| Streamlit | Builds the web interface |
| pandas and NumPy | Organizes data and performs calculations |
| Plotly | Interactive charts |
| Open-Meteo | Weather, forecast, and geocoding data |
| SQLite | Saves farms, irrigation logs, observations, and recommendations locally |
| scikit-learn | Optional machine-learning model |
| Gemini API | Optional natural-language explanation |
| pytest | Tests calculations and application logic |
| Git | Tracks development changes |

The core app should run without a Gemini API key. Live weather requires internet; offline demo mode uses bundled sample data.

## 11. Folder structure explained

```text
jalrakshak-ai/
├── app.py                 Main landing page
├── pages/                 Each page of the web app
├── core/                  Weather, crop, soil, calculations, ML, database
├── assets/                CSS and local visual assets
├── data/                  Bundled sample weather and runtime cache
├── models/                Optional trained model cache
├── tests/                 Automated tests
├── .streamlit/            Streamlit theme settings
├── .env.example           Example environment variables; no real secrets
├── requirements.txt       Python packages needed
├── DOCUMENTATION.md       This explanation
├── README.md              Setup and run instructions
├── PROGRESS.md            Completed phases and test results
├── DECISIONS.md           Assumptions and simplifications
├── DEMO_SCRIPT.md         Three-minute demonstration plan
└── JUDGE_QA.md            Likely judge questions and honest answers
```

The `pages/` files show information and collect user input. The `core/` files do the actual calculations. This separation makes the project easier to test and maintain.

## 12. How we will build it

We should build the project in small phases instead of asking a coding agent to generate everything at once.

1. **Start the app:** create folders, dependencies, theme, landing page, and empty page files.
2. **Get weather working:** add live weather, cache, and offline sample fallback.
3. **Add crop and soil information:** implement tables and unit conversions.
4. **Build the water-balance engine:** test the formulas with hand-calculated examples.
5. **Build the recommendation rules:** test cases such as recent rain, hot/dry weather, and harvested fields.
6. **Save farm data:** create farm setup, irrigation history, and farmer observations.
7. **Build the dashboard:** show recommendation, reasons, weather, and charts.
8. **Build the Digital Twin:** simulate heatwave and no-rain conditions.
9. **Test offline operation:** ensure the core demonstration works without internet.
10. **Add optional features:** ML, optimizer, chatbot, map, and additional polish only when the core works.
11. **Run final checks:** execute tests, start from a clean setup, and rehearse the demonstration.

After every phase, run tests, fix failures, update `PROGRESS.md`, record decisions, and commit the work.

## 13. How to run the project

The coding agent must fill in the exact instructions in `README.md` after verifying them. The expected local setup is:

1. Install Python 3.10 or later.
2. Open a terminal in the project folder.
3. Create and activate a virtual environment.
4. Install packages from `requirements.txt`.
5. Copy `.env.example` to `.env` if optional settings are needed.
6. Run `streamlit run app.py`.
7. To force offline demo mode, set `JALRAKSHAK_OFFLINE=1` in the environment before starting the app.

The final README must provide tested commands for Windows PowerShell and macOS/Linux. Do not claim a command works until it has been tested in the available environment.

## 14. How we will test it

We will test the important parts separately:
- Crop stages and crop coefficients
- Soil-water assumptions and unit conversions
- Weather response parsing and offline fallback
- Water balance for dry weather, rain, irrigation, and stress
- Recommendation decisions
- Database saving and loading
- Digital Twin behaviour
- ML validation and fallback, if ML is implemented
- Missing translations
- App pages in offline mode

Run:

```bash
python -m compileall .
pytest -q
streamlit run app.py
```

Network tests should be mocked for normal unit testing. A separate live API check may be run when internet is available.

## 15. Three-minute demonstration plan

**0:00–0:20 — Introduce the problem**  
“Farmers need to decide when to irrigate, but weather alone does not tell them how much water their crop may need.”

**0:20–0:50 — Set up a farm**  
Choose a demo farm or enter crop, soil, area, location, and sowing date.

**0:50–1:20 — Show the dashboard**  
Explain the recommendation, its reasons, estimated quantity, weather source, and disclaimer.

**1:20–2:00 — Show the Digital Twin**  
Choose Heatwave or Failed Monsoon and show how the estimated projection changes.

**2:00–2:30 — Show the ML feature or explain the fallback**  
If real validation results are available, show them. If not, be honest and show the working water-balance estimate.

**2:30–3:00 — Finish**  
“JalRakshak AI combines weather, crop information, explainable calculations, and optional calibrated ESP32 readings to support irrigation planning. The current hardware threshold is a simple baseline, the water balance is an estimate, and all recommendations should be checked in the field.”

## 16. Limitations we must explain honestly

- The ESP32 ingestion software is implemented, but physical wiring, probe calibration, and board-to-app operation still need a real hardware test.
- Soil-moisture percentages are calibrated relative readings, not volumetric water content.
- The root-zone water balance is an estimate, not a measurement.
- Weather forecasts may be wrong or unavailable.
- Crop and soil values are simplified assumptions.
- Rice/paddy is less suitable for this simplified model because it often uses standing water.
- No trained ML model is bundled. A training/evaluation script is available for a suitable measured or expert-labelled dataset; the simple threshold predictor is not validated.
- Digital Twin results are simulated.
- Water savings are simulated against a stated baseline, not proven on a farm.
- Telugu and Hindi translations should be checked by fluent speakers.
- Field testing and review by agricultural experts are needed before real-world reliance.

## 17. Final project message

JalRakshak AI is a practical software prototype that turns weather and crop information into an explainable irrigation estimate. Its main strength is helping a farmer understand **why** the system suggests watering or waiting, and how that suggestion might change under different weather conditions.

The goal is not to pretend that software can see the soil. The goal is to provide useful, transparent decision support that a farmer can check against real field conditions.
