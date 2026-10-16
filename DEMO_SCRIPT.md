# Three-minute demo

**0:00–0:20 — Home:** Introduce the irrigation decision and show the ESP32, soil-moisture sensor and DHT11. No pump or relay is used; the device only measures and sends readings.

**0:20–0:50 — Farm Setup:** Create a farm near Hyderabad and choose crop, soil, area, irrigation method and sowing date. For a reliable demo, set `JALRAKSHAK_OFFLINE=1` before launch.

**0:50–1:20 — Dashboard:** Show the weather-based advice, then Live Hardware Sensors and the separate rule-based prediction. Point out timestamps, stale/calibration status and the warning that the sensor percent is relative. If hardware is unavailable, use the explicitly labelled demo mode only to preview the UI; it cannot make a prediction.

**1:20–2:00 — Digital Twin:** Choose Heatwave or Failed Monsoon. Point out the simulation label and the changed forecast projection; historic weather is unchanged.

**2:00–2:30 — ML/Agronomist:** Explain that validated training data is unavailable, so the app does not claim ML accuracy. Show the offline explanation fallback.

**2:30–3:00 — Close:** Emphasize that recommendations are a rule baseline or water-balance estimate, not validated ML; check the field and use local agricultural advice.
