SN_TEAL = "#249c7b"

CHART_BLUES = 'Blues'
CHART_REDS = 'Reds'
CHART_RDYLGN = 'RdYlGn'
CHART_RDBU = 'RdBu'

RAG_RED = "#f2514d"
RAG_AMBER = "#f0a33d"
RAG_GREEN = "#249c7b"

RAG_MAP = {
    'red': RAG_RED,
    'amber': RAG_AMBER,
    'green': RAG_GREEN,
}


def rag_hex(status):
    return RAG_MAP.get(status, '#beb5d1')

CHART_TEMPLATE = {
    'layout': {
        'font': {'family': 'Inter, ui-sans-serif, system-ui, sans-serif', 'color': '#120f1f'},
        'paper_bgcolor': '#ffffff',
        'plot_bgcolor': '#ffffff',
        'margin': {'l': 40, 'r': 20, 't': 40, 'b': 40},
        'hovermode': 'x unified',
        'xaxis': {'gridcolor': '#e8e4f0', 'zerolinecolor': '#e8e4f0'},
        'yaxis': {'gridcolor': '#e8e4f0', 'zerolinecolor': '#e8e4f0'},
    }
}

CSS = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

    #root > div:first-child > div:first-child > div:first-child > div:first-child {
        background: #faf8ff;
    }

    .main .block-container {
        max-width: 1400px;
        padding: 1.5rem 2rem;
    }

    .stApp {
        background: #faf8ff;
    }

    h1, h2, h3, h4, h5, h6 {
        font-family: 'Inter', ui-sans-serif, system-ui, sans-serif;
        font-weight: 700;
        color: #120f1f;
    }

    section[data-testid="stSidebar"] {
        background: #ffffff;
        border-right: 1px solid #e8e4f0;
    }
    section[data-testid="stSidebar"] .sidebar-content {
        padding: 1.5rem 1rem;
    }
    section[data-testid="stSidebar"] h1 {
        font-family: 'Inter', ui-sans-serif, system-ui, sans-serif;
        font-weight: 800;
        font-size: 1.2rem;
        color: #249c7b;
    }

    .stTabs [data-baseweb="tab-list"] {
        gap: 0;
        background: #ffffff;
        border-radius: 8px;
        padding: 4px;
        box-shadow: 0 1px 3px rgba(36, 156, 123, 0.08);
        margin-bottom: 1.5rem;
    }
    .stTabs [data-baseweb="tab"] {
        height: auto;
        padding: 8px 20px;
        border-radius: 6px;
        font-family: 'Inter', ui-sans-serif, system-ui, sans-serif;
        font-size: 0.85rem;
        font-weight: 500;
        color: #beb5d1;
        transition: all 0.15s ease;
        letter-spacing: 0.3px;
    }
    .stTabs [aria-selected="true"] {
        background: #249c7b;
        color: #ffffff !important;
    }

    [data-testid="stMetricValue"] {
        font-family: 'Inter', ui-sans-serif, system-ui, sans-serif;
        font-size: 1.8rem;
        font-weight: 700;
        color: #120f1f;
    }
    [data-testid="stMetricLabel"] {
        font-size: 0.75rem;
        font-weight: 600;
        color: #beb5d1;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    [data-testid="stMetricDelta"] {
        font-size: 0.85rem;
        font-weight: 600;
    }

    div[data-testid="column"] {
        gap: 1rem;
    }

    hr {
        margin: 1.5rem 0;
        border-color: #e8e4f0;
    }

    .sn-metric-card {
        background: #ffffff;
        border-radius: 10px;
        padding: 1.25rem 1.5rem;
        box-shadow: 0 1px 3px rgba(36, 156, 123, 0.06), 0 1px 2px rgba(36, 156, 123, 0.04);
        transition: box-shadow 0.2s ease, transform 0.15s ease;
        margin-bottom: 0.5rem;
    }
    .sn-metric-card:hover {
        box-shadow: 0 8px 16px rgba(36, 156, 123, 0.08), 0 2px 4px rgba(36, 156, 123, 0.04);
        transform: translateY(-1px);
    }

    .sn-card-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 0.4rem;
    }
    .sn-card-label {
        font-family: 'Inter', ui-sans-serif, system-ui, sans-serif;
        font-size: 0.75rem;
        font-weight: 600;
        color: #beb5d1;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .sn-card-rag {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        display: inline-block;
    }
    .sn-card-value {
        font-family: 'Inter', ui-sans-serif, system-ui, sans-serif;
        font-size: 1.8rem;
        font-weight: 700;
        color: #120f1f;
        line-height: 1.2;
    }

    .sn-alert {
        border-radius: 8px;
        padding: 0.75rem 1rem;
        margin: 0.3rem 0;
        border-left: 3px solid;
        font-family: 'Inter', ui-sans-serif, system-ui, sans-serif;
        font-size: 0.85rem;
        background: #ffffff;
        box-shadow: 0 1px 2px rgba(36, 156, 123, 0.04);
    }
    .sn-alert-severity {
        font-family: 'Inter', ui-sans-serif, system-ui, sans-serif;
        font-weight: 700;
        font-size: 0.7rem;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }

    .sn-section-header {
        font-family: 'Inter', ui-sans-serif, system-ui, sans-serif;
        font-size: 1rem;
        font-weight: 600;
        color: #120f1f;
        margin: 1.5rem 0 1rem 0;
        padding-bottom: 0.5rem;
        border-bottom: 2px solid #249c7b;
    }

    .stDataFrame {
        border: 1px solid #e8e4f0;
        border-radius: 8px;
        overflow: hidden;
    }

    button[kind="secondary"] {
        background: #ffffff;
        border: 1px solid #e8e4f0;
        border-radius: 6px;
        font-weight: 500;
    }
    button[kind="secondary"]:hover {
        border-color: #249c7b;
        color: #249c7b;
    }

    .stPlotlyChart {
        background: #ffffff;
        border-radius: 10px;
        padding: 0.75rem;
        box-shadow: 0 1px 3px rgba(36, 156, 123, 0.04);
    }

    .stSpinner > div {
        border-color: #249c7b !important;
    }

    @media (max-width: 768px) {
        .main .block-container {
            padding: 1rem;
        }
    }
</style>
"""


def get_css(dark=False):
    if not dark:
        return CSS
    return CSS + """<style>
    .stApp, #root > div:first-child > div:first-child > div:first-child > div:first-child {
        background: #102326 !important;
    }
    section[data-testid="stSidebar"] {
        background: #1a2e31 !important;
        border-right: 1px solid #2a4042 !important;
    }
    h1, h2, h3, h4, h5, h6,
    [data-testid="stMetricValue"],
    .sn-card-value,
    .sn-section-header {
        color: #e8e4f0 !important;
    }
    .stTabs [data-baseweb="tab-list"],
    .sn-metric-card, .sn-alert,
    .stPlotlyChart,
    .stDataFrame,
    button[kind="secondary"] {
        background: #1a2e31 !important;
        border-color: #2a4042 !important;
    }
    .stTabs [data-baseweb="tab"] {
        color: #9ca3af !important;
    }
    hr { border-color: #2a4042 !important; }
    .stDataFrame { border-color: #2a4042 !important; }
    button[kind="secondary"] { border-color: #2a4042 !important; }
    button[kind="secondary"]:hover { border-color: #249c7b !important; }
    .sn-metric-card:hover {
        box-shadow: 0 8px 16px rgba(0,0,0,0.3), 0 2px 4px rgba(0,0,0,0.2) !important;
    }
    .stApp p { color: #9ca3af !important; }
</style>"""


DARK_TEMPLATE = {
    'layout': {
        'paper_bgcolor': '#1a2e31',
        'plot_bgcolor': '#1a2e31',
        'font': {'color': '#e8e4f0'},
        'xaxis': {'gridcolor': '#2a4042', 'zerolinecolor': '#2a4042'},
        'yaxis': {'gridcolor': '#2a4042', 'zerolinecolor': '#2a4042'},
    }
}


def get_chart_template(dark=False):
    if not dark:
        return CHART_TEMPLATE
    merged = {'layout': {}}
    merged['layout'].update(CHART_TEMPLATE['layout'])
    merged['layout'].update(DARK_TEMPLATE['layout'])
    merged['layout']['xaxis'] = {**CHART_TEMPLATE['layout']['xaxis'], **DARK_TEMPLATE['layout']['xaxis']}
    merged['layout']['yaxis'] = {**CHART_TEMPLATE['layout']['yaxis'], **DARK_TEMPLATE['layout']['yaxis']}
    merged['layout']['font'] = {**CHART_TEMPLATE['layout']['font'], **DARK_TEMPLATE['layout']['font']}
    return merged
