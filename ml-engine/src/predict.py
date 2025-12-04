import sys
import json
import joblib
import pandas as pd
import numpy as np
import os

# Suppress warnings to keep JSON output clean
import warnings
warnings.filterwarnings("ignore")

def predict(pitch, industry, city):
    # 1. Load the saved model
    # Resolve path relative to this script
    base_dir = os.path.dirname(os.path.abspath(__file__))
    model_path = os.path.join(base_dir, '../models/valuation_model.pkl')
    
    if not os.path.exists(model_path):
        return {"error": "Model file not found. Train it first!"}

    model = joblib.load(model_path)

    # 2. Prepare Input Data
    # We must match the DataFrame structure used during training
    input_data = pd.DataFrame({
        'pitch': [pitch],
        'industry': [industry],
        'city': [city]
    })

    # 3. Make Prediction
    try:
        log_prediction = model.predict(input_data)
        dollar_prediction = np.expm1(log_prediction)[0] # Convert log back to dollars
        
        return {
            "success": True,
            "predicted_valuation": round(dollar_prediction, 2),
            "currency": "USD",
            "confidence_score": "High" if dollar_prediction > 1000000 else "Medium"
        }
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    # Input comes from command line arguments
    # Usage: python predict.py "My Idea" "Technology" "New York"
    try:
        if len(sys.argv) < 4:
            print(json.dumps({"error": "Not enough arguments. Need: pitch, industry, city"}))
        else:
            pitch_arg = sys.argv[1]
            industry_arg = sys.argv[2]
            city_arg = sys.argv[3]
            
            result = predict(pitch_arg, industry_arg, city_arg)
            print(json.dumps(result)) # Print JSON so Node.js can read it
    except Exception as e:
        print(json.dumps({"error": str(e)}))