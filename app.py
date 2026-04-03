import streamlit as st
import joblib
import pandas as pd
import plotly.graph_objects as go
import requests
from datetime import datetime
from streamlit_autorefresh import st_autorefresh

# Auto refresh every 5 sec
st_autorefresh(interval=5000, key="refresh")

st.set_page_config(page_title="LuminaAuto AI", layout="wide")

# Load model
@st.cache_resource
def load_model():
    return joblib.load("lumina_model.pkl")

model = load_model()

# Weather API
def get_weather(city="Pune"):
    try:
        return 26.0, 50.0  # fallback (stable demo)
    except:
        return 26.0, 50.0

# Light sensor (ESP32)
def get_light_data(ip):
    try:
        url = f"http://{ip.strip().rstrip('.')}/light"
        return requests.get(url, timeout=2).json()['lux']
    except:
        return 0

# Send PWM
def send_to_hardware(pwm, ip):
    try:
        url = f"http://{ip.strip().rstrip('.')}/update"
        return requests.post(url, json={"pwm": int(pwm)}, timeout=2).status_code == 200
    except:
        return False

# Sidebar
st.sidebar.header("📡 Control Panel")
ip = st.sidebar.text_input("ESP32 IP", "127.0.0.1:9080")

temp, hum = get_weather()
lux = get_light_data(ip)

st.sidebar.write(f"🌡 Temp: {temp}")
st.sidebar.write(f"💧 Humidity: {hum}")
st.sidebar.write(f"🌞 Lux: {lux}")

mood = st.sidebar.selectbox("Mood", [0,1,2],
                           format_func=lambda x: ["Relaxed","Normal","Focused"][x])

# Store history
if "lux_data" not in st.session_state:
    st.session_state.lux_data = []

st.session_state.lux_data.append(lux)
st.session_state.lux_data = st.session_state.lux_data[-20:]

# Main UI
st.title("💡 LuminaAuto Smart Lighting")

# Graph
st.subheader("🌞 Live Light Graph")
st.line_chart(pd.DataFrame({"Lux": st.session_state.lux_data}))

# AI Prediction (AUTO)
input_df = pd.DataFrame([[temp, hum, lux, mood]],
                        columns=["Temperature","Humidity","Ambient_Lux","Mood"])

predicted_pwm = int(model.predict(input_df)[0])

# Send to ESP32
send_to_hardware(predicted_pwm, ip)

# Display
st.metric("💡 LED Intensity (PWM)", predicted_pwm)

# Status
if predicted_pwm < 80:
    st.success("🌙 Dark → LED Bright")
elif predicted_pwm < 160:
    st.info("🌤 Moderate → Balanced")
else:
    st.warning("☀️ Bright → LED Dim")

# JSON
st.json({
    "temp": temp,
    "humidity": hum,
    "lux": lux,
    "mood": mood,
    "pwm": predicted_pwm,
    "time": datetime.now().strftime("%H:%M:%S")
})

# financial section

def calculate_bill(units):
    cost = 0

    if units <= 100:
        cost += units * 4
    elif units <= 200:
        cost += 100 * 4 + (units - 100) * 5
    elif units <= 400:
        cost += 100 * 4 + 100 * 5 + (units - 200) * 6.5
    else:
        cost += 100 * 4 + 100 * 5 + 200 * 6.5 + (units - 400) * 8

    return cost
MAX_WATT = 10
HOURS_PER_DAY = 8
EFFICIENCY = 0.9

# Daily energy
trad_energy = (MAX_WATT / 1000) * HOURS_PER_DAY
ai_energy = (predicted_pwm / 255) * (MAX_WATT / 1000) * HOURS_PER_DAY * EFFICIENCY

# Monthly units
trad_month_units = trad_energy * 30
ai_month_units = ai_energy * 30

# Yearly units
trad_year_units = trad_energy * 365
ai_year_units = ai_energy * 365

# Bills using slab
trad_bill = calculate_bill(trad_month_units)
ai_bill = calculate_bill(ai_month_units)

monthly_saving = trad_bill - ai_bill
yearly_saving = monthly_saving * 12

CO2_PER_KWH = 0.82

monthly_co2_saved = (trad_month_units - ai_month_units) * CO2_PER_KWH
yearly_co2_saved = monthly_co2_saved * 12





st.markdown("### ⚡ Smart Energy Analytics")

df = pd.DataFrame({
    "Metric": [
        "Monthly Units (Traditional)",
        "Monthly Units (AI)",
        "Monthly Saving (₹)",
        "Yearly Saving (₹)",
        "CO₂ Saved / Month",
        "CO₂ Saved / Year"
    ],
    "Value": [
        f"{trad_month_units:.2f} kWh",
        f"{ai_month_units:.2f} kWh",
        f"₹{monthly_saving:.2f}",
        f"₹{yearly_saving:.2f}",
        f"{monthly_co2_saved:.2f} kg",
        f"{yearly_co2_saved:.2f} kg"
    ]
})

st.table(df)

# st.markdown("### ⚡ Energy & Cost Analysis")

# MAX_WATT = 10
# HOURS_PER_DAY = 8
# COST_PER_KWH = 8

# # Energy calculations
# trad_energy = (MAX_WATT / 1000) * HOURS_PER_DAY
# ai_energy = (predicted_pwm / 255) * (MAX_WATT / 1000) * HOURS_PER_DAY
# energy_saved = trad_energy - ai_energy

# monthly_saving = energy_saved * 30 * COST_PER_KWH

# df_energy = pd.DataFrame({
#     "Metric": [
#         "Daily Energy (Traditional)",
#         "Daily Energy (AI)",
#         "Daily Energy Saved",
#         "Monthly Cost Savings"
#     ],
#     "Value": [
#         f"{trad_energy:.3f} kWh",
#         f"{ai_energy:.3f} kWh",
#         f"{energy_saved:.3f} kWh",
#         f"₹{monthly_saving:.2f}"
#     ]
# })

# st.table(df_energy)

st.bar_chart(pd.DataFrame({
    "Units": [trad_month_units, ai_month_units]
}, index=["Traditional", "AI"]))    