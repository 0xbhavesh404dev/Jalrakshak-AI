import pytest
from core.db import *
def test_farm_crud_and_validation():
    init_db(); f={"name":"A","place":"Hyderabad","latitude":17,"longitude":78,"crop":"Tomato","soil":"Loamy","irrigation_method":"Drip","area_acres":1,"sowing_date":"2026-01-01"}; i=save_farm(f); assert get_farm(i)["name"]=="A"; delete_farm(i); assert get_farm(i) is None
def test_invalid_area_and_harvest_date_rejected():
    init_db(); f={"name":"A","place":"Hyderabad","latitude":17,"longitude":78,"crop":"Tomato","soil":"Loamy","irrigation_method":"Drip","area_acres":1,"sowing_date":"2026-02-01","harvest_date":"2026-01-01"}
    with pytest.raises(ValueError): save_farm(f)

def test_harvest_record_captures_farm_location_and_is_idempotent():
    from core.db import mark_harvested_today,get_harvest_event
    init_db(); f={"name":"Harvest test","place":"Warangal","latitude":17.9,"longitude":79.5,"crop":"Tomato","soil":"Loamy","irrigation_method":"Drip","area_acres":1,"sowing_date":"2026-01-01"}
    i=save_farm(f)
    try:
        first=mark_harvested_today(i,"2026-10-16"); second=mark_harvested_today(i,"2026-10-16")
        assert first["place"]=="Warangal" and first["latitude"]==17.9
        assert first["id"]==second["id"] and get_harvest_event(i,"2026-10-16")["date"]=="2026-10-16"
    finally: delete_farm(i)
