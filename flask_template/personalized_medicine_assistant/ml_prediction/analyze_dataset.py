import pandas as pd
import os

# Change to the data directory
os.chdir(r'c:\Users\NIHITH\OneDrive\Documents\PMA - Personalized Medical Assistant\flask_template\personalized_medicine_assistant\ml_prediction\data')

# Load the dataset
df = pd.read_csv('dataset_with_recommendations.csv')

print(f'Unique diseases: {df["Disease"].nunique()}')
print(f'Total rows: {len(df)}')
print('\nFirst 20 unique diseases:')
for i, disease in enumerate(df['Disease'].unique()[:20], 1):
    print(f'{i}. {disease}')

print('\nDataset columns:')
print(df.columns.tolist())

print('\nFirst row sample:')
print(df.iloc[0])