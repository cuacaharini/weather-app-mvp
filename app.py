import streamlit as st
import requests
from datetime import datetime

# =========================
# CONFIG
# =========================
if "OPENWEATHER_API_KEY" not in st.secrets:
    st.error("OPENWEATHER_API_KEY belum diset di Streamlit Secrets")
    st.stop()

API_KEY = st.secrets["OPENWEATHER_API_KEY"]

BASE_CURRENT_URL = "https://api.openweathermap.org/data/2.5/weather"
BASE_FORECAST_URL = "https://api.openweathermap.org/data/2.5/forecast"

# =========================
# SERVICE FUNCTIONS
# =========================
def get_current_weather(city: str) -> dict:
    params = {
        "q": city,
        "appid": API_KEY,
        "units": "metric",
        "lang": "id"
    }
    response = requests.get(BASE_CURRENT_URL, params=params, timeout=10)

    if response.status_code != 200:
        st.error(f"Gagal ambil current weather (HTTP {response.status_code})")
        st.stop()

    return response.json()


def get_forecast(city: str) -> dict:
    params = {
        "q": city,
        "appid": API_KEY,
        "units": "metric",
        "lang": "id"
    }
    response = requests.get(BASE_FORECAST_URL, params=params, timeout=10)

    if response.status_code != 200:
        st.error(f"Gagal ambil forecast (HTTP {response.status_code})")
        st.stop()

    return response.json()


# =========================
# NORMALIZATION (API CONTRACT)
# =========================
def normalize_current_weather(raw: dict) -> dict:
    return {
        "city": raw.get("name"),
        "country": raw.get("sys", {}).get("country"),
        "temp": raw.get("main", {}).get("temp"),
        "feels_like": raw.get("main", {}).get("feels_like"),
        "humidity": raw.get("main", {}).get("humidity"),
        "weather": raw.get("weather", [{}])[0].get("description"),
        "wind_speed": raw.get("wind", {}).get("speed"),
        "timestamp": raw.get("dt"),
        "datetime": datetime.utcfromtimestamp(raw.get("dt")).isoformat() + "Z"
    }


def normalize_forecast(raw: dict, limit: int = 8) -> list:
    """
    limit=8 -> 24 jam ke depan (3 jam x 8)
    """
    forecast_list = []

    for item in raw.get("list", [])[:limit]:
        forecast_list.append({
            "timestamp": item.get("dt"),
            "datetime": datetime.utcfromtimestamp(item.get("dt")).isoformat() + "Z",
            "temp": item.get("main", {}).get("temp"),
            "humidity": item.get("main", {}).get("humidity"),
            "weather": item.get("weather", [{}])[0].get("description"),
            "wind_speed": item.get("wind", {}).get("speed")
        })

    return forecast_list


# =========================
# STREAMLIT UI (MVP)
# =========================
st.set_page_config(page_title="Weather Data MVP", layout="centered")

st.title("Weather Data MVP")
st.caption("Cloud-only MVP | Data-first | OpenWeather Free Tier")

city = st.text_input("Nama Kota", value="Jakarta")

if st.button("Ambil Data"):
    # Current weather
    raw_current = get_current_weather(city)
    clean_current = normalize_current_weather(raw_current)

    st.subheader("Current Weather (API-ready)")
    st.json(clean_current)

    # Forecast
    raw_forecast = get_forecast(city)
    clean_forecast = normalize_forecast(raw_forecast)

    st.subheader("Forecast (24 Jam ke Depan)")
    st.json(clean_forecast)
