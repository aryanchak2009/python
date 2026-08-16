from datetime import datetime
from zoneinfo import ZoneInfo

CITY_TIMEZONES = {
    "Los Angeles": "America/Los_Angeles",
    "Denver": "America/Denver",
    "Chicago": "America/Chicago",
    "New York": "America/New_York",
    "Sao Paulo": "America/Sao_Paulo",
    "London": "Europe/London",
    "Paris": "Europe/Paris",
    "Berlin": "Europe/Berlin",
    "Cairo": "Africa/Cairo",
    "Moscow": "Europe/Moscow",
    "Dubai": "Asia/Dubai",
    "Mumbai": "Asia/Kolkata",
    "Bangkok": "Asia/Bangkok",
    "Shanghai": "Asia/Shanghai",
    "Tokyo": "Asia/Tokyo",
    "Seoul": "Asia/Seoul",
    "Sydney": "Australia/Sydney",
    "Auckland": "Pacific/Auckland",
}


def current_times():
    now = datetime.now(ZoneInfo("UTC"))
    return {city: now.astimezone(ZoneInfo(tz)) for city, tz in CITY_TIMEZONES.items()}


def print_world_times():
    times = sorted(current_times().items(), key=lambda item: item[1].utcoffset())
    name_width = max(len(city) for city in CITY_TIMEZONES)
    for city, city_time in times:
        print(f"{city:<{name_width}}  {city_time.strftime('%Y-%m-%d %H:%M:%S %Z (UTC%z)')}")


def find_city_time(query):
    matches = [city for city in CITY_TIMEZONES if query.lower() in city.lower()]
    if not matches:
        print(f"No city matching '{query}' found.")
        return
    now = datetime.now(ZoneInfo("UTC"))
    for city in matches:
        city_time = now.astimezone(ZoneInfo(CITY_TIMEZONES[city]))
        print(f"{city}: {city_time.strftime('%Y-%m-%d %H:%M:%S %Z (UTC%z)')}")


print("Current time around the world:\n")
print_world_times()

while True:
    query = input("\nSearch for a city (or press Enter to quit): ").strip()
    if not query:
        break
    find_city_time(query)
