
def calculate_initial_compass_bearing(pointA, pointB):
    import math
    """
    Calculates the bearing between two points.
    The formulae used is the following:
        θ = atan2(sin(Δlong).cos(lat2),
                  cos(lat1).sin(lat2) − sin(lat1).cos(lat2).cos(Δlong))
    :Parameters:
      - `pointA: The tuple representing the latitude/longitude for the
        first point. Latitude and longitude must be in decimal degrees
      - `pointB: The tuple representing the latitude/longitude for the
        second point. Latitude and longitude must be in decimal degrees
    :Returns:
      The bearing in degrees
    :Returns Type:
      float
    """
    if (type(pointA) != tuple) or (type(pointB) != tuple):
        raise TypeError("Only tuples are supported as arguments")

    lat1 = math.radians(pointA[0])
    lat2 = math.radians(pointB[0])

    diffLong = math.radians(pointB[1] - pointA[1])

    x = math.sin(diffLong) * math.cos(lat2)
    y = math.cos(lat1) * math.sin(lat2) - (math.sin(lat1)
            * math.cos(lat2) * math.cos(diffLong))

    initial_bearing = math.atan2(x, y)

    # Now we have the initial bearing but math.atan2 return values
    # from -180° to + 180° which is not what we want for a compass bearing
    # The solution is to normalize the initial bearing as shown below
    initial_bearing = math.degrees(initial_bearing)
    compass_bearing = (initial_bearing + 360) % 360

    return compass_bearing

def CalcularSigtePunto(x1,y1,x2,y2, distance):
    from math import sin,cos,atan
    # Prueba N 1
    xv = x2 - x1
    yv = y2 - y1

    angulo = atan(yv - xv)
    angulo = calculate_initial_compass_bearing((x1,y1),(x2,y2))

    print("angulo "+str(angulo))
    print("distancia "+str(distance))

    x = x2 + (distance * cos(angulo))
    y = y2 + (distance * sin(angulo))

    return x,y

from math import sin, cos, sqrt, atan2, radians,degrees, atan

# approximate radius of earth in km
R = 6373.0

# x1:-25.7152594961 y1:-58.230246
# x2:-25.6010160199 y2:-57.8429909091

x1 = -25.7152594961
y1 = -58.230246
x2 = -25.6010160199
y2 = -57.8429909091

velocidad = 25.9633

distance = velocidad * 0.25

x,y = CalcularSigtePunto(x1,y1,x2,y2, distance)

print(x)
print(y)
