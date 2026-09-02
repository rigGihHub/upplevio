from math import radians, sin, cos, sqrt, atan2

CITY_COORDS={
    "Örebro":(59.2753,15.2134),
    "Stockholm":(59.3293,18.0686),
    "Göteborg":(57.7089,11.9746),
    "Malmö":(55.6050,13.0038),
    "Jönköping":(57.7826,14.1618),
    "Uppsala":(59.8586,17.6389),
    "Västerås":(59.6099,16.5448),
    "Linköping":(58.4108,15.6214),
    "Norrköping":(58.5877,16.1924),
    "Oslo":(59.9139,10.7522),
    "Köpenhamn":(55.6761,12.5683),
}

def haversine_km(lat1,lon1,lat2,lon2):
    R=6371.0
    p1,p2=radians(lat1),radians(lat2)
    dp=radians(lat2-lat1);dl=radians(lon2-lon1)
    a=sin(dp/2)**2+cos(p1)*cos(p2)*sin(dl/2)**2
    return 2*R*atan2(sqrt(a),sqrt(1-a))

def coordinates_for_event(event):
    if event.latitude is not None and event.longitude is not None:
        return event.latitude,event.longitude
    return CITY_COORDS.get(event.city)

def distance_from_city(event,origin_city):
    origin=CITY_COORDS.get(origin_city)
    target=coordinates_for_event(event)
    if not origin or not target:
        return None
    return round(haversine_km(origin[0],origin[1],target[0],target[1]))
