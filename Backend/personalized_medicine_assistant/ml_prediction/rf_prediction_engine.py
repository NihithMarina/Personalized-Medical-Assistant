"""Random Forest based disease prediction strictly using provided dataset.

Features:
- Builds a binary presence vector for each distinct normalized symptom across dataset.
- Trains a RandomForestClassifier (balanced) to map symptoms -> Disease.
- On prediction: creates vector from user symptoms; returns top-1 + top-3 candidates.
- Recommendations (medicine / diet) pulled from the dataset row of predicted disease with
  the highest symptom overlap with the input (fallback first row if tie).

Assumptions:
- Dataset columns: Disease, Symptom_*, Medicine Recommendation, Diet Recommendation
- Symptom cells may contain comma-separated lists.

This engine is stateless after initialization; heavy objects cached at module scope."""
from __future__ import annotations
from pathlib import Path
from typing import List, Dict, Tuple
import pandas as pd
import numpy as np
import re
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score

_SYM_COL_PREFIX = "Symptom "
_SPACE_RE = re.compile(r"[_\s]+")

class RandomForestDatasetEngine:
    def __init__(self, dataset_path: str | None = None, n_estimators: int = 300, random_state: int = 42):
        data_dir = Path(__file__).resolve().parent / 'data'
        
        # Priority order for dataset files
        if dataset_path:
            self.dataset_path = Path(dataset_path)
        else:
            # Look for files in priority order
            preferred_files = [
                'Disease.xlsx',  # Current file name (capitalized)
                'disease.xlsx',
                'dataset_with_recommendations.csv',
                'disease_symptoms.csv',
                'dataset.csv'
            ]
            
            self.dataset_path = None
            for filename in preferred_files:
                filepath = data_dir / filename
                if filepath.exists():
                    self.dataset_path = filepath
                    break
            
            # If none found, look for any CSV or Excel file
            if not self.dataset_path:
                for file_path in data_dir.glob('*.csv'):
                    self.dataset_path = file_path
                    break
                for file_path in data_dir.glob('*.xlsx'):
                    self.dataset_path = file_path
                    break
                for file_path in data_dir.glob('*.xls'):
                    self.dataset_path = file_path
                    break
            
            if not self.dataset_path:
                raise FileNotFoundError("No dataset file found in data directory")
        
        self.n_estimators = n_estimators
        self.random_state = random_state
        
        # Load dataset based on file type
        if self.dataset_path.suffix.lower() in ['.xlsx', '.xls']:
            self.df = pd.read_excel(self.dataset_path)
        else:
            self.df = pd.read_csv(self.dataset_path)
        
        # Clean column names (remove leading/trailing spaces)
        self.df.columns = self.df.columns.str.strip()
        
        # Map column names for consistency
        column_mapping = {
            'Hyderation': 'Hydration',
            'Notes/Consideration': 'Notes'
        }
        self.df.rename(columns=column_mapping, inplace=True)
        
        print(f"Loaded dataset: {self.dataset_path.name}")
        print(f"Dataset shape: {self.df.shape}")
        print(f"Columns: {list(self.df.columns)}")
        
        self.symptom_columns = [c for c in self.df.columns if c.startswith(_SYM_COL_PREFIX)]
        self._normalize_cache: dict[str, str] = {}
        self.symptom_vocab: List[str] = []
        self.symptom_index: Dict[str, int] = {}
        self.model: RandomForestClassifier | None = None
        self._row_symptom_sets: List[set] = []  # parallel to df rows, for recommendation overlap
        self._prepare()
        self._train()

    # ---------------- Preparation -----------------
    def _norm(self, s: str) -> str:
        if not s or s != s:  # NaN
            return ''
        if s in self._normalize_cache:
            return self._normalize_cache[s]
        v = s.strip().lower()
        v = _SPACE_RE.sub(' ', v).strip().replace(' ', '_')
        self._normalize_cache[s] = v
        return v

    def _split_cell(self, cell: str) -> List[str]:
        if not cell or cell != cell:
            return []
        parts = [p.strip() for p in str(cell).split(',')] if ',' in str(cell) else [str(cell).strip()]
        return [self._norm(p) for p in parts if p and p.lower() != 'nan']

    def _prepare(self):
        vocab = set()
        row_sets: List[set] = []
        for _, row in self.df.iterrows():
            sset = set()
            for col in self.symptom_columns:
                for norm_sym in self._split_cell(row.get(col)):
                    if norm_sym:
                        sset.add(norm_sym)
            row_sets.append(sset)
            vocab.update(sset)
        self.symptom_vocab = sorted(vocab)
        self.symptom_index = {s: i for i, s in enumerate(self.symptom_vocab)}
        self._row_symptom_sets = row_sets

    def _vectorize(self, symptoms: List[str]) -> np.ndarray:
        vec = np.zeros(len(self.symptom_vocab), dtype=np.uint8)
        for s in symptoms:
            ns = self._norm(s)
            idx = self.symptom_index.get(ns)
            if idx is not None:
                vec[idx] = 1
        return vec

    def _row_vector(self, sset: set) -> np.ndarray:
        vec = np.zeros(len(self.symptom_vocab), dtype=np.uint8)
        for s in sset:
            idx = self.symptom_index.get(s)
            if idx is not None:
                vec[idx] = 1
        return vec

    def _train(self):
        # Build X, y
        # Use the correct column name (with trailing space)
        disease_col = 'Disease ' if 'Disease ' in self.df.columns else 'Disease'
        
        X = []
        y = []
        for (row_idx, row), sset in zip(self.df.iterrows(), self._row_symptom_sets):
            if not sset:
                continue
            X.append(self._row_vector(sset))
            y.append(row[disease_col])
        X = np.array(X)
        y = np.array(y)
        if len(X) == 0:
            raise ValueError("No training data extracted from dataset")
            
        # Check if we can use stratification (need at least 2 samples per class)
        from collections import Counter
        class_counts = Counter(y)
        min_samples = min(class_counts.values())
        use_stratify = min_samples >= 2
        
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, 
            test_size=0.25, 
            random_state=self.random_state, 
            stratify=y if use_stratify else None
        )
        self.model = RandomForestClassifier(
            n_estimators=self.n_estimators,
            random_state=self.random_state,
            class_weight='balanced_subsample',
            n_jobs=-1
        )
        self.model.fit(X_train, y_train)
        acc = accuracy_score(y_test, self.model.predict(X_test))
        print(f"[RF Engine] Trained RandomForest accuracy: {acc:.2%} on holdout {len(y_test)} samples")

    # ---------------- Prediction -----------------
    def predict(self, symptoms: List[str]) -> Dict[str, any]:
        if not symptoms:
            return {
                'predicted_disease': 'Unknown',
                'confidence': 0.0,
                'medicine_recommendation': 'Provide at least one symptom',
                'diet_recommendation': '—',
                'foods_to_avoid': '—',
                'status': 'no_symptoms'
            }
        if self.model is None:
            return {'predicted_disease': 'Unknown', 'confidence': 0.0, 'medicine_recommendation': 'Model not ready', 'diet_recommendation': '—', 'foods_to_avoid': '—', 'status': 'error'}
        vec = self._vectorize(symptoms)
        if vec.sum() == 0:
            return {
                'predicted_disease': 'Unknown',
                'confidence': 0.0,
                'medicine_recommendation': 'Symptoms not found in dataset vocabulary',
                'diet_recommendation': '—',
                'foods_to_avoid': '—',
                'status': 'unrecognized'
            }
        proba = self.model.predict_proba([vec])[0]
        classes = self.model.classes_
        top_idx = int(np.argmax(proba))
        top_disease = classes[top_idx]
        confidence = round(float(proba[top_idx] * 100), 1)
        # Top 3 candidates
        order = np.argsort(proba)[::-1][:3]
        top_candidates = [
            {'disease': classes[i], 'confidence': round(float(proba[i] * 100), 1)} for i in order
        ]
        med, diet, avoid = self._best_recommendations(top_disease, symptoms)
        return {
            'predicted_disease': top_disease,
            'confidence': confidence,
            'medicine_recommendation': med,
            'diet_recommendation': diet,
            'foods_to_avoid': avoid,
            'status': 'success',
            'candidates': top_candidates
        }

    def _best_recommendations(self, disease: str, input_symptoms: List[str]) -> Tuple[str, str, str]:
        # Choose the disease row with maximal overlap with input for recs
        input_norm = {self._norm(s) for s in input_symptoms if s}
        best_row = None
        best_inter_size = -1
        
        # Use the correct column name (with trailing space)
        disease_col = 'Disease ' if 'Disease ' in self.df.columns else 'Disease'
        
        for (idx, row), sset in zip(self.df.iterrows(), self._row_symptom_sets):
            if row[disease_col] != disease:
                continue
            inter_size = len(input_norm & sset)
            if inter_size > best_inter_size:
                best_inter_size = inter_size
                best_row = row
        
        if best_row is not None:
            # Get medicine recommendation from the 'Medicine' column
            med = str(best_row.get('Medicine', '')).strip()
            if not med or med.lower() in ['nan', 'none', '']:
                med = 'Consult a healthcare provider'
            
            # Get diet recommendation from the 'Diet Recommendation' column
            diet = str(best_row.get('Diet Recommendation', '')).strip()
            if not diet or diet.lower() in ['nan', 'none', '']:
                diet = 'Maintain a balanced diet'
            
            # Get foods to avoid from the 'Foods To Avoid' column
            avoid = str(best_row.get('Foods To Avoid', '')).strip()
            if not avoid or avoid.lower() in ['nan', 'none', '']:
                avoid = 'No specific foods to avoid mentioned'
                
            return med, diet, avoid
            
        # Fallback first matching row
        row = self.df[self.df[disease_col] == disease].iloc[0]
        
        # Get medicine recommendation from the 'Medicine' column
        med = str(row.get('Medicine', '')).strip()
        if not med or med.lower() in ['nan', 'none', '']:
            med = 'Consult a healthcare provider'
        
        # Get diet recommendation from the 'Diet Recommendation' column
        diet = str(row.get('Diet Recommendation', '')).strip()
        if not diet or diet.lower() in ['nan', 'none', '']:
            diet = 'Maintain a balanced diet'
        
        # Get foods to avoid from the 'Foods To Avoid' column
        avoid = str(row.get('Foods To Avoid', '')).strip()
        if not avoid or avoid.lower() in ['nan', 'none', '']:
            avoid = 'No specific foods to avoid mentioned'
        
        return (med, diet, avoid)

    def get_available_symptoms(self) -> List[str]:
        return [s.replace('_', ' ').title() for s in self.symptom_vocab]

# Module-level singleton for reuse
_engine_singleton: RandomForestDatasetEngine | None = None

def get_engine() -> RandomForestDatasetEngine:
    global _engine_singleton
    if _engine_singleton is None:
        _engine_singleton = RandomForestDatasetEngine()
    return _engine_singleton
