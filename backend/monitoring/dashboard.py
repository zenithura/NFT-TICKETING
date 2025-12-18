# File header: Interactive Dash web dashboard for real-time fraud detection monitoring.
# Displays KPIs, fraud scores, transaction volume, and model performance metrics.

"""
Interactive Monitoring Dashboard - Demo Version
Real-time fraud detection and system monitoring dashboard.
"""

import dash
from dash import dcc, html, Input, Output, State, ALL
import plotly.graph_objs as go
import plotly.express as px
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import dash_bootstrap_components as dbc
import requests
import json

# Purpose: Initialize Dash web application with LUX (Premium) styling.
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.LUX, dbc.icons.FONT_AWESOME])

# Monitoring API URL
MONITORING_API_URL = "http://localhost:8000/api/v1/metrics"

def load_sample_data():
    """Load sample transaction data with geographic and reputation data."""
    try:
        df = pd.read_csv('sprint3/demos/data/sample_transactions.csv')
        df['timestamp'] = pd.to_datetime(df['timestamp'])
    except FileNotFoundError:
        dates = pd.date_range(end=datetime.now(), periods=1000, freq='5min')
        df = pd.DataFrame({
            'timestamp': dates,
            'transaction_id': [f'txn_{i:06d}' for i in range(1000)],
            'is_fraud': np.random.random(1000) < 0.02,
            'price_paid': np.random.uniform(20, 200, 1000),
            'wallet_address': [f'0x{i%100:040x}' for i in range(1000)],
            'ip_address': [f'192.168.{np.random.randint(1,255)}.{np.random.randint(1,255)}' for _ in range(1000)],
            'country': np.random.choice(['USA', 'UK', 'Germany', 'China', 'Russia', 'Brazil', 'India'], 1000),
            'lat': np.random.uniform(-60, 80, 1000),
            'lon': np.random.uniform(-180, 180, 1000)
        })
    return df

df = load_sample_data()

def calculate_kpis(df, time_range='24h'):
    """Calculate real-time KPIs based on time range."""
    hours = int(time_range.replace('h', '').replace('d', '')) * (24 if 'd' in time_range else 1)
    recent_df = df[df['timestamp'] > datetime.now() - timedelta(hours=hours)]
    
    try:
        response = requests.get(f"{MONITORING_API_URL}/system", timeout=2)
        if response.status_code == 200:
            system_metrics = response.json()
            kpi_response = requests.get(f"{MONITORING_API_URL}/kpis", timeout=2)
            primary_kpis = kpi_response.json() if kpi_response.status_code == 200 else {}
            
            return {
                'transactions_per_hour': len(recent_df),
                'fraud_rate': primary_kpis.get('fraud_detection_rate', {}).get('value', 0),
                'api_latency': system_metrics.get('api_latency', {}).get('p95_latency_ms', 45.0),
                'revenue_per_hour': primary_kpis.get('revenue_per_hour', {}).get('value', 0),
                'conversion_rate': primary_kpis.get('conversion_rate', {}).get('value', 4.2)
            }
    except:
        pass
    
    return {
        'transactions_per_hour': len(recent_df),
        'fraud_rate': recent_df['is_fraud'].mean() * 100 if len(recent_df) > 0 else 0,
        'api_latency': np.random.uniform(40, 55),
        'revenue_per_hour': recent_df['price_paid'].sum() if 'price_paid' in recent_df.columns else 0,
        'conversion_rate': 4.2
    }

# Dashboard Layout
app.layout = dbc.Container([
    dcc.Store(id='theme-store', data='light'),
    # Wallet Reputation Modal
    dbc.Modal([
        dbc.ModalHeader(dbc.ModalTitle("🔍 Wallet Reputation Profile")),
        dbc.ModalBody(id="wallet-modal-content"),
        dbc.ModalFooter(
            dbc.Button("Close", id="close-wallet-modal", className="ms-auto", n_clicks=0)
        ),
    ], id="wallet-modal", size="lg", is_open=False),

    # Header & Interactive Control Panel
    dbc.Row([
        dbc.Col([
            html.H1([html.I(className="fas fa-shield-alt me-3"), "Intelligence Center v2.0"], 
                    className="text-center my-4 text-primary fw-bold"),
        ], width=10),
        dbc.Col([
            html.Div([
                html.I(className="fas fa-sun me-2 text-warning"),
                dbc.Checklist(
                    options=[{"label": "", "value": 1}],
                    value=[],
                    id="theme-toggle",
                    switch=True,
                    inline=True,
                    className="d-inline-block"
                ),
                html.I(className="fas fa-moon ms-2 text-primary"),
            ], className="text-end pt-4")
        ], width=2)
    ]),
    
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    dbc.Row([
                        dbc.Col([
                            html.Label("🕒 Time Horizon", className="text-muted small fw-bold"),
                            dcc.RadioItems(
                                id='time-range-filter',
                                options=[
                                    {'label': ' 1h ', 'value': '1h'},
                                    {'label': ' 6h ', 'value': '6h'},
                                    {'label': ' 24h ', 'value': '24h'},
                                    {'label': ' 7d ', 'value': '7d'},
                                ],
                                value='24h',
                                labelStyle={'display': 'inline-block', 'margin-right': '20px'},
                                className="text-primary"
                            )
                        ], width=4),
                        dbc.Col([
                            html.Label("🤖 Model Focus", className="text-muted small fw-bold"),
                            dcc.Dropdown(
                                id='model-focus-filter',
                                options=[
                                    {'label': 'All Models', 'value': 'ALL'},
                                    {'label': 'Bot Detection', 'value': 'bot'},
                                    {'label': 'Wash Trading', 'value': 'wash'},
                                    {'label': 'Scalping', 'value': 'scalp'},
                                ],
                                value='ALL',
                                className="border-0 shadow-sm"
                            )
                        ], width=4),
                        dbc.Col([
                            html.Div([
                                html.Span(id='last-updated-text', className="text-muted small me-3"),
                                dbc.Button([html.I(className="fas fa-sync-alt me-2"), "Sync Now"], 
                                           id='refresh-btn', color="primary", size="sm", className="px-4 shadow-sm")
                            ], className="text-end pt-4")
                        ], width=4)
                    ])
                ])
            ], className="mb-4 border-0 shadow-lg", style={'borderRadius': '15px'})
        ])
    ]),
    
    # KPI Cards
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H6("Volume", className="card-subtitle text-muted small"),
                    html.H3(id='kpi-transactions', className="text-primary fw-bold"),
                    html.P(id='kpi-transactions-delta', className="small mb-0")
                ])
            ], className="mb-3 border-0 shadow-sm", style={'borderRadius': '10px'})
        ], width=3),
        
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H6("Fraud Rate", className="card-subtitle text-muted small"),
                    html.H3(id='kpi-fraud-rate', className="text-danger fw-bold"),
                    html.P("Target: <2%", className="small text-muted mb-0")
                ])
            ], className="mb-3 border-0 shadow-sm", style={'borderRadius': '10px'})
        ], width=3),
        
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H6("Latency", className="card-subtitle text-muted small"),
                    html.H3(id='kpi-latency', className="text-warning fw-bold"),
                    html.P("Target: <50ms", className="small text-muted mb-0")
                ])
            ], className="mb-3 border-0 shadow-sm", style={'borderRadius': '10px'})
        ], width=3),
        
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H6("Revenue", className="card-subtitle text-muted small"),
                    html.H3(id='kpi-revenue', className="text-success fw-bold"),
                    html.P("Conversion: 4.2%", className="small text-muted mb-0")
                ])
            ], className="mb-3 border-0 shadow-sm", style={'borderRadius': '10px'})
        ], width=3),
    ]),

    # Phase 2: Global Threat Map & Model Drift
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader(html.H5("🌍 Global Threat Map", className="mb-0 fw-bold")),
                dbc.CardBody([
                    dcc.Graph(id='threat-map', config={'displayModeBar': False})
                ])
            ], className="mb-4 border-0 shadow-sm", style={'borderRadius': '15px'})
        ], width=8),
        dbc.Col([
            dbc.Card([
                dbc.CardHeader(html.H5("📉 Model Drift Monitor", className="mb-0 fw-bold")),
                dbc.CardBody([
                    dcc.Graph(id='drift-monitor', config={'displayModeBar': False})
                ])
            ], className="mb-4 border-0 shadow-sm", style={'borderRadius': '15px'})
        ], width=4)
    ]),
    
    # Main Intelligence Row
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader(html.H5("🕵️ Fraud Intelligence Feed", className="mb-0 fw-bold")),
                dbc.CardBody([
                    dcc.Graph(id='fraud-timeseries', config={'displayModeBar': False})
                ])
            ], className="mb-4 border-0 shadow-sm", style={'borderRadius': '15px'})
        ], width=8),
        dbc.Col([
            dbc.Card([
                dbc.CardHeader(html.H5("🤖 Model Health", className="mb-0 fw-bold")),
                dbc.CardBody([
                    html.Div(id='model-health-grid')
                ])
            ], className="mb-4 border-0 shadow-sm", style={'borderRadius': '15px'})
        ], width=4)
    ]),
    
    # Secondary Insights Row
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader(html.H5("📈 Traffic Patterns", className="mb-0 fw-bold")),
                dbc.CardBody([
                    dcc.Graph(id='traffic-chart', config={'displayModeBar': False})
                ])
            ], className="mb-4 border-0 shadow-sm", style={'borderRadius': '15px'})
        ], width=6),
        dbc.Col([
            dbc.Card([
                dbc.CardHeader(html.H5("⚖️ MAB Strategy Allocation", className="mb-0 fw-bold")),
                dbc.CardBody([
                    dcc.Graph(id='mab-chart', config={'displayModeBar': False})
                ])
            ], className="mb-4 border-0 shadow-sm", style={'borderRadius': '15px'})
        ], width=6),
    ]),
    
    # Security & SOAR Row
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader(html.H5("⚡ SOAR Automated Responses", className="mb-0 text-primary fw-bold")),
                dbc.CardBody([
                    html.Div(id='soar-actions-table')
                ])
            ], className="mb-4 border-0 shadow-sm", style={'borderRadius': '15px'})
        ], width=6),
        dbc.Col([
            dbc.Card([
                dbc.CardHeader(html.H5("🚨 Active Threat Alerts", className="mb-0 text-danger fw-bold")),
                dbc.CardBody([
                    html.Div(id='alerts-table')
                ])
            ], className="mb-4 border-0 shadow-sm", style={'borderRadius': '15px'})
        ], width=6),
    ]),
    
    # High-Risk Transaction Table
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader(html.H5("🔍 High-Risk Transaction Audit", className="mb-0 fw-bold")),
                dbc.CardBody([
                    html.Div(id='recent-fraud-table')
                ])
            ], className="mb-4 border-0 shadow-sm", style={'borderRadius': '15px'})
        ], width=12)
    ]),

    # Phase 2: Blockchain Ticker & System Health
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader(html.H5("⛓️ Blockchain Event Stream", className="mb-0 text-info fw-bold")),
                dbc.CardBody([
                    html.Div(id='blockchain-ticker', style={'height': '150px', 'overflowY': 'scroll'})
                ])
            ], className="mb-4 border-0 shadow-sm", style={'borderRadius': '15px'})
        ], width=8),
        dbc.Col([
            dbc.Card([
                dbc.CardHeader(html.H5("🖥️ System Health", className="mb-0 fw-bold")),
                dbc.CardBody([
                    html.Div(id='system-resource-monitor')
                ])
            ], className="mb-4 border-0 shadow-sm", style={'borderRadius': '15px'})
        ], width=4),
    ]),
    
    # Auto-refresh interval
    dcc.Interval(
        id='interval-component',
        interval=5*1000,  # 5 seconds
        n_intervals=0
    )
], fluid=True, style={'backgroundColor': '#f8f9fa', 'minHeight': '100vh', 'padding': '20px'})

# Theme Toggle Callback
app.clientside_callback(
    """
    function(toggle_value) {
        const theme = toggle_value.length > 0 ? 'dark' : 'light';
        if (theme === 'dark') {
            document.body.classList.add('dark-mode');
        } else {
            document.body.classList.remove('dark-mode');
        }
        return theme;
    }
    """,
    Output('theme-store', 'data'),
    Input('theme-toggle', 'value')
)

# Purpose: Update KPI card values based on interval timer trigger.
# Params: n (int) — interval counter from auto-refresh component.
# Returns: Tuple of KPI values (transactions, fraud rate, latency, revenue, delta).
# Side effects: Recalculates KPIs from data, formats for display.
@app.callback(
    [Output('kpi-transactions', 'children'),
     Output('kpi-fraud-rate', 'children'),
     Output('kpi-latency', 'children'),
     Output('kpi-revenue', 'children'),
     Output('kpi-transactions-delta', 'children'),
     Output('last-updated-text', 'children')],
    [Input('interval-component', 'n_intervals'),
     Input('time-range-filter', 'value'),
     Input('refresh-btn', 'n_clicks')]
)
def update_kpis(n, time_range, n_clicks):
    """Update KPI cards with real-time data."""
    kpis = calculate_kpis(df, time_range)
    
    delta = "▲ +12% (1h)" if kpis['transactions_per_hour'] > 1000 else "▼ -5% (1h)"
    delta_color = "text-success" if "▲" in delta else "text-danger"
    
    return (
        f"{kpis['transactions_per_hour']:,}",
        f"{kpis['fraud_rate']:.1f}%",
        f"{kpis['api_latency']:.0f}ms",
        f"${kpis['revenue_per_hour']:,.0f}",
        html.Span(delta, className=delta_color),
        f"Last Sync: {datetime.now().strftime('%H:%M:%S')}"
    )

@app.callback(
    Output('threat-map', 'figure'),
    [Input('interval-component', 'n_intervals'),
     Input('time-range-filter', 'value'),
     Input('theme-store', 'data')]
)
def update_threat_map(n, time_range, theme):
    """Update global threat heatmap."""
    hours = int(time_range.replace('h', '').replace('d', '')) * (24 if 'd' in time_range else 1)
    recent_df = df[df['timestamp'] > datetime.now() - timedelta(hours=hours)]
    fraud_df = recent_df[recent_df['is_fraud']]
    
    fig = go.Figure(go.Scattergeo(
        lat=fraud_df['lat'],
        lon=fraud_df['lon'],
        mode='markers',
        marker=dict(
            size=12,
            color='red',
            opacity=0.6,
            symbol='circle',
            line=dict(width=1, color='white')
        ),
        text=[f"Country: {c}<br>IP: {ip}" for c, ip in zip(fraud_df['country'], fraud_df['ip_address'])],
        hovertemplate='%{text}<extra></extra>'
    ))
    
    fig.update_layout(
        geo=dict(
            scope='world',
            projection_type='natural earth',
            showland=True,
            landcolor='#2d2d2d' if theme == 'dark' else 'rgb(243, 243, 243)',
            countrycolor='#444444' if theme == 'dark' else 'rgb(204, 204, 204)',
            showocean=True,
            oceancolor='#1a1a1a' if theme == 'dark' else 'rgb(230, 240, 250)',
            bgcolor='rgba(0,0,0,0)'
        ),
        margin=dict(l=0, r=0, t=0, b=0),
        height=400,
        template="plotly_dark" if theme == 'dark' else "plotly_white",
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)'
    )
    return fig

@app.callback(
    Output('drift-monitor', 'figure'),
    [Input('interval-component', 'n_intervals'),
     Input('theme-store', 'data')]
)
def update_drift_monitor(n, theme):
    """Update model drift and confidence chart."""
    models = ['RiskScore', 'BotDetect', 'ScalpDetect', 'WashTrade']
    confidence = [0.92, 0.88, 0.85, 0.78]
    drift = [0.02, 0.05, 0.08, 0.15] # Mock drift percentage
    
    fig = go.Figure()
    fig.add_trace(go.Bar(name='Confidence', x=models, y=confidence, marker_color='#0d6efd'))
    fig.add_trace(go.Scatter(name='Drift', x=models, y=drift, yaxis='y2', mode='lines+markers', line=dict(color='#dc3545')))
    
    fig.update_layout(
        template="plotly_dark" if theme == 'dark' else "plotly_white",
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=10, r=40, t=30, b=10),
        yaxis=dict(title="Confidence", range=[0, 1]),
        yaxis2=dict(title="Drift", overlaying='y', side='right', range=[0, 0.5]),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        height=400
    )
    return fig

@app.callback(
    Output('fraud-timeseries', 'figure'),
    [Input('interval-component', 'n_intervals'),
     Input('time-range-filter', 'value'),
     Input('model-focus-filter', 'value'),
     Input('theme-store', 'data')]
)
def update_fraud_chart(n, time_range, model_focus, theme):
    """Update fraud detection intelligence feed."""
    hours = int(time_range.replace('h', '').replace('d', '')) * (24 if 'd' in time_range else 1)
    recent_df = df[df['timestamp'] > datetime.now() - timedelta(hours=hours)]
    
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
            size=10,
            color=recent_df['fraud_score'],
            colorscale='RdYlGn_r',
            showscale=True,
            colorbar=dict(title="Risk Score", thickness=15)
        ),
        text=[f"Txn: {tid[:8]}<br>Score: {score:.2f}" 
              for tid, score in zip(recent_df['transaction_id'], recent_df['fraud_score'])],
        hovertemplate='%{text}<extra></extra>'
    ))
    
    fig.update_layout(
        template="plotly_dark" if theme == 'dark' else "plotly_white",
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=10, r=10, t=10, b=10),
        xaxis=dict(showgrid=False),
        yaxis=dict(showgrid=True, gridcolor='#444' if theme == 'dark' else '#eee'),
        height=350
    )
    return fig

@app.callback(
    Output('traffic-chart', 'figure'),
    [Input('interval-component', 'n_intervals'),
     Input('time-range-filter', 'value'),
     Input('theme-store', 'data')]
)
def update_traffic_chart(n, time_range, theme):
    """Update traffic patterns chart."""
    hours = int(time_range.replace('h', '').replace('d', '')) * (24 if 'd' in time_range else 1)
    recent_df = df[df['timestamp'] > datetime.now() - timedelta(hours=hours)]
    
    freq = '5min' if hours <= 1 else '15min' if hours <= 6 else '1h'
    hourly = recent_df.groupby(pd.Grouper(key='timestamp', freq=freq)).size().reset_index(name='count')
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=hourly['timestamp'],
        y=hourly['count'],
        mode='lines',
        fill='tozeroy',
        line=dict(color='#0d6efd', width=3),
        fillcolor='rgba(13, 110, 253, 0.1)'
    ))
    
    fig.update_layout(
        template="plotly_dark" if theme == 'dark' else "plotly_white",
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=10, r=10, t=10, b=10),
        xaxis=dict(showgrid=False),
        yaxis=dict(showgrid=True, gridcolor='#444' if theme == 'dark' else '#eee'),
        height=250
    )
    return fig

@app.callback(
    Output('mab-chart', 'figure'),
    [Input('interval-component', 'n_intervals'),
     Input('theme-store', 'data')]
)
def update_mab_chart(n, theme):
    """Update MAB performance chart."""
    heuristics = ['RiskScore', 'BotDetect', 'ScalpDetect', 'WashTrade']
    rewards = [0.85, 0.72, 0.65, 0.45]
    
    fig = go.Figure(go.Bar(
        x=heuristics,
        y=rewards,
        marker_color=['#0d6efd', '#6610f2', '#6f42c1', '#d63384'],
        opacity=0.8
    ))
    
    fig.update_layout(
        template="plotly_dark" if theme == 'dark' else "plotly_white",
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=10, r=10, t=30, b=10),
        yaxis=dict(title="Reward Score", range=[0, 1]),
        height=250
    )
    return fig

@app.callback(
    Output('model-health-grid', 'children'),
    [Input('interval-component', 'n_intervals')]
)
def update_model_health(n):
    """Update model health grid."""
    models = [
        ('Risk Score', 'Active', 'success'),
        ('Bot Detection', 'Active', 'success'),
        ('Fair Price', 'Training', 'info'),
        ('Scalping', 'Active', 'success'),
        ('Wash Trading', 'Active', 'success'),
        ('Recommender', 'Active', 'success'),
        ('Segmentation', 'Active', 'success'),
        ('Market Trend', 'Active', 'success'),
        ('Decision Rule', 'Active', 'success')
    ]
    
    items = []
    for name, status, color in models:
        items.append(html.Div([
            html.Span(name, className="small fw-bold"),
            dbc.Badge(status, color=color, className="float-end", pill=True)
        ], className="mb-2 pb-2 border-bottom"))
    
    return html.Div(items)

@app.callback(
    Output('blockchain-ticker', 'children'),
    [Input('interval-component', 'n_intervals')]
)
def update_blockchain_ticker(n):
    """Update live blockchain event stream."""
    events = [
        ('MINT', '0x71C...890', 'Ticket #4521'),
        ('TRANSFER', '0x123...abc', 'Ticket #1029'),
        ('BURN', '0xabc...123', 'Ticket #0582'),
        ('MINT', '0x456...def', 'Ticket #4522'),
        ('TRANSFER', '0xdef...456', 'Ticket #1030')
    ]
    
    items = []
    for action, wallet, details in events:
        color = "info" if action == 'MINT' else "warning" if action == 'TRANSFER' else "danger"
        items.append(html.Div([
            dbc.Badge(action, color=color, className="me-2"),
            html.Span(f"Wallet {wallet} -> {details}", className="small text-muted")
        ], className="mb-1 border-bottom pb-1"))
    
    return html.Div(items)

@app.callback(
    Output('system-resource-monitor', 'children'),
    [Input('interval-component', 'n_intervals')]
)
def update_system_resources(n):
    """Update system resource usage monitor."""
    cpu = np.random.uniform(20, 60)
    mem = np.random.uniform(40, 80)
    
    return html.Div([
        html.Div([
            html.Span("CPU Usage", className="small text-muted"),
            dbc.Progress(value=cpu, color="primary", className="mb-2", style={"height": "10px"}),
            html.Span(f"{cpu:.1f}%", className="small fw-bold float-end", style={"marginTop": "-25px"})
        ]),
        html.Div([
            html.Span("Memory Usage", className="small text-muted"),
            dbc.Progress(value=mem, color="info", className="mb-2", style={"height": "10px"}),
            html.Span(f"{mem:.1f}%", className="small fw-bold float-end", style={"marginTop": "-25px"})
        ])
    ])

@app.callback(
    Output('recent-fraud-table', 'children'),
    [Input('interval-component', 'n_intervals')]
)
def update_fraud_table(n):
    """Update recent high-risk transactions table with clickable wallets."""
    recent_fraud = df[df['is_fraud']].tail(5)
    
    rows = []
    for _, row in recent_fraud.iterrows():
        score = np.random.uniform(0.7, 0.95)
        rows.append(html.Tr([
            html.Td(row['timestamp'].strftime('%H:%M:%S'), className="text-muted"),
            html.Td(row['transaction_id'][:12], className="text-primary fw-bold"),
            html.Td(html.A(row['wallet_address'][:10] + '...', id={'type': 'wallet-link', 'index': row['wallet_address']}, href="#", className="text-info")),
            html.Td(f"{score:.2f}", className="text-danger fw-bold"),
            html.Td(dbc.Badge("BLOCKED", color="danger") if score > 0.85 else dbc.Badge("REVIEW", color="warning"))
        ]))
    
    return dbc.Table([
        html.Thead(html.Tr([html.Th("Time"), html.Th("Txn ID"), html.Th("Wallet"), html.Th("Score"), html.Th("Decision")])),
        html.Tbody(rows)
    ], borderless=True, hover=True, size='sm')

# Wallet Modal Callbacks
@app.callback(
    [Output("wallet-modal", "is_open"),
     Output("wallet-modal-content", "children")],
    [Input({'type': 'wallet-link', 'index': ALL}, 'n_clicks'),
     Input("close-wallet-modal", "n_clicks")],
    [State("wallet-modal", "is_open"),
     State('theme-store', 'data')]
)
def toggle_wallet_modal(n_clicks_list, close_clicks, is_open, theme):
    ctx = dash.callback_context
    if not ctx.triggered:
        return is_open, ""
    
    trigger_id = ctx.triggered[0]['prop_id']
    
    if "close-wallet-modal" in trigger_id:
        return False, ""
    
    if any(n_clicks_list):
        # Extract wallet address from trigger_id
        import json
        wallet_addr = json.loads(trigger_id.split('.')[0])['index']
        
        # Generate mock reputation data
        content = html.Div([
            dbc.Row([
                dbc.Col([
                    html.H6("Wallet Address", className="small"),
                    html.P(wallet_addr, className="fw-bold text-primary")
                ], width=12)
            ]),
            dbc.Row([
                dbc.Col([
                    html.Div([
                        html.H6("Risk Profile", className="small"),
                        html.H4("HIGH RISK", className="text-danger fw-bold"),
                        html.P("Flagged for: Potential Bot Activity", className="small")
                    ], className="p-3 bg-light rounded mb-3" if theme == 'light' else "p-3 bg-dark rounded mb-3 border border-secondary")
                ], width=6),
                dbc.Col([
                    html.Div([
                        html.H6("Transaction History", className="small"),
                        html.P("Total Txns: 142", className="mb-0"),
                        html.P("Success Rate: 98%", className="mb-0"),
                        html.P("Fraudulent: 12", className="text-danger")
                    ], className="p-3 bg-light rounded mb-3" if theme == 'light' else "p-3 bg-dark rounded mb-3 border border-secondary")
                ], width=6)
            ]),
            html.H6("Historical Risk Trend", className="small mt-3"),
            dcc.Graph(
                figure=go.Figure(go.Scatter(
                    y=[0.1, 0.15, 0.4, 0.85, 0.92],
                    x=['Jan', 'Feb', 'Mar', 'Apr', 'May'],
                    mode='lines+markers',
                    line=dict(color='#dc3545', width=3)
                )).update_layout(
                    height=200, 
                    margin=dict(l=20, r=20, t=20, b=20), 
                    template="plotly_dark" if theme == 'dark' else "plotly_white",
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)'
                )
            )
        ])
        return True, content
    
    return is_open, ""

if __name__ == '__main__':
    print("\n" + "🚀 Intelligence Center v2.0 starting on http://localhost:8050".center(60))
    app.run_server(debug=False, host='0.0.0.0', port=8050)
