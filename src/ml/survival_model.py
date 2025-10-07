"""
Survival Likelihood ML Model for Earthquake Rescue System
Predicts survival probability for detected victims based on various factors
"""

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.metrics import classification_report, roc_auc_score, roc_curve
import xgboost as xgb
import joblib
from typing import Dict, List, Tuple
import json

class SurvivalLikelihoodModel:
    def __init__(self):
        self.model = None
        self.scaler = StandardScaler()
        self.label_encoders = {}
        self.feature_columns = []
        self.is_trained = False
        
    def _create_synthetic_dataset(self, n_samples: int = 10000) -> pd.DataFrame:
        """Create synthetic training data for survival likelihood prediction"""
        np.random.seed(42)
        
        data = []
        
        for _ in range(n_samples):
            # Victim characteristics
            age = np.random.randint(5, 80)
            injury_level = np.random.choice(['none', 'minor', 'severe', 'unconscious'], 
                                         p=[0.1, 0.3, 0.4, 0.2])
            
            # Environmental factors
            time_since_detection = np.random.exponential(30)  # minutes
            distance_to_responder = np.random.exponential(200)  # meters
            rubble_density = np.random.uniform(0, 1)
            time_of_day = np.random.randint(0, 24)
            
            # Vitals based on injury level
            if injury_level == 'unconscious':
                hr = np.random.normal(40, 10)
                resp = np.random.normal(8, 2)
                spo2 = np.random.normal(70, 10)
            elif injury_level == 'severe':
                hr = np.random.normal(65, 15)
                resp = np.random.normal(15, 5)
                spo2 = np.random.normal(85, 8)
            elif injury_level == 'minor':
                hr = np.random.normal(80, 15)
                resp = np.random.normal(16, 3)
                spo2 = np.random.normal(95, 3)
            else:
                hr = np.random.normal(75, 10)
                resp = np.random.normal(18, 3)
                spo2 = np.random.normal(98, 2)
            
            # Drone/Detection factors
            detection_confidence = np.random.beta(2, 1)  # Skewed towards higher confidence
            comms_quality = np.random.uniform(0.5, 1.0)
            
            # Calculate survival probability based on realistic factors
            survival_prob = self._calculate_realistic_survival_probability(
                age, injury_level, time_since_detection, distance_to_responder,
                hr, resp, spo2, rubble_density, time_of_day
            )
            
            # Add some noise
            survival_prob += np.random.normal(0, 0.1)
            survival_prob = np.clip(survival_prob, 0, 1)
            
            # Binary survival outcome
            survived = 1 if survival_prob > 0.5 else 0
            
            data.append({
                'age': age,
                'injury_level': injury_level,
                'time_since_detection': time_since_detection,
                'distance_to_responder': distance_to_responder,
                'rubble_density': rubble_density,
                'time_of_day': time_of_day,
                'hr': hr,
                'resp': resp,
                'spo2': spo2,
                'detection_confidence': detection_confidence,
                'comms_quality': comms_quality,
                'survival_probability': survival_prob,
                'survived': survived
            })
        
        return pd.DataFrame(data)
    
    def _calculate_realistic_survival_probability(self, age, injury_level, time_since_detection,
                                                distance_to_responder, hr, resp, spo2,
                                                rubble_density, time_of_day) -> float:
        """Calculate realistic survival probability based on medical knowledge"""
        base_prob = 0.8  # Base survival probability
        
        # Age factor (older = lower survival)
        age_factor = max(0.3, 1 - (age - 5) / 75 * 0.4)
        
        # Injury level factor
        injury_factors = {
            'none': 1.0,
            'minor': 0.9,
            'severe': 0.6,
            'unconscious': 0.3
        }
        injury_factor = injury_factors.get(injury_level, 0.5)
        
        # Time factor (exponential decay)
        time_factor = np.exp(-time_since_detection / 120)  # Half-life of 2 hours
        
        # Distance factor
        distance_factor = max(0.3, 1 - distance_to_responder / 1000)
        
        # Vitals factors
        hr_factor = 1.0 if 60 <= hr <= 100 else 0.7
        resp_factor = 1.0 if 12 <= resp <= 20 else 0.6
        spo2_factor = max(0.2, spo2 / 100)
        
        # Environmental factors
        rubble_factor = 1 - rubble_density * 0.3
        time_factor_env = 1.0 if 6 <= time_of_day <= 18 else 0.8  # Night is worse
        
        # Combine all factors
        survival_prob = (base_prob * age_factor * injury_factor * time_factor * 
                        distance_factor * hr_factor * resp_factor * spo2_factor * 
                        rubble_factor * time_factor_env)
        
        return np.clip(survival_prob, 0, 1)
    
    def prepare_features(self, df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
        """Prepare features for training"""
        # Encode categorical variables
        le_injury = LabelEncoder()
        df['injury_level_encoded'] = le_injury.fit_transform(df['injury_level'])
        self.label_encoders['injury_level'] = le_injury
        
        # Select features
        feature_cols = [
            'age', 'injury_level_encoded', 'time_since_detection',
            'distance_to_responder', 'rubble_density', 'time_of_day',
            'hr', 'resp', 'spo2', 'detection_confidence', 'comms_quality'
        ]
        
        self.feature_columns = feature_cols
        X = df[feature_cols].values
        y = df['survived'].values
        
        # Scale features
        X_scaled = self.scaler.fit_transform(X)
        
        return X_scaled, y
    
    def train(self, X: np.ndarray, y: np.ndarray, model_type: str = 'xgboost'):
        """Train the survival likelihood model"""
        if model_type == 'xgboost':
            self.model = xgb.XGBClassifier(
                n_estimators=100,
                max_depth=6,
                learning_rate=0.1,
                random_state=42
            )
        elif model_type == 'random_forest':
            self.model = RandomForestClassifier(
                n_estimators=100,
                max_depth=10,
                random_state=42
            )
        elif model_type == 'gradient_boosting':
            self.model = GradientBoostingClassifier(
                n_estimators=100,
                max_depth=6,
                learning_rate=0.1,
                random_state=42
            )
        
        # Train the model
        self.model.fit(X, y)
        self.is_trained = True
        
        # Cross-validation score
        cv_scores = cross_val_score(self.model, X, y, cv=5, scoring='roc_auc')
        print(f"Cross-validation ROC-AUC: {cv_scores.mean():.3f} (+/- {cv_scores.std() * 2:.3f})")
        
        return self.model
    
    def predict_survival_likelihood(self, features: Dict) -> float:
        """Predict survival likelihood for a single victim"""
        if not self.is_trained:
            raise ValueError("Model must be trained before making predictions")
        
        # Prepare features in the same order as training
        feature_vector = np.array([
            features.get('age', 30),
            self.label_encoders['injury_level'].transform([features.get('injury_level', 'minor')])[0],
            features.get('time_since_detection', 30),
            features.get('distance_to_responder', 200),
            features.get('rubble_density', 0.5),
            features.get('time_of_day', 12),
            features.get('hr', 75),
            features.get('resp', 16),
            features.get('spo2', 95),
            features.get('detection_confidence', 0.8),
            features.get('comms_quality', 0.9)
        ]).reshape(1, -1)
        
        # Scale features
        feature_vector_scaled = self.scaler.transform(feature_vector)
        
        # Predict probability
        survival_prob = self.model.predict_proba(feature_vector_scaled)[0][1]
        
        return float(survival_prob)
    
    def evaluate_model(self, X: np.ndarray, y: np.ndarray) -> Dict:
        """Evaluate model performance"""
        if not self.is_trained:
            raise ValueError("Model must be trained before evaluation")
        
        y_pred = self.model.predict(X)
        y_pred_proba = self.model.predict_proba(X)[:, 1]
        
        # Calculate metrics
        roc_auc = roc_auc_score(y, y_pred_proba)
        
        # Feature importance
        if hasattr(self.model, 'feature_importances_'):
            feature_importance = dict(zip(self.feature_columns, self.model.feature_importances_))
        else:
            feature_importance = {}
        
        return {
            'roc_auc': roc_auc,
            'classification_report': classification_report(y, y_pred),
            'feature_importance': feature_importance
        }
    
    def save_model(self, filepath: str):
        """Save trained model and preprocessors"""
        if not self.is_trained:
            raise ValueError("Model must be trained before saving")
        
        model_data = {
            'model': self.model,
            'scaler': self.scaler,
            'label_encoders': self.label_encoders,
            'feature_columns': self.feature_columns
        }
        
        joblib.dump(model_data, filepath)
        print(f"Model saved to {filepath}")
    
    def load_model(self, filepath: str):
        """Load trained model and preprocessors"""
        model_data = joblib.load(filepath)
        
        self.model = model_data['model']
        self.scaler = model_data['scaler']
        self.label_encoders = model_data['label_encoders']
        self.feature_columns = model_data['feature_columns']
        self.is_trained = True
        
        print(f"Model loaded from {filepath}")

def main():
    """Main function to train and test the model"""
    # Create model instance
    model = SurvivalLikelihoodModel()
    
    # Generate synthetic training data
    print("Generating synthetic training data...")
    df = model._create_synthetic_dataset(n_samples=10000)
    print(f"Generated {len(df)} training samples")
    
    # Prepare features
    X, y = model.prepare_features(df)
    print(f"Feature matrix shape: {X.shape}")
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    # Train model
    print("Training XGBoost model...")
    model.train(X_train, y_train, model_type='xgboost')
    
    # Evaluate model
    print("Evaluating model...")
    results = model.evaluate_model(X_test, y_test)
    print(f"ROC-AUC Score: {results['roc_auc']:.3f}")
    print("\nFeature Importance:")
    for feature, importance in sorted(results['feature_importance'].items(), 
                                     key=lambda x: x[1], reverse=True):
        print(f"  {feature}: {importance:.3f}")
    
    # Save model
    model.save_model('survival_model.pkl')
    
    # Test prediction
    print("\nTesting prediction...")
    test_features = {
        'age': 45,
        'injury_level': 'severe',
        'time_since_detection': 60,
        'distance_to_responder': 300,
        'rubble_density': 0.7,
        'time_of_day': 14,
        'hr': 55,
        'resp': 12,
        'spo2': 80,
        'detection_confidence': 0.85,
        'comms_quality': 0.8
    }
    
    survival_prob = model.predict_survival_likelihood(test_features)
    print(f"Predicted survival likelihood: {survival_prob:.3f}")

if __name__ == "__main__":
    main()
