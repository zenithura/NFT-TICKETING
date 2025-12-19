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
import requests
import json

from web3 import Web3

# Purpose: Initialize Dash web application with Bootstrap styling.
# Side effects: Creates Flask app instance, configures Dash.
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.FLATLY, "https://use.fontawesome.com/releases/v5.15.4/css/all.css"])

# Blockchain Provider
w3 = Web3(Web3.HTTPProvider('http://localhost:8545'))

# Monitoring API URL
MONITORING_API_URL = "http://localhost:8000/api/v1/metrics"

# Purpose: Load sample transaction data from CSV or generate mock data if file missing.
# Returns: DataFrame with transaction data including timestamps and fraud labels.
# Side effects: Reads CSV file from filesystem or generates synthetic data.
def load_sample_data():
    """Load sample transaction data for dashboard."""
    countries = [
        ("India", 20.5937, 78.9629),
        ("USA", 37.0902, -95.7129),
        ("UK", 55.3781, -3.4360),
        ("China", 35.8617, 104.1954),
        ("Brazil", -14.2350, -51.9253),
        ("Russia", 61.5240, 105.3188),
        ("Germany", 51.1657, 10.4515),
        ("Japan", 36.2048, 138.2529)
    ]
    
    try:
        df = pd.read_csv('sprint3/demos/data/sample_transactions.csv')
        df['timestamp'] = pd.to_datetime(df['timestamp'])
    except FileNotFoundError:
        print("⚠️  Sample data not found, generating minimal dataset...")
        dates = pd.date_range(end=datetime.now(), periods=1000, freq='5min')
        df = pd.DataFrame({
            'timestamp': dates,
            'transaction_id': [f'txn_{i:06d}' for i in range(1000)],
            'is_fraud': np.random.random(1000) < 0.02,
            'price_paid': np.random.uniform(20, 200, 1000),
            'wallet_address': [f'0x{i%100:040x}' for i in range(1000)]
        })
    
    # Add location data
    loc_indices = np.random.choice(len(countries), len(df))
    df['country'] = [countries[i][0] for i in loc_indices]
    df['lat'] = [countries[i][1] for i in loc_indices]
    df['lon'] = [countries[i][2] for i in loc_indices]
    
    return df

df = load_sample_data()

# Purpose: Calculate key performance indicators from recent transaction data.
# Params: df (DataFrame) — transaction data with timestamps.
# Returns: Dictionary with transactions_per_hour, fraud_rate, api_latency, revenue_per_hour.
# Side effects: Filters data to last hour, computes aggregations.
def calculate_kpis(df):
    """Calculate real-time KPIs."""
    recent_df = df[df['timestamp'] > datetime.now() - timedelta(hours=1)]
    
    # Try to fetch from monitoring API
    try:
        response = requests.get(f"{MONITORING_API_URL}/system", timeout=2)
        if response.status_code == 200:
            system_metrics = response.json()
            
            # Also get primary KPIs
            kpi_response = requests.get(f"{MONITORING_API_URL}/kpis", timeout=2)
            primary_kpis = kpi_response.json() if kpi_response.status_code == 200 else {}
            
            api_latency = system_metrics.get('api_latency', {}).get('p95_latency_ms', 45.0)
            conversion_rate = primary_kpis.get('conversion_rate', {}).get('value', 0)
            revenue_per_hour = primary_kpis.get('revenue_per_hour', {}).get('value', 0)
            fraud_rate = primary_kpis.get('fraud_detection_rate', {}).get('value', 0)
            
            return {
                'transactions_per_hour': len(recent_df),
                'fraud_rate': fraud_rate,
                'api_latency': api_latency,
                'revenue_per_hour': revenue_per_hour,
                'conversion_rate': conversion_rate
            }
    except Exception as e:
        print(f"Could not fetch from monitoring API: {e}")
    
    # Fallback to mock data
    kpis = {
        'transactions_per_hour': len(recent_df),
        'fraud_rate': recent_df['is_fraud'].mean() * 100 if len(recent_df) > 0 else 0,
        'api_latency': np.random.uniform(40, 55),  # Mock latency
        'revenue_per_hour': recent_df['price_paid'].sum() if 'price_paid' in recent_df.columns else 0,
        'conversion_rate': 0
    }
    return kpis

def get_blockchain_metrics():
    """Fetch real-time blockchain metrics from Hardhat."""
    try:
        if w3.is_connected():
            block_number = w3.eth.block_number
            gas_price = w3.eth.gas_price / 1e9  # Convert to Gwei
            return {
                'block_number': block_number,
                'gas_price': f"{gas_price:.2f} Gwei",
                'status': "Connected",
                'status_color': "success"
            }
    except Exception as e:
        print(f"Blockchain connection error: {e}")
    
    return {
        'block_number': "N/A",
        'gas_price': "N/A",
        'status': "Disconnected",
        'status_color': "danger"
    }

# Dashboard Layout
app.layout = dbc.Container([
    # Header
    dbc.Row([
        dbc.Col([
            html.Div([
                html.I(className="fas fa-shield-alt fa-2x me-3"),
                html.H2("INTELLIGENCE CENTER V2.0", className="d-inline-block align-middle mb-0", style={'letterSpacing': '2px', 'fontWeight': 'bold'})
            ], className="d-flex align-items-center justify-content-center my-4")
        ])
    ]),
    
    # Filter Bar
    dbc.Card([
        dbc.CardBody([
            dbc.Row([
                dbc.Col([
                    html.Label("🕒 Time Horizon", className="text-muted small mb-1"),
                    dbc.RadioItems(
                        id='time-range-selector',
                        options=[
                            {'label': '1h', 'value': 1},
                            {'label': '6h', 'value': 6},
                            {'label': '24h', 'value': 24},
                            {'label': '7d', 'value': 168},
                        ],
                        value=24,
                        inline=True,
                        className="mt-1"
                    )
                ], width=3),
                dbc.Col([
                    html.Label("🤖 Model Focus", className="text-muted small mb-1"),
                    dcc.Dropdown(
                        id='model-focus-selector',
                        options=[
                            {'label': 'Bot Detection', 'value': 'bot'},
                            {'label': 'Fraud Score', 'value': 'fraud'},
                            {'label': 'Scalping', 'value': 'scalp'},
                        ],
                        value='bot',
                        clearable=False
                    )
                ], width=6),
                dbc.Col([
                    html.Div([
                        html.Span(id='last-sync-time', className="text-muted small me-3"),
                        dbc.Button([html.I(className="fas fa-sync-alt me-2"), "SYNC NOW"], color="dark", size="sm", id="sync-button")
                    ], className="d-flex align-items-center justify-content-end h-100")
                ], width=3)
            ])
        ])
    ], className="mb-4 shadow-sm border-0"),
    
    # KPI Row
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.P("VOLUME", className="text-muted small mb-1"),
                    html.H3(id='kpi-transactions', className="mb-0"),
                    html.P(id='kpi-transactions-delta', className="small mb-0")
                ])
            ], className="border-0 shadow-sm h-100")
        ], width=3),
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.P("FRAUD RATE", className="text-muted small mb-1"),
                    html.H3(id='kpi-fraud-rate', className="text-danger mb-0"),
                    html.P("Target: < 2%", className="text-muted small mb-0")
                ])
            ], className="border-0 shadow-sm h-100")
        ], width=3),
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.P("LATENCY", className="text-muted small mb-1"),
                    html.H3(id='kpi-latency', className="text-warning mb-0"),
                    html.P("Target: < 50ms", className="text-muted small mb-0")
                ])
            ], className="border-0 shadow-sm h-100")
        ], width=3),
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.P("REVENUE", className="text-muted small mb-1"),
                    html.H3(id='kpi-revenue', className="text-success mb-0"),
                    html.P(id='kpi-conversion', className="text-muted small mb-0")
                ])
            ], className="border-0 shadow-sm h-100")
        ], width=3),
    ], className="mb-4"),
    
    # Row 1: Map and Drift
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader([html.I(className="fas fa-globe-americas me-2"), "GLOBAL THREAT MAP"], className="bg-white border-0 font-weight-bold"),
                dbc.CardBody([
                    dcc.Graph(id='threat-map', style={'height': '400px'})
                ])
            ], className="border-0 shadow-sm h-100")
        ], width=8),
        dbc.Col([
            dbc.Card([
                dbc.CardHeader([html.I(className="fas fa-chart-bar me-2"), "MODEL DRIFT MONITOR"], className="bg-white border-0 font-weight-bold"),
                dbc.CardBody([
                    dcc.Graph(id='drift-monitor', style={'height': '400px'})
                ])
            ], className="border-0 shadow-sm h-100")
        ], width=4),
    ], className="mb-4"),
    
    # Row 2: Intelligence Feed and Model Health
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader([html.I(className="fas fa-user-secret me-2"), "FRAUD INTELLIGENCE FEED"], className="bg-white border-0 font-weight-bold"),
                dbc.CardBody([
                    dcc.Graph(id='fraud-timeseries', style={'height': '400px'})
                ])
            ], className="border-0 shadow-sm h-100")
        ], width=8),
        dbc.Col([
            dbc.Card([
                dbc.CardHeader([html.I(className="fas fa-robot me-2"), "MODEL HEALTH"], className="bg-white border-0 font-weight-bold"),
                dbc.CardBody([
                    html.Div(id='model-health-list')
                ])
            ], className="border-0 shadow-sm h-100")
        ], width=4),
    ], className="mb-4"),
    
    # Row 3: Traffic Patterns and MAB
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader([html.I(className="fas fa-chart-line me-2"), "TRAFFIC PATTERNS"], className="bg-white border-0 font-weight-bold"),
                dbc.CardBody([
                    dcc.Graph(id='traffic-chart', style={'height': '300px'})
                ])
            ], className="border-0 shadow-sm h-100")
        ], width=6),
        dbc.Col([
            dbc.Card([
                dbc.CardHeader([html.I(className="fas fa-balance-scale me-2"), "MAB STRATEGY ALLOCATION"], className="bg-white border-0 font-weight-bold"),
                dbc.CardBody([
                    dcc.Graph(id='mab-chart', style={'height': '300px'})
                ])
            ], className="border-0 shadow-sm h-100")
        ], width=6),
    ], className="mb-4"),
    
    # Row 4: SOAR and Alerts
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader([html.I(className="fas fa-bolt me-2"), "SOAR AUTOMATED RESPONSES"], className="bg-white border-0 font-weight-bold"),
                dbc.CardBody([
                    html.Div(id='soar-responses')
                ])
            ], className="border-0 shadow-sm h-100")
        ], width=6),
        dbc.Col([
            dbc.Card([
                dbc.CardHeader([html.I(className="fas fa-exclamation-triangle me-2"), "ACTIVE THREAT ALERTS"], className="bg-white border-0 font-weight-bold"),
                dbc.CardBody([
                    html.Div(id='alerts-table')
                ])
            ], className="border-0 shadow-sm h-100")
        ], width=6),
    ], className="mb-4"),
    
    # Row 5: Audit Table
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader([html.I(className="fas fa-search me-2"), "HIGH-RISK TRANSACTION AUDIT"], className="bg-white border-0 font-weight-bold"),
                dbc.CardBody([
                    html.Div(id='recent-fraud-table')
                ])
            ], className="border-0 shadow-sm")
        ], width=12)
    ], className="mb-4"),
    
    # Row 6: Event Stream and System Health
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader([html.I(className="fas fa-link me-2"), "BLOCKCHAIN EVENT STREAM"], className="bg-white border-0 font-weight-bold"),
                dbc.CardBody([
                    html.Div(id='blockchain-event-stream', style={'height': '200px', 'overflowY': 'scroll'})
                ])
            ], className="border-0 shadow-sm h-100")
        ], width=8),
        dbc.Col([
            dbc.Card([
                dbc.CardHeader([html.I(className="fas fa-desktop me-2"), "SYSTEM HEALTH"], className="bg-white border-0 font-weight-bold"),
                dbc.CardBody([
                    html.Div(id='system-health-bars')
                ])
            ], className="border-0 shadow-sm h-100")
        ], width=4),
    ], className="mb-4"),
    
    # Auto-refresh interval
    dcc.Interval(
        id='interval-component',
        interval=5*1000,  # 5 seconds
        n_intervals=0
    )
], fluid=True)

# Purpose: Update KPI card values based on interval timer trigger.
# Params: n (int) — interval counter from auto-refresh component.
# Returns: Tuple of KPI values.
@app.callback(
    [Output('kpi-transactions', 'children'),
     Output('kpi-fraud-rate', 'children'),
     Output('kpi-latency', 'children'),
     Output('kpi-revenue', 'children'),
     Output('kpi-transactions-delta', 'children'),
     Output('kpi-conversion', 'children'),
     Output('last-sync-time', 'children')],
    [Input('interval-component', 'n_intervals')]
)
def update_kpis(n):
    """Update KPI cards."""
    kpis = calculate_kpis(df)
    
    return (
        f"{kpis['transactions_per_hour']:,}",
        f"{kpis['fraud_rate']:.1f}%",
        f"{kpis['api_latency']:.0f}MS",
        f"${kpis['revenue_per_hour']:,.0f}",
        html.Span([
            html.I(className="fas fa-caret-down me-1"),
            "-5% (1h)"
        ], className="text-danger") if kpis['transactions_per_hour'] < 500 else html.Span([
            html.I(className="fas fa-caret-up me-1"),
            "+12% (1h)"
        ], className="text-success"),
        f"Conversion: {kpis['conversion_rate']:.1f}%",
        f"Last Sync: {datetime.now().strftime('%H:%M:%S')}"
    )

@app.callback(
    Output('threat-map', 'figure'),
    [Input('interval-component', 'n_intervals')]
)
def update_threat_map(n):
    """Update global threat map with real-time fraud data."""
    # Filter for recent high-risk transactions
    recent_fraud = df[df['is_fraud']].tail(20)
    
    if len(recent_fraud) == 0:
        # Fallback to empty map if no fraud
        fig = px.scatter_geo(lat=[0], lon=[0], opacity=0)
    else:
        fig = px.scatter_geo(
            recent_fraud, 
            lat='lat', 
            lon='lon', 
            hover_name='country',
            text='transaction_id',
            color_discrete_sequence=['#ff4d4d'],
            size_max=15
        )
        
        # Add a "pulse" effect by varying size slightly based on interval
        fig.update_traces(marker=dict(size=10 + (n % 5)))
    
    fig.update_layout(
        margin={"r":0,"t":0,"l":0,"b":0},
        geo=dict(
            showframe=False,
            showcoastlines=True,
            projection_type='equirectangular',
            bgcolor='rgba(0,0,0,0)',
            landcolor='#f8f9fa',
            coastlinecolor='#ccc'
        ),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)'
    )
    return fig

@app.callback(
    Output('drift-monitor', 'figure'),
    [Input('interval-component', 'n_intervals')]
)
def update_drift_monitor(n):
    """Update model drift monitor."""
    models = ['RiskScore', 'BotDetect', 'ScalpDetect', 'WashTrade']
    confidence = [0.92, 0.88, 0.85, 0.78]
    drift = [0.05, 0.08, 0.12, 0.25]
    
    fig = go.Figure()
    fig.add_trace(go.Bar(x=models, y=confidence, name='Confidence', marker_color='#007bff'))
    fig.add_trace(go.Scatter(x=models, y=drift, name='Drift', yaxis='y2', line=dict(color='#ff4d4d', width=2)))
    
    fig.update_layout(
        yaxis=dict(title='Confidence', range=[0, 1]),
        yaxis2=dict(title='Drift', overlaying='y', side='right', range=[0, 0.5]),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=40, r=40, t=40, b=40),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)'
    )
    return fig

@app.callback(
    Output('fraud-timeseries', 'figure'),
    [Input('interval-component', 'n_intervals'),
     Input('time-range-selector', 'value')]
)
def update_fraud_chart(n, hours):
    """Update fraud intelligence feed."""
    recent_df = df[df['timestamp'] > datetime.now() - timedelta(hours=hours)]
    
    # Add mock fraud scores
    recent_df = recent_df.copy()
    recent_df['fraud_score'] = np.where(
        recent_df['is_fraud'],
        np.random.uniform(0.7, 0.95, len(recent_df)),
        np.random.uniform(0.05, 0.4, len(recent_df))
    )
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=recent_df['timestamp'],
        y=recent_df['fraud_score'],
        mode='markers',
        marker=dict(
            size=8,
            color=recent_df['fraud_score'],
            colorscale='RdYlGn_r',
            showscale=True,
            colorbar=dict(title="Risk Score", thickness=15)
        )
    ))
    
    fig.update_layout(
        xaxis_title="Time",
        yaxis_title="Risk Score",
        margin=dict(l=40, r=40, t=40, b=40),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)'
    )
    return fig

@app.callback(
    Output('model-health-list', 'children'),
    [Input('interval-component', 'n_intervals')]
)
def update_model_health(n):
    """Update model health list."""
    models = [
        ("Risk Score", "Active", "success"),
        ("Bot Detection", "Active", "success"),
        ("Fair Price", "Training", "info"),
        ("Scalping", "Active", "success"),
        ("Wash Trading", "Active", "success"),
        ("Recommender", "Active", "success"),
        ("Segmentation", "Active", "success"),
        ("Market Trend", "Active", "success"),
        ("Decision Rule", "Active", "success"),
    ]
    
    items = []
    for name, status, color in models:
        items.append(html.Div([
            html.Span(name, className="text-muted"),
            dbc.Badge(status, color=color, className="ms-auto")
        ], className="d-flex align-items-center mb-2 pb-2 border-bottom"))
    
    return items

@app.callback(
    Output('traffic-chart', 'figure'),
    [Input('interval-component', 'n_intervals'),
     Input('time-range-selector', 'value')]
)
def update_traffic_chart(n, hours):
    """Update traffic patterns chart."""
    recent_df = df[df['timestamp'] > datetime.now() - timedelta(hours=hours)]
    hourly = recent_df.groupby(pd.Grouper(key='timestamp', freq='15min')).size().reset_index(name='count')
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=hourly['timestamp'],
        y=hourly['count'],
        mode='lines',
        fill='tozeroy',
        line=dict(color='#007bff', width=3)
    ))
    
    fig.update_layout(
        margin=dict(l=40, r=40, t=40, b=40),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(showgrid=False),
        yaxis=dict(showgrid=True, gridcolor='#eee')
    )
    return fig

@app.callback(
    Output('mab-chart', 'figure'),
    [Input('interval-component', 'n_intervals')]
)
def update_mab_chart(n):
    """Update MAB strategy allocation."""
    strategies = ['RiskScore', 'BotDetect', 'ScalpDetect', 'WashTrade']
    rewards = [0.85, 0.72, 0.65, 0.45]
    colors = ['#007bff', '#6610f2', '#6f42c1', '#e83e8c']
    
    fig = go.Figure(go.Bar(
        x=strategies,
        y=rewards,
        marker_color=colors
    ))
    
    fig.update_layout(
        yaxis_title="Reward Score",
        margin=dict(l=40, r=40, t=40, b=40),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)'
    )
    return fig

@app.callback(
    Output('recent-fraud-table', 'children'),
    [Input('interval-component', 'n_intervals')]
)
def update_fraud_table(n):
    """Update high-risk transaction audit table."""
    recent_fraud = df[df['is_fraud']].tail(5)
    
    table_header = [
        html.Thead(html.Tr([
            html.Th("TIME"),
            html.Th("TXN ID"),
            html.Th("WALLET"),
            html.Th("SCORE"),
            html.Th("DECISION")
        ]), className="bg-light")
    ]
    
    rows = []
    for _, row in recent_fraud.iterrows():
        score = np.random.uniform(0.8, 0.98)
        decision = "BLOCKED" if score > 0.9 else "REVIEW"
        color = "danger" if decision == "BLOCKED" else "warning"
        
        rows.append(html.Tr([
            html.Td(row['timestamp'].strftime('%H:%M:%S')),
            html.Td(row['transaction_id']),
            html.Td(row['wallet_address'][:10] + "...", className="text-info"),
            html.Td(f"{score:.2f}", className="text-danger font-weight-bold"),
            html.Td(dbc.Badge(decision, color=color))
        ]))
    
    return dbc.Table(table_header + [html.Tbody(rows)], borderless=True, hover=True, className="mb-0")

@app.callback(
    Output('blockchain-event-stream', 'children'),
    [Input('interval-component', 'n_intervals')]
)
def update_event_stream(n):
    """Update blockchain event stream."""
    events = [
        ("MINT", "Wallet 0x71c...890 -> Ticket #4521", "info"),
        ("TRANSFER", "Wallet 0x123...abc -> Ticket #1029", "warning"),
        ("BURN", "Wallet 0xabc...123 -> Ticket #0582", "danger"),
        ("MINT", "Wallet 0x456...def -> Ticket #4522", "info"),
        ("TRANSFER", "Wallet 0xdef...456 -> Ticket #1030", "warning"),
    ]
    
    items = []
    for type, msg, color in events:
        items.append(html.Div([
            dbc.Badge(type, color=color, className="me-2"),
            html.Span(msg, className="small text-muted")
        ], className="mb-2"))
    
    return items

@app.callback(
    Output('system-health-bars', 'children'),
    [Input('interval-component', 'n_intervals')]
)
def update_system_health(n):
    """Update system health progress bars."""
    cpu = np.random.uniform(30, 60)
    mem = np.random.uniform(60, 80)
    
    return [
        html.Div([
            html.Div([
                html.Span("CPU Usage", className="small text-muted"),
                html.Span(f"{cpu:.1f}%", className="small font-weight-bold ms-auto")
            ], className="d-flex mb-1"),
            dbc.Progress(value=cpu, color="dark", style={"height": "8px"}, className="mb-3")
        ]),
        html.Div([
            html.Div([
                html.Span("Memory Usage", className="small text-muted"),
                html.Span(f"{mem:.1f}%", className="small font-weight-bold ms-auto")
            ], className="d-flex mb-1"),
            dbc.Progress(value=mem, color="info", style={"height": "8px"})
        ])
    ]

@app.callback(
    Output('alerts-table', 'children'),
    [Input('interval-component', 'n_intervals')]
)
def update_alerts_table(n):
    """Update alerts table."""
    return html.Div([
        html.P("No active threat alerts detected.", className="text-muted small text-center my-4")
    ])

@app.callback(
    Output('soar-responses', 'children'),
    [Input('interval-component', 'n_intervals')]
)
def update_soar_responses(n):
    """Update SOAR responses."""
    return html.Div([
        html.P("Automated responses active and monitoring.", className="text-muted small text-center my-4")
    ])

if __name__ == '__main__':
    import os
    debug_mode = os.getenv('DEBUG', 'false').lower() == 'true'
    app.run_server(debug=debug_mode, host='0.0.0.0', port=8050)
