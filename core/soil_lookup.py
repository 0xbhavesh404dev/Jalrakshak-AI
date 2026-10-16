"""Best-effort point soil texture from ISRIC SoilGrids 250 m WCS maps."""
from functools import lru_cache
from io import BytesIO
import math

import requests
from PIL import Image

WCS_URLS = {
    "sand": "https://maps.isric.org/mapserv/sand",
    "clay": "https://maps.isric.org/mapserv/clay",
}
CRS_152160 = "http://www.opengis.net/def/crs/EPSG/0/152160"
PIXEL_M = 250
SEARCH_RADIUS_M = 2500
EARTH_RADIUS_M = 6371007.181

def texture_class(sand, clay):
    sand=float(sand); clay=float(clay)
    if sand>=70: return "Sandy"
    if clay>=40: return "Clay"
    if clay>=27 and sand<45: return "Clay loam"
    if sand>=43 and clay<20: return "Sandy loam"
    return "Loamy"

def _goode_xy(latitude, longitude):
    """Convert WGS84 coordinates to the Goode Homolosine CRS used by SoilGrids."""
    phi=math.radians(latitude); lam=math.radians(longitude); radius=EARTH_RADIUS_M
    transition=math.radians(40.7366)
    if abs(phi)<=transition:
        return radius*lam*math.cos(phi),radius*phi
    if abs(phi)==math.pi/2:
        theta=math.copysign(math.pi/2,phi)
    else:
        theta=phi
        for _ in range(20):
            f=2*theta+math.sin(2*theta)-math.pi*math.sin(phi)
            derivative=2+2*math.cos(2*theta)
            if abs(derivative)<1e-12: break
            step=f/derivative; theta-=step
            if abs(step)<1e-12: break
    x=2*math.sqrt(2)/math.pi*radius*lam*math.cos(theta)
    y=math.sqrt(2)*radius*math.sin(theta)-math.copysign(.05280*radius,phi)
    return x,y

def _coverage(url, property_name, latitude, longitude):
    x,y=_goode_xy(latitude,longitude); half=SEARCH_RADIUS_M
    params=[
        ("SERVICE","WCS"),("VERSION","2.0.1"),("REQUEST","GetCoverage"),
        ("COVERAGEID",f"{property_name}_0-5cm_mean"),("FORMAT","GEOTIFF_INT16"),
        ("SUBSETTINGCRS",CRS_152160),("OUTPUTCRS",CRS_152160),
        ("RESX",str(PIXEL_M)),("RESY",str(PIXEL_M)),
        ("SUBSET",f"X({x-half},{x+half})"),("SUBSET",f"Y({y-half},{y+half})"),
    ]
    response=requests.get(url,params=params,timeout=20); response.raise_for_status()
    image=Image.open(BytesIO(response.content)); tags=image.tag_v2
    tie=tags[33922]; scale=tags[33550]
    return image,(float(tie[3]),float(tie[4]),float(scale[0]),float(scale[1]))

@lru_cache(maxsize=128)
def lookup_soil(latitude,longitude):
    """Look up approximate topsoil texture near a point; None means unavailable."""
    try:
        latitude=float(latitude); longitude=float(longitude)
        if not (-90<=latitude<=90 and -180<=longitude<=180): return None
        sand,sand_geo=_coverage(WCS_URLS["sand"],"sand",latitude,longitude)
        clay,clay_geo=_coverage(WCS_URLS["clay"],"clay",latitude,longitude)
        # WCS responses can encode the same 250 m grid with tiny floating-point
        # differences in GeoTIFF tie points. Reject truly mismatched grids only.
        same_grid = (
            sand.size == clay.size
            and len(sand_geo) == len(clay_geo)
            and all(math.isclose(a, b, rel_tol=0, abs_tol=1e-5) for a, b in zip(sand_geo, clay_geo))
        )
        if not same_grid: return None
        origin_x,origin_y,pixel_x,pixel_y=sand_geo
        target_x,target_y=_goode_xy(latitude,longitude)
        best=None
        for row in range(sand.height):
            for col in range(sand.width):
                sand_gkg=int(sand.getpixel((col,row))); clay_gkg=int(clay.getpixel((col,row)))
                if not (0<sand_gkg<=1000 and 0<clay_gkg<=1000): continue
                cell_x=origin_x+(col+.5)*pixel_x
                cell_y=origin_y-(row+.5)*pixel_y
                distance=math.hypot(cell_x-target_x,cell_y-target_y)
                if distance<=SEARCH_RADIUS_M and (best is None or distance<best[0]):
                    best=(distance,sand_gkg/10,clay_gkg/10)
        if best is None: return None
        distance,sand_pct,clay_pct=best
        return {"soil":texture_class(sand_pct,clay_pct),"sand_pct":sand_pct,"clay_pct":clay_pct,
                "distance_m":round(distance),"source":"SoilGrids 250 m topsoil estimate (nearest valid pixel)"}
    except (requests.RequestException,ValueError,KeyError,TypeError,IndexError,OSError):
        return None
