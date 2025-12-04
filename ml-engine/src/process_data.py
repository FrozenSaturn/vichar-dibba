import pandas as pd
import re
import os

def clean_currency(x):
    if pd.isna(x):
        return 0
    # Convert to string, lowercase, remove commas
    x = str(x).replace(',', '').lower()
    
    match = re.search(r'\d+(\.\d+)?', x)
    if match:
        return float(match.group())
    return 0

def process_data(input_file, output_file):
    print(f"Loading data from {input_file}...")
    df = pd.read_csv(input_file)
    
    # 1. Clean Target Variable (Funding Amount)
    df['clean_amount'] = df['Amount in USD'].apply(clean_currency)
    
    # Filter: Keep valid funding amounts (e.g., $10k to $500M)
    # We remove 0s and extreme billion-dollar outliers which confuse the model
    df_clean = df[(df['clean_amount'] >= 10000) & (df['clean_amount'] <= 500000000)].copy()

    # 2. Clean Input Text (The "Pitch")
    # If 'SubVertical' (Pitch) is missing, use 'Industry Vertical' as fallback
    df_clean['SubVertical'] = df_clean['SubVertical'].fillna(df_clean['Industry Vertical'])
    
    # Ensure all text is string and lowercase
    df_clean['pitch'] = df_clean['SubVertical'].astype(str).str.lower().str.strip()
    
    # 3. Rename columns for clarity
    final_df = df_clean[['pitch', 'clean_amount', 'Industry Vertical', 'City  Location']]
    final_df.columns = ['pitch', 'funding_amount', 'industry', 'city']
    
    # 4. Drop any remaining rows with missing critical data
    final_df = final_df.dropna(subset=['pitch', 'funding_amount'])
    
    print(f"Data cleaned! {len(df)} rows -> {len(final_df)} rows.")
    final_df.to_csv(output_file, index=False)
    print(f"Saved to {output_file}")

if __name__ == "__main__":
    # Define paths relative to where you run the script
    base_dir = os.path.dirname(os.path.abspath(__file__))
    input_path = os.path.join(base_dir, '../data/startup_funding.csv')
    output_path = os.path.join(base_dir, '../data/cleaned_data.csv')
    
    # Ensure data directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    process_data(input_path, output_path)