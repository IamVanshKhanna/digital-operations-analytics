"""
Simple tests for dashboard functionality and data integrity.
"""
import pytest
import pandas as pd
from data.generate_all import generate_all
from analytics.ticket_metrics import compute_ticket_metrics, clean_tickets
from analytics.service_metrics import compute_service_metrics, clean_services
from analytics.application_metrics import compute_application_metrics, clean_applications


def test_dashboard_module_imports_successfully():
    """Test that the dashboard module loads without errors."""
    import importlib
    mod = importlib.import_module('dashboard.app')
    assert hasattr(mod, 'load_data')
    assert hasattr(mod, 'main')


def test_export_csv_tickets_data(data, config):
    """Test that ticket data can be exported as CSV."""
    cleaned, _ = clean_tickets(data['tickets'], config)
    csv_output = cleaned.to_csv(index=False)
    assert len(csv_output) > 0
    assert 'ticket_id' in csv_output
    assert 'timestamp' in csv_output


def test_export_csv_services_data(data, config):
    """Test that service health data can be exported as CSV."""
    cleaned, _ = clean_services(data['services'])
    csv_output = cleaned.to_csv(index=False)
    assert len(csv_output) > 0
    assert 'service' in csv_output
    assert 'response_time_ms' in csv_output


def test_export_csv_applications_data(data, config):
    """Test that application pipeline data can be exported as CSV."""
    cleaned, _ = clean_applications(data['applications'], config)
    csv_output = cleaned.to_csv(index=False)
    assert len(csv_output) > 0
    assert 'application_id' in csv_output
    assert 'stage' in csv_output


def test_export_creates_usable_csv_files():
    """Test that exported CSV files contain expected columns."""
    data = generate_all()
    config = data['config']

    # Test tickets export
    cleaned_tickets, _ = clean_tickets(data['tickets'], config)
    tickets_csv = cleaned_tickets.to_csv(index=False)
    assert tickets_csv.count('\n') > 0  # Has header and at least one data row
    assert 'ticket_id' in tickets_csv

    # Test services export
    cleaned_services, _ = clean_services(data['services'])
    services_csv = cleaned_services.to_csv(index=False)
    assert services_csv.count('\n') > 0
    assert 'service' in services_csv

    # Test applications export
    cleaned_apps, _ = clean_applications(data['applications'], config)
    apps_csv = cleaned_apps.to_csv(index=False)
    assert apps_csv.count('\n') > 0
    assert 'application_id' in apps_csv