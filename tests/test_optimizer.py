from core.optimizer import optimize_schedule

def test_minimum_event_schedule():
    x=optimize_schedule([5,12,7],[8,8,8],5,max_events=2)
    assert x["feasible"] and x["events"]==1 and x["days"]==[1]

def test_infeasible_schedule_is_reported():
    x=optimize_schedule([15],[5],2,max_events=1)
    assert not x["feasible"]
