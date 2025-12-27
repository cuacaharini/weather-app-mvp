import streamlit as st
import requests
from datetime import datetime, timezone, timedelta
import pandas as pd
import altair as alt

# =================================================
# TIMEZONE CONFIG (UTC+7 / WIB)
# =================================================
WIB = timezone(timedelta(hours=7))

def to_wib(ts: int) -> str:
    return datetime.fromtimestamp(ts, tz=WIB).strftime("%d %b %H:%M")

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
            "Waktu": to_wib(item["dt"]),
            "Suhu": item["main"]["temp"]
        })
    return pd.DataFrame(rows)

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
        1: ("Baik", "Kualitas udara sangat baik, aman untuk semua aktivitas."),
        2: ("Sedang", "Masih aman, tapi kelompok sensitif sebaiknya mengurangi aktivitas berat."),
        3: ("Tidak Sehat (Sensitif)", "Anak-anak & lansia sebaiknya mengurangi aktivitas luar."),
        4: ("Tidak Sehat", "Hindari aktivitas luar ruangan dalam waktu lama."),
        5: ("Sangat Tidak Sehat", "Sebaiknya tetap di dalam ruangan.")
    }.get(aqi, ("Tidak diketahui", ""))

# =================================================
# UI
# =================================================
st.set_page_config(page_title="Weather App MVP", layout="wide")

st.markdown("## 🌤️ Weather App MVP")
st.caption("Forecast Visual • Air Quality Explained • Timezone WIB (UTC+7)")

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
    forecast_df = normalize_forecast(forecast_raw)
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
    # FORECAST CHART
    # =========================
    st.markdown("### ⏱️ Forecast 24 Jam Ke Depan")

    chart = alt.Chart(forecast_df).mark_line(point=True).encode(
        x=alt.X("Waktu", title="Waktu"),
        y=alt.Y("Suhu", title="Suhu (°C)"),
        tooltip=["Waktu", "Suhu"]
    ).properties(height=300)

    st.altair_chart(chart, use_container_width=True)

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

    with st.expander("ℹ️ Penjelasan Istilah Kualitas Udara"):
        st.markdown("""
**AQI (Air Quality Index)**  
Angka ringkasan kualitas udara (1–5). Semakin kecil, semakin baik.

**PM2.5**  
Partikel sangat halus (<2.5µm). Bisa masuk ke paru-paru dan aliran darah.  
➡️ Paling berbahaya untuk kesehatan.

**PM10**  
Partikel debu lebih besar (<10µm). Bisa mengiritasi saluran pernapasan.

**CO (Carbon Monoxide)**  
Gas beracun dari kendaraan & pembakaran. Tinggi → berbahaya jika terhirup lama.
        """)

    st.caption(f"Update kualitas udara: {air['time']} (WIB)")
