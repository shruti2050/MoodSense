import streamlit as st
import joblib
import pandas as pd
import plotly.graph_objects as go
import requests
from datetime import datetime

# --- 1. PAGE CONFIG ---
st.set_page_config(page_title="MoodSense AI", page_icon="💡", layout="wide")

@st.cache_resource
def load_model():
    # Ensure 'lumina_model.pkl' is in the same folder as this script
    return joblib.load('lumina_model.pkl')

model = load_model()

# --- 2. WEATHER & HARDWARE LOGIC ---
def get_weather(city="Pune"):
    api_key = "YOUR_API_KEY" # Optional: Replace with real key for live data
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric"
    try:
        response = requests.get(url, timeout=2).json()
        return response['main']['temp'], response['main']['humidity']
    except:
        return 26.0, 50.0 

def send_to_hardware(predicted_pwm, gateway_url):
    # Clean the URL to remove any trailing dots or spaces
    clean_url = gateway_url.strip().rstrip('.')
    url = f"http://{clean_url}/update" 
    payload = {"pwm": int(predicted_pwm)}
    try:
        # Short timeout to keep the UI responsive
        response = requests.post(url, json=payload, timeout=1.5)
        return response.status_code == 200
    except:
        return False

# --- 3. SIDEBAR INPUTS ---
st.sidebar.header("📡 System Control Panel")
city_input = st.sidebar.text_input("Location", "Pune")
w_temp, w_hum = get_weather(city_input)

st.sidebar.markdown("---")
st.sidebar.subheader("🔌 Hardware Sync")
# Defaulting to 127.0.0.1 as it is more stable than 'localhost' on Windows
wokwi_ip = st.sidebar.text_input("Gateway Address", "127.0.0.1:9080")

st.sidebar.markdown("---")
st.sidebar.subheader("🎛️ Sensor Simulation")
room_temp = st.sidebar.slider("Room Temp (°C)", 15, 40, int(w_temp))
ambient_lux = st.sidebar.slider("Ambient Lux", 0, 1000, 200)
mood = st.sidebar.selectbox("User Mood", [0, 1, 2], 
                            format_func=lambda x: ["Relaxed", "Normal", "Focused"][x])

# --- 4. MAIN PANEL ---
st.title("💡 LuminaAuto: AI Lighting Control")
st.info(f"System Online | Location: {city_input} | External Temp: {w_temp}°C")

# --- 5. THE BUTTON & PREDICTION ---
st.markdown("### 🚀 AI Command Center")

# Updated for 2026 Streamlit compatibility
if st.button("RUN AI INFERENCE", width='stretch'):
    
    # 1. PREDICTION LOGIC (Must come before Sync)
    input_df = pd.DataFrame([[room_temp, w_hum, ambient_lux, mood]], 
                            columns=['Temperature', 'Humidity', 'Ambient_Lux', 'Mood'])
    
    # Calculate the PWM value
    prediction = model.predict(input_df)[0]
    predicted_pwm = int(prediction)
    
    # Calculate energy saved vs full intensity (255)
    energy_saved = max(0, ((255 - predicted_pwm) / 255) * 100)

    # 2. HARDWARE SYNC LOGIC
    sync_status = send_to_hardware(predicted_pwm, wokwi_ip)
    
    if sync_status:
        st.success(f"✅ Hardware Synced: LED intensity set to {predicted_pwm}")
    else:
        st.error("❌ Hardware Offline: Ensure Wokwi Simulator is running and Port 9080 is forwarded.")

    # --- 6. VISUAL RESULTS ---
    st.markdown("---")
    
    # Big Result Display
    st.markdown(f"""
        <div style="background-color:#1e2130; padding:20px; border-radius:10px; border: 2px solid #00ffcc; text-align:center;">
            <h1 style="color:#00ffcc; margin:0;">Target Intensity: {predicted_pwm} PWM</h1>
            <p style="color:white; margin:0;">AI Decision Sent to ESP32 Actuator</p>
        </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns([1, 1])

    with col1:
        # Efficiency Gauge
        fig = go.Figure(go.Indicator(
            mode = "gauge+number",
            value = energy_saved,
            title = {'text': "Energy Savings %"},
            gauge = {'axis': {'range': [0, 100]}, 'bar': {'color': "#00ff00"}}
        ))
        fig.update_layout(height=300, paper_bgcolor='rgba(0,0,0,0)', font={'color': "white"})
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        # JSON Bundle display
        st.write("**📦 JSON Data Bundle (Outbound)**")
        st.json({
            "temp_sensor": room_temp,
            "ambient_lux": ambient_lux,
            "mood_index": mood,
            "actuation_pwm": predicted_pwm,
            "timestamp": datetime.now().strftime("%H:%M:%S")
        })

    # --- 7. FINANCIAL IMPACT ---
    st.markdown("### 💰 Financial Impact")
    trad_cost = 1200 # Placeholder for traditional monthly cost
    savings = int(trad_cost * (energy_saved/100))
    
    df_calc = pd.DataFrame({
        "Metric": ["Monthly Cost (Traditional)", "Monthly Cost (AI Optimized)", "Total Savings"],
        "Value": [f"₹{trad_cost}", f"₹{trad_cost - savings}", f"₹{savings}"]
    })
    st.table(df_calc)

else:
    st.warning("Awaiting user command. Adjust sensors and click the button above to begin.")