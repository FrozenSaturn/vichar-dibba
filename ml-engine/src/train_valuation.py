import pandas as pd
import numpy as np
import joblib
import os

from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, r2_score

# --- CONFIGURATION ---
DATA_PATH = '../data/cleaned_data.csv'  # Path to the file we created in step 1
MODEL_PATH = '../models/valuation_model.pkl'

def train():
    print("Starting Training Process...")
    
    # 1. Load Data

    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_file = os.path.join(base_dir, DATA_PATH)
    
    if not os.path.exists(data_file):
        print(f"Error: Data file not found at {data_file}")
        return

    df = pd.read_csv(data_file)
    print(f"Loaded {len(df)} rows of data.")

    # 2. Prepare Features (X) and Target (y)
    X = df[['pitch', 'industry', 'city']]
    
    # --- CRITICAL: THE LOG TRANSFORM TO NORMALIZE ---
    y = np.log1p(df['funding_amount']) 

    # Split for validation
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # 3. Define the Preprocessing Pipeline
    # This teaches the model how to handle Text vs Categories automatically
    
    # A. Text Processing (The Pitch) -> TF-IDF
    # We look for top 1000 keywords, and also pairs of words (ngrams) like "ai platform"
    text_features = 'pitch'
    text_transformer = TfidfVectorizer(max_features=1000, ngram_range=(1,2), stop_words='english')

    # B. Category Processing (Industry, City) -> OneHot
    # We convert "Bengaluru" into a binary vector [0, 0, 1, 0...]
    categorical_features = ['industry', 'city']
    categorical_transformer = OneHotEncoder(handle_unknown='ignore')

    # Bundle them together
    preprocessor = ColumnTransformer(
        transformers=[
            ('text', text_transformer, text_features),
            ('cat', categorical_transformer, categorical_features)
        ]
    )

    # 4. Define the Model
    # RandomForest is robust and doesn't overfit easily on small data
    model = Pipeline(steps=[
        ('preprocessor', preprocessor),
        ('regressor', RandomForestRegressor(n_estimators=100, max_depth=20, random_state=42, n_jobs=-1))
    ])

    # 5. Train the Model
    print("Training Random Forest (this may take a moment)...")
    model.fit(X_train, y_train)

    # 6. Evaluate
    print("Evaluating...")
    y_pred_log = model.predict(X_test)
    
    # Convert predictions BACK from Log scale to Dollars
    y_pred_dollars = np.expm1(y_pred_log)
    y_test_dollars = np.expm1(y_test)
    
    mae = mean_absolute_error(y_test_dollars, y_pred_dollars)
    print(f"Training Complete.")
    print(f"   Mean Absolute Error (Accuracy): ${mae:,.2f}")
    print(f"   (This is the average deviation from the actual funding amount)")

    # 7. Save the Model
    output_file = os.path.join(base_dir, MODEL_PATH)
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    joblib.dump(model, output_file)
    print(f"Model saved to {output_file}")

    # --- Quick Test ---
    print("\n🔍 Running a quick test inference...")
    test_idea = pd.DataFrame({
        'pitch': ['ai powered supply chain management on blockchain'],
        'industry': ['Technology'],
        'city': ['Bengaluru']
    })
    prediction_log = model.predict(test_idea)
    prediction_dollars = np.expm1(prediction_log)[0]
    print(f"   Input: {test_idea['pitch'][0]}")
    print(f"   Predicted Valuation: ${prediction_dollars:,.2f}")

if __name__ == "__main__":
    train()