import pytest
import pandas as pd
from analytics.ticket_metrics import clean_tickets
from analytics.service_metrics import clean_services
from analytics.application_metrics import clean_applications


def test_data_generation_creates_all_sources(data):
    assert 'tickets' in data
    assert 'services' in data
    assert 'applications' in data
    assert 'incidents' in data
    assert 'quality_issues' in data
    assert 'config' in data


def test_tickets_have_expected_columns(data):
    df = data['tickets']
    expected = {'ticket_id', 'timestamp', 'category', 'priority', 'status', 'assignee', 'resolution_time_hours', 'customer_satisfaction'}
    assert expected.issubset(set(df.columns)), f"Missing columns: {expected - set(df.columns)}"


def test_services_have_expected_columns(data):
    df = data['services']
    expected = {'service', 'timestamp', 'status', 'response_time_ms'}
    assert expected.issubset(set(df.columns))


def test_applications_have_expected_columns(data):
    df = data['applications']
    expected = {'application_id', 'timestamp', 'role', 'source', 'stage', 'days_in_stage', 'offer_amount'}
    assert expected.issubset(set(df.columns))


def test_quality_issues_exist_for_all_sources(data):
    for source in ['tickets', 'services', 'applications']:
        issues = data['quality_issues'].get(source, [])
        assert len(issues) > 0, f"No quality issues reported for {source}"


def test_cleaning_detects_ticket_issues(data, config):
    cleaned, report = clean_tickets(data['tickets'], config)
    assert isinstance(report, dict)
    assert 'total_issues' in report


def test_cleaning_removes_future_timestamps(data, config):
    cleaned, report = clean_tickets(data['tickets'], config)
    now = pd.Timestamp.now()
    assert cleaned['timestamp'].max() <= now


def test_cleaning_fixes_negative_resolution(data, config):
    cleaned, report = clean_tickets(data['tickets'], config)
    assert cleaned['resolution_time_hours'].min() >= 0


def test_service_cleaning_detects_issues(data):
    cleaned, report = clean_services(data['services'])
    assert isinstance(report, dict)
    assert 'total_issues' in report
    assert 'duplicates' in report
    assert 'out_of_order' in report
    assert report['out_of_order'] > 0
    assert report['duplicates'] > 0


def test_application_cleaning_detects_issues(data, config):
    cleaned, report = clean_applications(data['applications'], config)
    assert isinstance(report, dict)
    assert 'total_issues' in report


def test_incidents_have_expected_structure(data):
    incidents = data['incidents']
    if len(incidents) > 0:
        expected = {'service', 'start_time', 'end_time', 'duration_minutes', 'cause_category'}
        assert expected.issubset(set(incidents.columns))


def test_generation_creates_reasonable_row_counts(data):
    assert 500 <= len(data['tickets']) <= 1500
    assert 10000 <= len(data['services']) <= 50000
    assert 100 <= len(data['applications']) <= 400
