import json
import os

NOTEBOOK_PATH = "backend/data_science/notebooks/comprehensive_analysis.ipynb"

def create_notebook():
    cells = []

    # 1. Header
    cells.append({
        "cell_type": "markdown",
        "metadata": {},
        "source": [
            "# 📊 Comprehensive Data Science Analysis\n",
            "\n",
            "This notebook provides a complete analysis of the NFT Ticketing Platform's Data Science module.\n",
            "It explores the synthetic data, visualizes features, and evaluates the trained models.\n",
            "\n",
            "## Modules Covered:\n",
            "1. **Scalping Detection**\n",
            "2. **Risk Scoring**\n",
            "3. **Bot Detection**\n",
            "4. **Market Trend Prediction**"
        ]
    })

    # 2. Imports
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
            "import joblib\n",
            "import os\n",
            "import sys\n",
            "\n",
            "# Configure plotting\n",
            "sns.set_theme(style=\"whitegrid\")\n",
            "plt.rcParams['figure.figsize'] = (12, 6)\n",
            "\n",
            "# Paths\n",
            "DATA_DIR = \"../data/processed\"\n",
            "ARTIFACTS_DIR = \"../artifacts\"\n",
            "\n",
            "print(\"Libraries loaded successfully!\")"
        ]
    })

    # 3. Scalping Detection Section
    cells.append({
        "cell_type": "markdown",
        "metadata": {},
        "source": [
            "## 1. 🎫 Scalping Detection Analysis\n",
            "Analyzing ticket resale patterns to detect scalping behavior."
        ]
    })

    cells.append({
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [
            "# Load Data\n",
            "scalping_df = pd.read_csv(os.path.join(DATA_DIR, \"scalping_features.csv\"))\n",
            "print(f\"Loaded {len(scalping_df)} ticket records\")\n",
            "scalping_df.head()"
        ]
    })

    cells.append({
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [
            "# Visualize Price Differences\n",
            "plt.figure(figsize=(10, 6))\n",
            "sns.histplot(data=scalping_df, x='price_diff', bins=20, kde=True, color='orange')\n",
            "plt.title('Distribution of Price Markups (Resale Price - Base Price)')\n",
            "plt.xlabel('Price Difference ($)')\n",
            "plt.ylabel('Count')\n",
            "plt.show()"
        ]
    })

    # 4. Risk & Bot Detection Section
    cells.append({
        "cell_type": "markdown",
        "metadata": {},
        "source": [
            "## 2. 🚨 Risk & Bot Detection Analysis\n",
            "Analyzing user transaction patterns to identify high-risk users and potential bots."
        ]
    })

    cells.append({
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [
            "# Load Data\n",
            "risk_df = pd.read_csv(os.path.join(DATA_DIR, \"user_risk_features.csv\"))\n",
            "print(f\"Loaded {len(risk_df)} user profiles\")\n",
            "risk_df.head()"
        ]
    })

    cells.append({
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [
            "# Visualize User Velocity vs Amount\n",
            "plt.figure(figsize=(10, 6))\n",
            "sns.scatterplot(data=risk_df, x='velocity', y='avg_amount', size='total_amount', hue='fraud_rate', sizes=(20, 200))\n",
            "plt.title('User Transaction Velocity vs Average Amount')\n",
            "plt.xlabel('Velocity (Tx/Hour)')\n",
            "plt.ylabel('Average Transaction Amount ($)')\n",
            "plt.show()"
        ]
    })

    # 5. Market Trend Section
    cells.append({
        "cell_type": "markdown",
        "metadata": {},
        "source": [
            "## 3. 📈 Market Trend Analysis\n",
            "Analyzing daily transaction volume to predict market trends."
        ]
    })

    cells.append({
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [
            "# Load Data\n",
            "trend_df = pd.read_csv(os.path.join(DATA_DIR, \"market_trend_features.csv\"))\n",
            "trend_df['date'] = pd.to_datetime(trend_df['date'])\n",
            "trend_df = trend_df.sort_values('date')\n",
            "\n",
            "# Plot Volume\n",
            "plt.figure(figsize=(12, 6))\n",
            "plt.plot(trend_df['date'], trend_df['total_volume'], marker='o', linestyle='-', color='purple')\n",
            "plt.title('Daily Transaction Volume Trend')\n",
            "plt.xlabel('Date')\n",
            "plt.ylabel('Total Volume ($)')\n",
            "plt.grid(True, alpha=0.3)\n",
            "plt.show()"
        ]
    })

    # 6. Model Evaluation
    cells.append({
        "cell_type": "markdown",
        "metadata": {},
        "source": [
            "## 4. 🤖 Model Artifacts Inspection\n",
            "Checking the trained model files."
        ]
    })

    cells.append({
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [
            "print(\"Available Model Artifacts:\")\n",
            "for f in os.listdir(ARTIFACTS_DIR):\n",
            "    if f.endswith('.joblib'):\n",
            "        size_kb = os.path.getsize(os.path.join(ARTIFACTS_DIR, f)) / 1024\n",
            "        print(f\"- {f:<30} ({size_kb:.1f} KB)\")"
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
    
    print(f"✓ Notebook generated at: {NOTEBOOK_PATH}")

if __name__ == "__main__":
    create_notebook()
