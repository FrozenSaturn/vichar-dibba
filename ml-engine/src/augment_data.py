import pandas as pd
import numpy as np
import os
import random

# --- CONFIG ---
REAL_DATA_PATH = '../data/cleaned_data.csv'
OUTPUT_PATH = '../data/augmented_data.csv'

def augment_data():
    print("🧪 Generating Smarter Synthetic Negative Data...")
    
    # 1. Load Real Data
    base_dir = os.path.dirname(os.path.abspath(__file__))
    input_file = os.path.join(base_dir, REAL_DATA_PATH)
    
    if not os.path.exists(input_file):
        print("❌ Error: Cleaned data not found.")
        return

    df_real = pd.read_csv(input_file)
    
    # Capture the unique lists of real locations/industries
    real_industries = df_real['industry'].dropna().unique().tolist()
    real_cities = df_real['city'].dropna().unique().tolist()
    
    print(f"   Loaded {len(df_real)} real high-value startups.")

    # 2. Define "Small Business" Templates
    bad_idea_keywords = [
        "lemonade stand", "local bakery", "dog walking service", "home cleaning", 
        "freelance consulting", "math tutoring", "selling cookies", "knitting store",
        "personal blog", "gaming youtube channel", "lawn mowing", "car wash",
        "babysitting app", "handmade jewelry", "t-shirt printing", "grocery store",
        "coffee shop", "barber shop", "nail salon", "handyman service",
        "street food stall", "used book store", "flower shop", "pet sitting"
    ]

    # 3. Generate 2000 "Bad" Rows
    synthetic_data = []
    
    for i in range(2000): 
        # Pick a random "bad" description
        pitch_base = random.choice(bad_idea_keywords)
        
        # Randomize metadata using REAL categories
        # This prevents the model from associating "Logistics" with "Bad"
        rand_industry = random.choice(real_industries)
        rand_city = random.choice(real_cities)
        
        synthetic_data.append({
            'pitch': pitch_base,
            'industry': rand_industry,
            'city': rand_city,
            # Random valuation between $5k and $25k
            'funding_amount': np.random.randint(5000, 25000) 
        })

    df_synthetic = pd.DataFrame(synthetic_data)
    print(f"   Created {len(df_synthetic)} synthetic low-value rows.")

    # 4. Combine Real + Synthetic
    df_final = pd.concat([df_real, df_synthetic], ignore_index=True)
    
    # Shuffle
    df_final = df_final.sample(frac=1, random_state=42).reset_index(drop=True)

    # 5. Save
    output_file = os.path.join(base_dir, OUTPUT_PATH)
    df_final.to_csv(output_file, index=False)
    print(f"✅ Saved Smarter Augmented Dataset to: {output_file}")
    print(f"   Total Training Rows: {len(df_final)}")

if __name__ == "__main__":
    augment_data()