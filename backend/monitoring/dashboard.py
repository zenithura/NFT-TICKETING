"""
Premium Monitoring Dashboard - Intelligence Center v2.0
Real-time fraud detection, system monitoring, and blockchain analytics.
"""

import os
import sys
import dash
from dash import dcc, html, Input, Output, State, ALL, no_update
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import dash_bootstrap_components as dbc
import requests
import json
import psutil
import platform
import socket
from web3 import Web3   
from typing import Dict, List, Optional, Tuple, Union
from collections import defaultdict
import time
import logging
from functools import lru_cache

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('dashboard.log')
    ]
)
logger = logging.getLogger(__name__)

# Constants
REFRESH_INTERVAL = 5000  # 5 seconds
HISTORY_WINDOW = 24 * 60 * 60  # 24 hours in seconds
CACHE_TTL = 60  # Cache TTL in seconds

# Add parent directory to sys.path to import local modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from database import get_supabase_admin
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False
    print("Warning: Supabase client not available")

# Initialize Dash app with enhanced configuration
app = dash.Dash(
    __name__,
    external_stylesheets=[
        dbc.themes.BOOTSTRAP,
        "https://use.fontawesome.com/releases/v5.15.4/css/all.css",
        "https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap",
        {
            'href': 'https://cdn.jsdelivr.net/npm/bootstrap-icons@1.8.1/font/bootstrap-icons.css',
            'rel': 'stylesheet'
        }
    ],
    external_scripts=[
        {
            'src': 'https://cdn.jsdelivr.net/npm/chart.js@3.7.0/dist/chart.min.js',
            'integrity': 'sha512-TW5s0IT/I+JdJ8JkM1G1Xh6k3V4XE+3lR9l2Q5z8v5k1q5q5k5Q1d1Yw5Uw5Q5V5Q5V5Q5V5Q5V5Q5V5Q5V5Q5',
            'crossorigin': 'anonymous',
            'async': True
        }
    ],
    assets_folder='assets',
    meta_tags=[
        {"name": "viewport", "content": "width=device-width, initial-scale=1, shrink-to-fit=no"},
        {"http-equiv": "X-UA-Compatible", "content": "IE=edge"},
        {"name": "description", "content": "Real-time NFT Ticketing Dashboard"},
        {"name": "theme-color", "content": "#1a1a2e"},
        {"name": "apple-mobile-web-app-capable", "content": "yes"},
        {"name": "apple-mobile-web-app-status-bar-style", "content": "black-translucent"}
    ],
    suppress_callback_exceptions=True,
    update_title='Loading...',
    title='NFT Ticketing Dashboard',
    assets_ignore='.*\.(map|LICENSE|_)\.*',
    compress=True,
    prevent_initial_callbacks=True
)

# Configure server
server = app.server
server.secret_key = os.environ.get('SECRET_KEY', os.urandom(24))

# Configuration
w3 = Web3(Web3.HTTPProvider(os.getenv('RPC_URL', 'http://localhost:8545')))

def get_real_data(table_name, limit=100):
    """Fetch real data from Supabase."""
    if not SUPABASE_AVAILABLE:
        return None
    try:
        db = get_supabase_admin()
        response = db.table(table_name).select("*").order("created_at", desc=True).limit(limit).execute()
        return pd.DataFrame(response.data) if response.data else None
    except Exception as e:
        print(f"Error fetching from {table_name}: {e}")
        return None

@lru_cache(maxsize=32)
def get_system_metrics() -> Dict[str, float]:
    """Collect system-level metrics."""
    try:
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        return {
            'cpu_percent': cpu_percent,
            'memory_percent': memory.percent,
            'disk_percent': disk.percent,
            'network_sent': psutil.net_io_counters().bytes_sent,
            'network_recv': psutil.net_io_counters().bytes_recv,
            'boot_time': psutil.boot_time(),
            'process_count': len(psutil.pids())
        }
    except Exception as e:
        logger.error(f"Error getting system metrics: {e}")
        return {}

def calculate_kpis() -> Dict[str, Union[int, float]]:
    """Calculate real-time KPIs from Supabase with enhanced metrics."""
    kpis = {
        'transactions_per_hour': 0,
        'fraud_rate': 0.0,
        'api_latency': 0,
        'revenue_per_hour': 0.0,
        'active_users': 0,
        'success_rate': 100.0,
        'avg_ticket_price': 0.0,
        'peak_tps': 0,
        'block_height': 0,
        'gas_price': 0,
        'pending_txs': 0,
        **get_system_metrics()
    }
    
    if not SUPABASE_AVAILABLE:
        logger.warning("Supabase not available, using mock data")
        return {
            **kpis,
            'transactions_per_hour': 124,
            'fraud_rate': 1.2,
            'api_latency': 38,
            'revenue_per_hour': 1250.0,
            'active_users': 850,
            'success_rate': 99.8,
            'avg_ticket_price': 0.05,
            'peak_tps': 42,
            'block_height': 15000000,
            'gas_price': 15.7,
            'pending_txs': 123
        }
    
    try:
        db = get_supabase_admin()
        now = datetime.utcnow()
        one_hour_ago = (now - timedelta(hours=1)).isoformat()
        
        # Batch database queries
        with db.client.session() as session:
            # Get transactions and revenue
            orders = session.table("orders")\
                .select("total_amount,created_at,status")\
                .gte("created_at", one_hour_ago)\
                .execute()
                
            # Get bot detections
            bots = session.table("bot_detection")\
                .select("risk_score,detected_at")\
                .gte("detected_at", one_hour_ago)\
                .execute()
                
            # Get web requests for latency and success rate
            web_requests = session.table("web_requests")\
                .select("response_time_ms,status_code,created_at")\
                .order("created_at", desc=True)\
                .limit(1000)\
                .execute()
                
            # Get active users (last 24h)
            active_users = session.rpc('count_recent_users', {'hours': 24}).execute()
        
        # Process transactions
        if orders.data:
            successful_orders = [o for o in orders.data if o.get('status') == 'completed']
            kpis['transactions_per_hour'] = len(successful_orders)
            kpis['revenue_per_hour'] = sum(float(o.get('total_amount', 0)) for o in successful_orders)
            kpis['avg_ticket_price'] = kpis['revenue_per_hour'] / len(successful_orders) if successful_orders else 0
            
            # Calculate TPS (transactions per second) peak in the last hour
            if successful_orders:
                timestamps = [pd.to_datetime(o['created_at']) for o in successful_orders]
                if timestamps:
                    time_diffs = [(timestamps[i+1] - timestamps[i]).total_seconds() for i in range(len(timestamps)-1)]
                    if time_diffs:
                        kpis['peak_tps'] = int(1 / min(time_diffs)) if min(time_diffs) > 0 else 0
        
        # Process bot detections
        if bots.data:
            total_actions = kpis['transactions_per_hour'] + len(bots.data)
            if total_actions > 0:
                kpis['fraud_rate'] = (len(bots.data) / total_actions) * 100
        
        # Process web requests
        if web_requests.data:
            latencies = [r['response_time_ms'] for r in web_requests.data if 'response_time_ms' in r]
            if latencies:
                kpis['api_latency'] = int(np.percentile(latencies, 95))
                
            # Calculate success rate
            total_requests = len(web_requests.data)
            if total_requests > 0:
                successful_requests = sum(1 for r in web_requests.data if 200 <= r.get('status_code', 0) < 400)
                kpis['success_rate'] = (successful_requests / total_requests) * 100
        
        # Get active users
        if hasattr(active_users, 'data') and active_users.data:
            kpis['active_users'] = active_users.data[0].get('count', 0) if active_users.data else 0
        
        # Get blockchain data
        try:
            if w3.is_connected():
                kpis['block_height'] = w3.eth.block_number
                kpis['gas_price'] = float(w3.from_wei(w3.eth.gas_price, 'gwei'))
                kpis['pending_txs'] = len(w3.eth.get_block('pending', full_transactions=True).transactions)
        except Exception as e:
            logger.warning(f"Could not fetch blockchain data: {e}")
        
        logger.info(f"Calculated KPIs: {kpis}")
        return kpis
        
    except Exception as e:
        logger.error(f"Error calculating KPIs: {e}", exc_info=True)
        # Return partial data if available
        return {k: v for k, v in kpis.items() if v is not None}
        
    return kpis

# Dashboard Layout
app.layout = html.Div([
    dcc.Store(id='theme-store', data='dark'),
    
    dbc.Container([
        # Header
        dbc.Row([
            dbc.Col([
                html.Div([
                    html.H1([
                        html.I(className="fas fa-shield-alt me-3", style={'color': '#38bdf8'}),
                        "Intelligence Center ",
                        html.Span("v2.0", style={'fontSize': '1.5rem', 'opacity': '0.7'})
                    ], className="my-4 fw-bold", style={'letterSpacing': '1px'}),
                ], className="d-flex align-items-center")
            ], width=8),
            dbc.Col([
                html.Div([
                    html.Div(id="blockchain-status", className="me-4"),
                    dbc.Button([
                        html.I(className="fas fa-moon me-2"), "Dark Mode"
                    ], id="theme-toggle", color="outline-info", size="sm", className="rounded-pill")
                ], className="d-flex align-items-center justify-content-end h-100")
            ], width=4)
        ], className="mb-4"),

        # KPI Cards
        dbc.Row([
            # Transactions Card
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.Div([
                            html.Div([
                                html.Span("Total Transactions", className="text-uppercase small text-muted"),
                                html.Div([
                                    html.Span("1h", className="badge bg-primary-soft ms-2"),
                                    html.Span(id="tx-trend-arrow", className="ms-2")
                                ], className="d-flex align-items-center")
                            ], className="d-flex justify-content-between align-items-center mb-2"),
                            html.H3(id="kpi-tx-count", className="mb-0"),
                            html.Div([
                                html.Small(id="tx-trend-text", className="text-muted"),
                                html.Small(" vs previous hour", className="text-muted")
                            ], className="d-flex align-items-center")
                        ])
                    ])
                ], className="h-100 border-0 shadow-sm")
            ], md=3, className="mb-4"),
            
            # Fraud Detection Card
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.Div([
                            html.Div([
                                html.Span("Fraud Rate", className="text-uppercase small text-muted"),
                                dbc.Badge("Real-time", color="danger", className="ms-2")
                            ], className="d-flex justify-content-between align-items-center mb-2"),
                            html.H3(id="kpi-fraud-rate", className="mb-0"),
                            html.Div([
                                dbc.Progress(
                                    id="fraud-progress",
                                    value=0,
                                    max=100,
                                    color="danger",
                                    className="my-2"
                                ),
                                html.Small("Target: ", className="text-muted"),
                                html.Span("< 2.0%", className="text-danger fw-bold")
                            ])
                        ])
                    ])
                ], className="h-100 border-0 shadow-sm")
            ], md=3, className="mb-4"),
            
            # System Health Card
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.Div([
                            html.Div([
                                html.Span("System Health", className="text-uppercase small text-muted"),
                                html.Span(id="system-status-badge", className="badge bg-success")
                            ], className="d-flex justify-content-between align-items-center mb-2"),
                            html.Div([
                                html.Div([
                                    html.Small("CPU:", className="text-muted"),
                                    html.Span(id="cpu-usage", className="ms-2 fw-bold"),
                                    html.Div(
                                        dbc.Progress(
                                            id="cpu-progress",
                                            value=0,
                                            max=100,
                                            color="primary",
                                            className="my-1"
                                        )
                                    )
                                ], className="mb-2"),
                                html.Div([
                                    html.Small("Memory:", className="text-muted"),
                                    html.Span(id="memory-usage", className="ms-2 fw-bold"),
                                    html.Div(
                                        dbc.Progress(
                                            id="memory-progress",
                                            value=0,
                                            max=100,
                                            color="info",
                                            className="my-1"
                                        )
                                    )
                                ])
                            ])
                        ])
                    ])
                ], className="h-100 border-0 shadow-sm")
            ], md=3, className="mb-4"),
            
            # Blockchain Status Card
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.Div([
                            html.Div([
                                html.Span("Blockchain", className="text-uppercase small text-muted"),
                                html.Span(id="blockchain-status-badge", className="badge bg-success")
                            ], className="d-flex justify-content-between align-items-center mb-2"),
                            html.Div([
                                html.Div([
                                    html.Small("Block:", className="text-muted"),
                                    html.Span(id="block-height", className="ms-2 font-monospace"),
                                    html.Small("Gas:", className="text-muted ms-3"),
                                    html.Span(id="gas-price", className="ms-2 font-monospace")
                                ], className="mb-2"),
                                html.Div([
                                    html.Small("Pending TXs:", className="text-muted"),
                                    html.Span(id="pending-txs", className="ms-2 font-monospace"),
                                    html.Small("Peak TPS:", className="text-muted ms-3"),
                                    html.Span(id="peak-tps", className="ms-2 font-monospace")
                                ])
                            ])
                        ])
                    ])
                ], className="h-100 border-0 shadow-sm")
            ], md=3, className="mb-4"),
        ], className="mb-4"),

        # Main Charts
        dbc.Row([
            dbc.Col([
                html.Div([
                    html.Div([
                        html.H5("Fraud Score Distribution", className="mb-0"),
                        dbc.Badge("Real-time", color="danger", className="ms-2 status-badge")
                    ], className="d-flex align-items-center mb-4"),
                    dcc.Graph(id="fraud-dist-chart", config={'displayModeBar': False})
                ], className="glass-card p-4 h-100")
            ], width=8),
            dbc.Col([
                html.Div([
                    html.H5("System Health", className="mb-4"),
                    html.Div(id="system-health-stats")
                ], className="glass-card p-4 h-100")
            ], width=4),
        ], className="mb-4"),

        # Charts Row
        dbc.Row([
            # Transactions Chart
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.H5("Transaction Analytics", className="mb-0"),
                        dbc.ButtonGroup([
                            dbc.Button("24h", id="tx-range-24h", color="outline-primary", size="sm", className="active"),
                            dbc.Button("7d", id="tx-range-7d", color="outline-primary", size="sm"),
                            dbc.Button("30d", id="tx-range-30d", color="outline-primary", size="sm")
                        ], className="btn-group-toggle")
                    ], className="d-flex justify-content-between align-items-center"),
                    dbc.CardBody([
                        dcc.Graph(
                            id="tx-chart",
                            config={"displayModeBar": False},
                            style={"height": "300px"}
                        )
                    ])
                ], className="h-100 border-0 shadow-sm")
            ], lg=8, className="mb-4"),
            
            # System Metrics
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.H5("System Metrics", className="mb-0"),
                        dbc.Badge("Live", color="success", className="ms-2")
                    ]),
                    dbc.CardBody([
                        html.Div(id="system-metrics-chart")
                    ])
                ], className="h-100 border-0 shadow-sm")
            ], lg=4, className="mb-4"),
        ], className="mb-4"),
        
        # Tables Row
        dbc.Row([
            # Alerts Table
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.H5("Recent Security Alerts", className="mb-0"),
                        dbc.Button("View All", color="link", size="sm", className="p-0")
                    ], className="d-flex justify-content-between align-items-center"),
                    dbc.CardBody([
                        html.Div(id="alerts-table-container", className="table-responsive")
                    ])
                ], className="h-100 border-0 shadow-sm")
            ], lg=6, className="mb-4"),
            
            # Transaction Feed
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.H5("Live Transaction Feed", className="mb-0"),
                        dbc.Button("Refresh", id="refresh-tx-feed", color="link", size="sm", className="p-0")
                    ], className="d-flex justify-content-between align-items-center"),
                    dbc.CardBody([
                        html.Div(id="tx-table-container", className="tx-feed")
                    ])
                ], className="h-100 border-0 shadow-sm")
            ], lg=6, className="mb-4"),
        ]),

        # Footer
        html.Footer([
            html.P([
                "© 2025 NFT Ticketing Platform | ",
                html.Span(id="live-clock", className="fw-bold")
            ], className="text-center text-muted mt-5 small")
        ]),

        dcc.Interval(id='interval-fast', interval=2000, n_intervals=0),
        dcc.Interval(id='interval-slow', interval=10000, n_intervals=0),
    ], fluid=True, className="py-4")
], id="main-container", className="dark-mode")

# Callbacks
@app.callback(
    [Output("kpi-tx-count", "children"),
     Output("kpi-fraud-rate", "children"),
     Output("kpi-latency", "children"),
     Output("kpi-revenue", "children")],
    [Input("interval-slow", "n_intervals")]
)
def update_kpi_values(n):
    kpis = calculate_kpis()
    return (
        f"{kpis['transactions_per_hour']}",
        f"{kpis['fraud_rate']:.1f}%",
        f"{kpis['api_latency']}ms",
        f"${kpis['revenue_per_hour']:,.2f}"
    )

@app.callback(
    Output("fraud-dist-chart", "figure"),
    [Input("interval-slow", "n_intervals")]
)
def update_fraud_chart(n):
    # Fetch real bot detections
    df = get_real_data("bot_detection", limit=50)
    
    if df is None or df.empty:
        # Generate mock data for visualization if empty
        times = [datetime.now() - timedelta(minutes=i*5) for i in range(50)]
        scores = [np.random.beta(2, 5) for _ in range(50)]
        df = pd.DataFrame({'detected_at': times, 'risk_score': scores})
    else:
        df['detected_at'] = pd.to_datetime(df['detected_at'])

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df['detected_at'],
        y=df['risk_score'],
        mode='markers+lines',
        line=dict(color='#38bdf8', width=1),
        marker=dict(
            size=8,
            color=df['risk_score'],
            colorscale=[[0, '#34d399'], [0.5, '#fbbf24'], [1, '#f87171']],
            showscale=False
        ),
        fill='tozeroy',
        fillcolor='rgba(56, 189, 248, 0.1)'
    ))

    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#94a3b8'),
        margin=dict(l=0, r=0, t=0, b=0),
        height=300,
        xaxis=dict(showgrid=False, zeroline=False),
        yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.05)', zeroline=False, range=[0, 1])
    )
    return fig

@app.callback(
    Output("blockchain-status", "children"),
    [Input("interval-fast", "n_intervals")]
)
def update_blockchain_status(n):
    try:
        if w3.is_connected():
            block = w3.eth.block_number
            return dbc.Badge([
                html.I(className="fas fa-link me-2"),
                f"Mainnet Node: #{block}"
            ], color="success", className="status-badge")
    except:
        pass
    return dbc.Badge([
        html.I(className="fas fa-unlink me-2"),
        "Node Offline"
    ], color="danger", className="status-badge")

@app.callback(
    Output("alerts-table-container", "children"),
    [Input("interval-slow", "n_intervals")]
)
def update_alerts_table(n):
    df = get_real_data("security_alerts", limit=5)
    if df is None or df.empty:
        return html.P("No active security alerts", className="text-success small")
    
    rows = []
    for _, row in df.iterrows():
        severity = row.get('severity', 'LOW')
        color = "danger" if severity in ['HIGH', 'CRITICAL'] else "warning" if severity == 'MEDIUM' else "info"
        
        rows.append(html.Tr([
            html.Td(row.get('created_at', '')[11:19], className="text-muted small"),
            html.Td(row.get('attack_type', 'Unknown')),
            html.Td(dbc.Badge(severity, color=color, className="status-badge")),
            html.Td(row.get('status', 'NEW'), className="small")
        ]))
    
    return dbc.Table([
        html.Thead(html.Tr([html.Th("Time"), html.Th("Type"), html.Th("Severity"), html.Th("Status")])),
        html.Tbody(rows)
    ], hover=True, responsive=True, className="mb-0")

@app.callback(
    Output("tx-table-container", "children"),
    [Input("interval-slow", "n_intervals")]
)
def update_tx_table(n):
    df = get_real_data("orders", limit=5)
    if df is None or df.empty:
        return html.P("Waiting for transactions...", className="text-muted small")
    
    rows = []
    for _, row in df.iterrows():
        rows.append(html.Tr([
            html.Td(row.get('created_at', '')[11:19], className="text-muted small"),
            html.Td(f"#{row.get('order_id', '0')}", className="fw-bold"),
            html.Td(f"{row.get('total_amount', 0):.4f} ETH", className="text-success"),
            html.Td(dbc.Badge(row.get('status', 'PENDING'), color="primary", className="status-badge"))
        ]))
    
    return dbc.Table([
        html.Thead(html.Tr([html.Th("Time"), html.Th("Order"), html.Th("Amount"), html.Th("Status")])),
        html.Tbody(rows)
    ], hover=True, responsive=True, className="mb-0")

@app.callback(
    Output("live-clock", "children"),
    [Input("interval-fast", "n_intervals")]
)
def update_clock(n):
    return datetime.now().strftime("%H:%M:%S UTC")

@app.callback(
    [Output("main-container", "className"),
     Output("theme-toggle", "children")],
    [Input("theme-toggle", "n_clicks")],
    [State("theme-store", "data")]
)
def toggle_theme(n, current_theme):
    if n is None:
        return "dark-mode", [html.I(className="fas fa-sun me-2"), "Light Mode"]
    
    if current_theme == "dark":
        return "light-mode", [html.I(className="fas fa-moon me-2"), "Dark Mode"]
    else:
        return "dark-mode", [html.I(className="fas fa-sun me-2"), "Light Mode"]

@app.callback(
    Output("theme-store", "data"),
    [Input("theme-toggle", "n_clicks")],
    [State("theme-store", "data")]
)
def update_theme_store(n, current_theme):
    if n is None: return current_theme
    return "light" if current_theme == "dark" else "dark"

if __name__ == '__main__':
    debug_mode = os.getenv('DEBUG', 'false').lower() == 'true'
    app.run_server(debug=debug_mode, host='0.0.0.0', port=8050)
