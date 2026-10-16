from dataclasses import dataclass
from datetime import date

@dataclass(frozen=True)
class Crop:
    stages: tuple[int, int, int, int]
    kc: tuple[float, float, float]
    max_root: float
    p: float

CROPS = {
    "Tomato": Crop((30,40,40,25),(.60,1.15,.80),.8,.40),
    "Chilli": Crop((30,35,40,20),(.60,1.05,.90),.6,.30),
    "Cotton": Crop((30,50,55,45),(.35,1.15,.70),1.0,.65),
    "Maize": Crop((20,35,40,30),(.30,1.20,.60),.8,.55),
    "Groundnut": Crop((25,35,45,25),(.40,1.15,.60),.6,.50),
    "Rice (paddy)": Crop((30,30,60,30),(1.05,1.20,.90),.5,.20),
}

def kc_for(crop: str, age_days: int) -> float:
    c=CROPS[crop]; i,d,m,l=c.stages; a=max(0, age_days)
    if a < i: return c.kc[0]
    if a < i+d: return c.kc[0]+(c.kc[1]-c.kc[0])*(a-i)/d
    if a < i+d+m: return c.kc[1]
    if a < i+d+m+l: return c.kc[1]+(c.kc[2]-c.kc[1])*(a-i-d-m)/l
    return c.kc[2]

def root_depth(crop: str, age_days: int) -> float:
    c=CROPS[crop]; initial, development, *_=c.stages
    return c.max_root * min(1.0, .25 + .75*max(0,age_days-initial)/development)

def p_adjusted(p: float, etc: float) -> float:
    return min(.8,max(.1,p+.04*(5-etc)))

def crop_status(sowing_date, today=None, harvest_date=None, crop=None):
    today=today or date.today()
    if isinstance(sowing_date,str): sowing_date=date.fromisoformat(sowing_date)
    if isinstance(harvest_date,str) and harvest_date: harvest_date=date.fromisoformat(harvest_date)
    if today < sowing_date: return "not_yet_sown"
    if harvest_date is None and crop in CROPS:
        harvest_date=estimated_harvest(crop,sowing_date)
    if harvest_date:
        if today > harvest_date: return "fallow"
        if (harvest_date-today).days <= 7: return "late_stage"
    return "growing"

def estimated_harvest(crop: str, sowing_date: date) -> date:
    return date.fromordinal(sowing_date.toordinal()+sum(CROPS[crop].stages))
