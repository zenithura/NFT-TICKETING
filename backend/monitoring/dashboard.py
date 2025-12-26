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
        },
        '/assets/custom.css'  # Load custom CSS
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
        {"name": "theme-color", "content": "#0f172a"},
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
        # Handle both Supabase client and SQLite wrapper
        if hasattr(db, 'table'):
            query = db.table(table_name).select("*").order("created_at", desc=True).limit(limit)
            response = query.execute()
            # Check if response is an object with data attribute (Supabase) or just data (SQLite wrapper might differ)
            data = response.data if hasattr(response, 'data') else response
            return pd.DataFrame(data) if data else None
        return None
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
        return kpis
    
    try:
        db = get_supabase_admin()
        now = datetime.utcnow()
        one_hour_ago = (now - timedelta(hours=1)).isoformat()
        
        # Fetch data
        orders_df = get_real_data("orders", limit=1000)
        bots_df = get_real_data("bot_detection", limit=1000)
        web_df = get_real_data("web_requests", limit=1000)
        
        # Process transactions
        if orders_df is not None and not orders_df.empty:
            # Filter for last hour if created_at exists
            if 'created_at' in orders_df.columns:
                orders_df['created_at'] = pd.to_datetime(orders_df['created_at'])
                recent_orders = orders_df[orders_df['created_at'] >= pd.Timestamp.now(tz=None) - pd.Timedelta(hours=1)]
            else:
                recent_orders = orders_df

            successful_orders = recent_orders[recent_orders['status'] == 'completed']
            kpis['transactions_per_hour'] = len(successful_orders)
            kpis['revenue_per_hour'] = successful_orders['total_amount'].sum() if 'total_amount' in successful_orders.columns else 0
            kpis['avg_ticket_price'] = kpis['revenue_per_hour'] / len(successful_orders) if not successful_orders.empty else 0
            
            # Calculate TPS
            if not successful_orders.empty and len(successful_orders) > 1:
                time_diffs = successful_orders['created_at'].diff().dt.total_seconds().abs()
                min_diff = time_diffs[time_diffs > 0].min()
                if pd.notna(min_diff) and min_diff > 0:
                    kpis['peak_tps'] = int(1 / min_diff)
        
        # Process bot detections
        if bots_df is not None and not bots_df.empty:
            total_actions = kpis['transactions_per_hour'] + len(bots_df)
            if total_actions > 0:
                kpis['fraud_rate'] = (len(bots_df) / total_actions) * 100
        
        # Process web requests
        if web_df is not None and not web_df.empty:
            if 'response_time_ms' in web_df.columns:
                kpis['api_latency'] = int(web_df['response_time_ms'].quantile(0.95))
            
            if 'status_code' in web_df.columns:
                total = len(web_df)
                success = len(web_df[(web_df['status_code'] >= 200) & (web_df['status_code'] < 400)])
                kpis['success_rate'] = (success / total) * 100 if total > 0 else 100

        # Get blockchain data
        try:
            if w3.is_connected():
                kpis['block_height'] = w3.eth.block_number
                kpis['gas_price'] = float(w3.from_wei(w3.eth.gas_price, 'gwei'))
                kpis['pending_txs'] = len(w3.eth.get_block('pending', full_transactions=True).transactions)
        except Exception as e:
            # logger.warning(f"Could not fetch blockchain data: {e}")
            pass
        
        return kpis
        
    except Exception as e:
        logger.error(f"Error calculating KPIs: {e}", exc_info=True)
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
                    html.Div(id="live-clock", className="fw-bold text-muted")
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
                                ], className="d-flex align-items-center")
                            ], className="d-flex justify-content-between align-items-center mb-2"),
                            html.H3(id="kpi-tx-count", className="mb-0"),
                            html.Div([
                                html.Small(id="kpi-revenue", className="text-success fw-bold"),
                                html.Small(" revenue", className="text-muted ms-1")
                            ], className="mt-2")
                        ])
                    ])
                ], className="h-100 glass-card")
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
                                    className="my-2",
                                    style={"height": "6px"}
                                ),
                                html.Small("Target: < 2.0%", className="text-muted")
                            ])
                        ])
                    ])
                ], className="h-100 glass-card")
            ], md=3, className="mb-4"),
            
            # API Latency Card
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.Div([
                            html.Div([
                                html.Span("API Latency", className="text-uppercase small text-muted"),
                                html.I(className="fas fa-bolt text-warning")
                            ], className="d-flex justify-content-between align-items-center mb-2"),
                            html.H3(id="kpi-latency", className="mb-0"),
                            html.Small("95th Percentile", className="text-muted mt-2 d-block")
                        ])
                    ])
                ], className="h-100 glass-card")
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
                                ], className="mb-1"),
                                html.Div([
                                    html.Small("Gas:", className="text-muted"),
                                    html.Span(id="gas-price", className="ms-2 font-monospace")
                                ])
                            ])
                        ])
                    ])
                ], className="h-100 glass-card")
            ], md=3, className="mb-4"),
        ], className="mb-4"),

        # Main Charts
        dbc.Row([
            dbc.Col([
                html.Div([
                    html.Div([
                        html.H5("Fraud Score Distribution", className="mb-0"),
                        dbc.Badge("Live Feed", color="info", className="ms-2 status-badge")
                    ], className="d-flex align-items-center mb-4"),
                    dcc.Graph(id="fraud-dist-chart", config={'displayModeBar': False})
                ], className="glass-card p-4 h-100")
            ], width=8),
            dbc.Col([
                html.Div([
                    html.H5("System Health", className="mb-4"),
                    html.Div([
                        html.Div([
                            html.Span("CPU Usage", className="text-muted small"),
                            html.H4(id="cpu-usage", className="mb-1"),
                            dbc.Progress(id="cpu-progress", value=0, color="primary", className="mb-3", style={"height": "4px"})
                        ]),
                        html.Div([
                            html.Span("Memory Usage", className="text-muted small"),
                            html.H4(id="memory-usage", className="mb-1"),
                            dbc.Progress(id="memory-progress", value=0, color="info", className="mb-3", style={"height": "4px"})
                        ]),
                        html.Div([
                            html.Span("Disk Usage", className="text-muted small"),
                            html.H4(id="disk-usage", className="mb-1"),
                            dbc.Progress(id="disk-progress", value=0, color="warning", className="mb-3", style={"height": "4px"})
                        ])
                    ])
                ], className="glass-card p-4 h-100")
            ], width=4),
        ], className="mb-4"),

        # Tables Row
        dbc.Row([
            # Alerts Table
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.H5("Recent Security Alerts", className="mb-0"),
                        html.Span(className="live-indicator")
                    ], className="d-flex justify-content-between align-items-center"),
                    dbc.CardBody([
                        html.Div(id="alerts-table-container", className="table-responsive")
                    ])
                ], className="h-100 glass-card")
            ], lg=6, className="mb-4"),
            
            # Transaction Feed
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.H5("Live Transaction Feed", className="mb-0"),
                        html.Span(className="live-indicator")
                    ], className="d-flex justify-content-between align-items-center"),
                    dbc.CardBody([
                        html.Div(id="tx-table-container", className="tx-feed")
                    ])
                ], className="h-100 glass-card")
            ], lg=6, className="mb-4"),
        ]),

        # Footer
        html.Footer([
            html.P([
                "© 2025 NFT Ticketing Platform | Intelligence Center v2.0",
            ], className="text-center text-muted mt-5 small")
        ]),

        dcc.Interval(id='interval-fast', interval=2000, n_intervals=0),
        dcc.Interval(id='interval-slow', interval=5000, n_intervals=0),
    ], fluid=True, className="py-4")
], id="main-container", className="dark-mode")

# Callbacks
@app.callback(
    [Output("kpi-tx-count", "children"),
     Output("kpi-fraud-rate", "children"),
     Output("kpi-latency", "children"),
     Output("kpi-revenue", "children"),
     Output("fraud-progress", "value"),
     Output("block-height", "children"),
     Output("gas-price", "children"),
     Output("cpu-usage", "children"),
     Output("memory-usage", "children"),
     Output("disk-usage", "children"),
     Output("cpu-progress", "value"),
     Output("memory-progress", "value"),
     Output("disk-progress", "value")],
    [Input("interval-slow", "n_intervals")]
)
def update_kpi_values(n):
    kpis = calculate_kpis()
    return (
        f"{kpis['transactions_per_hour']}",
        f"{kpis['fraud_rate']:.1f}%",
        f"{kpis['api_latency']}ms",
        f"${kpis['revenue_per_hour']:,.2f}",
        kpis['fraud_rate'],
        f"#{kpis['block_height']}",
        f"{kpis['gas_price']:.1f} Gwei",
        f"{kpis.get('cpu_percent', 0)}%",
        f"{kpis.get('memory_percent', 0)}%",
        f"{kpis.get('disk_percent', 0)}%",
        kpis.get('cpu_percent', 0),
        kpis.get('memory_percent', 0),
        kpis.get('disk_percent', 0)
    )

@app.callback(
    Output("fraud-dist-chart", "figure"),
    [Input("interval-slow", "n_intervals")]
)
def update_fraud_chart(n):
    df = get_real_data("bot_detection", limit=50)
    
    if df is None or df.empty:
        # Empty state
        fig = go.Figure()
        fig.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            annotations=[dict(text="No Data Available", showarrow=False, font=dict(color="white"))]
        )
        return fig

    if 'detected_at' in df.columns:
        df['detected_at'] = pd.to_datetime(df['detected_at'])

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df['detected_at'],
        y=df['risk_score'],
        mode='markers+lines',
        line=dict(color='#38bdf8', width=2, shape='spline'),
        marker=dict(
            size=8,
            color=df['risk_score'],
            colorscale=[[0, '#34d399'], [0.5, '#fbbf24'], [1, '#f87171']],
            showscale=False,
            line=dict(color='white', width=1)
        ),
        fill='tozeroy',
        fillcolor='rgba(56, 189, 248, 0.1)'
    ))

    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#94a3b8', family="Inter"),
        margin=dict(l=0, r=0, t=10, b=0),
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
            return dbc.Badge([
                html.I(className="fas fa-link me-2"),
                "Connected"
            ], color="success", className="status-badge")
    except:
        pass
    return dbc.Badge([
        html.I(className="fas fa-unlink me-2"),
        "Offline"
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
            html.Td(str(row.get('created_at', ''))[11:19], className="text-muted small"),
            html.Td(row.get('attack_type', 'Unknown')),
            html.Td(dbc.Badge(severity, color=color, className="status-badge")),
            html.Td(row.get('status', 'NEW'), className="small")
        ]))
    
    return dbc.Table([
        html.Thead(html.Tr([html.Th("Time"), html.Th("Type"), html.Th("Severity"), html.Th("Status")])),
        html.Tbody(rows)
    ], hover=True, responsive=True, className="mb-0 table-hover")

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
        amount = row.get('total_amount', 0)
        status = row.get('status', 'PENDING')
        status_color = "success" if status == 'completed' else "warning" if status == 'pending' else "danger"
        
        rows.append(html.Tr([
            html.Td(str(row.get('created_at', ''))[11:19], className="text-muted small"),
            html.Td(f"#{row.get('id', row.get('order_id', '0'))}", className="fw-bold"),
            html.Td(f"{amount:.4f} ETH", className="text-success font-monospace"),
            html.Td(dbc.Badge(status, color=status_color, className="status-badge"))
        ]))
    
    return dbc.Table([
        html.Thead(html.Tr([html.Th("Time"), html.Th("Order"), html.Th("Amount"), html.Th("Status")])),
        html.Tbody(rows)
    ], hover=True, responsive=True, className="mb-0 table-hover")

@app.callback(
    Output("live-clock", "children"),
    [Input("interval-fast", "n_intervals")]
)
def update_clock(n):
    return datetime.now().strftime("%H:%M:%S UTC")

if __name__ == '__main__':
    debug_mode = os.getenv('DEBUG', 'false').lower() == 'true'
    app.run_server(debug=debug_mode, host='0.0.0.0', port=8050)
