import math


def haversine_distance(lat1, lon1, lat2, lon2):
    R = 6371.0  # Earth's radius in kilometers

    lat1_rad, lon1_rad = math.radians(lat1), math.radians(lon1)
    lat2_rad, lon2_rad = math.radians(lat2), math.radians(lon2)

    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad

    a = math.sin(dlat / 2) ** 2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2) ** 2
    c = 2 * math.asin(math.sqrt(a))

    return R * c


city1 = input("Enter first city name: ")
lat1 = float(input(f"Enter latitude of {city1}: "))
lon1 = float(input(f"Enter longitude of {city1}: "))

city2 = input("Enter second city name: ")
lat2 = float(input(f"Enter latitude of {city2}: "))
lon2 = float(input(f"Enter longitude of {city2}: "))

distance = haversine_distance(lat1, lon1, lat2, lon2)
print(f"The distance between {city1} and {city2} is {distance:.2f} km")
