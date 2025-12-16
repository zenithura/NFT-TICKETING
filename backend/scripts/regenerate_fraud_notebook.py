import json
import os

NOTEBOOK_PATH = "backend/data_science/notebooks/fraud_model_evaluation.ipynb"

def create_notebook():
    cells = []

    # 1. Header
    cells.append({
        "cell_type": "markdown",
        "metadata": {},
        "source": [
            "# Sprint 3 Data Science Report\n",
            "## NFT Ticketing Platform - Fraud Detection Model Evaluation\n",
            "\n",
            "**Report Date**: 2025-12-16  \n",
            "**Model Version**: v1.2.3  \n",
            "**Platform Scale**: 50k-200k daily events\n"
        ]
    })

    # 2. Data Loading
    cells.append({
        "cell_type": "markdown",
        "metadata": {},
        "source": [
            "## 1. Data Preparation\n",
            "\n",
            "### Load and Explore Data\n"
        ]
    })

    cells.append({
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [
            "import pandas as pd\n",
            "import numpy as np\n",
            "import matplotlib.pyplot as plt\n",
            "import seaborn as sns\n",
            "from sklearn.model_selection import train_test_split\n",
            "from sklearn.metrics import roc_auc_score, precision_recall_curve, auc, confusion_matrix, classification_report\n",
            "import warnings\n",
            "warnings.filterwarnings('ignore')\n",
            "\n",
            "# Load data from the new raw data folder\n",
            "try:\n",
            "    df = pd.read_csv('../data/raw/transactions.csv')\n",
            "    print(\"✅ Loaded transactions from ../data/raw/transactions.csv\")\n",
            "except FileNotFoundError:\n",
            "    print(\"⚠️ Data file not found. Generating sample data for demonstration.\")\n",
            "    # Generate sample data if file missing\n",
            "    np.random.seed(42)\n",
            "    n = 1000\n",
            "    df = pd.DataFrame({\n",
            "        'transaction_id': [f'txn_{i:06d}' for i in range(n)],\n",
            "        'amount': np.random.exponential(100, n),\n",
            "        'is_fraud': (np.random.random(n) < 0.05).astype(int)\n",
            "    })\n",
            "\n",
            "print(f\"Dataset shape: {df.shape}\")\n",
            "print(f\"Fraud rate: {df['is_fraud'].mean():.2%}\")\n",
            "df.head()\n"
        ]
    })

    # 3. Feature Engineering (Mock)
    cells.append({
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [
            "# Mock Feature Engineering (since raw transactions might not have all features)\n",
            "if 'txn_velocity_1h' not in df.columns:\n",
            "    df['txn_velocity_1h'] = np.random.poisson(2, len(df))\n",
            "    df['wallet_age_days'] = np.random.exponential(30, len(df))\n",
            "    df['avg_ticket_hold_time'] = np.random.normal(48, 12, len(df))\n",
            "    df['price_deviation_ratio'] = np.random.normal(0, 0.3, len(df))\n",
            "\n",
            "feature_cols = ['amount', 'txn_velocity_1h', 'wallet_age_days', 'avg_ticket_hold_time', 'price_deviation_ratio']\n",
            "df[feature_cols].describe()\n"
        ]
    })

    # 4. Model Training
    cells.append({
        "cell_type": "markdown",
        "metadata": {},
        "source": [
            "## 2. Model Training\n"
        ]
    })

    cells.append({
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [
            "# Prepare features and target\n",
            "X = df[feature_cols].fillna(0)\n",
            "y = df['is_fraud'].astype(int)\n",
            "\n",
            "# Train/test split\n",
            "X_train, X_test, y_train, y_test = train_test_split(\n",
            "    X, y, test_size=0.2, stratify=y, random_state=42\n",
            ")\n",
            "\n",
            "from sklearn.ensemble import RandomForestClassifier\n",
            "\n",
            "model = RandomForestClassifier(n_estimators=100, random_state=42)\n",
            "model.fit(X_train, y_train)\n",
            "print(\"✅ Model training complete\")\n"
        ]
    })

    # 5. Evaluation
    cells.append({
        "cell_type": "markdown",
        "metadata": {},
        "source": [
            "## 3. Performance Metrics\n"
        ]
    })

    cells.append({
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [
            "# Generate predictions\n",
            "y_pred = model.predict(X_test)\n",
            "\n",
            "# Classification report\n",
            "print(\"\\nClassification Report:\")\n",
            "print(classification_report(y_test, y_pred, target_names=['Legit', 'Fraud']))\n"
        ]
    })

    # Construct Notebook JSON
    notebook = {
        "cells": cells,
        "metadata": {
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3"
            },
            "language_info": {
                "codemirror_mode": {
                    "name": "ipython",
                    "version": 3
                },
                "file_extension": ".py",
                "mimetype": "text/x-python",
                "name": "python",
                "nbconvert_exporter": "python",
                "pygments_lexer": "ipython3",
                "version": "3.8.10"
            }
        },
        "nbformat": 4,
        "nbformat_minor": 5
    }

    # Write file
    os.makedirs(os.path.dirname(NOTEBOOK_PATH), exist_ok=True)
    with open(NOTEBOOK_PATH, 'w') as f:
        json.dump(notebook, f, indent=2)
    
    print(f"✓ Notebook regenerated at: {NOTEBOOK_PATH}")

if __name__ == "__main__":
    create_notebook()
