# Data Science Evaluation Report

## Overview
This report summarizes the implementation and evaluation of the data science models for Sprint 3. We implemented 5 models covering risk scoring, recommendations, decision rules, segmentation, and market trend prediction.

## Models Implemented

### 1. Risk Score Model
- **Type**: Random Forest Classifier (with heuristic fallback).
- **Goal**: Detect high-risk transactions.
- **Inputs**: Transaction Amount, User Transaction Count.
- **Output**: Risk Score (0.0 - 1.0).
- **Evaluation**:
    - The model uses a pre-trained dummy Random Forest on synthetic data.
    - Fallback logic ensures functionality even without `scikit-learn`.
    - **Bias**: The synthetic data assumes high amounts are risky, which might flag legitimate high-value users.

### 2. Recommender Model
- **Type**: Content-Based Filtering.
- **Goal**: Recommend items based on user preference.
- **Inputs**: Preferred Category.
- **Output**: List of recommended items.
- **Evaluation**:
    - Successfully filters items by category.
    - Fallback to "popular" items (sorted by price) if no match found.
    - **Limitations**: Very simple logic, doesn't account for user history depth.

### 3. Real-time Decision Rule
- **Type**: Statistical (Bollinger Bands).
- **Goal**: Detect anomalies in real-time streams.
- **Inputs**: Value stream (e.g., transaction amounts).
- **Output**: "NORMAL" or "ANOMALY".
- **Evaluation**:
    - Uses a sliding window of 20 items.
    - Triggers if value is > 2 standard deviations from mean.
    - **Robustness**: Good for detecting sudden spikes.

### 4. User Segmentation
- **Type**: K-Means Clustering.
- **Goal**: Segment users into behavioral groups.
- **Inputs**: Average Transaction Value, Frequency.
- **Output**: Cluster ID (0, 1, 2).
- **Evaluation**:
    - Clusters users into Low Value/Freq, High Value/Freq, Medium Value/High Freq.
    - **Interpretation**: Cluster 1 represents high-value users.

### 5. Market Trend Prediction
- **Type**: Linear Regression.
- **Goal**: Predict future trends.
- **Inputs**: Time Index.
- **Output**: Predicted Value.
- **Evaluation**:
    - Fits a line to historical data.
    - **Accuracy**: Limited to linear trends.

## A/B Testing Framework
- Implemented `ABTestManager` supporting:
    - **Deterministic A/B**: Hash-based routing.
    - **Multi-Armed Bandit**: Epsilon-Greedy strategy.
- Allows dynamic routing of users to different model variants.

## KPIs
- **Conversion Rate**: Tracked via `KPICalculator`.
- **Time-to-Finality**: Average time tracked.

## Future Improvements
- Train models on real production data.
- Persist models to disk (pickle/joblib) instead of retraining on startup.
- Integrate with a real feature store.
