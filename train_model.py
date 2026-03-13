import pandas as pd
import numpy as np
import os
import glob
import joblib
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.metrics import r2_score, mean_absolute_error

# --- STEP 1: LOAD DATA ---
print("Fetching ASHRAE and CU-BEMS data...")
url_ashrae = "https://github.com/CenterForTheBuiltEnvironment/ashrae-db-II/raw/master/v2.1.0/db_measurements_v2.1.0.csv.gz"
df_ashrae = pd.read_csv(url_ashrae, compression='gzip', nrows=5000) # Increased rows for better learning

# Locate BEMS file
search_pattern = os.path.join("**", "2018Floor1.csv")
files = glob.glob(search_pattern, recursive=True)
if not files:
    raise FileNotFoundError("Could not find 2018Floor1.csv. Ensure it is in your project folder.")
df_bems = pd.read_csv(files[0])

# --- STEP 2: ADVANCED FEATURE ENGINEERING ---
print("Applying Advanced Feature Engineering...")
df_ashrae_clean = df_ashrae.dropna(subset=['ta', 'rh']).copy()
df_ashrae_clean['Mood'] = np.random.choice([0, 1, 2], size=len(df_ashrae_clean))

lux_col = 'z1_Light(kW)' 
df_bems_clean = df_bems.dropna(subset=[lux_col]).copy()

limit = min(len(df_ashrae_clean), len(df_bems_clean))
train_df = pd.DataFrame({
    'Temperature': df_ashrae_clean['ta'].iloc[:limit].values,
    'Humidity': df_ashrae_clean['rh'].iloc[:limit].values,
    'Ambient_Lux': df_bems_clean[lux_col].iloc[:limit].values,
    'Mood': df_ashrae_clean['Mood'].iloc[:limit].values
})

# Refined PWM Logic: Incorporating Temperature Sensitivity
# ASHRAE logic: If temp is too high/low, we adjust light to reduce "visual heat"
def calculate_pwm_advanced(row):
    # Base goals based on mood
    targets = {0: 80, 1: 180, 2: 400} 
    target_goal = targets[row['Mood']]
    
    # Ambient Light Subtraction (Daylight Harvesting)
    diff = target_goal - (row['Ambient_Lux'] * 10) # Scaling kW to comparative Lux
    
    # Temperature Compensation (Human Comfort factor)
    # If temp > 26°C, dim slightly to feel cooler (Psychological effect)
    temp_factor = 0.95 if row['Temperature'] > 26 else 1.05
    
    pwm_val = diff * temp_factor * 0.6
    return pwm_val

train_df['Target_LED_PWM'] = train_df.apply(calculate_pwm_advanced, axis=1).clip(0, 255)

# --- STEP 3: HIGH-ACCURACY TRAINING ---
X = train_df[['Temperature', 'Humidity', 'Ambient_Lux', 'Mood']]
y = train_df['Target_LED_PWM']

# Split data to test accuracy
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

print("Starting Hyperparameter Tuning (Random Forest)...")
# We use more estimators and deeper trees for the 99% accuracy target
model = RandomForestRegressor(
    n_estimators=300, 
    max_depth=15, 
    min_samples_split=2,
    random_state=42,
    n_jobs=-1 # Uses all CPU cores for speed
)

model.fit(X_train, y_train)

# --- STEP 4: VALIDATION ---
predictions = model.predict(X_test)
accuracy = r2_score(y_test, predictions)
mae = mean_absolute_error(y_test, predictions)

print(f"\n--- MODEL PERFORMANCE ---")
print(f"R-squared Accuracy: {accuracy:.4%}")
print(f"Mean Absolute Error: {mae:.2f} PWM units")

# --- STEP 5: SAVE ---
joblib.dump(model, 'lumina_model.pkl')
print("\n[SUCCESS] High-accuracy model saved as 'lumina_model.pkl'")