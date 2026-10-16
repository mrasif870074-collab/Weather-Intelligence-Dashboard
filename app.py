
import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import folium

from streamlit_folium import st_folium


# ==================== PAGE CONFIGURATION ====================

st.set_page_config(
    page_title="Weather Intelligence",
    page_icon="🌦️",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ==================== DARK THEME AND CSS ====================

st.markdown(
    """
    <style>
    .stApp {
        background: linear-gradient(135deg, #070b1b, #101936, #080d20);
        color: #ffffff;
    }

    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #101633, #080d20);
        border-right: 1px solid #263b69;
    }

    h1, h2, h3 {
        color: #38bdf8 !important;
    }

    p, label, span, li {
        color: #f8fafc;
    }

    .weather-title {
        color: #38bdf8;
        font-size: clamp(25px, 3vw, 42px);
        font-weight: 800;
        margin-bottom: 5px;
    }

    .welcome-text {
        color: #38bdf8 !important;
        font-size: 17px;
        font-weight: 700;
    }

    .weather-card {
        background: linear-gradient(145deg, #1c2b50, #101a35);
        border: 1px solid #385080;
        border-radius: 16px;
        padding: 19px;
        min-height: 125px;
        margin-bottom: 10px;
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.2);
    }

    .card-label {
        color: #cbd5e1;
        font-size: 14px;
        margin-bottom: 9px;
    }

    .card-value {
        color: #ffffff;
        font-size: clamp(23px, 2.3vw, 32px);
        font-weight: 750;
        overflow-wrap: anywhere;
    }

    .section-heading {
        color: #38bdf8 !important;
        font-size: 23px;
        font-weight: 750;
        margin-top: 20px;
        margin-bottom: 12px;
    }

    /* Make typed input text readable */
    div[data-testid="stTextInput"] input {
        background-color: #ffffff !important;
        color: #111827 !important;
        -webkit-text-fill-color: #111827 !important;
        caret-color: #111827 !important;
        border: 2px solid #38bdf8 !important;
        border-radius: 9px !important;
    }

    div[data-testid="stTextInput"] input::placeholder {
        color: #64748b !important;
        opacity: 1;
    }

    /* Fix selectbox text and dropdown readability */
    div[data-baseweb="select"] > div {
        background-color: #ffffff !important;
        color: #111827 !important;
        border-color: #38bdf8 !important;
    }

    div[data-baseweb="select"] input {
        color: #111827 !important;
        -webkit-text-fill-color: #111827 !important;
    }

    div[data-baseweb="select"] span {
        color: #111827 !important;
    }

    ul[data-testid="stSelectboxVirtualDropdown"] {
        background-color: #ffffff !important;
    }

    div[role="option"] {
        background-color: #ffffff !important;
        color: #111827 !important;
    }

    div[role="option"] * {
        color: #111827 !important;
    }

    /* Buttons */
    div.stButton > button,
    div.stFormSubmitButton > button,
    div.stDownloadButton > button {
        background: linear-gradient(90deg, #0284c7, #06b6d4) !important;
        color: #ffffff !important;
        border: none !important;
        border-radius: 10px !important;
        font-weight: 700 !important;
        min-height: 43px;
        width: 100%;
    }

    div.stButton > button p,
    div.stFormSubmitButton > button p,
    div.stDownloadButton > button p {
        color: #ffffff !important;
    }

    div[data-testid="stMetric"] {
        background: #111c39;
        border: 1px solid #334b79;
        border-radius: 12px;
        padding: 14px;
    }

    div[data-testid="stMetricLabel"] {
        color: #dbeafe !important;
    }

    div[data-testid="stMetricValue"] {
        color: #ffffff !important;
    }

    div[data-testid="stAlert"] p {
        color: inherit;
    }

    .stCaption {
        color: #cbd5e1 !important;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# ==================== API CONFIGURATION ====================

GEO_URL = "https://geocoding-api.open-meteo.com/v1/search"
WEATHER_URL = "https://api.open-meteo.com/v1/forecast"


# ==================== WEATHER CONDITION ====================

def weather_condition(code):
    """Convert WMO weather codes into readable descriptions."""

    conditions = {
        0: ("Clear Sky", "☀️"),
        1: ("Mainly Clear", "🌤️"),
        2: ("Partly Cloudy", "⛅"),
        3: ("Overcast", "☁️"),
        45: ("Fog", "🌫️"),
        48: ("Depositing Rime Fog", "🌫️"),
        51: ("Light Drizzle", "🌦️"),
        53: ("Moderate Drizzle", "🌦️"),
        55: ("Dense Drizzle", "🌧️"),
        56: ("Freezing Drizzle", "🌧️"),
        57: ("Dense Freezing Drizzle", "🌧️"),
        61: ("Slight Rain", "🌧️"),
        63: ("Moderate Rain", "🌧️"),
        65: ("Heavy Rain", "🌧️"),
        66: ("Freezing Rain", "🌧️"),
        67: ("Heavy Freezing Rain", "🌧️"),
        71: ("Slight Snowfall", "🌨️"),
        73: ("Moderate Snowfall", "🌨️"),
        75: ("Heavy Snowfall", "❄️"),
        77: ("Snow Grains", "❄️"),
        80: ("Rain Showers", "🌦️"),
        81: ("Moderate Rain Showers", "🌧️"),
        82: ("Violent Rain Showers", "⛈️"),
        85: ("Snow Showers", "🌨️"),
        86: ("Heavy Snow Showers", "❄️"),
        95: ("Thunderstorm", "⛈️"),
        96: ("Thunderstorm with Hail", "⛈️"),
        99: ("Thunderstorm with Heavy Hail", "⛈️"),
    }

    return conditions.get(code, ("Weather Unavailable", "🌡️"))


# ==================== API FUNCTIONS ====================

@st.cache_data(ttl=600, show_spinner=False)
def search_cities(city_name):
    """Search for matching cities using Open-Meteo geocoding."""

    response = requests.get(
        GEO_URL,
        params={
            "name": city_name,
            "count": 10,
            "language": "en",
            "format": "json",
        },
        timeout=15,
    )
    response.raise_for_status()
    return response.json().get("results", [])


@st.cache_data(ttl=600, show_spinner=False)
def get_weather(latitude, longitude, timezone):
    """Fetch current weather, hourly data and a seven-day forecast."""

    response = requests.get(
        WEATHER_URL,
        params={
            "latitude": latitude,
            "longitude": longitude,
            "timezone": timezone,
            "forecast_days": 7,
            "current": (
                "temperature_2m,"
                "relative_humidity_2m,"
                "apparent_temperature,"
                "is_day,"
                "precipitation,"
                "weather_code,"
                "surface_pressure,"
                "wind_speed_10m"
            ),
            "hourly": (
                "temperature_2m,"
                "relative_humidity_2m,"
                "precipitation_probability,"
                "precipitation,"
                "wind_speed_10m"
            ),
            "daily": (
                "weather_code,"
                "temperature_2m_max,"
                "temperature_2m_min,"
                "precipitation_probability_max,"
                "sunrise,"
                "sunset"
            ),
        },
        timeout=20,
    )
    response.raise_for_status()
    return response.json()


# ==================== SIDEBAR ====================

st.sidebar.markdown("## 📍 Search City")
st.sidebar.caption("Search for a city and select the correct location.")

if "city_results" not in st.session_state:
    st.session_state.city_results = []
    st.session_state.selected_city = None
    st.session_state.search_error = ""

with st.sidebar.form("city_search_form"):
    city_input = st.text_input(
        "Enter city name",
        value="Delhi",
        placeholder="e.g. Delhi, Mumbai, Dubai",
    )

    search_clicked = st.form_submit_button(
        "🔎 Search Cities",
        width="stretch",
    )

if search_clicked:
    if not city_input.strip():
        st.session_state.search_error = "Please enter a city name."
        st.session_state.city_results = []
    else:
        try:
            with st.spinner("Searching locations..."):
                results = search_cities(city_input.strip())

            st.session_state.city_results = results
            st.session_state.search_error = ""

            if results:
                st.session_state.selected_city = 0
            else:
                st.session_state.search_error = (
                    "No matching city found. Try another spelling."
                )

        except requests.RequestException:
            st.session_state.search_error = (
                "Unable to connect to the weather service. "
                "Check your internet connection and try again."
            )

if st.session_state.search_error:
    st.sidebar.error(st.session_state.search_error)

if not st.session_state.city_results:
    try:
        st.session_state.city_results = search_cities("Delhi")
        st.session_state.selected_city = 0
    except requests.RequestException:
        st.sidebar.warning(
            "Search for a city after checking your internet connection."
        )

selected_location = None

if st.session_state.city_results:
    city_results = st.session_state.city_results

    def location_label(location):
        parts = [
            location.get("name", ""),
            location.get("admin1", ""),
            location.get("country", ""),
        ]
        return ", ".join(part for part in parts if part)

    selected_index = st.sidebar.selectbox(
        "Choose the correct location",
        options=list(range(len(city_results))),
        format_func=lambda index: location_label(city_results[index]),
        index=(
            st.session_state.selected_city
            if st.session_state.selected_city is not None
            and st.session_state.selected_city < len(city_results)
            else 0
        ),
    )

    selected_location = city_results[selected_index]
    st.session_state.selected_city = selected_index

st.sidebar.divider()
st.sidebar.markdown("### 🌐 Dashboard")
st.sidebar.caption("Weather data provided by Open-Meteo.")
st.sidebar.caption("Forecasts are estimates, not official warnings.")


# ==================== MAIN DASHBOARD ====================

st.markdown(
    '<div class="weather-title">'
    '🌦️ Weather Intelligence Dashboard'
    '</div>',
    unsafe_allow_html=True,
)

st.caption(
    "Live Weather | Interactive Charts | 7-Day Forecast | City Comparison"
)

if selected_location is None:
    st.error(
        "No city is selected. Enter a city in the sidebar and search again."
    )
    st.stop()

city_name = selected_location.get("name", "Selected City")
country = selected_location.get("country", "")
latitude = selected_location["latitude"]
longitude = selected_location["longitude"]
timezone = selected_location.get("timezone", "auto")

try:
    with st.spinner(f"Loading weather data for {city_name}..."):
        weather = get_weather(latitude, longitude, timezone)

except requests.RequestException:
    st.error(
        "Could not load weather data. Check your internet connection "
        "and search again."
    )
    st.stop()

current = weather.get("current", {})
hourly = weather.get("hourly", {})
daily = weather.get("daily", {})

if not current or not daily:
    st.error("Weather data is incomplete. Please try again.")
    st.stop()

condition, condition_icon = weather_condition(
    current.get("weather_code", -1)
)

st.markdown(
    f'<div class="section-heading">{condition_icon} {condition}</div>',
    unsafe_allow_html=True,
)

st.markdown(
    f'<div class="welcome-text">Welcome! Current selection: '
    f'{city_name}, {country}</div>',
    unsafe_allow_html=True,
)

st.caption(
    f"Local time: {current.get('time', 'N/A')} | "
    f"Latitude: {latitude:.2f} | Longitude: {longitude:.2f}"
)

st.markdown(
    '<div class="section-heading">🌡️ Current Weather</div>',
    unsafe_allow_html=True,
)


# ==================== WEATHER METRIC CARDS ====================

temperature = current.get("temperature_2m")
feels_like = current.get("apparent_temperature")
humidity = current.get("relative_humidity_2m")
wind_speed = current.get("wind_speed_10m")
precipitation = current.get("precipitation")
pressure = current.get("surface_pressure")
is_day = current.get("is_day")

day_night = (
    "Day" if is_day == 1 else "Night" if is_day == 0 else "N/A"
)

metrics = [
    ("🌡️ Temperature", temperature, "°C"),
    ("🥵 Feels Like", feels_like, "°C"),
    ("💧 Humidity", humidity, "%"),
    ("💨 Wind Speed", wind_speed, "km/h"),
    ("🌧️ Precipitation", precipitation, "mm"),
    ("🧭 Pressure", pressure, "hPa"),
    ("🌞 Day / Night", day_night, ""),
]

metric_cols = st.columns(4)

for index, (label, value, unit) in enumerate(metrics):
    with metric_cols[index % 4]:
        if value is None:
            display_value = "N/A"
        elif isinstance(value, (int, float)):
            display_value = f"{value:.1f} {unit}".strip()
        else:
            display_value = f"{value} {unit}".strip()

        st.markdown(
            f"""
            <div class="weather-card">
                <div class="card-label">{label}</div>
                <div class="card-value">{display_value}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


# ==================== WEATHER ALERTS ====================

st.markdown(
    '<div class="section-heading">🚨 Weather Alerts</div>',
    unsafe_allow_html=True,
)

alerts = []

hourly_times = pd.to_datetime(hourly.get("time", []))
now = pd.to_datetime(current.get("time"))

if hourly_times.size:
    if hourly_times.tz is not None:
        now = now.tz_localize(hourly_times.tz)

    next_24h = hourly_times >= now
    next_24h = next_24h & (
        hourly_times <= now + pd.Timedelta(hours=24)
    )

    rain_values = hourly.get("precipitation_probability", [])
    rain_values = [
        value
        for value, valid in zip(rain_values, next_24h)
        if valid and value is not None
    ]

    if rain_values:
        max_rain = max(rain_values)

        if max_rain >= 70:
            alerts.append(
                f"High rain probability: up to {max_rain}% "
                "in the next 24 hours. Carry rain protection."
            )
        elif max_rain >= 40:
            alerts.append(
                f"Rain may occur: maximum probability {max_rain}% "
                "in the next 24 hours."
            )

if wind_speed is not None and wind_speed >= 40:
    alerts.append(
        f"Strong wind detected: {wind_speed:.1f} km/h. "
        "Take extra care outdoors."
    )

if temperature is not None and temperature >= 40:
    alerts.append(
        f"High temperature: {temperature:.1f}°C. "
        "Stay hydrated and avoid prolonged heat exposure."
    )
elif temperature is not None and temperature <= 5:
    alerts.append(
        f"Low temperature: {temperature:.1f}°C. "
        "Dress warmly."
    )

if alerts:
    for alert in alerts:
        st.warning(f"⚠️ {alert}")
else:
    st.success(
        "No threshold-based alerts triggered by the available forecast."
    )

st.caption(
    "These are app-generated alerts based on forecast thresholds, "
    "not official severe-weather warnings."
)


# ==================== INTERACTIVE WEATHER MAP ====================

st.markdown(
    '<div class="section-heading">🗺️ Interactive Weather Map</div>',
    unsafe_allow_html=True,
)

weather_map = folium.Map(
    location=[latitude, longitude],
    zoom_start=9,
    tiles="OpenStreetMap",
)

folium.Marker(
    location=[latitude, longitude],
    tooltip=city_name,
    popup=(
        f"{city_name}<br>"
        f"Temperature: {temperature} °C<br>"
        f"Condition: {condition}"
    ),
    icon=folium.Icon(color="blue", icon="cloud"),
).add_to(weather_map)

st_folium(
    weather_map,
    height=420,
    use_container_width=True,
    key="weather_map",
)


# ==================== INTERACTIVE WEATHER CHARTS ====================

st.markdown(
    '<div class="section-heading">📊 Interactive Weather Charts</div>',
    unsafe_allow_html=True,
)

st.caption(
    "Select a weather variable below. Use the chart toolbar to zoom, "
    "pan, or download the chart."
)

chart_options = {
    "Temperature (°C)": ("temperature_2m", "Temperature (°C)"),
    "Humidity (%)": ("relative_humidity_2m", "Humidity (%)"),
    "Rain Probability (%)": (
        "precipitation_probability",
        "Rain Probability (%)",
    ),
    "Precipitation (mm)": ("precipitation", "Precipitation (mm)"),
    "Wind Speed (km/h)": ("wind_speed_10m", "Wind Speed (km/h)"),
}

selected_chart = st.selectbox(
    "Choose a weather variable",
    options=list(chart_options.keys()),
    index=0,
    key="weather_chart_variable",
)

hourly_df = pd.DataFrame(hourly)

if "time" in hourly_df.columns:
    hourly_df["time"] = pd.to_datetime(hourly_df["time"])

    chart_key, chart_title = chart_options[selected_chart]

    if chart_key in hourly_df.columns:
        chart_df = hourly_df[["time", chart_key]].copy()
        chart_df = chart_df.dropna(subset=[chart_key])

        if not chart_df.empty:
            chart_df = chart_df.head(48)

            fig = px.line(
                chart_df,
                x="time",
                y=chart_key,
                title=f"{selected_chart} — Next 48 Hours",
                markers=True,
                labels={
                    "time": "Local Time",
                    chart_key: chart_title,
                },
                template="plotly_dark",
            )

            fig.update_layout(
                paper_bgcolor="#0b1125",
                plot_bgcolor="#111c39",
                font=dict(color="#f8fafc", size=13),
                title_font=dict(color="#38bdf8", size=20),
                xaxis=dict(
                    title="Local Time",
                    gridcolor="#263653",
                ),
                yaxis=dict(
                    title=chart_title,
                    gridcolor="#263653",
                ),
                margin=dict(l=20, r=20, t=65, b=20),
            )

            fig.update_traces(line_width=3)

            st.plotly_chart(
                fig,
                width="stretch",
                config={"displaylogo": False},
            )
        else:
            st.info("No chart data is available for this variable.")
    else:
        st.warning("This weather variable is not available.")
else:
    st.warning("Hourly weather data is unavailable.")


# ==================== SEVEN-DAY FORECAST ====================

st.markdown(
    '<div class="section-heading">📅 7-Day Weather Forecast</div>',
    unsafe_allow_html=True,
)

forecast_df = pd.DataFrame(daily)

if not forecast_df.empty:
    forecast_df["Condition"] = forecast_df["weather_code"].apply(
        lambda code: weather_condition(code)[0]
    )

    forecast_df = forecast_df.rename(
        columns={
            "time": "Date",
            "Condition": "Weather",
            "temperature_2m_max": "Max Temperature (°C)",
            "temperature_2m_min": "Min Temperature (°C)",
            "precipitation_probability_max": "Rain Chance (%)",
            "sunrise": "Sunrise",
            "sunset": "Sunset",
        }
    )

    display_columns = [
        "Date",
        "Weather",
        "Max Temperature (°C)",
        "Min Temperature (°C)",
        "Rain Chance (%)",
        "sunrise",
        "sunset",
    ]

    forecast_display = forecast_df[
        [column for column in display_columns if column in forecast_df]
    ].rename(
        columns={
            "sunrise": "Sunrise",
            "sunset": "Sunset",
        }
    )

    st.dataframe(
        forecast_display,
        hide_index=True,
        width="stretch",
    )

    st.download_button(
        "📥 Download 7-Day Forecast CSV",
        data=forecast_display.to_csv(index=False).encode("utf-8"),
        file_name=f"{city_name.lower().replace(' ', '_')}_weather_forecast.csv",
        mime="text/csv",
        width="stretch",
    )



# ==================== CITY COMPARISON ====================

st.markdown(
    '<div class="section-heading">🌍 City Weather Comparison</div>',
    unsafe_allow_html=True,
)

st.caption(
    "Compare current temperatures and weather conditions in other cities."
)

comparison_cities = st.multiselect(
    "Choose cities to compare",
    options=[
        "Delhi",
        "Mumbai",
        "Kolkata",
        "Chennai",
        "Bengaluru",
        "Hyderabad",
        "Dubai",
        "London",
        "New York",
    ],
    default=["Mumbai", "Dubai"],
    key="comparison_cities",
)

if st.button("Compare Cities", width="stretch"):
    comparison_rows = []
    comparison_errors = []

    # Use only cities selected in the comparison dropdown.
    # Do not add the main dashboard city here.
    cities_to_check = comparison_cities.copy()

    if not cities_to_check:
        st.warning("Please select at least one city to compare.")

    else:
        with st.spinner("Fetching comparison data..."):
            for name in cities_to_check:
                try:
                    locations = search_cities(name)

                    if not locations:
                        comparison_errors.append(
                            f"No location found for {name}."
                        )
                        continue

                    location = locations[0]

                    data = get_weather(
                        location["latitude"],
                        location["longitude"],
                        location.get("timezone", "auto"),
                    )

                    observation = data.get("current", {})

                    comparison_rows.append(
                        {
                            "City": name,
                            "Country": location.get("country", "N/A"),
                            "Temperature (°C)": observation.get(
                                "temperature_2m"
                            ),
                            "Humidity (%)": observation.get(
                                "relative_humidity_2m"
                            ),
                            "Wind Speed (km/h)": observation.get(
                                "wind_speed_10m"
                            ),
                            "Condition": weather_condition(
                                observation.get("weather_code", -1)
                            )[0],
                        }
                    )

                except (
                    requests.RequestException,
                    KeyError,
                    TypeError,
                ):
                    comparison_errors.append(
                        f"Could not load weather data for {name}."
                    )

        if comparison_rows:
            comparison_df = pd.DataFrame(comparison_rows)

            st.subheader("City Comparison Results")

            st.dataframe(
                comparison_df,
                hide_index=True,
                width="stretch",
            )

            numeric_df = comparison_df.dropna(
                subset=["Temperature (°C)"]
            )

            if not numeric_df.empty:
                comparison_fig = px.bar(
                    numeric_df,
                    x="City",
                    y="Temperature (°C)",
                    color="Temperature (°C)",
                    title="Current Temperature by City",
                    template="plotly_dark",
                    hover_data=["Country", "Condition"],
                )

                comparison_fig.update_layout(
                    paper_bgcolor="#0b1125",
                    plot_bgcolor="#111c39",
                    font=dict(color="#f8fafc"),
                    title_font=dict(color="#38bdf8", size=20),
                    coloraxis_showscale=False,
                )

                st.plotly_chart(
                    comparison_fig,
                    width="stretch",
                    config={"displaylogo": False},
                )

            st.download_button(
                "📥 Download City Comparison CSV",
                data=comparison_df.to_csv(
                    index=False
                ).encode("utf-8"),
                file_name="city_weather_comparison.csv",
                mime="text/csv",
                width="stretch",
            )

        else:
            st.error("No comparison data could be retrieved.")

        for error in comparison_errors:
            st.warning(error)

        


# ==================== FOOTER ====================

st.divider()

st.caption(
    "Weather data: Open-Meteo | Map: OpenStreetMap | "
    "Forecasts are estimates and may change."
)

st.caption(
    "Weather Intelligence Dashboard | Built with Python, "
    "Streamlit, Pandas, Plotly and Folium"
)

