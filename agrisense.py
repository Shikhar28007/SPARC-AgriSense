
import streamlit as st
import pickle
import pandas as pd
import requests
import db_manager
import time

st.set_page_config(page_title="SPARC", layout="wide")

hide_streamlit_style = """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Fira+Code:wght@400;500;600&family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap');

    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    /* ─── Light Scratchpad Canvas ─── */
    .stApp {
        background-color: #faf9f5 !important;
        background-image: 
            radial-gradient(#dcd8cf 1px, transparent 1px) !important;
        background-size: 20px 20px !important;
        color: #2b2d42 !important;
        font-family: 'Plus Jakarta Sans', -apple-system, sans-serif !important;
    }

    /* ─── Scratchpad Header & Banners ─── */
    .scratchpad-banner {
        display: flex;
        align-items: center;
        justify-content: space-between;
        flex-wrap: wrap;
        gap: 10px;
        background: #fffefb;
        border: 1.5px dashed #cfc9bb;
        border-radius: 8px;
        padding: 10px 16px;
        margin-bottom: 20px;
        box-shadow: 2px 2px 0px rgba(0, 0, 0, 0.04);
    }
    .draft-badge {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        background: #fef3c7;
        color: #92400e;
        font-family: 'Fira Code', monospace;
        font-size: 0.78rem;
        font-weight: 600;
        padding: 4px 10px;
        border-radius: 4px;
        border: 1px solid #fde68a;
    }
    .dev-stage-badge {
        font-family: 'Fira Code', monospace;
        font-size: 0.75rem;
        color: #57534e;
        background: #f5f4ef;
        padding: 4px 10px;
        border-radius: 4px;
        border: 1px solid #e7e4dc;
    }

    /* ─── Sticky Note Callout ─── */
    .sticky-note {
        background: #fffbe6;
        border-left: 4px solid #eab308;
        border-top: 1px solid #fef08a;
        border-right: 1px solid #fef08a;
        border-bottom: 1px solid #fef08a;
        padding: 12px 16px;
        border-radius: 4px;
        font-size: 0.88rem;
        color: #713f12;
        margin: 12px 0;
        box-shadow: 1px 2px 4px rgba(0,0,0,0.02);
    }

    /* ─── Notebook Tabs ─── */
    button[data-baseweb="tab"] {
        background-color: #f1ede4 !important;
        border: 1px solid #ded9cb !important;
        border-bottom: none !important;
        border-radius: 8px 8px 0 0 !important;
        padding: 8px 18px !important;
        margin-right: 5px !important;
        font-weight: 600 !important;
        color: #57534e !important;
        font-family: 'Fira Code', monospace !important;
        font-size: 0.85rem !important;
    }
    button[data-baseweb="tab"][aria-selected="true"] {
        background-color: #ffffff !important;
        border-top: 3px solid #2d6a4f !important;
        color: #1b4332 !important;
        box-shadow: 0 -2px 5px rgba(0,0,0,0.02) !important;
    }

    /* ─── Metric Paper Cards ─── */
    div[data-testid="stMetric"] {
        background: #ffffff !important;
        border: 1.5px solid #e8e4da !important;
        border-radius: 8px !important;
        padding: 12px 16px !important;
        box-shadow: 2px 2px 0px rgba(0,0,0,0.03) !important;
    }
    div[data-testid="stMetricLabel"] {
        font-size: 0.82rem !important;
        color: #78716c !important;
        font-family: 'Fira Code', monospace !important;
    }
    div[data-testid="stMetricValue"] {
        color: #1b4332 !important;
        font-weight: 700 !important;
    }

    /* ─── Inputs & Sliders on Light Paper ─── */
    div[data-baseweb="input"], div[data-baseweb="select"] {
        background-color: #ffffff !important;
        border-radius: 6px !important;
        border: 1px solid #d6d0c4 !important;
    }

    /* ─── Buttons ─── */
    button[kind="primary"] {
        background-color: #2d6a4f !important;
        border-color: #2d6a4f !important;
        border-radius: 6px !important;
        font-weight: 600 !important;
        box-shadow: 2px 2px 0px rgba(0,0,0,0.1) !important;
    }
    button[kind="primary"]:hover {
        background-color: #1b4332 !important;
        border-color: #1b4332 !important;
    }
    </style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

try:
    with open("crop_model.pkl", "rb") as file:
        model = pickle.load(file)
except FileNotFoundError:
    st.error("System Error: model data not found. Please ensure crop_model.pkl is in the repository.")
    model = None

# ─────────────────────────── CONSTANTS ───────────────────────────

REGIONAL_SOIL_DATA = {
    "chandigarh": {"n": 75, "p": 45, "k": 40, "type": "Loamy"},
    "ludhiana": {"n": 78, "p": 42, "k": 38, "type": "Sandy Loam"},
    "ambala": {"n": 76, "p": 44, "k": 42, "type": "Alluvial"},
    "new delhi": {"n": 70, "p": 40, "k": 45, "type": "Sandy Alluvial"},
    "lucknow": {"n": 85, "p": 40, "k": 45, "type": "Alluvial"},
    "parsandan": {"n": 82, "p": 42, "k": 44, "type": "Gangetic Alluvial"},
    "kanpur": {"n": 86, "p": 43, "k": 47, "type": "Alluvial"},
    "varanasi": {"n": 84, "p": 45, "k": 48, "type": "Alluvial"},
    "jaipur": {"n": 50, "p": 35, "k": 30, "type": "Sandy/Arid"},
    "jodhpur": {"n": 45, "p": 30, "k": 25, "type": "Desert Soil"},
    "ahmedabad": {"n": 60, "p": 45, "k": 50, "type": "Sandy Loam"},
    "bhopal": {"n": 70, "p": 45, "k": 50, "type": "Black/Red"},
    "indore": {"n": 65, "p": 50, "k": 55, "type": "Medium Black"},
    "pune": {"n": 60, "p": 50, "k": 55, "type": "Black Soil"},
    "nagpur": {"n": 58, "p": 52, "k": 58, "type": "Black Cotton Soil"},
    "patna": {"n": 85, "p": 48, "k": 42, "type": "Alluvial"},
    "kolkata": {"n": 90, "p": 50, "k": 60, "type": "Clayey Alluvial"},
    "guwahati": {"n": 75, "p": 35, "k": 30, "type": "Acidic Alluvial"},
    "bhubaneswar": {"n": 72, "p": 40, "k": 35, "type": "Red/Laterite"},
    "bengaluru": {"n": 65, "p": 40, "k": 45, "type": "Red Soil"},
    "mysuru": {"n": 68, "p": 42, "k": 48, "type": "Red Loam"},
    "hyderabad": {"n": 65, "p": 45, "k": 50, "type": "Red/Black"},
    "chennai": {"n": 80, "p": 55, "k": 60, "type": "Red/Laterite"},
    "coimbatore": {"n": 75, "p": 50, "k": 55, "type": "Red Loamy"},
    "kochi": {"n": 70, "p": 30, "k": 40, "type": "Coastal Laterite"}
}

CROP_WATER_NEEDS = {
    'rice': 1200, 'maize': 600, 'jute': 1000, 'cotton': 800, 'coconut': 1500,
    'papaya': 1000, 'orange': 900, 'apple': 800, 'muskmelon': 400, 'watermelon': 400,
    'grapes': 700, 'mango': 1000, 'banana': 1500, 'pomegranate': 600, 'lentil': 300,
    'blackgram': 350, 'mungbean': 350, 'mothbeans': 300, 'pigeonpeas': 500,
    'kidneybeans': 400, 'chickpea': 350, 'coffee': 1500
}

ALL_CROPS = sorted([
    "rice", "maize", "jute", "cotton", "coconut", "papaya", "orange", "apple",
    "muskmelon", "watermelon", "grapes", "mango", "banana", "pomegranate",
    "lentil", "blackgram", "mungbean", "mothbeans", "pigeonpeas",
    "kidneybeans", "chickpea", "coffee"
])

# Ideal growing ranges per crop (temp °C min/max, rainfall mm min/max)
CROP_IDEAL_CONDITIONS = {
    "rice":        {"temp_min": 20, "temp_max": 35, "rain_min": 150, "rain_max": 300},
    "maize":       {"temp_min": 18, "temp_max": 27, "rain_min": 60,  "rain_max": 110},
    "jute":        {"temp_min": 24, "temp_max": 37, "rain_min": 150, "rain_max": 250},
    "cotton":      {"temp_min": 21, "temp_max": 35, "rain_min": 50,  "rain_max": 150},
    "coconut":     {"temp_min": 20, "temp_max": 32, "rain_min": 100, "rain_max": 300},
    "papaya":      {"temp_min": 22, "temp_max": 35, "rain_min": 100, "rain_max": 250},
    "orange":      {"temp_min": 15, "temp_max": 30, "rain_min": 100, "rain_max": 200},
    "apple":       {"temp_min": 10, "temp_max": 24, "rain_min": 100, "rain_max": 200},
    "muskmelon":   {"temp_min": 24, "temp_max": 35, "rain_min": 25,  "rain_max": 60},
    "watermelon":  {"temp_min": 24, "temp_max": 35, "rain_min": 40,  "rain_max": 60},
    "grapes":      {"temp_min": 15, "temp_max": 35, "rain_min": 50,  "rain_max": 100},
    "mango":       {"temp_min": 24, "temp_max": 38, "rain_min": 100, "rain_max": 250},
    "banana":      {"temp_min": 20, "temp_max": 35, "rain_min": 100, "rain_max": 250},
    "pomegranate": {"temp_min": 18, "temp_max": 35, "rain_min": 50,  "rain_max": 150},
    "lentil":      {"temp_min": 15, "temp_max": 28, "rain_min": 30,  "rain_max": 100},
    "blackgram":   {"temp_min": 25, "temp_max": 35, "rain_min": 60,  "rain_max": 120},
    "mungbean":    {"temp_min": 25, "temp_max": 35, "rain_min": 35,  "rain_max": 70},
    "mothbeans":   {"temp_min": 24, "temp_max": 32, "rain_min": 25,  "rain_max": 75},
    "pigeonpeas":  {"temp_min": 18, "temp_max": 38, "rain_min": 60,  "rain_max": 200},
    "kidneybeans": {"temp_min": 15, "temp_max": 25, "rain_min": 60,  "rain_max": 150},
    "chickpea":    {"temp_min": 15, "temp_max": 25, "rain_min": 60,  "rain_max": 100},
    "coffee":      {"temp_min": 15, "temp_max": 28, "rain_min": 150, "rain_max": 300},
}

# Heuristic mitigation steps keyed by condition type
MITIGATION_STRATEGIES = {
    "too_hot": (
        "🌡️ **Temperature Mitigation (Too Hot)**\n"
        "- Deploy **shade nets / greenhouse shading** to reduce canopy temperature by 5–8°C.\n"
        "- Implement **drip irrigation** with evening watering cycles to cool root zones.\n"
        "- Apply **reflective mulch** (silver / white plastic) to deflect solar radiation.\n"
        "- Consider planting **windbreaks** or intercropping with tall shade-giving species."
    ),
    "too_cold": (
        "❄️ **Temperature Mitigation (Too Cold)**\n"
        "- Use **polyhouse / polytunnel** structures to trap warmth.\n"
        "- Apply **thick organic mulch** (straw, leaves) to insulate the soil.\n"
        "- Employ **frost-protection sprinklers** during sub-zero nights.\n"
        "- Select **cold-tolerant cultivars** if available for this crop."
    ),
    "too_wet": (
        "🌧️ **Excess Rainfall Mitigation**\n"
        "- Install **raised beds** and improve field drainage channels.\n"
        "- Apply **fungicide protocols** proactively to prevent root rot and blight.\n"
        "- Use **ridge planting** to keep root zones above waterlogged soil.\n"
        "- Consider **rainwater harvesting** structures to divert excess flow."
    ),
    "too_dry": (
        "🏜️ **Insufficient Rainfall Mitigation**\n"
        "- Deploy **heavy artificial irrigation** (drip or sprinkler systems).\n"
        "- Apply **water-retention polymers** (hydrogels) in the root zone.\n"
        "- Use **deep mulching** to reduce soil evaporation by up to 70%.\n"
        "- Practice **deficit irrigation scheduling** to maximize water-use efficiency."
    ),
    "poor_air": (
        "🌫️ **Air Quality Mitigation**\n"
        "- Plant **bio-filter hedgerows** (e.g., Neem, Moringa) around field perimeters.\n"
        "- Use **foliar washing sprays** (plain water mist) to clean particulate deposits on leaves.\n"
        "- Schedule critical growth-phase activities during **low-pollution hours** (early morning).\n"
        "- Monitor crop leaves for **chlorosis / necrosis** caused by gaseous pollutants."
    ),
}

OWM_API_KEY = "474928493d640bda234fb2612a2d9091"

# ─────────────────────── HELPER FUNCTIONS ────────────────────────

def recommend_crop(nitrogen, phosphorus, potassium, temp, rainfall):
    if not model: return None
    if any(val < 0 for val in [nitrogen, phosphorus, potassium, temp, rainfall]):
        st.error("Error: input data cannot be negative.")
        return None
    if temp > 60 or rainfall > 1000:
        st.warning("Warning: high weather values detected. Result may be inaccurate.")
        
    model_input = [[nitrogen, phosphorus, potassium, rainfall, temp]]
    
    probabilities = model.predict_proba(model_input)[0]
    top_3_indices = probabilities.argsort()[-3:][::-1]
    return [(model.classes_[i], probabilities[i] * 100) for i in top_3_indices]


def get_live_weather_by_city(city_name):
    """Resolve city name → lat/lon via Geocoding API, then fetch weather."""
    geo_url = f"http://api.openweathermap.org/geo/1.0/direct?q={city_name}&limit=1&appid={OWM_API_KEY}"
    geo_response = requests.get(geo_url).json()
    
    if isinstance(geo_response, dict) and "cod" in geo_response:
        st.error(f"Weather API Error: {geo_response.get('message', 'Unauthorized')}")
        return None, None, None, None
        
    if not geo_response:
        return None, None, None, None
        
    lat, lon = geo_response[0]['lat'], geo_response[0]['lon']
    return _fetch_weather_data(lat, lon)


def get_live_weather_by_coords(lat, lon):
    """Fetch weather + air pollution data directly from lat/lon."""
    return _fetch_weather_data(lat, lon)


def _fetch_weather_data(lat, lon):
    """Core function: calls Weather API + Air Pollution API. Returns (temp, rain, air_data, city_name)."""
    # --- Weather API ---
    weather_url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&units=metric&appid={OWM_API_KEY}"
    try:
        weather_response = requests.get(weather_url, timeout=10).json()
    except requests.RequestException:
        return None, None, None, None

    if weather_response.get("cod") != 200:
        return None, None, None, None

    temp = weather_response['main']['temp']
    rainfall = weather_response.get('rain', {}).get('1h', 0) * 24
    city_name = weather_response.get('name', 'Unknown')

    # --- Air Pollution API ---
    air_url = f"http://api.openweathermap.org/data/2.5/air_pollution?lat={lat}&lon={lon}&appid={OWM_API_KEY}"
    air_data = None
    try:
        air_response = requests.get(air_url, timeout=10).json()
        if "list" in air_response and len(air_response["list"]) > 0:
            entry = air_response["list"][0]
            air_data = {
                "aqi": entry["main"]["aqi"],
                "co":  entry["components"].get("co", 0),
                "no2": entry["components"].get("no2", 0),
                "o3":  entry["components"].get("o3", 0),
                "pm2_5": entry["components"].get("pm2_5", 0),
                "pm10":  entry["components"].get("pm10", 0),
            }
    except requests.RequestException:
        pass  # Air data is supplementary; don't block on failure

    return temp, rainfall, air_data, city_name


def get_location_from_ip():
    """IP-based fallback geolocation using ipinfo.io (no key required for low volume)."""
    try:
        resp = requests.get("https://ipinfo.io/json", timeout=5).json()
        loc = resp.get("loc", "")
        if loc:
            lat_str, lon_str = loc.split(",")
            return float(lat_str), float(lon_str), resp.get("city", "Unknown")
    except Exception:
        pass
    return None, None, None


def estimate_water_requirement(crop, live_temp):
    base_water = CROP_WATER_NEEDS.get(crop.lower(), 600)
    evaporation_factor = max(0, (live_temp - 25) * 0.02)
    return round(base_water * (1 + evaporation_factor))


def predict_failure_risk(confidence_score, live_temp, live_rain):
    base_risk = 100 - confidence_score
    weather_penalty = 0
    if live_temp > 38 or live_temp < 10: weather_penalty += 15
    if live_rain > 800 or live_rain < 30: weather_penalty += 20
    return min(base_risk + weather_penalty, 95.0)


def aqi_label(aqi_value):
    """Convert numeric AQI (1-5) to a human-readable label."""
    return {1: "Good ✅", 2: "Fair 🟡", 3: "Moderate 🟠", 4: "Poor 🔴", 5: "Very Poor ☠️"}.get(aqi_value, "Unknown")


def diagnose_conditions(target_crop, temp, rainfall, air_data):
    """
    Compare live conditions against ideal ranges for the target crop.
    Returns a list of (condition_key, human_message) tuples.
    """
    issues = []
    ideal = CROP_IDEAL_CONDITIONS.get(target_crop.lower())
    if not ideal:
        return issues

    if temp > ideal["temp_max"]:
        issues.append(("too_hot", f"Current temperature of **{temp:.1f}°C** exceeds the ideal max of {ideal['temp_max']}°C for {target_crop.capitalize()}."))
    elif temp < ideal["temp_min"]:
        issues.append(("too_cold", f"Current temperature of **{temp:.1f}°C** is below the ideal min of {ideal['temp_min']}°C for {target_crop.capitalize()}."))

    if rainfall > ideal["rain_max"]:
        issues.append(("too_wet", f"Estimated rainfall of **{rainfall:.1f} mm** exceeds the ideal max of {ideal['rain_max']} mm for {target_crop.capitalize()}."))
    elif rainfall < ideal["rain_min"]:
        issues.append(("too_dry", f"Estimated rainfall of **{rainfall:.1f} mm** is below the ideal min of {ideal['rain_min']} mm for {target_crop.capitalize()}."))

    if air_data and air_data.get("aqi", 1) >= 4:
        issues.append(("poor_air", f"Poor air quality detected (AQI: {air_data['aqi']} – {aqi_label(air_data['aqi'])}). Elevated pollutants may stress {target_crop.capitalize()} growth."))

    return issues


def harvest_celebration():
    """Injects a custom CSS animation to rain agricultural emojis on success."""
    celebration_html = """
    <style>
    .emoji-rain {
        position: fixed;
        top: -10vh;
        font-size: 2.5rem;
        user-select: none;
        animation: fall 3s linear forwards;
        z-index: 99999;
    }
    @keyframes fall {
        to { transform: translateY(110vh) rotate(360deg); }
    }
    </style>
    <div class="emoji-rain" style="left: 10%; animation-delay: 0.1s;">🌾</div>
    <div class="emoji-rain" style="left: 20%; animation-delay: 0.4s;">🌽</div>
    <div class="emoji-rain" style="left: 30%; animation-delay: 0.2s;">🌱</div>
    <div class="emoji-rain" style="left: 40%; animation-delay: 0.5s;">🍎</div>
    <div class="emoji-rain" style="left: 50%; animation-delay: 0.1s;">🌻</div>
    <div class="emoji-rain" style="left: 60%; animation-delay: 0.6s;">🥕</div>
    <div class="emoji-rain" style="left: 70%; animation-delay: 0.3s;">🌾</div>
    <div class="emoji-rain" style="left: 80%; animation-delay: 0.7s;">🍅</div>
    <div class="emoji-rain" style="left: 90%; animation-delay: 0.2s;">🌱</div>
    """
    st.markdown(celebration_html, unsafe_allow_html=True)


# ──────────────────────── APPLICATION UI ─────────────────────────

st.markdown("""
<div class="scratchpad-banner">
    <div>
        <span class="draft-badge">📝 LAB SCRATCHPAD • ACTIVE DRAFT</span>
        <span style="font-weight: 700; color: #2d6a4f; margin-left: 8px; font-size: 1.1rem;">SPARC Workbench</span>
    </div>
    <div style="display: flex; gap: 8px; align-items: center;">
        <span class="dev-stage-badge">STATUS: IN-DEVELOPMENT</span>
        <span class="dev-stage-badge">STAGE: v0.4-dev</span>
    </div>
</div>
""", unsafe_allow_html=True)

st.title("🌱 SPARC")
st.subheader("Smart Python-based Agricultural Recommendation and Classification System")

st.markdown("""
<div class="sticky-note">
    📌 <b>Lab Scratchpad Note:</b> This prototype is currently in active development stage. Integrating real-time OpenWeatherMap air pollution telemetry, browser geolocation, and heuristic crop mitigation algorithms.
</div>
""", unsafe_allow_html=True)

tab1, tab2, tab3, tab4 = st.tabs([
    "🌱 Crop Predictor",
    "🎯 Precision Consultant",
    "📈 Soil Visualization",
    "🛠️ Admin Logs"
])

# ━━━━━━━━━━━━━━━━━━━ TAB 1 – CROP PREDICTOR (ORIGINAL) ━━━━━━━━━━━━━━━━━━━
with tab1:
    st.write("### Live Weather Integration")
    city = st.text_input("Enter your city to fetch live weather (Optional):")
    live_temp, live_rain = None, None

    if city:
        live_temp, live_rain, _, resolved_city = get_live_weather_by_city(city)
        if live_temp is not None:
            st.success(f"Live Weather in {city.capitalize()}: {live_temp}°C, {live_rain:.1f}mm Rain")
        else:
            st.error("City not found. Using manual sliders below.")

    st.divider()
    st.write("### Agricultural Inputs")
    
    default_n, default_p, default_k = 85, 40, 43 
    soil_type = "Unknown"
    
    if city and city.lower() in REGIONAL_SOIL_DATA:
        region_data = REGIONAL_SOIL_DATA[city.lower()]
        default_n = region_data["n"]
        default_p = region_data["p"]
        default_k = region_data["k"]
        soil_type = region_data["type"]
        st.success(f"🌍 Auto-loaded standard **{soil_type}** soil profile for {city.capitalize()}.")
    elif city:
        st.info("City not in regional soil database. Using standard default nutrients.")

    col1, col2, col3 = st.columns(3)
    with col1: n = st.number_input("Nitrogen (N)", min_value=0, value=default_n, key="tab1_n")
    with col2: p = st.number_input("Phosphorus (P)", min_value=0, value=default_p, key="tab1_p")
    with col3: k = st.number_input("Potassium (K)", min_value=0, value=default_k, key="tab1_k")

    final_temp = st.slider("Temperature (°C)", 0.0, 50.0, float(live_temp) if live_temp else 25.0, key="tab1_temp")
    final_rain = st.slider("Rainfall (mm)", 0.0, 500.0, float(live_rain) if live_rain else 200.0, key="tab1_rain")

    if st.button("Recommend Crop", type="primary"):
        with st.spinner("Analyzing soil macro-nutrients and live meteorological data..."):
            time.sleep(1.5) 
            results = recommend_crop(n, p, k, final_temp, final_rain)
        
        if results:
            st.toast("Soil and weather analysis complete!", icon="🚜")
            harvest_celebration()
            
            top_crop = results[0][0]
            confidence = results[0][1]
            est_water = estimate_water_requirement(top_crop, final_temp)
            risk_percent = predict_failure_risk(confidence, final_temp, final_rain)
            
            st.success(f"### 🌱 Primary Recommendation: {top_crop.capitalize()} ({confidence:.1f}% Match)")
            st.info(f"**Alternative Options:** {results[1][0].capitalize()} ({results[1][1]:.1f}%), {results[2][0].capitalize()} ({results[2][1]:.1f}%)")
            
            st.write("---")
            st.write("### 📊 Live Predictive Analytics")
            metric_col1, metric_col2 = st.columns(2)
            
            with metric_col1:
                st.metric(
                    label="Estimated Seasonal Water Need", 
                    value=f"{est_water} mm", 
                    delta="Adjusted for local evaporation" if final_temp > 25 else "Standard baseline",
                    delta_color="off"
                )
                
            with metric_col2:
                if risk_percent < 30:
                    st.success(f"Crop Failure Risk: {risk_percent:.1f}% (Low)")
                elif risk_percent < 60:
                    st.warning(f"Crop Failure Risk: {risk_percent:.1f}% (Moderate)")
                else:
                    st.error(f"Crop Failure Risk: {risk_percent:.1f}% (High)")
                    
            db_manager.log_prediction(n, p, k, final_temp, final_rain, top_crop.capitalize())


# ━━━━━━━━━━━━━━━ TAB 2 – PRECISION CONSULTANT (NEW) ━━━━━━━━━━━━━━━━━━━━━
with tab2:
    st.write("### 🎯 Precision Consultant Mode")
    st.caption("AI-driven viability analysis with atmospheric health monitoring and risk mitigation.")

    # ── Step 1: Auto-Geolocation ──
    st.write("#### 📍 Step 1 — Location Detection")

    geo_lat, geo_lon, geo_city = None, None, None

    # Try browser geolocation first
    try:
        from streamlit_geolocation import streamlit_geolocation
        location = streamlit_geolocation()
        if location and location.get("latitude") and location.get("longitude"):
            # Filter out 0.0/0.0 which streamlit_geolocation returns before permission
            lat_val = location["latitude"]
            lon_val = location["longitude"]
            if not (lat_val == 0.0 and lon_val == 0.0):
                geo_lat, geo_lon = lat_val, lon_val
    except ImportError:
        st.info("ℹ️ `streamlit-geolocation` not installed. Falling back to IP-based detection.")

    # IP-based fallback
    if geo_lat is None:
        ip_lat, ip_lon, ip_city = get_location_from_ip()
        if ip_lat is not None:
            geo_lat, geo_lon, geo_city = ip_lat, ip_lon, ip_city
            st.info(f"📡 IP-based location detected: **{geo_city}** ({geo_lat:.4f}, {geo_lon:.4f})")

    # Manual override option
    with st.expander("🔧 Manual Coordinate Override"):
        override_lat = st.number_input("Latitude", value=geo_lat if geo_lat else 28.6139, format="%.4f", key="pc_lat")
        override_lon = st.number_input("Longitude", value=geo_lon if geo_lon else 77.2090, format="%.4f", key="pc_lon")
        if st.button("Use Manual Coordinates"):
            geo_lat, geo_lon = override_lat, override_lon

    if geo_lat is not None and geo_lon is not None:
        st.success(f"📍 Active Coordinates: **{geo_lat:.4f}° N, {geo_lon:.4f}° E**")
    else:
        st.warning("Could not detect location. Please allow browser permission or enter coordinates manually above.")

    st.divider()

    # ── Step 2: Fetch Weather + Air Pollution ──
    st.write("#### 🌦️ Step 2 — Live Atmospheric Data")

    pc_temp, pc_rain, pc_air, pc_resolved_city = None, None, None, None

    if geo_lat is not None and geo_lon is not None:
        pc_temp, pc_rain, pc_air, pc_resolved_city = get_live_weather_by_coords(geo_lat, geo_lon)

    if pc_temp is not None:
        wcol1, wcol2, wcol3 = st.columns(3)
        with wcol1:
            st.metric("🌡️ Temperature", f"{pc_temp:.1f}°C")
        with wcol2:
            st.metric("🌧️ Est. Rainfall", f"{pc_rain:.1f} mm")
        with wcol3:
            st.metric("📍 Resolved City", pc_resolved_city or "N/A")

        # Atmospheric Health Panel
        if pc_air:
            st.write("##### 🫁 Atmospheric Health")
            aqi_val = pc_air["aqi"]
            acol1, acol2, acol3, acol4 = st.columns(4)
            with acol1:
                st.metric("Air Quality Index", aqi_label(aqi_val))
            with acol2:
                st.metric("CO", f"{pc_air['co']:.1f} µg/m³")
            with acol3:
                st.metric("NO₂", f"{pc_air['no2']:.1f} µg/m³")
            with acol4:
                st.metric("O₃", f"{pc_air['o3']:.1f} µg/m³")

            # Extra particulates row
            pcol1, pcol2 = st.columns(2)
            with pcol1:
                st.metric("PM2.5", f"{pc_air['pm2_5']:.1f} µg/m³")
            with pcol2:
                st.metric("PM10", f"{pc_air['pm10']:.1f} µg/m³")

            if aqi_val >= 4:
                st.error("⚠️ **Hazardous air detected.** Elevated pollutants can cause leaf damage, stunted growth, and reduced yields.")
            elif aqi_val == 3:
                st.warning("⚠️ Moderate air quality — sensitive crops may be slightly affected.")
            else:
                st.success("✅ Air quality is favorable for agriculture.")
        else:
            st.info("Air pollution data unavailable for this location.")
    else:
        st.info("Set your location above to fetch live atmospheric data.")

    st.divider()

    # ── Step 3: Soil Inputs & Target Crop ──
    st.write("#### 🧪 Step 3 — Soil Profile & Target Crop")

    # Auto-load soil if resolved city is in the database
    pc_default_n, pc_default_p, pc_default_k = 85, 40, 43
    pc_soil_type = "Unknown"
    if pc_resolved_city and pc_resolved_city.lower() in REGIONAL_SOIL_DATA:
        rd = REGIONAL_SOIL_DATA[pc_resolved_city.lower()]
        pc_default_n, pc_default_p, pc_default_k = rd["n"], rd["p"], rd["k"]
        pc_soil_type = rd["type"]
        st.success(f"🌍 Auto-loaded **{pc_soil_type}** soil profile for {pc_resolved_city}.")

    sc1, sc2, sc3 = st.columns(3)
    with sc1: pc_n = st.number_input("Nitrogen (N)", min_value=0, value=pc_default_n, key="pc_n")
    with sc2: pc_p = st.number_input("Phosphorus (P)", min_value=0, value=pc_default_p, key="pc_p")
    with sc3: pc_k = st.number_input("Potassium (K)", min_value=0, value=pc_default_k, key="pc_k")

    pc_final_temp = st.slider(
        "Temperature (°C)", 0.0, 50.0,
        float(pc_temp) if pc_temp is not None else 25.0,
        key="pc_temp"
    )
    pc_final_rain = st.slider(
        "Rainfall (mm)", 0.0, 500.0,
        float(pc_rain) if pc_rain is not None else 200.0,
        key="pc_rain"
    )

    target_crop = st.selectbox(
        "🎯 Select the crop you want to cultivate:",
        ALL_CROPS,
        format_func=lambda x: x.capitalize(),
        key="target_crop"
    )

    st.divider()

    # ── Step 4: Run Analysis ──
    if st.button("🔬 Run Precision Analysis", type="primary", key="pc_run"):
        with st.spinner("Running AI viability cross-check and atmospheric analysis..."):
            time.sleep(1.5)
            results = recommend_crop(pc_n, pc_p, pc_k, pc_final_temp, pc_final_rain)

        if results:
            top_crop = results[0][0]
            confidence = results[0][1]
            top_3_names = [r[0].lower() for r in results]

            st.write("---")
            st.write("### 🔬 Precision Consultant Report")

            target_is_viable = (target_crop.lower() == top_crop.lower())
            target_in_top3 = target_crop.lower() in top_3_names

            # ── VIABLE ──
            if target_is_viable:
                harvest_celebration()
                st.toast("Target crop matches AI recommendation!", icon="🎯")
                st.success(
                    f"### ✅ Viability Confirmed\n"
                    f"Your target crop **{target_crop.capitalize()}** is the **#1 AI recommendation** "
                    f"for your current soil and weather conditions with **{confidence:.1f}%** confidence."
                )
                est_water = estimate_water_requirement(target_crop, pc_final_temp)
                st.metric("💧 Estimated Seasonal Water Need", f"{est_water} mm")

            # ── PARTIAL MATCH (in top 3 but not #1) ──
            elif target_in_top3:
                match_entry = next(r for r in results if r[0].lower() == target_crop.lower())
                st.warning(
                    f"### ⚠️ Partial Viability\n"
                    f"Your target crop **{target_crop.capitalize()}** is viable (ranked in AI top-3 "
                    f"at **{match_entry[1]:.1f}%** confidence) but is **not the optimal choice**.\n\n"
                    f"The AI's top pick is **{top_crop.capitalize()}** ({confidence:.1f}%)."
                )
                # Still show condition diagnostics if any
                issues = diagnose_conditions(target_crop, pc_final_temp, pc_final_rain, pc_air)
                if issues:
                    st.write("#### ⚠️ Condition Warnings")
                    for _, msg in issues:
                        st.warning(msg)

            # ── HIGH FAILURE RISK ──
            else:
                st.error(
                    f"### 🚨 High Failure Risk Detected\n"
                    f"Your target crop **{target_crop.capitalize()}** does **not** appear in the AI's "
                    f"top recommendations for your current conditions."
                )

                # Flag specific failure conditions
                issues = diagnose_conditions(target_crop, pc_final_temp, pc_final_rain, pc_air)

                if issues:
                    st.write("#### 🔍 Failure Condition Analysis")
                    for _, msg in issues:
                        st.error(msg)
                else:
                    st.info(
                        f"No extreme weather or air quality flags, but the soil nutrient profile "
                        f"(N={pc_n}, P={pc_p}, K={pc_k}) does not align with {target_crop.capitalize()}'s requirements."
                    )

                # Takeaway: Top 3 alternatives
                st.write("#### 🌿 Takeaway — AI-Recommended Alternatives")
                for i, (crop_name, crop_conf) in enumerate(results, 1):
                    emoji = ["🥇", "🥈", "🥉"][i - 1]
                    st.info(f"{emoji} **{crop_name.capitalize()}** — {crop_conf:.1f}% match")

                # Actionable mitigation steps
                st.write("#### 🛠️ Actionable Mitigation Steps")
                st.caption(f"If you still insist on growing **{target_crop.capitalize()}**, apply these strategies:")

                if issues:
                    for condition_key, _ in issues:
                        strategy = MITIGATION_STRATEGIES.get(condition_key)
                        if strategy:
                            st.markdown(strategy)
                else:
                    # Generic soil-focused mitigation when no weather/air issues found
                    st.markdown(
                        f"🧪 **Soil Amendment Strategy for {target_crop.capitalize()}**\n"
                        f"- Get a **lab soil test** to compare your NPK against {target_crop.capitalize()}'s ideal profile.\n"
                        f"- Apply **targeted fertilizers** to correct nutrient imbalances.\n"
                        f"- Consider **crop rotation** with a nitrogen-fixing legume in the prior season.\n"
                        f"- Use **composting / vermicompost** to improve overall soil organic matter."
                    )

                st.write("---")
                st.caption(
                    f"💡 **Summary:** The AI recommends **{top_crop.capitalize()}** ({confidence:.1f}%) "
                    f"over your target **{target_crop.capitalize()}** for this field. "
                    f"Proceed with caution and apply the mitigation steps above if you choose to override."
                )

            # Log to database
            db_manager.log_prediction(
                pc_n, pc_p, pc_k, pc_final_temp, pc_final_rain,
                f"{target_crop.capitalize()} (Target) → {top_crop.capitalize()} (AI)"
            )


# ━━━━━━━━━━━━━━━━━━ TAB 3 – SOIL VISUALIZATION ━━━━━━━━━━━━━━━━━━━━━━━━━━
with tab3:
    st.write("### Soil Macronutrient Balance")
    st.write("This chart dynamically visualizes the nutrient profile entered in the Predictor tab.")
    
    nutrient_data = pd.DataFrame({
        "Nutrient": ["Nitrogen", "Phosphorus", "Potassium"],
        "Levels": [
            st.session_state.get("tab1_n", 85),
            st.session_state.get("tab1_p", 40),
            st.session_state.get("tab1_k", 43)
        ]
    })
    
    st.bar_chart(nutrient_data, x="Nutrient", y="Levels", color="#2ecc71")


# ━━━━━━━━━━━━━━━━━━━━━ TAB 4 – ADMIN LOGS ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with tab4:
    st.write("### System Database")
    logs = db_manager.fetch_all_logs()
    if logs:
        df = pd.DataFrame(logs, columns=["ID", "Timestamp", "N", "P", "K", "Temp (°C)", "Rain (mm)", "Predicted Crop"])
        st.dataframe(df, use_container_width=True)
    else:
        st.info("No predictions logged yet. Run the model to populate the database.")