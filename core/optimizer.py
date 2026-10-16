"""Conservative schedule helper; exhaustive schedules are intentionally bounded."""
from itertools import product

def optimize_schedule(depletion,raw,irrigation_net_per_event,max_events=3):
    """Find a minimum-event set of days that keeps projected depletion <= RAW.

    Inputs are day-wise pre-irrigation depletion and thresholds; returned schedule is
    a transparent toy projection and must be labelled simulated in the UI.
    """
    n=len(depletion)
    for count in range(max_events+1):
        for selected in product((0,1),repeat=n):
            if sum(selected)!=count: continue
            d=0.0
            for i in range(n):
                d=max(0,min(depletion[i]-selected[i]*irrigation_net_per_event, max(raw[i],depletion[i])))
                if d>raw[i]: break
            else: return {"feasible":True,"days":[i for i,x in enumerate(selected) if x],"events":count,"total_net_mm":count*irrigation_net_per_event}
    return {"feasible":False,"days":[],"events":None,"total_net_mm":None}
