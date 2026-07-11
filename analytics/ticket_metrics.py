from typing import Tuple, Dict, List, Any
import pandas as pd
import numpy as np
from analytics.metrics import detect_anomalies, week_over_week_change
from analytics.types import TicketMetrics, QualityReport


def clean_tickets(df: pd.DataFrame, config: Dict[str, Any]) -> Tuple[pd.DataFrame, QualityReport]:
    cfg = config['data']['tickets']
    report = {}
    df = df.copy()
    rows_before = len(df)

    if df.empty:
        report['total_issues'] = 0
        report['rows_before'] = 0
        return df, report

    df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
    now = pd.Timestamp.now()

    n_future = df['timestamp'].gt(now).sum()
    report['future_timestamps'] = n_future
    df = df[df['timestamp'] <= now]

    n_missing_csat = df['customer_satisfaction'].isna().sum()
    report['missing_csat'] = n_missing_csat
    csat_median = df['customer_satisfaction'].median()
    df['customer_satisfaction'] = df['customer_satisfaction'].fillna(csat_median)

    n_neg_res = df['resolution_time_hours'].lt(0).sum()
    report['negative_resolution'] = n_neg_res
    df['resolution_time_hours'] = df['resolution_time_hours'].abs()

    clean_cats = set(cfg['categories'])
    n_typo = (~df['category'].isin(clean_cats)).sum()
    report['category_typos'] = n_typo
    cat_map = {c: c.lower().strip() for c in df['category'].unique()}
    cat_map = {k: v for k, v in cat_map.items() if v in clean_cats}
    df['category'] = df['category'].map(cat_map).fillna('bug')

    before_dedup = len(df)
    df = df.drop_duplicates(subset='ticket_id')
    report['duplicates_removed'] = before_dedup - len(df)

    report['total_issues'] = n_future + n_missing_csat + n_neg_res + n_typo + report['duplicates_removed']
    report['rows_before'] = rows_before

    return df, report


def compute_ticket_metrics(df: pd.DataFrame, config: Dict[str, Any]) -> Tuple[TicketMetrics, pd.Series, pd.Series]:
    metrics = {}
    df = df.copy()
    if df.empty:
        return _empty_ticket_metrics(), pd.Series(dtype=float), pd.Series(dtype=float)

    df['date'] = df['timestamp'].dt.date

    metrics['total_tickets'] = len(df)

    metrics['open_tickets'] = int(df['status'].isin(['open', 'in_progress']).sum())

    valid_resolved = df[df['resolution_time_hours'].notna() & (df['resolution_time_hours'] > 0)]
    metrics['avg_resolution_hours'] = round(valid_resolved['resolution_time_hours'].mean(), 1)
    metrics['median_resolution_hours'] = round(valid_resolved['resolution_time_hours'].median(), 1)
    metrics['p95_resolution_hours'] = round(valid_resolved['resolution_time_hours'].quantile(0.95), 1)

    sla_hours = config['analytics']['sla_hours']
    sla_breaches = valid_resolved[valid_resolved['resolution_time_hours'] > sla_hours]
    metrics['sla_breach_rate'] = round(len(sla_breaches) / len(valid_resolved) * 100, 1) if len(valid_resolved) > 0 else 0.0
    metrics['sla_compliance_pct'] = round(100 - metrics['sla_breach_rate'], 1)

    metrics['avg_csat'] = round(df['customer_satisfaction'].mean(), 2)
    metrics['csat_trend'] = round(week_over_week_change(df.groupby('date')['customer_satisfaction'].mean()), 1)

    daily_counts = df.groupby('date').size()
    metrics['daily_avg_volume'] = round(daily_counts.mean(), 1)
    metrics['volume_trend'] = round(week_over_week_change(daily_counts), 1)
    anomaly_mask = detect_anomalies(daily_counts, config['analytics']['anomaly_z_threshold'])
    metrics['volume_anomalies'] = int(anomaly_mask.sum())
    metrics['_volume_anomaly_mask'] = anomaly_mask
    metrics['_daily_counts_index'] = daily_counts.index

    metrics['category_distribution'] = df['category'].value_counts().to_dict()

    metrics['priority_distribution'] = df['priority'].value_counts().to_dict()

    daily_resolution = valid_resolved.groupby('date')['resolution_time_hours'].mean()
    metrics['resolution_trend'] = round(week_over_week_change(daily_resolution), 1)

    return metrics, daily_counts, daily_resolution


def _empty_ticket_metrics() -> TicketMetrics:
    return {
        'total_tickets': 0, 'open_tickets': 0,
        'avg_resolution_hours': 0, 'median_resolution_hours': 0, 'p95_resolution_hours': 0,
        'sla_breach_rate': 0.0, 'sla_compliance_pct': 100.0, 'avg_csat': 0.0, 'csat_trend': 0.0,
        'daily_avg_volume': 0, 'volume_trend': 0.0, 'volume_anomalies': 0,
        'category_distribution': {}, 'priority_distribution': {},
        'resolution_trend': 0.0, '_volume_anomaly_mask': pd.Series(dtype=bool), '_daily_counts_index': pd.Index([]),
    }


def compute_sla_table(df, sla_hours):
    if df.empty:
        return pd.DataFrame()
    valid = df[df['resolution_time_hours'].notna() & (df['resolution_time_hours'] > 0)].copy()
    valid['breach'] = valid['resolution_time_hours'] > sla_hours
    sla = valid.groupby('category').agg(
        total=('breach', 'count'),
        breaches=('breach', 'sum'),
    )
    sla['compliance_pct'] = round((1 - sla['breaches'] / sla['total']) * 100, 1)
    return sla.reset_index()
