import pandas as pd
import numpy as np

# --- 1. PREPARE ASHRAE (The 'Mood' Brain) ---
# Filter for 'Neutral' to 'Warm' sensations to find focus-level benchmarks
df_ashrae_clean = df_ashrae.dropna(subset=['ta', 'thermal_sensation'])

# Create a 'Mood_Target' based on thermal sensation
# Sensation > 0 (Warm) = 'Focused' (2), Sensation 0 = 'Normal' (1), Sensation < 0 = 'Relaxed' (0)
df_ashrae_clean['Mood_Target'] = pd.cut(df_ashrae_clean['thermal_sensation'], 
                                        bins=[-4, -0.5, 0.5, 4], 
                                        labels=[0, 1, 2])

# --- 2. PREPARE CU-BEMS (The 'Environment' Body) ---
# We need to find the Lux column. If 'z1_Light(kW)' was found, 
# look for 'z1_AmbientLight(lux)' in the same file.
lux_cols = [c for c in df_bems.columns if 'lux' in c.lower()]
target_lux_col = lux_cols[0] if lux_cols else 'z1_Light(kW)' # Fallback

df_bems_clean = df_bems.copy()
df_bems_clean['Ambient_Lux'] = df_bems_clean[target_lux_col]

# --- 3. THE CONCEPTUAL MERGE ---
# Since we are training a general model, we combine the features
# We take a sample of both to create a balanced training set
min_len = min(len(df_ashrae_clean), len(df_bems_clean))

train_df = pd.DataFrame({
    'Temperature': df_ashrae_clean['ta'].iloc[:min_len].values,
    'Humidity': df_ashrae_clean['rh'].iloc[:min_len].values,
    'Ambient_Lux': df_bems_clean['Ambient_Lux'].iloc[:min_len].values,
    'Mood': df_ashrae_clean['Mood_Target'].iloc[:min_len].values
})

# --- 4. CREATE THE TARGET VARIABLE ---
# Logic: If Mood is 'Focused', target is 500 lux. If 'Relaxed', target is 200 lux.
train_df['Target_LED_PWM'] = np.where(train_df['Mood'] == 2, 500, 250) - train_df['Ambient_Lux']
train_df['Target_LED_PWM'] = train_df['Target_LED_PWM'].clip(0, 255) # Keep in ESP32 range

print("\n[SUCCESS] Hybrid Training Set Created!")
print(train_df.head())