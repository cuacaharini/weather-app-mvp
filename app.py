import streamlit as st
import requests
from datetime import datetime, timezone, timedelta
import pandas as pd

# =================================================
# TIMEZONE CONFIG (UTC+7 / WIB)
# =================================================
WIB = timezone(timedelta(hours=7))

def to_wib(ts: int) -> str:
    return datetime.fromtimestamp(ts, tz=WIB).strftime("%d %b %H:%M")

def to_wib_date(ts: int) -> str:
    return datetime.fromtimestamp(ts, tz=WIB).strftime("%d %b %Y")

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
# SERVICE
# =================================================
def get_json(url, params):
    r = requests.get(url, params=params, timeout=10)
    if r.status_code != 200:
        st.error(f"API error ({r.status_code})")
        st.stop()
    return r.json()

def geocode(city):
    data = get_json(BASE_GEO_URL, {
        "q": city,
        "limit": 1,
        "appid": API_KEY
    })
    if not data:
        st.error("Kota tidak ditemukan")
        st.stop()
    return data[0]

# =================================================
# NORMALIZATION
# =================================================
def normalize_current(raw):
    return {
        "temp": raw["main"]["temp"],
        "feels": raw["main"]["feels_like"],
        "humidity": raw["main"]["humidity"],
        "weather": raw["weather"][0]["description"].title(),
        "wind": raw["wind"]["speed"],
        "time": to_wib(raw["dt"])
    }

def normalize_forecast(raw, limit=8):
    rows = []
    for item in raw["list"][:limit]:
        rows.append({
            "date": to_wib_date(item["dt"]),
            "time": to_wib(item["dt"]),
            "temp": item["main"]["temp"],
            "humidity": item["main"]["humidity"],
            "weather": item["weather"][0]["description"].title(),
            "wind": item["wind"]["speed"]
        })
    return rows

def normalize_air(raw):
    d = raw["list"][0]
    return {
        "AQI": d["main"]["aqi"],
        "PM2.5": d["components"]["pm2_5"],
        "PM10": d["components"]["pm10"],
        "CO": d["components"]["co"],
        "time": to_wib(d["dt"])
    }

# =================================================
# AIR QUALITY EXPLANATION
# =================================================
def aqi_description(aqi):
    return {
        1: ("Baik", "Udara sangat baik dan aman untuk semua aktivitas."),
        2: ("Sedang", "Masih aman, kelompok sensitif sebaiknya waspada."),
        3: ("Tidak Sehat (Sensitif)", "Kurangi aktivitas luar bagi anak & lansia."),
        4: ("Tidak Sehat", "Hindari aktivitas luar ruangan lama."),
        5: ("Sangat Tidak Sehat", "Sebaiknya tetap di dalam ruangan.")
    }.get(aqi, ("Tidak diketahui", ""))

# =================================================
# UI
# =================================================
st.set_page_config(page_title="Weather App MVP", layout="wide")

st.markdown("## 🌤️ Weather App MVP")
st.caption("Modern Forecast Cards • Air Quality Explained • WIB (UTC+7)")

with st.sidebar:
    city = st.text_input("🌍 Nama Kota", "Jakarta")
    load = st.button("🔍 Ambil Data")

if load:
    loc = geocode(city)

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

    # =========================
    # CURRENT WEATHER
    # =========================
    st.markdown(f"### 📍 {loc['name']}, {loc['country']}")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("🌡️ Suhu", f"{current['temp']} °C")
    c2.metric("🤒 Terasa", f"{current['feels']} °C")
    c3.metric("💧 Kelembapan", f"{current['humidity']} %")
    c4.metric("🌬️ Angin", f"{current['wind']} m/s")

    st.info(f"**{current['weather']}** — Update: {current['time']}")

    # =========================
    # FORECAST CARDS (MODERN)
    # =========================
    st.markdown("### ⏱️ Forecast 24 Jam Ke Depan")

    grouped = {}
    for item in forecast:
        grouped.setdefault(item["date"], []).append(item)

    for date, items in grouped.items():
        st.markdown(f"#### 📅 {date}")
        cols = st.columns(len(items))

        for col, item in zip(cols, items):
            with col:
                st.markdown(
                    f"""
                    <div style="
                        padding:16px;
                        border-radius:14px;
                        background:linear-gradient(180deg,#ffffff,#f3f6fa);
                        box-shadow:0 4px 12px rgba(0,0,0,0.06);
                        text-align:center;
                    ">
                        <div style="font-size:14px;color:#666">{item['time']}</div>
                        <div style="font-size:28px;font-weight:600;margin:8px 0">
                            {item['temp']}°C
                        </div>
                        <div style="font-size:14px">{item['weather']}</div>
                        <hr style="margin:10px 0">
                        <div style="font-size:13px">💧 {item['humidity']}%</div>
                        <div style="font-size:13px">🌬️ {item['wind']} m/s</div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

    # =========================
    # AIR QUALITY
    # =========================
    st.markdown("### 🌫️ Kualitas Udara")

    level, desc = aqi_description(air["AQI"])

    a1, a2, a3, a4 = st.columns(4)
    a1.metric("AQI", f"{air['AQI']} ({level})")
    a2.metric("PM2.5", f"{air['PM2.5']} µg/m³")
    a3.metric("PM10", f"{air['PM10']} µg/m³")
    a4.metric("CO", f"{air['CO']} µg/m³")

    st.success(desc)
    st.caption(f"Update kualitas udara: {air['time']} (WIB)")
