import streamlit as st
import requests
from datetime import datetime, timezone, timedelta

# =================================================
# TIMEZONE CONFIG (UTC+7 / WIB)
# =================================================
WIB = timezone(timedelta(hours=7))

def to_wib_datetime(ts: int) -> str:
    return datetime.fromtimestamp(ts, tz=WIB).strftime("%d %b %Y %H:%M WIB")

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
    res = requests.get(
        BASE_GEO_URL,
        params={"q": city, "limit": 1, "appid": API_KEY},
        timeout=10
    )
    if res.status_code != 200 or not res.json():
        st.error("Lokasi tidak ditemukan")
        st.stop()

    d = res.json()[0]
    return {"city": d["name"], "country": d["country"], "lat": d["lat"], "lon": d["lon"]}


def get_json(url: str, params: dict) -> dict:
    res = requests.get(url, params=params, timeout=10)
    if res.status_code != 200:
        st.error(f"API error ({res.status_code})")
        st.stop()
    return res.json()

# =================================================
# NORMALIZATION
# =================================================
def normalize_current(raw):
    ts = raw["dt"]
    return {
        "temp": raw["main"]["temp"],
        "feels": raw["main"]["feels_like"],
        "humidity": raw["main"]["humidity"],
        "weather": raw["weather"][0]["description"].title(),
        "wind": raw["wind"]["speed"],
        "time": to_wib_datetime(ts),
    }


def normalize_forecast(raw, limit=8):
    rows = []
    for item in raw["list"][:limit]:
        rows.append({
            "Waktu": to_wib_datetime(item["dt"]),
            "Suhu (°C)": item["main"]["temp"],
            "Cuaca": item["weather"][0]["description"].title(),
            "Angin (m/s)": item["wind"]["speed"]
        })
    return rows


def normalize_air(raw):
    d = raw["list"][0]
    return {
        "AQI": d["main"]["aqi"],
        "PM2.5": d["components"]["pm2_5"],
        "PM10": d["components"]["pm10"],
        "CO": d["components"]["co"],
        "Waktu": to_wib_datetime(d["dt"])
    }

# =================================================
# UI
# =================================================
st.set_page_config(page_title="Weather App MVP", layout="wide")

st.markdown("## 🌤️ Weather App MVP")
st.caption("Current Weather • Forecast 24 Jam • Air Quality (UTC+7 WIB)")

with st.sidebar:
    city = st.text_input("🌍 Nama Kota", "Jakarta")
    load = st.button("🔍 Ambil Data")

if load:
    loc = geocode_city(city)

    current_raw = get_json(BASE_WEATHER_URL, {
        "lat": loc["lat"], "lon": loc["lon"],
        "appid": API_KEY, "units": "metric", "lang": "id"
    })
    forecast_raw = get_json(BASE_FORECAST_URL, {
        "lat": loc["lat"], "lon": loc["lon"],
        "appid": API_KEY, "units": "metric", "lang": "id"
    })
    air_raw = get_json(BASE_AIR_URL, {
        "lat": loc["lat"], "lon": loc["lon"], "appid": API_KEY
    })

    current = normalize_current(current_raw)
    forecast = normalize_forecast(forecast_raw)
    air = normalize_air(air_raw)

    # =======================
    # CURRENT WEATHER CARDS
    # =======================
    st.markdown(f"### 📍 {loc['city']}, {loc['country']}")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("🌡️ Suhu", f"{current['temp']} °C")
    c2.metric("🤒 Terasa", f"{current['feels']} °C")
    c3.metric("💧 Kelembapan", f"{current['humidity']} %")
    c4.metric("🌬️ Angin", f"{current['wind']} m/s")

    st.info(f"**{current['weather']}** — Update: {current['time']}")

    # =======================
    # FORECAST TABLE
    # =======================
    st.markdown("### ⏱️ Forecast 24 Jam Ke Depan")
    st.dataframe(forecast, use_container_width=True)

    # =======================
    # AIR QUALITY
    # =======================
    st.markdown("### 🌫️ Kualitas Udara")

    a1, a2, a3, a4 = st.columns(4)
    a1.metric("AQI", air["AQI"])
    a2.metric("PM2.5", air["PM2.5"])
    a3.metric("PM10", air["PM10"])
    a4.metric("CO", air["CO"])

    st.caption(f"Update: {air['Waktu']}")
