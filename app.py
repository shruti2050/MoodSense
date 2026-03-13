import streamlit as st
import joblib
import pandas as pd
import plotly.graph_objects as go
import requests
from datetime import datetime

# --- 1. PAGE CONFIG ---
st.set_page_config(page_title="LuminaAuto AI", page_icon="💡", layout="wide")

@st.cache_resource
def load_model():
    return joblib.load('lumina_model.pkl')

model = load_model()

# --- 2. WEATHER API LOGIC ---
def get_weather(city="Pune"):
    api_key = "YOUR_API_KEY" # Placeholder
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric"
    try:
        response = requests.get(url).json()
        return response['main']['temp'], response['main']['humidity']
    except:
        return 26.0, 50.0 

# --- 3. SIDEBAR INPUTS ---
st.sidebar.header("📡 System Control Panel")
city_input = st.sidebar.text_input("Location for Weather API", "Pune")
w_temp, w_hum = get_weather(city_input)

st.sidebar.markdown("---")
room_temp = st.sidebar.slider("BHE132 Room Temp (°C)", 15, 40, int(w_temp))
ambient_lux = st.sidebar.slider("Ambient Sunlight (Lux)", 0, 1000, 200)
mood = st.sidebar.selectbox("User Mood", [0, 1, 2], 
                            format_func=lambda x: ["Relaxed", "Normal", "Focused"][x])

# --- 4. MAIN PANEL ---
st.title("💡 LuminaAuto: AI Lighting Control")
st.info(f"System Status: Online | Location: {city_input} | External Temp: {w_temp}°C")

# --- 5. THE BUTTON & PREDICTION ---
st.markdown("### 🚀 AI Command Center")
if st.button("RUN AI INFERENCE", use_container_width=True):
    
    # Bundle data and predict
    input_df = pd.DataFrame([[room_temp, w_hum, ambient_lux, mood]], 
                            columns=['Temperature', 'Humidity', 'Ambient_Lux', 'Mood'])
    
    predicted_pwm = int(model.predict(input_df)[0])
    energy_saved = ((255 - predicted_pwm) / 255) * 100

    # --- 6. FRONT VIEW RESULTS ---
    st.markdown("---")
    
    # BIG PWM DISPLAY (What you asked for)
    st.markdown(f"""
        <div style="background-color:#1e2130; padding:20px; border-radius:10px; border: 2px solid #00ffcc; text-align:center;">
            <h1 style="color:#00ffcc; margin:0;">Target Intensity: {predicted_pwm} PWM</h1>
            <p style="color:white; margin:0;">This value is now active on the ESP32 Actuator</p>
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
        fig.update_layout(height=300)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        # JSON Bundle display
        st.write("**📦 JSON Data Bundle (Sent to Hardware)**")
        st.json({
            "temp_sensor": room_temp,
            "ambient_lux": ambient_lux,
            "mood_index": mood,
            "actuation_pwm": predicted_pwm
        })

    # --- 7. SAVINGS TABLE ---
    st.markdown("### 💰 Financial Impact")
    trad_cost = 1200 # Fixed estimate for demo
    savings = int(trad_cost * (energy_saved/100))
    
    df_calc = pd.DataFrame({
        "Metric": ["Annual Cost (Trad)", "Annual Cost (AI)", "Total Savings"],
        "Value": [f"₹{trad_cost}", f"₹{trad_cost - savings}", f"₹{savings}"]
    })
    st.table(df_calc)

else:
    st.warning("Awaiting user command. Adjust sliders and click the button above to begin.")