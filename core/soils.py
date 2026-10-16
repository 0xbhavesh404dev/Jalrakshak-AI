SOILS={"Sandy":(80,"Drains quickly; stores less plant-available water."),"Sandy loam":(110,"A balanced, moderately free-draining soil."),"Loamy":(140,"A balanced soil with moderate water storage."),"Clay loam":(160,"Holds more water and drains more slowly."),"Clay":(180,"Stores more water but can drain slowly.")}
EFFICIENCY={"Drip":.90,"Sprinkler":.75,"Flood/furrow":.60}
def awc(soil): return SOILS[soil][0]
def efficiency(method): return EFFICIENCY[method]
def litres(gross_mm, area_acres):
    if gross_mm < 0 or area_acres < 0: raise ValueError("Water depth and area must be non-negative")
    return gross_mm*4047*area_acres
