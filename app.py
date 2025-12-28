import streamlit as st
import requests
from datetime import datetime, timezone, timedelta

# =================================================
# PAGE CONFIG
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
# SESSION STATE
# =================================================
if "last_city" not in st.session_state:
    st.session_state.last_city = "Jakarta"

if "auto_location" not in st.session_state:
    st.session_state.auto_location = True

# =================================================
# HELPERS
# =================================================
def fetch(url, params):
    r = requests.get(url, params=params, timeout=10)
    if r.status_code != 200:
        st.error("Gagal mengambil data cuaca")
        st.stop()
    return r.json()

def geocode(city):
    data = fetch(BASE_GEO, {
        "q": city,
        "limit": 5,
        "appid": API_KEY
    })
    return data

def weather_icon(desc):
    d = desc.lower()
    if "hujan" in d: return "🌧️"
    if "petir" in d: return "⛈️"
    if "awan" in d: return "☁️"
    if "cerah" in d or "clear" in d: return "☀️"
    if "kabut" in d: return "🌫️"
    return "🌥️"

# =================================================
# HEADER
# =================================================
st.markdown("## 🌤️ Weather App MVP")
st.caption("Auto Location • Autocomplete • Remember Location • WIB")

# =================================================
# TOGGLE AUTO LOCATION
# =================================================
st.session_state.auto_location = st.toggle(
    "📍 Gunakan lokasi otomatis",
    value=st.session_state.auto_location
)

# =================================================
# INPUT KOTA + AUTOCOMPLETE
# =================================================
city_input = st.text_input(
    "Nama Kota",
    value=st.session_state.last_city,
    placeholder="Ketik nama kota..."
)

suggestions = []
if len(city_input) >= 3:
    suggestions = geocode(city_input)

if suggestions:
    city_selected = st.selectbox(
        "Pilih kota",
        [f"{c['name']}, {c.get('country','')}" for c in suggestions],
        index=0
    )
    city = city_selected.split(",")[0]
else:
    city = city_input

load = st.button("Ambil Data", use_container_width=True)

# =================================================
# LOAD DATA
# =================================================
if load:
    st.session_state.last_city = city

    with st.spinner("Ngambil data cuaca dulu yaa..."):
        geo = geocode(city)[0]

        current = fetch(BASE_WEATHER, {
            "lat": geo["lat"], "lon": geo["lon"],
            "appid": API_KEY, "units": "metric", "lang": "id"
        })

        forecast = fetch(BASE_FORECAST, {
            "lat": geo["lat"], "lon": geo["lon"],
            "appid": API_KEY, "units": "metric", "lang": "id"
        })

        air = fetch(BASE_AIR, {
            "lat": geo["lat"], "lon": geo["lon"], "appid": API_KEY
        })

    # =================================================
    # CURRENT WEATHER
    # =================================================
    icon = weather_icon(current["weather"][0]["description"])
    temp = current["main"]["temp"]
    wind = current["wind"]["speed"]
    humidity = current["main"]["humidity"]

    st.markdown(f"### 📍 {geo['name']}, {geo['country']}")
    st.markdown(f"## {icon} {temp}°C")
    st.caption(f"{current['weather'][0]['description'].title()} • {to_wib(current['dt'])}")

    c1, c2, c3 = st.columns(3)
    c1.metric("🌡️ Suhu", f"{temp} °C")
    c2.metric("🌬️ Angin", f"{wind} m/s")
    c3.metric("💧 Kelembapan", f"{humidity} %")

    # =================================================
    # FORECAST CARDS
    # =================================================
    st.markdown("### ⏱️ Forecast 24 Jam")

    cols = st.columns(4)
    for i, item in enumerate(forecast["list"][:8]):
        with cols[i % 4]:
            st.markdown(
                f"""
                <div style="padding:14px;border-radius:14px;
                background:#f5f7fb;box-shadow:0 4px 10px rgba(0,0,0,0.05)">
                <div>{to_wib(item['dt'])}</div>
                <div style="font-size:24px">
                    {weather_icon(item['weather'][0]['description'])}
                    {item['main']['temp']}°C
                </div>
                <div>{item['weather'][0]['description'].title()}</div>
                <hr>
                💧 {item['main']['humidity']}% <br>
                🌬️ {item['wind']['speed']} m/s
                </div>
                """,
                unsafe_allow_html=True
            )

    # =================================================
    # AIR QUALITY
    # =================================================
    st.markdown("### 🌫️ Kualitas Udara")

    air_data = air["list"][0]
    aqi = air_data["main"]["aqi"]
    pm25 = air_data["components"]["pm2_5"]
    pm10 = air_data["components"]["pm10"]
    co = air_data["components"]["co"]

    a1, a2, a3, a4 = st.columns(4)
    a1.metric("AQI", aqi)
    a2.metric("PM2.5", pm25)
    a3.metric("PM10", pm10)
    a4.metric("CO", co)

    # =================================================
    # FUN EXPLANATION (BOTTOM)
    # =================================================
    st.markdown("### 😎 Cara Baca Angkanya (Santai Version)")

    st.markdown(f"""
**🌡️ Suhu**
- &lt; 24°C → Adem, enak buat tidur
- 24–30°C → Normal Indonesia
- &gt; 30°C → Panas, kipas & AC mulai berasa penting 😅

**🌬️ Angin**
- &lt; 2 m/s → Hampir gak berasa
- 2–5 m/s → Sepoi-sepoi
- &gt; 5 m/s → Anginnya kenceng, topi bisa terbang

**💧 Kelembapan**
- &lt; 50% → Udara kering
- 50–70% → Paling nyaman
- &gt; 70% → Gerah, gampang keringetan

**🌫️ AQI**
- 1 → Udara bersih, tarik napas puas
- 2–3 → Masih oke, tapi sensitif hati-hati
- 4–5 → Kurangi aktivitas luar, cari indoor

**PM2.5 & PM10**
- Angka kecil → Aman
- Angka gede → Debu halus, bisa bikin batuk & sesak

**CO (Carbon Monoxide)**
- Rendah → Aman
- Tinggi → Bahaya, biasanya dari asap kendaraan
""")
