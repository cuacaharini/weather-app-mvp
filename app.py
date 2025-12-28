import streamlit as st
import requests
from datetime import datetime, timezone, timedelta

# =================================================
# PAGE CONFIG (MOBILE FRIENDLY)
# =================================================
st.set_page_config(
    page_title="Weather App MVP",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# =================================================
# TIMEZONE (WIB)
# =================================================
WIB = timezone(timedelta(hours=7))

def to_wib(ts: int) -> str:
    return datetime.fromtimestamp(ts, tz=WIB).strftime("%d %b %H:%M")

def to_wib_date(ts: int) -> str:
    return datetime.fromtimestamp(ts, tz=WIB).strftime("%d %b %Y")

# =================================================
# API CONFIG
# =================================================
if "OPENWEATHER_API_KEY" not in st.secrets:
    st.error("OPENWEATHER_API_KEY belum diset")
    st.stop()

API_KEY = st.secrets["OPENWEATHER_API_KEY"]

BASE_WEATHER = "https://api.openweathermap.org/data/2.5/weather"
BASE_FORECAST = "https://api.openweathermap.org/data/2.5/forecast"
BASE_GEO = "https://api.openweathermap.org/geo/1.0/direct"
BASE_AIR = "https://api.openweathermap.org/data/2.5/air_pollution"

# =================================================
# WEATHER ICON MAPPING
# =================================================
def weather_icon(desc: str) -> str:
    d = desc.lower()
    if "hujan" in d: return "🌧️"
    if "petir" in d: return "⛈️"
    if "awan" in d: return "☁️"
    if "cerah" in d or "clear" in d: return "☀️"
    if "kabut" in d or "mist" in d: return "🌫️"
    return "🌥️"

# =================================================
# AQI DESCRIPTION (EXTENDED)
# =================================================
def aqi_detail(aqi: int):
    return {
        1: ("Baik", "Udara sangat bersih. Aman untuk semua aktivitas luar ruangan."),
        2: ("Sedang", "Masih aman, tapi orang sensitif sebaiknya waspada."),
        3: ("Tidak Sehat (Sensitif)", "Anak-anak, lansia, dan penderita asma sebaiknya membatasi aktivitas luar."),
        4: ("Tidak Sehat", "Kurangi aktivitas luar. Risiko gangguan pernapasan meningkat."),
        5: ("Sangat Tidak Sehat", "Hindari aktivitas luar ruangan. Risiko serius bagi kesehatan.")
    }.get(aqi, ("Tidak diketahui", ""))

# =================================================
# SERVICE
# =================================================
def fetch(url, params):
    r = requests.get(url, params=params, timeout=10)
    if r.status_code != 200:
        st.error("Gagal mengambil data cuaca")
        st.stop()
    return r.json()

def geocode(city):
    data = fetch(BASE_GEO, {"q": city, "limit": 1, "appid": API_KEY})
    if not data:
        st.error("Kota tidak ditemukan")
        st.stop()
    return data[0]

# =================================================
# UI HEADER
# =================================================
st.markdown("## 🌤️ Weather App MVP")
st.caption("Modern Forecast • Daily Summary • Air Quality • WIB (UTC+7)")

# =========================
# INPUT (TOP, MOBILE FRIENDLY)
# =========================
c1, c2 = st.columns([3, 1])
with c1:
    city = st.text_input("Nama Kota", value="Jakarta", label_visibility="collapsed")
with c2:
    load = st.button("Ambil Data", use_container_width=True)

# =================================================
# SKELETON LOADING
# =================================================
if load:
    with st.spinner("Mengambil data cuaca..."):
        # =========================
        # FETCH DATA
        # =========================
        loc = geocode(city)

        current = fetch(BASE_WEATHER, {
            "lat": loc["lat"], "lon": loc["lon"],
            "appid": API_KEY, "units": "metric", "lang": "id"
        })

        forecast = fetch(BASE_FORECAST, {
            "lat": loc["lat"], "lon": loc["lon"],
            "appid": API_KEY, "units": "metric", "lang": "id"
        })

        air = fetch(BASE_AIR, {
            "lat": loc["lat"], "lon": loc["lon"], "appid": API_KEY
        })

    # =========================
    # CURRENT WEATHER
    # =========================
    weather_desc = current["weather"][0]["description"]
    icon = weather_icon(weather_desc)

    st.markdown(f"### 📍 {loc['name']}, {loc['country']}")
    st.markdown(f"## {icon} {current['main']['temp']}°C")
    st.caption(f"{weather_desc.title()} • Update {to_wib(current['dt'])}")

    c1, c2, c3 = st.columns(3)
    c1.metric("🤒 Terasa", f"{current['main']['feels_like']} °C")
    c2.metric("💧 Kelembapan", f"{current['main']['humidity']} %")
    c3.metric("🌬️ Angin", f"{current['wind']['speed']} m/s")

    # =========================
    # DAILY SUMMARY (TODAY / TOMORROW)
    # =========================
    st.markdown("### 📅 Ringkasan Harian")

    today = to_wib_date(forecast["list"][0]["dt"])
    tomorrow = to_wib_date(forecast["list"][8]["dt"])

    d1, d2 = st.columns(2)

    with d1:
        st.markdown("#### Hari Ini")
        st.metric("🌡️ Suhu", f"{forecast['list'][0]['main']['temp']} °C")
        st.caption(weather_icon(forecast['list'][0]['weather'][0]['description']) +
                   " " + forecast['list'][0]['weather'][0]['description'].title())

    with d2:
        st.markdown("#### Besok")
        st.metric("🌡️ Suhu", f"{forecast['list'][8]['main']['temp']} °C")
        st.caption(weather_icon(forecast['list'][8]['weather'][0]['description']) +
                   " " + forecast['list'][8]['weather'][0]['description'].title())

    # =========================
    # FORECAST CARDS (RESPONSIVE)
    # =========================
    st.markdown("### ⏱️ Forecast 24 Jam Ke Depan")

    cols = st.columns(4)
    for i, item in enumerate(forecast["list"][:8]):
        with cols[i % 4]:
            st.markdown(
                f"""
                <div style="
                    padding:14px;
                    border-radius:14px;
                    background:#f5f7fb;
                    box-shadow:0 4px 10px rgba(0,0,0,0.05);
                    margin-bottom:12px;
                ">
                    <div style="font-size:13px;color:#555">{to_wib(item['dt'])}</div>
                    <div style="font-size:26px;font-weight:600">
                        {weather_icon(item['weather'][0]['description'])}
                        {item['main']['temp']}°C
                    </div>
                    <div style="font-size:13px">{item['weather'][0]['description'].title()}</div>
                    <hr>
                    <div style="font-size:12px">💧 {item['main']['humidity']}%</div>
                    <div style="font-size:12px">🌬️ {item['wind']['speed']} m/s</div>
                </div>
                """,
                unsafe_allow_html=True
            )

    # =========================
    # AIR QUALITY
    # =========================
    st.markdown("### 🌫️ Kualitas Udara")

    aqi = air["list"][0]["main"]["aqi"]
    level, desc = aqi_detail(aqi)

    a1, a2, a3, a4 = st.columns(4)
    a1.metric("AQI", f"{aqi} ({level})")
    a2.metric("PM2.5", f"{air['list'][0]['components']['pm2_5']} µg/m³")
    a3.metric("PM10", f"{air['list'][0]['components']['pm10']} µg/m³")
    a4.metric("CO", f"{air['list'][0]['components']['co']} µg/m³")

    st.success(desc)

    with st.expander("ℹ️ Penjelasan Kualitas Udara"):
        st.markdown("""
**AQI (Air Quality Index)**  
Ringkasan kualitas udara (1–5). Semakin kecil → semakin sehat.

**PM2.5**  
Partikel sangat halus, paling berbahaya karena bisa masuk ke paru-paru & darah.

**PM10**  
Debu lebih besar, bisa menyebabkan iritasi saluran napas.

**CO (Carbon Monoxide)**  
Gas beracun dari kendaraan & pembakaran. Tinggi → berbahaya jika terhirup lama.
        """)

    st.caption(f"Update kualitas udara: {to_wib(air['list'][0]['dt'])} WIB")
