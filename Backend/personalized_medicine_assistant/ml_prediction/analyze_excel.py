import pandas as pd
import os

# Path to the Excel file
excel_path = r"c:\Users\NIHITH\OneDrive\Documents\PMA - Personalized Medical Assistant\flask_template\personalized_medicine_assistant\ml_prediction\data\disease.xlsx"

try:
    # Read the Excel file
    print("Reading Excel file...")
    df = pd.read_excel(excel_path)
    
    print(f"\n=== EXCEL FILE ANALYSIS ===")
    print(f"File: {os.path.basename(excel_path)}")
    print(f"Shape: {df.shape} (rows x columns)")
    
    print(f"\n=== COLUMN NAMES ===")
    for i, col in enumerate(df.columns):
        print(f"{i+1:2d}. {col}")
    
    print(f"\n=== FIRST 5 ROWS ===")
    print(df.head())
    
    print(f"\n=== DATA TYPES ===")
    print(df.dtypes)
    
    print(f"\n=== UNIQUE VALUES IN FIRST COLUMN ===")
    first_col = df.columns[0]
    print(f"Column '{first_col}' has {df[first_col].nunique()} unique values:")
    print(df[first_col].value_counts().head(10))
    
    print(f"\n=== SAMPLE DATA ===")
    print("First row:")
    print(df.iloc[0].to_dict())
    
except Exception as e:
    print(f"Error reading Excel file: {e}")
    print("\nTrying to read sheet names...")
    try:
        xl_file = pd.ExcelFile(excel_path)
        print(f"Available sheets: {xl_file.sheet_names}")
    except Exception as e2:
        print(f"Error reading sheet names: {e2}")