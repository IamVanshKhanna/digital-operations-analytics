import pytest
import pandas as pd
import numpy as np
from analytics.metrics import detect_anomalies, week_over_week_change, rag_status
from analytics.ticket_metrics import compute_ticket_metrics, clean_tickets
from analytics.service_metrics import compute_service_metrics, clean_services
from analytics.application_metrics import compute_application_metrics, clean_applications


def test_ticket_metrics_produce_valid_values(data, config):
    cleaned, _ = clean_tickets(data['tickets'], config)
    metrics, daily, res = compute_ticket_metrics(cleaned, config)
    assert metrics['total_tickets'] > 0
    assert metrics['avg_resolution_hours'] > 0
    assert metrics['total_tickets'] >= metrics['open_tickets']
    assert 1 <= metrics['avg_csat'] <= 5


def test_service_metrics_produce_valid_values(data, config):
    cleaned, _ = clean_services(data['services'])
    metrics = compute_service_metrics(cleaned, data['incidents'], config)
    assert 0 <= metrics['uptime_pct'] <= 100
    assert metrics['avg_response_time_ms'] > 0
    assert metrics['total_incidents'] >= 0


def test_application_metrics_produce_valid_values(data, config):
    cleaned, _ = clean_applications(data['applications'], config)
    metrics, daily = compute_application_metrics(cleaned, config)
    assert metrics['total_applications'] > 0
    assert 0 <= metrics['conversion_rate'] <= 100
    assert len(metrics['funnel']) > 0


def test_anomaly_detection_returns_boolean_series():
    series = pd.Series(np.random.normal(10, 2, 100))
    anomalies = detect_anomalies(series, z_threshold=2.0)
    assert hasattr(anomalies, 'dtype')
    assert anomalies.dtype == bool
    assert len(anomalies) == len(series)


def test_anomaly_detection_detects_outliers():
    normal = np.random.normal(10, 1, 98)
    outliers = np.array([30, -20])
    series = pd.Series(np.concatenate([normal, outliers]))
    anomalies = detect_anomalies(series, z_threshold=2.0)
    assert anomalies[-2:].sum() >= 1


def test_week_over_week_change():
    series = pd.Series(np.arange(20, dtype=float))
    change = week_over_week_change(series)
    assert isinstance(change, float)


def test_week_over_week_change_short_series():
    series = pd.Series([1, 2, 3])
    change = week_over_week_change(series)
    assert change == 0.0


def test_rag_status_higher_is_better():
    assert rag_status(99.9, 99.5, 99.0, True) == 'green'
    assert rag_status(99.3, 99.5, 99.0, True) == 'amber'
    assert rag_status(98.0, 99.5, 99.0, True) == 'red'


def test_rag_status_lower_is_better():
    assert rag_status(1, 5, 10, False) == 'green'
    assert rag_status(7, 5, 10, False) == 'amber'
    assert rag_status(15, 5, 10, False) == 'red'


def test_anomaly_mask_returned_in_metrics(data, config):
    cleaned, _ = clean_tickets(data['tickets'], config)
    metrics, _, _ = compute_ticket_metrics(cleaned, config)
    assert '_volume_anomaly_mask' in metrics
    assert '_daily_counts_index' in metrics


def test_funnel_excludes_rejected_from_base(data, config):
    cleaned, _ = clean_applications(data['applications'], config)
    metrics, _ = compute_application_metrics(cleaned, config)
    funnel = metrics['funnel']
    if len(funnel) > 0:
        first = funnel[0]
        assert first['from_previous_pct'] == 100.0


def test_empty_dataframe_does_not_crash():
    import pandas as pd
    from analytics.ticket_metrics import clean_tickets, compute_ticket_metrics, compute_sla_table
    from analytics.service_metrics import clean_services, compute_service_metrics, compute_per_service_uptime, compute_incident_timeline
    from analytics.application_metrics import clean_applications, compute_application_metrics, compute_source_effectiveness
    from analytics.metrics import rag_status

    config = {'analytics': {'sla_hours': 48, 'anomaly_z_threshold': 2.0}, 'data': {'tickets': {'categories': ['bug'], 'dirty_categories': ['Bug']}, 'applications': {'stages': []}}}
    empty = pd.DataFrame()

    c, r = clean_tickets(empty, config); assert r['total_issues'] == 0
    c, r = clean_services(empty); assert r['total_issues'] == 0
    c, r = clean_applications(empty, config); assert r['total_issues'] == 0
    m, dc, dr = compute_ticket_metrics(empty, config); assert m['total_tickets'] == 0
    m = compute_service_metrics(empty, pd.DataFrame(), config); assert m['uptime_pct'] == 0.0
    m, dc = compute_application_metrics(empty, config); assert m['total_applications'] == 0
    assert len(compute_sla_table(empty, 48)) == 0
    assert len(compute_per_service_uptime(empty)) == 0
    assert len(compute_incident_timeline(None)) == 0
    assert len(compute_incident_timeline(pd.DataFrame())) == 0
    assert len(compute_source_effectiveness(empty)) == 0
    assert rag_status(None, 95, 90, True) == 'red'
    assert rag_status('abc', 95, 90, True) == 'red'


def test_category_distribution_is_complete(data, config):
    cleaned, _ = clean_tickets(data['tickets'], config)
    metrics, _, _ = compute_ticket_metrics(cleaned, config)
    total_from_cats = sum(metrics['category_distribution'].values())
    assert total_from_cats > 0
