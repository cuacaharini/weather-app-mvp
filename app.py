import streamlit as st
import requests
from datetime import datetime, timezone, timedelta

# =================================================
# TIMEZONE CONFIG (UTC+7 / WIB)
# =================================================
WIB = timezone(timedelta(hours=7))

def to_wib_datetime(timestamp: int) -> str:
    return datetime.fromtimestamp(timestamp, tz=WIB).isoformat()

# =================================================
# CONFIG
# =================================================
if "OPENWEATHER_API_KEY" not in st.secrets:
    st.error("OPENWEATHER_API_KEY belum diset di Streamlit Secrets")
    st.stop()

API_KEY = st.secrets["OPENWEATHER_API_KEY"]

BASE_WEATHER_URL = "https://api.openweathermap.org/data/2.5/weather"
BASE_FORECAST_URL = "https://api.openweathermap.org/data/2.5/forecast"
BASE_GEO_URL = "https://api.openweathermap.org/geo/1.0/direct"
BASE_AIR_URL = "https://api.openweathermap.org/data/2.5/air_pollution"

# =================================================
# SERVICE LAYER
# =================================================
def geocode_city(city: str) -> dict:
    params = {
        "q": city,
        "limit": 1,
        "appid": API_KEY
    }
    res = requests.get(BASE_GEO_URL, params=params, timeout=10)

    if res.status_code != 200 or not res.json():
        st.error("Gagal geocoding lokasi")
        st.stop()

    data = res.json()[0]
    return {
        "city": data.get("name"),
        "country": data.get("country"),
        "lat": data.get("lat"),
        "lon": data.get("lon")
    }


def get_current_weather(lat: float, lon: float) -> dict:
    params = {
        "lat": lat,
        "lon": lon,
        "appid": API_KEY,
        "units": "metric",
        "lang": "id"
    }
    res = requests.get(BASE_WEATHER_URL, params=params, timeout=10)

    if res.status_code != 200:
        st.error(f"Gagal ambil current weather (HTTP {res.status_code})")
        st.stop()

    return res.json()


def get_forecast(lat: float, lon: float) -> dict:
    params = {
        "lat": lat,
        "lon": lon,
        "appid": API_KEY,
        "units": "metric",
        "lang": "id"
    }
    res = requests.get(BASE_FORECAST_URL, params=params, timeout=10)

    if res.status_code != 200:
        st.error(f"Gagal ambil forecast (HTTP {res.status_code})")
        st.stop()

    return res.json()


def get_air_pollution(lat: float, lon: float) -> dict:
    params = {
        "lat": lat,
        "lon": lon,
        "appid": API_KEY
    }
    res = requests.get(BASE_AIR_URL, params=params, timeout=10)

    if res.status_code != 200:
        st.error(f"Gagal ambil air pollution (HTTP {res.status_code})")
        st.stop()

    return res.json()

# =================================================
# NORMALIZATION (API CONTRACT)
# =================================================
def normalize_current_weather(raw: dict) -> dict:
    ts = raw["dt"]
    return {
        "temp": raw["main"]["temp"],
        "feels_like": raw["main"]["feels_like"],
        "humidity": raw["main"]["humidity"],
        "weather": raw["weather"][0]["description"],
        "wind_speed": raw["wind"]["speed"],
        "timestamp": ts,
        "datetime_wib": to_wib_datetime(ts)
    }


def normalize_forecast(raw: dict, limit: int = 8) -> list:
    """
    limit=8 -> 24 jam ke depan (3 jam x 8)
    """
    result = []
    for item in raw["list"][:limit]:
        ts = item["dt"]
        result.append({
            "timestamp": ts,
            "datetime_wib": to_wib_datetime(ts),
            "temp": item["main"]["temp"],
            "humidity": item["main"]["humidity"],
            "weather": item["weather"][0]["description"],
            "wind_speed": item["wind"]["speed"]
        })
    return result


def normalize_air_pollution(raw: dict) -> dict:
    data = raw["list"][0]
    ts = data["dt"]
    return {
        "aqi": data["main"]["aqi"],  # 1=Good, 5=Very Poor
        "components": data["components"],
        "timestamp": ts,
        "datetime_wib": to_wib_datetime(ts)
    }

# =================================================
# STREAMLIT UI (MVP / DATA EXPLORER)
# =================================================
st.set_page_config(page_title="Weather Data MVP", layout="centered")
st.title("Weather Data MVP")
st.caption("Current • Forecast • Geocoding • Air Quality | Timezone WIB (UTC+7)")

city = st.text_input("Nama Kota", value="Jakarta")

if st.button("Ambil Data"):
    # Geocoding
    location = geocode_city(city)

    # Current Weather
    current_raw = get_current_weather(location["lat"], location["lon"])
    current_clean = normalize_current_weather(current_raw)

    # Forecast
    forecast_raw = get_forecast(location["lat"], location["lon"])
    forecast_clean = normalize_forecast(forecast_raw)

    # Air Pollution
    air_raw = get_air_pollution(location["lat"], location["lon"])
    air_clean = normalize_air_pollution(air_raw)

    # FINAL API-READY RESPONSE
    response = {
        "location": location,
        "current": current_clean,
        "forecast_24h": forecast_clean,
        "air_quality": air_clean,
        "timezone": "UTC+7 (WIB)"
    }

    st.subheader("API-ready Response")
    st.json(response)
