# JalRakshak AI — agent handoff and coordination log

Last updated: 2026-10-16 (Asia/Calcutta)

## Source of truth

Read `JalRakshak_AI_Documentation.md` first, then `JalRakshak_AI_Master_Prompt.md`. This file records what exists and what remains, to prevent repeated work. Update the phase table and verification section whenever work changes. Do not claim a check passed unless its command was run and its output reviewed.

## Coordination rules for the next agent

1. Inspect this handoff and `git status` before editing; avoid recreating completed files.
2. Work one phase at a time using BUILD → RUN → VERIFY → FIX → LOG → COMMIT → NEXT.
3. Keep domain calculations in `core/`, presentation in `pages/`; `core/` must not import Streamlit.
4. Add observed command output/date to the Verification log and record design deviations in `DECISIONS.md`.
5. Preserve the honesty constraints: estimates are not measurements, sample data is not training data, surface moisture is separate from root-zone millimetres, and simulated savings are not field savings.
6. Keep credentials blank in `.env.example`; never add secrets to source, logs, or this file.
7. Continue with outstanding P0 items before optional P1 work. Do not ask questions; make conservative assumptions and log them.

## Phase checklist

| Phase | Status | Notes |
|---|---|---|
| 0 Scaffold and runnable app | Implemented; server started | Streamlit landing page, theme, requirements, env template, ignore rules, pages; fresh Git repository initialized. |
| 1 Weather + offline fallback | Implemented; live API and unit checks pass | Free Open-Meteo geocoding/weather, response validation, hourly fill for missing daily totals, coordinate-keyed cache, explicit demo mode. No key required. |
| 2 Crop/soil calculations | Implemented; unit tests pass | Crop stages, root depth, adjusted p, soil water capacity, efficiencies, conversions. |
| 3 Water balance + decisions | Implemented; unit tests pass | Pure calculation module; uses actual use after stress coefficient. Broader mass-balance examples still needed. |
| 4 Database + farm setup | Implemented; CRUD unit test passes | SQLite CRUD, farm form, logs and observations. End-to-end restart persistence not manually checked. |
| 5 Dashboard + weather | Implemented; server health HTTP 200 | Simple recommendation, current weather and soil-moisture summary, collapsed seven-day forecast, source label and unavailable-data handling. |
| 5a Weather harvest outlook, optional soil map/photo | Implemented; 29 tests pass | Crop-calendar date plus forecast rain watch. Optional SoilGrids 250 m WCS lookup and camera/Gemini surface estimate; API key blank. Browser geolocation is requested only after a user presses its button. |
| 6 Digital Twin | Implemented; scenario unit test passes | Forecast-only scenario modifiers and presets. Optimizer not wired into UI. |
| 7 Offline UX + core tests | Implemented; 36 tests pass | Mocked API coverage includes missing daily values and hourly recovery. Streamlit page-render smoke check still needs browser review. |
| 8 ML forecast | Intentionally unavailable | No real training data. Keep separate surface-moisture target and honest fallback. |
| 9 Optimizer + Water Usage | Partial | CSV, logs/history, basic optimizer function; no tested schedule replay/baseline comparison. |
| 10 AI Agronomist | Partial | Deterministic fallback and optional Gemini request; API behavior not live-verified; credentials blank. |
| 11 UI polish/map | Simplified | Sidebar exposes only Home, Set up field, Today's field outlook, and Field notes. Weather exploration, scenarios, and AI Q&A are removed from navigation; source files remain for possible future reintroduction. |
| 12 Final QA + demo | Partial | Compile/tests pass; local server health endpoint returns HTTP 200. User browser review and demo rehearsal remain. |
| 13 ESP32 ingestion | Implemented in software; physical verification pending | FastAPI service, safe SQLite table creation, validated ingestion/latest/history endpoints, LAN token guard, ESP32 Arduino sketch, dashboard readings/history and rule baseline, optional labeled-data ML trainer. Physical wiring/calibration still needs the actual board. |

## Latest UX pass

- Navigation groups Home, Set up your farm, and Today's advice under `GET STARTED`; Weather, scenarios, questions, and logs under `EXPLORE`.
- Home explains the two-step flow and has direct calls to action. Farm Setup uses everyday labels and explains soil and location fields. Dashboard leads with “What should I do today?”, a plain-language next step, understandable metrics, the input-quality definition, and optional calculation details.
- Page-level `st.set_page_config` calls were removed so the app shell owns page setup and grouped navigation.
- Streamlit dependency minimum is 1.50 because the refreshed UI uses the `width="stretch"` API.
- Runtime reported `TypeError` for unsupported `type=` on `st.page_link`; removed the argument from all page links. Home now uses a high-contrast green gradient hero, the app background has a soft green/gold gradient, and sidebar/card contrast was strengthened.
- Core tests and compilation rerun after this UX pass: 18 tests passed; compilation passed. Streamlit health endpoint returned HTTP 200 on `127.0.0.1:8765`; visual review is pending from the user because the browser policy denied my reload action.
- Dashboard workflow now explains field selection, surface outlook, irrigation advice, field notes, and harvest recording. Surface outlook uses recent observed daily weather and states it is not a soil measurement. Rules: >=5 mm latest observed day or >=8 mm over last three observed days means “Likely wet”; >=2 mm means “Likely drying”; no significant rain plus average high >=32°C or ET0 >=5 mm/day means “Likely dry”; warm, nearly rain-free days can show “Slightly dry.” Thresholds are illustrative and should be tuned against local field observations.
- “Record harvest today” stores date and selected field's saved place/coordinates, idempotently per field/day. This uses farm setup location; the app does not capture device GPS. A recorded harvest changes today's crop status to fallow for irrigation advice.
- Farm location controls were outside the submit form so changing a search query refreshes only after a deliberate Search click; location dropdown and coordinate-entry mode are always visible. Dashboard links directly to Farm Setup. Soil map/camera controls sit in a collapsed optional expander.
- 2026-10-16: Applied the user's dark glass UI concept to the app shell and Dashboard. Sidebar starts collapsed; the recommendation and wet/dry status are computed from the selected farm's weather and crop data. No mock/example numbers are shown as live data.
- 2026-10-16: Simplified Dashboard after user screenshot feedback. Removed technical metric tiles (root-zone %, ETc, rain totals, crop stage), large harvest weather panel, and two charts from the main view. Main page now focuses on field surface wet/dry status, one non-redundant next action, compact harvest date, and optional harvest record. Soil map/photo remain collapsed and optional.
- Harvest timing shows the crop-calendar or entered expected date plus a near-date rain watch; it does not claim forecast weather can prove crop maturity. Camera input is held in memory for the page session and photo analysis is optional Gemini vision; prompt explicitly excludes colour as a moisture cue. API key remains blank.
- 2026-10-16 verification: `python -m compileall app.py pages core tests` passed; `python -m pytest --basetemp=.pytest-tmp -q` passed (**28 passed**); `git diff --check` passed with only CRLF normalization warnings. Live-mode Streamlit is running on `127.0.0.1:8766`; `/_stcore/health` returned HTTP 200. Port 8765 was unavailable when starting the revised live-mode process. Live weather still depends on API/network reachability; fallback uses cache or visibly labelled sample weather.
- AppTest smoke run for the standalone farm page did not return within the 15-second timeout; no page-render pass is claimed. The location picker logic and server health were checked; visual review remains with the user.
- 2026-10-16: Simplified sidebar to the core setup → outlook flow plus field notes. Removed Weather, scenario simulation, and AI Q&A from user-facing navigation. Kept requested harvest timing/record and optional soil map/photo tools.
- 2026-10-16: Added explicit browser location permission flow (button click required), coordinate-entry and place-search fallbacks, and automatic soil-texture estimation during setup when the user selects “Not sure.” Soil lookup requests paired sand/clay coverage subsets from SoilGrids WCS and tolerates tiny GeoTIFF grid-coordinate differences. Mapped texture is approximate, not a field measurement. API key remains blank.
- 2026-10-16: Screenshot showed the harvest action and soil/photo expander using pale text on a white surface. Added higher-specificity dark-theme CSS for Streamlit buttons and expander summary/body, including hover, keyboard focus, and disabled states.
- 2026-10-16: Combined duplicate wet/dry and irrigation banners into one plain-language “Today's advice” card. Keep technical weather reasons and numeric water estimates out of the default dashboard view.
- 2026-10-16: Weather sample banner traced to failed DNS resolution for `api.open-meteo.com`. Removed the prior paid customer-key branch per the new requirement: the free API needs no key. Fixed the request to use supported hourly soil layers instead of an unsupported daily soil-moisture field. Normal live failures now return an unavailable state (or same-location cache), not the bundled Hyderabad demo forecast.
- 2026-10-16: Added current/hourly/daily data normalization, 15-minute in-memory cache, asynchronous thread wrapper with UI spinner, current weather and moisture estimates, 24-hour rain total, ET₀, and a collapsed 7-day forecast table/chart. Soil moisture is depth-weighted from Open-Meteo's supported hourly layers and used to update today's crop-specific root-zone stress estimate when the full profile is available; otherwise the existing water-balance estimate is used. Assumptions/limits are recorded in the main documentation.
- 2026-10-16 verification: `python -m compileall -q app.py core pages tests`, `python -m pytest --basetemp=.pytest-tmp -q` (**31 passed**), and `git diff --check` passed.

## Verification log

- 2026-10-16: Added ESP32 sensor API and firmware path, same-database `sensor_readings` schema, dashboard sensor/history view, stale/calibration checks and an explicitly non-ML threshold baseline. Added optional chronological Random Forest training/evaluation script and labelled CSV template. Fixed a direct-open Weather page crash caused by its obsolete `sm_model` column expectation and fixed SQLite connections to close after each operation. Verified `./.venv/bin/python -m compileall -q app.py sensor_api.py core pages tests training` and `./.venv/bin/python -m pytest --basetemp=.pytest-tmp -q` (**43 passed**). Live local API health/read/write/latest/history smoke test passed against a temporary database; dashboard and Weather page AppTest smoke runs had zero exceptions in offline mode. No physical ESP32 was available or tested.

- Initial inspection: Python 3.12.10 available. Workspace had no Git repository; initialized a new `main` repository on 2026-10-16. No prior history existed.
- `python -m compileall .` completed successfully after implementation.
- `python -m pytest --basetemp=.pytest-tmp -q` completed: **18 passed**. The explicit basetemp is needed because the sandbox blocks pytest's default temp directory outside the workspace.
- After the core dashboard simplification, `python -m pytest --basetemp=.pytest-tmp -q` completed: **29 passed**. Added a paired sand/clay pixel and slightly offset WCS grid regression test; `python -m compileall -q app.py core pages tests` passed. `git diff --check` passed (Git reports expected LF-to-CRLF normalization warnings on Windows).
- WCS point lookup previously returned a valid Hyderabad estimate (Clay loam, nearest valid cell 395 m); WCS is best-effort and may return no data for other locations. Browser review is currently blocked by the in-app browser URL policy; do not bypass it. Streamlit startup did not reach its listening log/port check in this session, so no live server health pass is claimed.
- `git diff --check` completed; only Git's Windows line-ending normalization warnings were emitted.
- `core.weather._sample()` returned 67 rows with expected columns and the `OFFLINE DEMO DATA — sample weather` source label.
- `python -m streamlit run app.py --server.headless true --server.port 8765` started Uvicorn and printed local/network URLs. The sandbox denied a local HTTP health request, so no browser or endpoint health check is claimed. Streamlit `AppTest` stalled before returning and was interrupted.
- Open-Meteo forecast/geocoding variables and Gemini REST path/header were checked against current official docs; Gemini default is configurable.
- Network downloads: no training data downloaded. Public weather API is used only at app runtime; synthetic bundled sample is for demo fallback only.

## Credentials / external setup

- `GEMINI_API_KEY=` intentionally blank in `.env.example`. Optional Gemini explanations work only after the owner places their key in a local, untracked `.env` file.
- `GEMINI_MODEL` defaults to `gemini-3.8-flash`; it can be changed in `.env` if account/model availability differs.
- No key expected for Open-Meteo public endpoints. Network can be unavailable; offline sample mode is provided.
- Photo classification requires `GEMINI_API_KEY` and internet. No key is in the repo; captured photos are not persisted. SoilGrids lookup is best-effort; no result falls back to the manually selected soil. Browser GPS prompts only on button click; users can search a place or enter coordinates instead.

## Remaining work / constraints

- User visual review in the browser is still needed for the final dashboard and location controls; a programmatic page-render check stalled previously.
- Keep ML training explicitly deferred until a suitable labelled, licensed soil-moisture dataset is obtained and validated. No dataset was downloaded in this task.
- Public weather/geocoding access requires internet. When live and same-location cached responses are unavailable, the dashboard withholds advice instead of showing a misleading sample forecast.
- Gemini photo analysis stays disabled until the owner adds a key in a local `.env`; do not put credentials in the repo.
- Soil texture mapped from SoilGrids and moisture profile-derived root-zone depletion are approximate model estimates, not in-field measurements.
- The project was built as one initial snapshot because no app/repository history existed; no phase-by-phase commits have been made yet. Create later phase commits after their checks pass.


- 2026-10-16 (latest weather integration verification): Removed unnecessary `past_hours`/`forecast_hours` caps so Open-Meteo returns the full 60-day historical hourly series alongside the seven-day forecast. The rolling response had a null daily ET₀ and precipitation cell, causing the service to discard otherwise valid weather. Daily gaps now fill from same-location hourly totals where available; truly missing values still fail validation. Added a regression test. Exact default request returned 67 daily rows with 7 forecast days, 0 missing ET₀/precipitation values, current weather, and supported soil layers. The irrigation decision model ran using the API moisture profile (`SKIP_RAIN_EXPECTED`; `soil_moisture_used=True`). `compileall` passed; pytest: **36 passed**; `git diff --check` passed with Windows line-ending warnings. Home-page source text now accurately says advice is withheld when live and cached data are unavailable.

- 2026-10-16: UI polish pass after browser review. Dashboard now has a premium botanical/glass hero, location and outlook chips, a clearer next-step panel, stronger weather tiles, and responsive mobile layout. Root cause of the previously plain screen was `st.markdown` not installing the global `<style>` block on Streamlit 1.66; `core.ui.apply_css()` now uses `st.html(Path(...styles.css))`, called from each main user-facing page. `.streamlit/config.toml` provides the same dark green palette as a native theme. Browser screenshot confirmed styled dashboard; local health endpoint returned HTTP 200. Keep the information architecture simple and do not restore removed technical panels.

- 2026-10-16: Owner supplied a Gemini credential for optional soil-photo assessment. Stored it only in the ignored local `.env` (never in source, examples, or this handoff), kept the model setting in config, and restarted Streamlit. Authenticated Gemini model-list request returned HTTP 200 and confirmed the configured model is available. No farm photo or other farm data was sent during validation; actual photo analysis runs only when the user submits a captured image.
