from core.ml import forecast_surface_moisture
def test_ml_honest_fallback():
    assert not forecast_surface_moisture(None)["available"]
