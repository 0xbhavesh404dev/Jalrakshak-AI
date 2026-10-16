from core.crops import *
def test_crop_stage_boundaries():
    assert kc_for("Tomato",0)==.6 and kc_for("Tomato",30)==.6
    assert abs(kc_for("Tomato",50)-.875)<1e-9
    assert kc_for("Tomato",110)==1.15
    assert root_depth("Tomato",30)==.2 and root_depth("Tomato",70)==.8
def test_crop_status_and_estimated_harvest():
    from datetime import date,timedelta
    assert crop_status(date.today()+timedelta(days=1))=="not_yet_sown"
    assert estimated_harvest("Tomato",date(2026,1,1))==date(2026,5,16)
