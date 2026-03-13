import pandas as pd
import os
import glob

# --- 1. LOAD ASHRAE DATASET (From Cloud) ---
url_measurements = "https://github.com/CenterForTheBuiltEnvironment/ashrae-db-II/raw/master/v2.1.0/db_measurements_v2.1.0.csv.gz"

print("Step 1: Fetching ASHRAE Mood/Preference Data...")
try:
    # We read 1000 rows for the demo to keep it fast
    df_ashrae = pd.read_csv(url_measurements, compression='gzip', low_memory=False, nrows=1000)
    print("[SUCCESS] ASHRAE Data Loaded.")
    print(df_ashrae[['ta', 'rh', 'thermal_sensation']].head())
except Exception as e:
    print(f"[ERROR] ASHRAE Cloud fetch failed: {e}")

print("\n" + "="*30 + "\n")

# --- 2. LOAD CU-BEMS DATASET (From Local Folder) ---
# Based on your screenshot, the path is: raw\Database_QC-master\archive (2)\2018Floor1.csv
# We use 'r' before the string to handle backslashes in Windows
# --- 2. CU-BEMS LOAD (Dynamic Path Search) ---
print("Step 2: Searching for CU-BEMS 2018Floor1.csv...")

# This searches all subfolders for the file so you don't have to guess the path
search_pattern = os.path.join("**", "2018Floor1.csv")
files = glob.glob(search_pattern, recursive=True)

if files:
    file_path = files[0] # Take the first match found
    print(f"[FOUND] File located at: {file_path}")
    try:
        df_bems = pd.read_csv(file_path)
        print("[SUCCESS] CU-BEMS Sensor Data Loaded.")
        
        # Displaying identified columns for Light and Lux
        cols = [c for c in df_bems.columns if 'Light' in c or 'lux' in c]
        print(df_bems[cols].head())
    except Exception as e:
        print(f"[ERROR] Could not read CSV: {e}")
else:
    print("[ERROR] 2018Floor1.csv not found in any subfolder.")
    print("Current files in directory:", os.listdir())


    import pandas as pd
import numpy as np

# 1. Identify the Lux column dynamically
# This looks for any column that mentions 'lux' or 'Illuminance'
lux_col = [col for col in df_bems.columns if 'lux' in col.lower() or 'light' in col.lower()]

if lux_col:
    target_col = lux_col[0]
    print(f"[INFO] Using column: '{target_col}' for Ambient Light")
    
    # 2. Perform the cleaning on the found column
    df_bems_clean = df_bems.dropna(subset=[target_col])
    
    # 3. Standardize the name for the ML model
    df_bems_clean = df_bems_clean.rename(columns={target_col: 'Ambient_Lux'})
else:
    print("[ERROR] No Lux or Light column found! Check your CSV columns:")
    print(df_bems.columns.tolist())



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