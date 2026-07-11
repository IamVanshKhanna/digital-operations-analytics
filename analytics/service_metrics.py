from typing import Tuple, Dict, List, Any, Optional
import pandas as pd
import numpy as np
from analytics.metrics import detect_anomalies, week_over_week_change
from analytics.types import ServiceMetrics, QualityReport


def clean_services(df: pd.DataFrame) -> Tuple[pd.DataFrame, QualityReport]:
    report = {}
    df = df.copy()

    if df.empty:
        report['total_issues'] = 0
        return df, report

    df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')

    n_missing = df['response_time_ms'].isna().sum()
    report['missing_response'] = n_missing
    df['response_time_ms'] = df['response_time_ms'].fillna(df['response_time_ms'].median())

    n_neg = df['response_time_ms'].lt(0).sum()
    report['negative_response'] = n_neg
    df['response_time_ms'] = df['response_time_ms'].abs()

    n_out = 0
    for service in df['service'].unique():
        mask = df['service'] == service
        sdf = df[mask].copy()
        diffs = sdf['timestamp'].diff().dt.total_seconds() / 60
        n_out += (diffs < 0).sum()
    report['out_of_order'] = n_out

    n_dup = df.duplicated(subset=['service', 'timestamp']).sum()
    report['duplicates'] = n_dup
    df = df.drop_duplicates(subset=['service', 'timestamp'])

    df = df.sort_values('timestamp').reset_index(drop=True)

    report['total_issues'] = n_missing + n_neg + n_dup + n_out
    return df, report


def compute_service_metrics(
    df: pd.DataFrame,
    incidents_df: Optional[pd.DataFrame],
    config: Dict[str, Any]
) -> ServiceMetrics:
    metrics = {}
    df = df.copy()

    if df.empty:
        metrics.update({'uptime_pct': 0.0, 'degraded_pct': 0.0, 'total_incidents': 0,
                        'avg_mttr_minutes': 0.0, 'max_mttr_minutes': 0,
                        'avg_response_time_ms': 0.0, 'p95_response_time_ms': 0.0,
                        'response_trend': 0.0, 'uptime_response_ms': 0.0})
        return metrics

    df['date'] = df['timestamp'].dt.date

    total_checks = len(df)
    down_checks = len(df[df['status'] == 'down'])
    degraded_checks = len(df[df['status'] == 'degraded'])
    metrics['uptime_pct'] = round((1 - down_checks / total_checks) * 100, 2) if total_checks > 0 else 100.0
    metrics['degraded_pct'] = round(degraded_checks / total_checks * 100, 2) if total_checks > 0 else 0.0

    metrics['total_incidents'] = len(incidents_df) if incidents_df is not None else 0

    if incidents_df is not None and len(incidents_df) > 0:
        metrics['avg_mttr_minutes'] = round(incidents_df['duration_minutes'].mean(), 1)
        metrics['max_mttr_minutes'] = int(incidents_df['duration_minutes'].max())
    else:
        metrics['avg_mttr_minutes'] = 0
        metrics['max_mttr_minutes'] = 0

    metrics['avg_response_time_ms'] = round(df['response_time_ms'].mean(), 1)
    metrics['p95_response_time_ms'] = round(df['response_time_ms'].quantile(0.95), 1)

    daily_response = df.groupby('date')['response_time_ms'].mean()
    metrics['response_trend'] = round(week_over_week_change(daily_response), 1)

    up_df = df[df['status'] == 'up']
    metrics['uptime_response_ms'] = round(up_df['response_time_ms'].mean(), 1) if len(up_df) > 0 else 0

    return metrics


def compute_per_service_uptime(df: pd.DataFrame) -> pd.DataFrame:
    results = []
    if df.empty:
        return pd.DataFrame(results)
    for service in df['service'].unique():
        sdf = df[df['service'] == service]
        total = len(sdf)
        down = len(sdf[sdf['status'] == 'down'])
        degraded = len(sdf[sdf['status'] == 'degraded'])
        uptime = round((1 - down / total) * 100, 2) if total > 0 else 100.0
        avg_resp = round(sdf['response_time_ms'].mean(), 1)
        results.append({
            'service': service,
            'uptime_pct': uptime,
            'down_checks': down,
            'degraded_checks': degraded,
            'avg_response_ms': avg_resp,
            'total_checks': total,
        })
    return pd.DataFrame(results).sort_values('uptime_pct')


def compute_incident_timeline(incidents_df):
    if incidents_df is None or incidents_df.empty:
        return pd.DataFrame()
    tl = incidents_df.copy()
    tl['date'] = tl['start_time'].dt.date
    return tl.groupby('date').size().reset_index(name='incidents')
