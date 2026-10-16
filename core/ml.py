"""Modular, optional classifiers. No fitted model is bundled or claimed accurate."""
from pathlib import Path

FEATURES=("soil_moisture_percent","temperature_c","humidity_percent","et0_mm",
          "rain_next_24h_mm","crop_age_days","water_balance_depletion_mm","water_balance_raw_mm")
TARGET="irrigation_needed"

def forecast_surface_moisture(history):
    # Retained compatibility with the original optional surface moisture page.
    return {"available":False,"message":"ML forecast unavailable — no suitable validated surface-moisture training data or model is bundled."}

def predict_irrigation(features, model_path="models/irrigation_rf.joblib"):
    """Load an explicitly trained local model. Only load artifacts you trust."""
    path=Path(model_path)
    if not path.is_file(): return {"available":False,"message":"ML unavailable — no trained model file is installed."}
    try:
        import joblib
        import pandas as pd
        model=joblib.load(path)
        row={name:float(features[name]) for name in FEATURES}
        prediction=int(model.predict(pd.DataFrame([row],columns=FEATURES))[0])
        probability=float(model.predict_proba(pd.DataFrame([row],columns=FEATURES))[0][1]) if hasattr(model,"predict_proba") else None
        return {"available":True,"irrigation_needed":bool(prediction),"probability":probability,
                "message":"Random Forest inference; model quality depends on its documented evaluation dataset."}
    except (ImportError,KeyError,TypeError,ValueError,OSError) as exc:
        return {"available":False,"message":f"ML unavailable — model could not be loaded or features were invalid ({type(exc).__name__})."}
