import datetime
import time
import pandas as pd
import plotly.express as px
import requests
import streamlit as st

# Set page configuration
st.set_page_config(
    page_title="World Population Clock by R nimisha",
    page_icon="🌍",
    layout="wide",
)


# Fetch base population data from World Bank API
@st.cache_data(ttl=86400)  # Cache API call for 24 hours
def get_world_bank_population():
    """Fetches total global population and country-level population data from World Bank API."""
    try:
        # World Bank API for global total population (Indicator: SP.POP.TOTL)
        world_url = "https://api.worldbank.org/v2/country/WLD/indicator/SP.POP.TOTL?format=json&per_page=5"
        world_response = requests.get(world_url, timeout=10).json()

        # Extract most recent available estimate
        world_data = world_response[1]
        latest_world_entry = next(
            item for item in world_data if item["value"] is not None
        )
        base_population = latest_world_entry["value"]
        base_year = int(latest_world_entry["date"])

        # World Bank API for country-level populations
        countries_url = "https://api.worldbank.org/v2/country/all/indicator/SP.POP.TOTL?format=json&per_page=300&date=2022"
        countries_response = requests.get(countries_url, timeout=10).json()

        country_list = []
        if len(countries_response) > 1:
            for entry in countries_response[1]:
                # Exclude regional aggregates (keep individual countries)
                if entry["value"] and entry["countryiso3code"]:
                    country_list.append(
                        {
                            "Country": entry["country"]["value"],
                            "ISO3": entry["countryiso3code"],
                            "Population": entry["value"],
                        }
                    )

        df = pd.DataFrame(country_list)
        df = df.sort_values(by="Population", ascending=False).reset_index(
            drop=True
        )

        return base_population, base_year, df

    except Exception as e:
        # Fallback values if API is unavailable
        st.warning(f"Could not reach API ({e}). Using estimated fallback data.")
        fallback_df = pd.DataFrame(
            [
                {"Country": "India", "ISO3": "IND", "Population": 1428627663},
                {"Country": "China", "ISO3": "CHN", "Population": 1411750000},
                {
                    "Country": "United States",
                    "ISO3": "USA",
                    "Population": 333287557,
                },
                {"Country": "Indonesia", "ISO3": "IDN", "Population": 275501339},
                {"Country": "Pakistan", "ISO3": "PAK", "Population": 235824862},
            ]
        )
        return 8_000_000_000, 2023, fallback_df


# Load data
base_pop, base_year, country_df = get_world_bank_population()

# Estimated global growth rate (~0.88% annual growth, approx. 2.23 people per second)
GROWTH_RATE_PER_SEC = 2.23

# Calculate current estimate based on elapsed seconds since base year
base_datetime = datetime.datetime(base_year, 1, 1, tzinfo=datetime.timezone.utc)
now_utc = datetime.datetime.now(datetime.timezone.utc)
elapsed_seconds = (now_utc - base_datetime).total_seconds()
current_estimated_pop = int(base_pop + (elapsed_seconds * GROWTH_RATE_PER_SEC))

# --- UI Header ---
st.title("🌍 Real-Time World Population Dashboard")
st.markdown(
    f"*Source data anchored from **World Bank API** baseline ({base_year}) with real-time growth modeling.*"
)

# --- Top Section: Live Ticking Metric ---
st.subheader("Estimated Current Global Population")
metric_placeholder = st.empty()

# Render live ticker metric
metric_placeholder.metric(
    label="Live Estimated World Population",
    value=f"{current_estimated_pop:,}",
    delta=f"+{GROWTH_RATE_PER_SEC:.2f} per sec",
)

st.divider()

# --- Main Dashboard Tabs ---
tab1, tab2 = st.tabs(["📊 Global Distribution", "🔝 Top Countries"])

with tab1:
    st.subheader("World Population Map")

    # Choropleth map using Plotly Express
    fig_map = px.choropleth(
        country_df,
        locations="ISO3",
        color="Population",
        hover_name="Country",
        color_continuous_scale=px.colors.sequential.Plasma,
        title="Country Population Distribution",
    )
    fig_map.update_layout(margin={"r": 0, "t": 40, "l": 0, "b": 0})
    st.plotly_chart(fig_map, use_container_width=True)

with tab2:
    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader("Top 10 Most Populous Countries")
        top_10 = country_df.head(10)
        fig_bar = px.bar(
            top_10,
            x="Population",
            y="Country",
            orientation="h",
            color="Population",
            color_continuous_scale="Blues",
        )
        fig_bar.update_layout(yaxis={"categoryorder": "total ascending"})
        st.plotly_chart(fig_bar, use_container_width=True)

    with col2:
        st.subheader("Data Table")
        st.dataframe(
            country_df[["Country", "Population"]],
            use_container_width=True,
            height=400,
        )

# Auto-refresh loop for real-time ticking clock effect
time.sleep(1)
st.rerun()
