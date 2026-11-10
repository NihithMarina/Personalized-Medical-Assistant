Dataset support for ml_prediction

You can provide a CSV at:

  personalized_medicine_assistant/ml_prediction/data/disease_symptoms.csv

Two supported formats:

1) Long/list format
   Columns: disease, symptoms, (optional) medicines, (optional) diet
   - symptoms can be comma-separated or semicolon-separated

   Example:
   disease,symptoms,medicines,diet
   Flu,"fever,cough,body_aches","Antivirals, rest","Fluids, vitamin C"
   Diabetes,"excessive thirst, frequent urination, blurred vision",Metformin,"Low carb diet"

2) One-hot format
   Columns: disease, <symptom1>, <symptom2>, ... (optional: medicines, diet)
   - Each symptom column is 0/1 or true/false/yes/no

   Example:
   disease,fever,cough,body_aches,blurred_vision,medicines,diet
   Flu,1,1,1,0,"Antivirals, rest","Fluids, vitamin C"
   Diabetes,0,0,0,1,Metformin,"Low carb diet"

3) Multi-column string format (Symptom_1..Symptom_N)
   Columns: disease, Symptom_1, Symptom_2, ... (optional: medicines, diet)
   - Each Symptom_* cell contains a symptom name string (or can be blank)

   Example:
   Disease,Symptom_1,Symptom_2,Symptom_3
   Flu,fever,cough,body_aches
   Diabetes,blurred_vision,excessive_thirst,frequent_urination

Notes
- The engine will detect the format automatically.
- When a CSV exists, the model is trained from it on first use; otherwise it falls back to the built-in synthetic dataset.
- Medicines/diet are optional; if not provided, defaults from the builtin catalog are used.
- If you change the CSV while the server is running, restart the server to retrain.

Auto-discovery order
1. disease_symptoms.csv
2. dataset.csv
3. First .csv file in this folder (alphabetical)

Medicines and diet sidecar
- You can provide per-disease medicines/diet in a separate file named `disease_info.csv` in this same folder.
- Columns: `Disease, Medicines, Diet`
- These values override defaults in the app for any matching disease names.
