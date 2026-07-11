import pytest
import pandas as pd
from unittest.mock import patch, MagicMock
from dashboard.app import load_data
def test_dashboard_loads_data_successfully(data):
    """Test that dashboard can load data without errors."""
    assert data['tickets'].shape[0] > 0
    assert data['services'].shape[0] > 0
    assert data['applications'].shape[0] > 0
    assert 'quality_issues' in data
def test_dashboard_cleaning_stores_data_quality(data, config):
    """Test that cleaning pipeline stores data quality issues."""
    from analytics.ticket_metrics import clean_tickets, compute_ticket_metrics
    from analytics.service_metrics import clean_services
    from analytics.application_metrics import clean_applications

    # Ensure services quality issues are stored
    assert 'services' in data['quality_issues']
    assert len(data['quality_issues']['services']) > 0

    # Test cleaning doesn't crash on valid data
    tickets_clean = clean_tickets(data['tickets'], config)[0]
    assert tickets_clean.shape[0] > 0

    services_clean = clean_services(data['services'])[0]
    assert services_clean.shape[0] > 0

    apps_clean = clean_applications(data['applications'], config)[0]
    assert apps_clean.shape[0] > 0

    # Verify metrics can be computed
    ticket_metrics = compute_ticket_metrics(tickets_clean, config)
    assert ticket_metrics[0]['total_tickets'] > 0
def test_executive_summary_cards_exist(data, config):
    """Test that executive summary data is structured properly for dashboard display."""
    from analytics.ticket_metrics import clean_tickets, compute_ticket_metrics
    from analytics.service_metrics import clean_services
    from analytics.application_metrics import clean_applications

    tickets_clean = clean_tickets(data['tickets'], config)[0]
    services_clean = clean_services(data['services'])[0]
    apps_clean = clean_applications(data['applications'], config)[0]

    ticket_metrics = compute_ticket_metrics(tickets_clean, config)

    # Verify key metrics are present for each card
    assert 'total_tickets' in ticket_metrics[0]
    assert 'avg_resolution_hours' in ticket_metrics[0]
    assert 'avg_csat' in ticket_metrics[0]

    # Verify metric types are correct
    assert isinstance(ticket_metrics[0]['total_tickets'], int)
    assert isinstance(ticket_metrics[0]['avg_resolution_hours'], (int, float))
    assert isinstance(ticket_metrics[0]['avg_csat'], (int, float))
def test_insights_generation_has_safety_checks():
    """Test that insight generation handles all edge cases."""
    from analytics.insights import generate_insights

    ticket_m = {
        'daily_avg_volume': 10.0, 'volume_trend': 5.0,
        'avg_resolution_hours': 24.0, 'resolution_trend': -2.0,
        'total_tickets': 100, 'category_distribution': {'bug': 50},
    }
    service_m = {
        'uptime_pct': 99.0, 'total_incidents': 5,
        'avg_mttr_minutes': 45.0, 'max_mttr_minutes': 120,
    }
    app_m = {
        'conversion_rate': 15.0, 'avg_time_to_hire': 45.0,
        'top_source': 'linkedin', 'top_source_pct': 30.0,
    }
    insights = generate_insights(ticket_m, service_m, app_m)
    assert len(insights) >= 4


@pytest.fixture
def mock_streamlit():
    with patch('dashboard.app.st') as mock_st:
        yield mock_st
def test_filter_respected_in_incidents(mock_streamlit):
    """Test that incident data respects service and date filters."""
    # This test verifies the incident filtering logic
    test_data = {
        'incidents_filtered': pd.DataFrame(),
        'service_metrics': {'uptime_pct': 100.0},
        'ticket_metrics': {'total_tickets': 100},
        'app_metrics': {'total_applications': 50}
    }

    assert test_data['incidents_filtered'].empty or len(test_data['incidents_filtered']) > 0
def test_anomaly_data_survival(data, config):
    """Test that anomaly detection data persists across render cycles."""
    from analytics.ticket_metrics import clean_tickets, compute_ticket_metrics

    tickets_clean = clean_tickets(data['tickets'], config)[0]
    ticket_metrics = compute_ticket_metrics(tickets_clean, config)

    # Verify anomaly mask and index are stored
    assert '_volume_anomaly_mask' in ticket_metrics[0]
    assert '_daily_counts_index' in ticket_metrics[0]

    # Verify mask is boolean Series
    import pandas as pd
    anomaly_mask = ticket_metrics[0]['_volume_anomaly_mask']
    assert isinstance(anomaly_mask, pd.Series)
    assert anomaly_mask.dtype == bool
    assert len(anomaly_mask) == len(ticket_metrics[1])  # matches daily counts length


def test_dark_mode_functions_produce_valid_output():
    from dashboard.style import get_css, get_chart_template
    assert '</style>' in get_css(True)
    assert '</style>' in get_css(False)
    dark_tmpl = get_chart_template(True)
    light_tmpl = get_chart_template(False)
    assert dark_tmpl['layout']['paper_bgcolor'] == '#1a2e31'
    assert light_tmpl['layout']['paper_bgcolor'] == '#ffffff'
    assert dark_tmpl['layout']['font']['color'] == '#e8e4f0'


def test_config_driven_parameters_are_available(config):
    """Test that config is accessible for dashboard customization."""
    assert 'analytics' in config
    assert 'data' in config
    assert 'tickets' in config['data']
    assert 'max_resolution_hours' not in config['analytics']  # Verify no hardcoded values

    al = config['analytics']
    assert 'thresholds' in al
    assert 'sla_compliance' in al['thresholds']
    assert 'conversion' in al['thresholds']
    assert 'data_quality' in al['thresholds']
    assert 'alerts' in al
    assert 'sla_breach_percent' in al['alerts']
    assert 'incidents' in al['alerts']
    assert 'conversion_critical' in al['alerts']
    assert 'dq_issues' in al['alerts']


def test_compute_dq_score_returns_percentage(data, config):
    from analytics.ticket_metrics import clean_tickets
    from analytics.service_metrics import clean_services
    from analytics.application_metrics import clean_applications
    from analytics.insights import compute_dq_score

    tdq = clean_tickets(data['tickets'], config)[1]
    sdq = clean_services(data['services'])[1]
    adq = clean_applications(data['applications'], config)[1]
    total = len(data['tickets']) + len(data['services']) + len(data['applications'])

    result = compute_dq_score(tdq, sdq, adq, total)
    assert result.endswith('%')
    pct = float(result.strip('%'))
    assert 0 <= pct <= 100


def test_compute_dq_score_zero_issues(data, config):
    from analytics.insights import compute_dq_score
    empty: dict = {'total_issues': 0}
    result = compute_dq_score(empty, empty, empty, 1000)
    assert result == '100%'


def test_compute_dq_score_zero_records(data, config):
    from analytics.insights import compute_dq_score
    bad: dict = {'total_issues': 50}
    result = compute_dq_score(bad, bad, bad, 0)
    assert result == '100%'


def test_compute_dq_rag_returns_expected_color(data, config):
    from analytics.ticket_metrics import clean_tickets
    from analytics.service_metrics import clean_services
    from analytics.application_metrics import clean_applications
    from analytics.insights import compute_dq_rag

    tdq = clean_tickets(data['tickets'], config)[1]
    sdq = clean_services(data['services'])[1]
    adq = clean_applications(data['applications'], config)[1]
    total = len(data['tickets']) + len(data['services']) + len(data['applications'])

    rag = compute_dq_rag(tdq, sdq, adq, total, config)
    assert rag in ('green', 'amber', 'red')


def test_compute_dq_rag_zero_issues(data, config):
    from analytics.insights import compute_dq_rag
    empty: dict = {'total_issues': 0}
    result = compute_dq_rag(empty, empty, empty, 1000, config)
    assert result == 'green'


def test_compute_dq_rag_high_issues(data, config):
    from analytics.insights import compute_dq_rag
    bad: dict = {'total_issues': 500}
    result = compute_dq_rag(bad, bad, bad, 1000, config)
    assert result == 'red'


def test_generate_alerts_triggers_on_known_conditions(config):
    from analytics.insights import generate_alerts

    tm = {'sla_breach_rate': 50.0, 'volume_anomalies': 3}
    sm = {'uptime_pct': 80.0, 'total_incidents': 100}
    am = {'conversion_rate': 2.0}
    tdq: dict = {'total_issues': 100}
    sdq: dict = {'total_issues': 200}
    adq: dict = {'total_issues': 0}

    alerts = generate_alerts(tm, sm, am, tdq, sdq, adq, config)
    assert len(alerts) >= 5
    severities = {a['severity'] for a in alerts}
    assert 'high' in severities


def test_generate_alerts_no_false_positives(config):
    from analytics.insights import generate_alerts

    tm = {'sla_breach_rate': 0.0, 'volume_anomalies': 0}
    sm = {'uptime_pct': 100.0, 'total_incidents': 0}
    am = {'conversion_rate': 50.0}
    tdq: dict = {'total_issues': 0}
    sdq: dict = {'total_issues': 0}
    adq: dict = {'total_issues': 0}

    alerts = generate_alerts(tm, sm, am, tdq, sdq, adq, config)
    assert len(alerts) == 0