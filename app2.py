import streamlit as st
import requests
import pandas as pd

# Page setup
st.set_page_config(page_title="Global Earth Temperature Dashboard", page_icon="🌍", layout="centered")

st.title("🌍 Earth Temperature Data Dashboard by R. Nimisha")
st.write("Fetch real-time and forecast temperature data for any location using the open-source **Open-Meteo API**.")

# Sidebar - Location input
st.sidebar.header("📍 Location Settings")

# Preset popular cities or manual coordinate entry
cities = {
    "London": (51.5074, -0.1278),
    "New York": (40.7128, -74.0060),
    "Tokyo": (35.6762, 139.6503),
    "Sydney": (-33.8688, 151.2093),
    "São Paulo": (-23.5505, -46.6333),
    "Custom": None
}

selected_city = st.sidebar.selectbox("Choose a preset city:", list(cities.keys()))

if selected_city == "Custom":
    lat = st.sidebar.number_input("Latitude", value=0.0, format="%.4f")
    lon = st.sidebar.number_input("Longitude", value=0.0, format="%.4f")
else:
    lat, lon = cities[selected_city]
    st.sidebar.write(f"**Latitude:** {lat}, **Longitude:** {lon}")

temp_unit = st.sidebar.radio("Temperature Unit", ["Celsius (°C)", "Fahrenheit (°F)"])
unit_param = "celsius" if "Celsius" in temp_unit else "fahrenheit"
unit_symbol = "°C" if unit_param == "celsius" else "°F"

# API Call Function
@st.cache_data(ttl=600)  # Cache data for 10 minutes
def fetch_temperature_data(latitude, longitude, unit):
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "current_weather": True,
        "hourly": "temperature_2m",
        "temperature_unit": unit,
        "timezone": "auto"
    }
    response = requests.get(url, params=params)
    if response.status_code == 200:
        return response.json()
    else:
        st.error(f"Error fetching data from API (Status Code: {response.status_code})")
        return None

# Load Data
with st.spinner("Fetching temperature data..."):
    data = fetch_temperature_data(lat, lon, unit_param)

if data:
    # Display Current Weather Metrics
    current = data.get("current_weather", {})
    current_temp = current.get("temperature", "N/A")
    wind_speed = current.get("windspeed", "N/A")

    st.subheader("Current Conditions")
    col1, col2 = st.columns(2)
    col1.metric(label="Current Temperature", value=f"{current_temp} {unit_symbol}")
    col2.metric(label="Wind Speed", value=f"{wind_speed} km/h")

    st.markdown("---")

    # Display Hourly Temperature Chart
    st.subheader("Hourly Temperature Forecast")
    hourly_data = data.get("hourly", {})
    
    if "time" in hourly_data and "temperature_2m" in hourly_data:
        df = pd.DataFrame({
            "Time": pd.to_datetime(hourly_data["time"]),
            f"Temperature ({unit_symbol})": hourly_data["temperature_2m"]
        })
        df.set_index("Time", inplace=True)

        # Plot line chart
        st.line_chart(df)

        # Show Raw Data toggle
        if st.checkbox("Show Raw Data Table"):
            st.dataframe(df)
