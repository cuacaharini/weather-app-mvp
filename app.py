import streamlit as st
import requests

API_KEY = st.secrets["OPENWEATHER_API_KEY"]

def get_current_weather(city: str) -> dict:
    url = "https://api.openweathermap.org/data/2.5/weather"
    params = {
        "q": city,
        "appid": API_KEY,
        "units": "metric",
        "lang": "id"
    }
    response = requests.get(url, params=params, timeout=10)
    response.raise_for_status()
    return response.json()

def normalize_weather(raw: dict) -> dict:
    return {
        "city": raw.get("name"),
        "country": raw.get("sys", {}).get("country"),
        "temp": raw.get("main", {}).get("temp"),
        "humidity": raw.get("main", {}).get("humidity"),
        "weather": raw.get("weather", [{}])[0].get("description"),
        "wind_speed": raw.get("wind", {}).get("speed"),
        "timestamp": raw.get("dt")
    }

st.title("Weather Data MVP")

city = st.text_input("Nama Kota", "Jakarta")

if st.button("Ambil Data"):
    raw = get_current_weather(city)
    clean = normalize_weather(raw)

    st.subheader("Clean Data (API-ready)")
    st.json(clean)
