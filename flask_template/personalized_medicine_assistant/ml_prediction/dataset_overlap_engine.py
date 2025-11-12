import pandas as pd
from pathlib import Path
from typing import List, Dict, Tuple
import re

class DatasetOverlapPredictionEngine:
    """Deterministic dataset-driven prediction using symptom overlap.

    Steps:
    - Load CSV once (expects columns: Disease, Symptom_*, Medicine Recommendation, Diet Recommendation)
    - Normalize symptoms (lowercase, underscores)
    - For an input symptom list: normalize, build a set
    - Compute per-row Jaccard similarity: |intersection| / |union|
    - Aggregate by disease keeping best scoring row (tie-break: larger intersection, then first occurrence)
    - Return top disease if score >= threshold; else unknown response
    """

    def __init__(self, dataset_path: str | None = None, min_threshold: float = 0.12):
        data_dir = Path(__file__).resolve().parent / 'data'
        self.dataset_path = Path(dataset_path) if dataset_path else data_dir / 'dataset_with_recommendations.csv'
        self.min_threshold = min_threshold
        self.df = pd.read_csv(self.dataset_path)
        self.symptom_columns = [c for c in self.df.columns if c.startswith('Symptom_')]
        self._compiled_rows: list[dict] = []
        self._normalize_cache: dict[str,str] = {}
        self._prepare()

    _space_re = re.compile(r'[_\s]+')

    def _norm(self, s: str) -> str:
        if not s or s != s:  # NaN check
            return ''
        if s in self._normalize_cache:
            return self._normalize_cache[s]
        v = s.strip().lower()
        v = self._space_re.sub(' ', v).strip()
        v = v.replace(' ', '_')
        self._normalize_cache[s] = v
        return v

    def _split_cell(self, cell: str) -> list[str]:
        if not cell or cell != cell:
            return []
        if ',' in cell:
            parts = [self._norm(p) for p in cell.split(',')]
        else:
            parts = [self._norm(cell)]
        return [p for p in parts if p]

    def _prepare(self):
        for idx, row in self.df.iterrows():
            symptom_set = set()
            for col in self.symptom_columns:
                cell = row.get(col)
                for s in self._split_cell(str(cell)):
                    symptom_set.add(s)
            self._compiled_rows.append({
                'disease': row.get('Disease'),
                'symptoms': symptom_set,
                'medicine': str(row.get('Medicine Recommendation', '')).strip(),
                'diet': str(row.get('Diet Recommendation', '')).strip(),
                'row_index': idx
            })
        # Build global symptom list
        all_symptoms = set()
        for r in self._compiled_rows:
            all_symptoms.update(r['symptoms'])
        self.available_symptoms = sorted(all_symptoms)

    def get_available_symptoms(self) -> List[str]:
        # Convert to display form
        return [s.replace('_', ' ').title() for s in self.available_symptoms]

    def predict(self, symptoms: List[str]) -> Dict[str, any]:
        if not symptoms:
            return {
                'predicted_disease': 'Unknown',
                'confidence': 0.0,
                'medicine_recommendation': 'Provide at least one symptom',
                'diet_recommendation': '—',
                'status': 'no_symptoms'
            }
        input_norm = {self._norm(s) for s in symptoms if s}
        if not input_norm:
            return {
                'predicted_disease': 'Unknown',
                'confidence': 0.0,
                'medicine_recommendation': 'Symptoms not recognized in dataset',
                'diet_recommendation': '—',
                'status': 'unrecognized'
            }
        best: dict | None = None
        best_score = 0.0
        for r in self._compiled_rows:
            inter = input_norm & r['symptoms']
            if not inter:
                continue
            union = input_norm | r['symptoms']
            score = len(inter) / len(union)
            if score > best_score:
                best_score = score
                best = {**r, 'intersection': inter, 'score': score}
            elif abs(score - best_score) < 1e-9 and best is not None:
                # tie-break on intersection size
                if len(inter) > len(best['intersection']):
                    best = {**r, 'intersection': inter, 'score': score}
        if not best or best_score < self.min_threshold:
            return {
                'predicted_disease': 'Unknown',
                'confidence': round(best_score * 100, 1),
                'medicine_recommendation': 'Insufficient dataset match. Refine symptoms.',
                'diet_recommendation': 'General balanced diet, hydration, rest.',
                'status': 'low_match',
                'debug': {'score': best_score, 'threshold': self.min_threshold}
            }
        return {
            'predicted_disease': best['disease'],
            'confidence': round(best_score * 100, 1),
            'medicine_recommendation': best['medicine'] or 'Consult a healthcare provider',
            'diet_recommendation': best['diet'] or 'Maintain balanced diet',
            'status': 'success',
            'debug': {
                'score': best_score,
                'matched_symptoms': sorted(best['intersection']),
                'input_symptoms': sorted(input_norm),
                'row_index': best['row_index']
            }
        }

# Convenience alias
DatasetEngine = DatasetOverlapPredictionEngine
