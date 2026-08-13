import pandas as pd
import plotly.express as px
import requests
import streamlit as st

# Set page configuration
st.set_page_config(
    page_title="India Cities Temperature Dashboard R nimisha",
    page_icon="🌡️",
    layout="wide",
)

# Major Indian Cities with Coordinates
INDIAN_CITIES = {
    "Mumbai": {"lat": 19.0760, "lon": 72.8777, "state": "Maharashtra"},
    "Delhi": {"lat": 28.6139, "lon": 77.2090, "state": "Delhi"},
    "Bengaluru": {"lat": 12.9716, "lon": 77.5946, "state": "Karnataka"},
    "Hyderabad": {"lat": 17.3850, "lon": 78.4867, "state": "Telangana"},
    "Chennai": {"lat": 13.0827, "lon": 80.2707, "state": "Tamil Nadu"},
    "Kolkata": {"lat": 22.5726, "lon": 88.3639, "state": "West Bengal"},
    "Ahmedabad": {"lat": 23.0225, "lon": 72.5714, "state": "Gujarat"},
    "Pune": {"lat": 18.5204, "lon": 73.8567, "state": "Maharashtra"},
    "Jaipur": {"lat": 26.9124, "lon": 75.7873, "state": "Rajasthan"},
    "Lucknow": {"lat": 26.8467, "lon": 80.9462, "state": "Uttar Pradesh"},
    "Chandigarh": {"lat": 30.7333, "lon": 76.7794, "state": "Punjab/Haryana"},
    "Srinagar": {"lat": 34.0837, "lon": 74.7973, "state": "Jammu & Kashmir"},
    "Guwahati": {"lat": 26.1445, "lon": 91.7362, "state": "Assam"},
    "Kochi": {"lat": 9.9312, "lon": 76.2673, "state": "Kerala"},
    "Bhubaneswar": {"lat": 20.2961, "lon": 85.8245, "state": "Odisha"},
}


# Map weather codes to human-readable text & emoji
def decode_wmo_code(code):
    wmo_map = {
        0: ("Clear sky", "☀️"),
        1: ("Mainly clear", "🌤️"),
        2: ("Partly cloudy", "⛅"),
        3: ("Overcast", "☁️"),
        45: ("Fog", "🌫️"),
        48: ("Rime fog", "🌫️"),
        51: ("Light drizzle", "🌧️"),
        53: ("Moderate drizzle", "🌧️"),
        55: ("Dense drizzle", "🌧️"),
        61: ("Slight rain", "🌧️"),
        63: ("Moderate rain", "🌧️"),
        65: ("Heavy rain", "🌧️"),
        80: ("Rain showers", "🌦️"),
        95: ("Thunderstorm", "🌩️"),
    }
    return wmo_map.get(code, ("Unknown", "🌡️"))


# Fetch temperature data for multiple locations in batch from Open-Meteo
@st.cache_data(ttl=600)  # Cache results for 10 minutes
def fetch_weather_data():
    lats = [str(info["lat"]) for info in INDIAN_CITIES.values()]
    lons = [str(info["lon"]) for info in INDIAN_CITIES.values()]

    # Open-Meteo multi-location API request
    url = f"https://api.open-meteo.com/v1/forecast?latitude={','.join(lats)}&longitude={','.join(lons)}&current=temperature_2m,relative_humidity_2m,apparent_temperature,weather_code,wind_speed_10m&timezone=Asia/Kolkata"

    try:
        response = requests.get(url, timeout=10)
        data = response.json()

        results = []
        city_names = list(INDIAN_CITIES.keys())

        # If requesting multiple points, API returns a list of result objects
        for i, item in enumerate(data if isinstance(data, list) else [data]):
            city_name = city_names[i]
            current = item.get("current", {})

            temp = current.get("temperature_2m")
            feels_like = current.get("apparent_temperature")
            humidity = current.get("relative_humidity_2m")
            wind_speed = current.get("wind_speed_10m")
            weather_code = current.get("weather_code", 0)

            condition, emoji = decode_wmo_code(weather_code)

            results.append(
                {
                    "City": city_name,
                    "State": INDIAN_CITIES[city_name]["state"],
                    "Latitude": INDIAN_CITIES[city_name]["lat"],
                    "Longitude": INDIAN_CITIES[city_name]["lon"],
                    "Temperature (°C)": temp,
                    "Feels Like (°C)": feels_like,
                    "Humidity (%)": humidity,
                    "Wind Speed (km/h)": wind_speed,
                    "Condition": condition,
                    "Emoji": emoji,
                }
            )

        return pd.DataFrame(results)

    except Exception as e:
        st.error(f"Error fetching data from Open-Meteo API: {e}")
        return pd.DataFrame()


# Header Section
st.title("🇮🇳 India Cities Live Temperature Dashboard")
st.markdown("Powered by **Open-Meteo API** (No API Key required)")

# Refresh button
if st.button("🔄 Refresh Data"):
    st.cache_data.clear()
    st.rerun()

# Load weather data
df = fetch_weather_data()

if not df.empty:
    # --- Top KPI Summary Cards ---
    st.subheader("Key Weather Highlights")

    hottest_city = df.loc[df["Temperature (°C)"].idxmax()]
    coolest_city = df.loc[df["Temperature (°C)"].idxmin()]
    avg_temp = df["Temperature (°C)"].mean()

    col1, col2, col3 = st.columns(3)
    col1.metric(
        label="🔥 Hottest City",
        value=f"{hottest_city['City']}",
        delta=f"{hottest_city['Temperature (°C)']} °C",
    )
    col2.metric(
        label="❄️ Coolest City",
        value=f"{coolest_city['City']}",
        delta=f"{coolest_city['Temperature (°C)']} °C",
        delta_color="inverse",
    )
    col3.metric(
        label="🌡️ Avg Temperature across Major Cities",
        value=f"{avg_temp:.1f} °C",
    )

    st.divider()

    # --- Interactive Layout Tabs ---
    tab_map, tab_chart, tab_details = st.tabs(
        ["🗺️ Interactive Map", "📊 Temperature Comparison", "📋 Detailed Data"]
    )

    with tab_map:
        st.subheader("Map View")

        # Map showing temperatures geographically
        fig_map = px.scatter_mapbox(
            df,
            lat="Latitude",
            lon="Longitude",
            color="Temperature (°C)",
            size="Temperature (°C)",
            hover_name="City",
            hover_data={
                "Temperature (°C)": True,
                "Condition": True,
                "Humidity (%)": True,
                "Latitude": False,
                "Longitude": False,
            },
            color_continuous_scale="Viridis",
            size_max=20,
            zoom=3.8,
            center={"lat": 20.5937, "lon": 78.9629},  # Center of India
            mapbox_style="open-street-map",
        )
        fig_map.update_layout(
            margin={"r": 0, "t": 0, "l": 0, "b": 0}, height=500
        )
        st.plotly_chart(fig_map, use_container_width=True)

    with tab_chart:
        st.subheader("Temperature Ranking (°C)")
        df_sorted = df.sort_values("Temperature (°C)", ascending=True)

        fig_bar = px.bar(
            df_sorted,
            x="Temperature (°C)",
            y="City",
            orientation="h",
            color="Temperature (°C)",
            color_continuous_scale="Thermal",
            text="Temperature (°C)",
        )
        fig_bar.update_traces(texttemplate="%{text:.1f} °C", textposition="outside")
        fig_bar.update_layout(
            height=500, yaxis_title="City", xaxis_title="Temperature (°C)"
        )
        st.plotly_chart(fig_bar, use_container_width=True)

    with tab_details:
        st.subheader("Live Weather Data by City")

        # Filter option
        selected_city = st.selectbox(
            "Select a city for detailed view:", ["All"] + list(df["City"])
        )

        if selected_city != "All":
            city_data = df[df["City"] == selected_city].iloc[0]
            st.info(
                f"**{city_data['City']}, {city_data['State']}** — {city_data['Emoji']} {city_data['Condition']}"
            )

            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Temperature", f"{city_data['Temperature (°C)']} °C")
            c2.metric("Feels Like", f"{city_data['Feels Like (°C)']} °C")
            c3.metric("Humidity", f"{city_data['Humidity (%)']}%")
            c4.metric("Wind Speed", f"{city_data['Wind Speed (km/h)']} km/h")
        else:
            st.dataframe(
                df[
                    [
                        "Emoji",
                        "City",
                        "State",
                        "Temperature (°C)",
                        "Feels Like (°C)",
                        "Condition",
                        "Humidity (%)",
                        "Wind Speed (km/h)",
                    ]
                ],
                use_container_width=True,
                height=450,
            )
else:
    st.warning("Unable to display weather data at this moment.")
