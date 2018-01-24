from math import sin, cos, sqrt, atan2, radians,degrees, atan

# approximate radius of earth in km
R = 6373.0

lat1 = radians(-25.71722)
lon1 = radians(-58.2130966667)
lat2 = radians(-25.5745666667)
lon2 = radians(-57.9705616667)

dlon = lon2 - lon1
dlat = lat2 - lat1

a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
c = 2 * atan2(sqrt(a), sqrt(1 - a))

distance = R * c

m = dlon / dlat
grados = degrees(atan(m))


velocidad = 25.9633

distance = velocidad * 0.16666

x2 = lat2 + distance * cos(grados)
y2 = lon2 + distance * sin(grados)

print(x2)
print(y2)

print(grados)