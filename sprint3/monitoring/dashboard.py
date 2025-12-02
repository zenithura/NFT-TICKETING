# File header: Interactive Dash web dashboard for real-time fraud detection monitoring.
# Displays KPIs, fraud scores, transaction volume, and model performance metrics.

"""
Interactive Monitoring Dashboard - Demo Version
Real-time fraud detection and system monitoring dashboard.
"""

import dash
from dash import dcc, html, Input, Output
import plotly.graph_objs as go
import plotly.express as px
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import dash_bootstrap_components as dbc

# Purpose: Initialize Dash web application with Bootstrap styling.
# Side effects: Creates Flask app instance, configures Dash.
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

# Purpose: Load sample transaction data from CSV or generate mock data if file missing.
# Returns: DataFrame with transaction data including timestamps and fraud labels.
# Side effects: Reads CSV file from filesystem or generates synthetic data.
def load_sample_data():
    """Load sample transaction data for dashboard."""
    try:
        df = pd.read_csv('sprint3/demos/data/sample_transactions.csv')
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        return df
    except FileNotFoundError:
        # Generate minimal sample data if file doesn't exist
        print("⚠️  Sample data not found, generating minimal dataset...")
        dates = pd.date_range(end=datetime.now(), periods=1000, freq='5min')
        return pd.DataFrame({
            'timestamp': dates,
            'transaction_id': [f'txn_{i:06d}' for i in range(1000)],
            'is_fraud': np.random.random(1000) < 0.02,
            'price_paid': np.random.uniform(20, 200, 1000),
            'wallet_address': [f'0x{i%100:040x}' for i in range(1000)]
        })

df = load_sample_data()

# Purpose: Calculate key performance indicators from recent transaction data.
# Params: df (DataFrame) — transaction data with timestamps.
# Returns: Dictionary with transactions_per_hour, fraud_rate, api_latency, revenue_per_hour.
# Side effects: Filters data to last hour, computes aggregations.
def calculate_kpis(df):
    """Calculate real-time KPIs."""
    recent_df = df[df['timestamp'] > datetime.now() - timedelta(hours=1)]
    
    kpis = {
        'transactions_per_hour': len(recent_df),
        'fraud_rate': recent_df['is_fraud'].mean() * 100 if len(recent_df) > 0 else 0,
        'api_latency': np.random.uniform(40, 55),  # Mock latency
        'revenue_per_hour': recent_df['price_paid'].sum() if 'price_paid' in recent_df.columns else 0
    }
    return kpis

# Dashboard Layout
app.layout = dbc.Container([
    # Header
    dbc.Row([
        dbc.Col([
            html.H1("🎫 NFT Ticketing - Monitoring Dashboard", className="text-center my-4"),
            html.P(f"Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}", 
                   className="text-center text-muted")
        ])
    ]),
    
    # KPI Cards
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H5("📊 Transactions/Hour", className="card-title"),
                    html.H2(id='kpi-transactions', className="text-primary"),
                    html.P(id='kpi-transactions-delta', className="text-muted")
                ])
            ], className="mb-3")
        ], width=3),
        
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H5("🚨 Fraud Rate", className="card-title"),
                    html.H2(id='kpi-fraud-rate', className="text-danger"),
                    html.P("Target: <2%", className="text-muted")
                ])
            ], className="mb-3")
        ], width=3),
        
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H5("⚡ API Latency (p95)", className="card-title"),
                    html.H2(id='kpi-latency', className="text-warning"),
                    html.P("Target: <50ms", className="text-muted")
                ])
            ], className="mb-3")
        ], width=3),
        
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H5("💰 Revenue/Hour", className="card-title"),
                    html.H2(id='kpi-revenue', className="text-success"),
                    html.P("Baseline: $11.2k", className="text-muted")
                ])
            ], className="mb-3")
        ], width=3),
    ]),
    
    # Fraud Detection Chart
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H5("Fraud Score Distribution (Last 24 Hours)"),
                    dcc.Graph(id='fraud-timeseries')
                ])
            ])
        ], width=12)
    ], className="mb-3"),
    
    # Traffic and Model Performance
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H5("Transaction Volume"),
                    dcc.Graph(id='traffic-chart')
                ])
            ])
        ], width=6),
        
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H5("Fraud Detection Performance"),
                    dcc.Graph(id='performance-chart')
                ])
            ])
        ], width=6),
    ], className="mb-3"),
    
    # Recent High-Risk Transactions
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H5("🚨 Recent High-Risk Transactions"),
                    html.Div(id='recent-fraud-table')
                ])
            ])
        ])
    ], className="mb-3"),
    
    # Auto-refresh interval
    dcc.Interval(
        id='interval-component',
        interval=5*1000,  # 5 seconds
        n_intervals=0
    )
], fluid=True)

# Purpose: Update KPI card values based on interval timer trigger.
# Params: n (int) — interval counter from auto-refresh component.
# Returns: Tuple of KPI values (transactions, fraud rate, latency, revenue, delta).
# Side effects: Recalculates KPIs from data, formats for display.
@app.callback(
    [Output('kpi-transactions', 'children'),
     Output('kpi-fraud-rate', 'children'),
     Output('kpi-latency', 'children'),
     Output('kpi-revenue', 'children'),
     Output('kpi-transactions-delta', 'children')],
    [Input('interval-component', 'n_intervals')]
)
def update_kpis(n):
    """Update KPI cards."""
    kpis = calculate_kpis(df)
    
    return (
        f"{kpis['transactions_per_hour']:,}",
        f"{kpis['fraud_rate']:.1f}%",
        f"{kpis['api_latency']:.0f}ms",
        f"${kpis['revenue_per_hour']:,.0f}",
        "▲ +12% (1h)" if kpis['transactions_per_hour'] > 1000 else "▼ -5% (1h)"
    )

# Purpose: Update fraud score time series chart with recent transaction data.
# Params: n (int) — interval counter from auto-refresh component.
# Returns: Plotly figure object with scatter plot and threshold lines.
# Side effects: Filters data to last 24 hours, generates mock fraud scores, creates chart.
@app.callback(
    Output('fraud-timeseries', 'figure'),
    [Input('interval-component', 'n_intervals')]
)
def update_fraud_chart(n):
    """Update fraud detection time series."""
    recent_df = df[df['timestamp'] > datetime.now() - timedelta(hours=24)]
    
    # Add mock fraud scores
    recent_df = recent_df.copy()
    recent_df['fraud_score'] = np.where(
        recent_df['is_fraud'],
        np.random.uniform(0.7, 0.95, len(recent_df)),
        np.random.uniform(0.05, 0.4, len(recent_df))
    )
    
    fig = go.Figure()
    
    # Add scatter plot
    fig.add_trace(go.Scatter(
        x=recent_df['timestamp'],
        y=recent_df['fraud_score'],
        mode='markers',
        marker=dict(
            size=6,
            color=recent_df['fraud_score'],
            colorscale='RdYlGn_r',
            showscale=True,
            colorbar=dict(title="Fraud Score")
        ),
        text=[f"TxnID: {tid}<br>Score: {score:.2f}" 
              for tid, score in zip(recent_df['transaction_id'], recent_df['fraud_score'])],
        hovertemplate='%{text}<extra></extra>'
    ))
    
    # Add threshold lines
    fig.add_hline(y=0.85, line_dash="dash", line_color="red", 
                  annotation_text="BLOCKED (>0.85)")
    fig.add_hline(y=0.65, line_dash="dash", line_color="orange", 
                  annotation_text="REVIEW (>0.65)")
    fig.add_hline(y=0.40, line_dash="dash", line_color="yellow", 
                  annotation_text="2FA (>0.40)")
    
    fig.update_layout(
        xaxis_title="Time",
        yaxis_title="Fraud Score",
        hovermode='closest',
        height=400
    )
    
    return fig

# Purpose: Update transaction volume chart grouped by time intervals.
# Params: n (int) — interval counter from auto-refresh component.
# Returns: Plotly figure with line chart of transaction counts per 15 minutes.
# Side effects: Filters data to last 6 hours, groups by time, creates chart.
@app.callback(
    Output('traffic-chart', 'figure'),
    [Input('interval-component', 'n_intervals')]
)
def update_traffic_chart(n):
    """Update traffic chart."""
    recent_df = df[df['timestamp'] > datetime.now() - timedelta(hours=6)]
    
    # Group by hour
    hourly = recent_df.groupby(pd.Grouper(key='timestamp', freq='15min')).size().reset_index(name='count')
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=hourly['timestamp'],
        y=hourly['count'],
        mode='lines+markers',
        fill='tozeroy',
        line=dict(color='#1f77b4', width=2)
    ))
    
    fig.update_layout(
        xaxis_title="Time",
        yaxis_title="Transactions per 15min",
        hovermode='x unified',
        height=300
    )
    
    return fig

# Purpose: Update confusion matrix visualization for model performance.
# Params: n (int) — interval counter from auto-refresh component.
# Returns: Plotly bar chart showing confusion matrix counts.
# Side effects: Creates mock confusion matrix data, generates chart.
@app.callback(
    Output('performance-chart', 'figure'),
    [Input('interval-component', 'n_intervals')]
)
def update_performance_chart(n):
    """Update model performance chart."""
    # Mock confusion matrix data
    confusion_data = pd.DataFrame({
        'Actual': ['Fraud', 'Fraud', 'Legit', 'Legit'],
        'Predicted': ['Fraud', 'Legit', 'Fraud', 'Legit'],
        'Count': [142, 18, 89, 11751]
    })
    
    fig = px.bar(
        confusion_data,
        x='Actual',
        y='Count',
        color='Predicted',
        barmode='group',
        title="Confusion Matrix (Last 24h)"
    )
    
    fig.update_layout(height=300)
    
    return fig

# Purpose: Update table displaying recent high-risk fraudulent transactions.
# Params: n (int) — interval counter from auto-refresh component.
# Returns: HTML table component with transaction details.
# Side effects: Filters data to fraud cases, generates mock scores, creates table.
@app.callback(
    Output('recent-fraud-table', 'children'),
    [Input('interval-component', 'n_intervals')]
)
def update_fraud_table(n):
    """Update recent high-risk transactions table."""
    recent_fraud = df[df['is_fraud']].tail(10)
    
    if len(recent_fraud) == 0:
        return html.P("No high-risk transactions in recent period", className="text-muted")
    
    table_header = [
        html.Thead(html.Tr([
            html.Th("Time"),
            html.Th("Transaction ID"),
            html.Th("Wallet"),
            html.Th("Score"),
            html.Th("Decision")
        ]))
    ]
    
    rows = []
    for _, row in recent_fraud.iterrows():
        score = np.random.uniform(0.7, 0.95)  # Mock score
        decision = "BLOCKED" if score > 0.85 else "REVIEW"
        
        rows.append(html.Tr([
            html.Td(row['timestamp'].strftime('%H:%M:%S')),
            html.Td(row['transaction_id'][:12] + '...'),
            html.Td(row['wallet_address'][:10] + '...'),
            html.Td(f"{score:.2f}", className="text-danger"),
            html.Td(decision, className="badge bg-danger" if decision == "BLOCKED" else "badge bg-warning")
        ]))
    
    table_body = [html.Tbody(rows)]
    
    return dbc.Table(table_header + table_body, bordered=True, hover=True, size='sm')

if __name__ == '__main__':
    print("=" * 60)
    print("NFT Ticketing Monitoring Dashboard")
    print("=" * 60)
    print("\n🚀 Starting dashboard on http://localhost:8050")
    print("\nFeatures:")
    print("  ✅ Real-time KPI monitoring")
    print("  ✅ Fraud detection visualization")
    print("  ✅ Transaction volume tracking")
    print("  ✅ Model performance metrics")
    print("  ✅ Auto-refresh every 5 seconds")
    print("\n" + "=" * 60)
    
    app.run_server(debug=True, host='0.0.0.0', port=8050)
