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

from web3 import Web3

# Purpose: Initialize Dash web application with Bootstrap styling.
# Side effects: Creates Flask app instance, configures Dash.
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

# Monitoring API URL
MONITORING_API_URL = "http://localhost:8000/api/v1/metrics"

def load_sample_data():
    """Load sample transaction data for dashboard."""
    try:
        df = pd.read_csv('sprint3/demos/data/sample_transactions.csv')
        df['timestamp'] = pd.to_datetime(df['timestamp'])
    except FileNotFoundError:
        # Generate minimal sample data if file doesn't exist
        print("⚠️  Sample data not found, generating minimal dataset...")
        dates = pd.date_range(end=datetime.now(), periods=1000, freq='5min')
        df = pd.DataFrame({
            'timestamp': dates,
            'transaction_id': [f'txn_{i:06d}' for i in range(1000)],
            'is_fraud': np.random.random(1000) < 0.02,
            'price_paid': np.random.uniform(20, 200, 1000),
            'wallet_address': [f'0x{i%100:040x}' for i in range(1000)]
        })

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
            html.H1("🎫 NFT Ticketing - Monitoring Dashboard", className="text-center my-4"),
            html.P(f"Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}", 
                   className="text-center text-muted")
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
    
    # Alerts Section
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.Div(id='recent-fraud-table')
                ])
            ])
        ])
    ], className="mb-3"),
    
    # System KPIs Section
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H5("📈 System KPIs", className="card-title"),
                    html.Div(id='system-kpis')
                ])
            ])
        ], width=6),
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H5("🔍 SIEM Findings", className="card-title"),
                    html.Div(id='siem-findings')
                ])
            ])
        ], width=6)
    ], className="mb-3"),
    
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
# Returns: Tuple of KPI values.
@app.callback(
    [Output('kpi-transactions', 'children'),
     Output('kpi-fraud-rate', 'children'),
     Output('kpi-latency', 'children'),
     Output('kpi-revenue', 'children'),
     Output('kpi-transactions-delta', 'children')],
    [Input('interval-component', 'n_intervals')]
)
def update_kpis(n, time_range, n_clicks):
    """Update KPI cards with real-time data."""
    kpis = calculate_kpis(df, time_range)
    
    delta = "▲ +12% (1h)" if kpis['transactions_per_hour'] > 1000 else "▼ -5% (1h)"
    delta_color = "text-success" if "▲" in delta else "text-danger"
    
    return (
        f"{kpis['transactions_per_hour']:,}",
        f"{kpis['fraud_rate']:.1f}%",
        f"{kpis['api_latency']:.0f}MS",
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
        mode='lines',
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

# Wallet Modal Callbacks
@app.callback(
    Output('alerts-table', 'children'),
    [Input('interval-component', 'n_intervals')]
)
def update_alerts_table(n):
    """Update alerts table."""
    try:
        # Try to fetch alerts from monitoring API
        response = requests.get("http://localhost:5002/api/v1/alerts", timeout=2)
        if response.status_code == 200:
            alerts = response.json()
            if alerts:
                table_header = [
                    html.Thead(html.Tr([
                        html.Th("Time"),
                        html.Th("Alert"),
                        html.Th("Severity"),
                        html.Th("Message")
                    ]))
                ]
                rows = []
                for alert in alerts[:10]:  # Last 10 alerts
                    severity_color = {
                        'CRITICAL': 'danger',
                        'HIGH': 'danger',
                        'MEDIUM': 'warning',
                        'LOW': 'info'
                    }.get(alert.get('severity', 'LOW'), 'secondary')
                    
                    rows.append(html.Tr([
                        html.Td(alert.get('created_at', '')[:19] if alert.get('created_at') else ''),
                        html.Td(alert.get('name', '')),
                        html.Td(
                            html.Span(alert.get('severity', 'LOW'), 
                                    className=f"badge bg-{severity_color}")
                        ),
                        html.Td(alert.get('message', ''))
                    ]))
                
                table_body = [html.Tbody(rows)]
                return dbc.Table(table_header + table_body, bordered=True, hover=True, size='sm')
            else:
                return html.P("No active alerts", className="text-success")
        else:
            return html.P("Unable to fetch alerts", className="text-muted")
    except Exception as e:
        return html.P(f"Error: {str(e)}", className="text-danger")

@app.callback(
    Output('system-kpis', 'children'),
    [Input('interval-component', 'n_intervals')]
)
def update_system_kpis(n):
    """Update system KPIs."""
    try:
        response = requests.get(f"{MONITORING_API_URL}/system", timeout=2)
        if response.status_code == 200:
            metrics = response.json()
            
            kpi_items = []
            for metric_name, metric_data in metrics.items():
                if isinstance(metric_data, dict) and 'kpi_name' in metric_data:
                    kpi_items.append(html.Div([
                        html.Strong(f"{metric_name.replace('_', ' ').title()}: "),
                        html.Span(str(metric_data.get('value', metric_data.get('avg_lag_seconds', 'N/A'))))
                    ], className="mb-2"))
            
            return html.Div(kpi_items) if kpi_items else html.P("No metrics available", className="text-muted")
        else:
            return html.P("Unable to fetch system KPIs", className="text-muted")
    except Exception as e:
        return html.P(f"Error: {str(e)}", className="text-danger")

@app.callback(
    Output('siem-findings', 'children'),
    [Input('interval-component', 'n_intervals')]
)
def update_siem_findings(n):
    """Update SIEM findings."""
    try:
        # This would connect to SIEM API when available
        return html.P("SIEM integration coming soon", className="text-muted")
    except Exception as e:
        return html.P(f"Error: {str(e)}", className="text-danger")

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
    
    # Purpose: Determine debug mode from environment variable (default: False for production).
    # Side effects: Reads DEBUG environment variable.
    import os
    debug_mode = os.getenv('DEBUG', 'false').lower() == 'true'
    
    # Purpose: Start Dash server with environment-based debug configuration.
    # Side effects: Starts HTTP server, enables debug mode only if DEBUG=true.
    app.run_server(debug=debug_mode, host='0.0.0.0', port=8050)
