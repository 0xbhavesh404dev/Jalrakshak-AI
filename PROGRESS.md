# Build progress

Status is recorded in [PROJECT_HANDOFF.md](PROJECT_HANDOFF.md). This log reflects actual work in this workspace. Tests are not marked passed until run and observed.

## Current snapshot

- Scaffold and core application implemented from the master prompt.
- `python -m compileall .`: passed.
- `python -m pytest --basetemp=.pytest-tmp -q`: 18 passed (2026-10-16).
- `streamlit run app.py` started its local server; HTTP health check and AppTest were blocked/stalled in this environment. See handoff log.
- UX pass: grouped navigation into “Get Started” and “Explore”; rewrote Home, Farm Setup, and Dashboard around a two-step farmer workflow with plain-language prompts and metrics.
- Minimum Streamlit requirement is now 1.50 for the explicit responsive widget sizing used by the refreshed UI.
- Fixed Home navigation crash: `st.page_link()` does not accept `type`; removed that unsupported argument from all page links.
- Replaced white canvas with pale green/gold gradient, dark green navigation sidebar, high-contrast hero panel, and raised cards. Visual browser review still pending.
- Dashboard now has a step-by-step usage guide, a separate rain/heat-based wet/dry surface estimate, and a “Record harvest today” action that saves the selected field location with the date. Uses saved farm location, not phone GPS.
- Added tests for wet/dry rules and harvest location persistence: 24 tests pass; compileall passes.
- Fixed Farm Setup location search: the town search and nearest-place dropdown now render before the farm form; press Search to refresh results, or enter coordinates. Added direct Dashboard link to change location. Soil map and camera moved under a collapsed optional section to reduce clutter.
- Added harvest weather watch, optional SoilGrids lookup, and live camera photo capture with optional Gemini vision (color explicitly excluded). API key stays blank; photo held in session only. Current test count: 28 passed; compile passed. Live-mode server at http://127.0.0.1:8766 returned HTTP 200. Port 8765 unavailable at launch.
- Implemented the provided dark glass dashboard visual direction using live farm data, conditional recommendation banners, four dynamic metrics and real Plotly root-zone/rain-vs-ETc charts. Sidebar now starts collapsed. Rechecked: 28 tests pass, compileall passes.
- Simplified again from user's screenshot feedback: removed four technical tiles and charts and reduced repeated recommendation details. Main dashboard now focuses on wet/dry outlook, one suggested action, a compact harvest date and harvest log; photo/map tools stay optional and collapsed.
- Simplified the sidebar to Home, Set up field, Today's field outlook, and Field notes. Weather deep dive, scenario simulator, and AI Q&A are no longer in the primary website navigation.
- Added user-click-only browser geolocation, with town search and coordinate entry as alternatives. Selecting “Not sure” for soil triggers a best-effort SoilGrids WCS topsoil lookup during setup. Dashboard map lookup handles small raster coordinate differences and explains that a mapped estimate is approximate.
- Current verification: `python -m compileall -q app.py core pages tests` passed; `python -m pytest --basetemp=.pytest-tmp -q` passed (**29 passed**); `git diff --check` passed with Windows LF/CRLF warnings. UI browser review and a listening server health check could not be confirmed in this turn.
- Fixed screenshot contrast issue: harvest action buttons and expander summaries now have explicit dark-theme surfaces, readable text, hover/focus states, and visible disabled styling.
- Simplified Dashboard after user's latest screenshot: removed the separate technical wet/dry panel and duplicate recommendation banner; one “Today's advice” card now gives a plain action and short reason.
- Weather fallback investigation: `JALRAKSHAK_OFFLINE` is false; a direct request failed DNS resolution for `api.open-meteo.com`. The old request also asked for a soil-moisture daily variable when Open-Meteo documents soil moisture as hourly. Reworked the free, no-key endpoint request to use supported current/hourly/daily parameters.
- Added location-keyed short-lived caching, async worker-thread fetching with loading spinner, response validation, null-safe current values, hourly 24-hour rain total, depth-weighted API soil moisture, ET₀ and seven-day forecast. API moisture updates today's crop/soil-specific root-zone stress estimate when required profile layers are available. Data source is clearly shown; without live or cached data, advice is withheld (demo sample remains explicit-only).
- Current verification after weather changes: 35 tests passed before the latest refinements; rerun suite and live API check are pending. The direct API request in this execution environment previously failed DNS; do not claim live request success until verified.
- Optional live Gemini key remains blank by design.
- ML forecast intentionally unavailable pending real historical data and validation.

- ESP32 software integration is implemented: `hardware/esp32_sensor.ino`, local `sensor_api.py`, validated SQLite persistence, latest/history API, Dashboard sensor status/chart and a rule-based prediction. Calibration starts disabled. Optional demo values are visibly simulated, not persisted, and cannot predict irrigation. Added an optional labeled-data Random Forest training/evaluation script; no trained model or physical hardware test is claimed.
- Fixed the hidden Weather page: it expected a removed `sm_model` daily column and would fail when opened directly; it now reads the current soil-moisture profile from DataFrame metadata.
- Hardware integration verification on 2026-10-16: compilation passed; pytest passed (**43 passed**) including API endpoints, payload validation, persistence, stale/disconnected data, prediction conflict, demo, and token guard cases. A temporary-database live API round-trip passed (health 200, POST 201, latest/history 200); Streamlit health returned 200; Dashboard and standalone Weather AppTest runs each had zero exceptions with offline sample weather. Actual board wiring/calibration remains pending. FastAPI TestClient emits one upstream AnyIO deprecation warning under the local Python 3.14 environment.

- Fixed default live forecast being discarded when one daily ET₀ or rainfall field was null: the app now uses same-day hourly API totals for missing daily values, keeps the full historical hourly response, and still rejects unresolved required-data gaps. Updated Home copy so it no longer suggests that live failures silently use sample weather.
- Live Open-Meteo check succeeded for Hyderabad coordinates: 67 daily rows, 7 forecast days, complete ET₀ and precipitation after hourly gap-fill, current conditions and soil-moisture layers. The crop-water balance and recommendation also ran; the decision consumed API-derived soil moisture.
- Latest checks: `python -m compileall -q app.py core pages tests` passed; `python -m pytest --basetemp=.pytest-tmp -q` passed (**36 passed**); `git diff --check` passed with expected Windows LF/CRLF warnings.

- Dashboard UI visual pass: replaced generic/plain surfaces with a deep botanical theme, a field identity hero, next-step recommendation panel, elevated weather metrics and responsive layout. Found and fixed global CSS missing from the live browser: switched from `st.markdown` to `st.html` and explicitly load styles on Home, Farm Setup, Dashboard and Field Notes. Native dark theme added as fallback. Verified with browser screenshot and server HTTP 200.

- Gemini soil-photo setup: key stored only in local ignored `.env`; authenticated model-list validation succeeded (HTTP 200; configured model present). No image was uploaded during validation. Actual Gemini photo request happens only when a user chooses “Estimate surface from photo.”
