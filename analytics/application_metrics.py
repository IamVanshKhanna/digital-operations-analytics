from typing import Tuple, Dict, List, Any
import pandas as pd
import numpy as np
from analytics.metrics import week_over_week_change
from analytics.types import AppMetrics, QualityReport


STAGE_ORDER = ['applied', 'screened', 'interviewed', 'offered', 'accepted']


def clean_applications(df: pd.DataFrame, config: Dict[str, Any]) -> Tuple[pd.DataFrame, QualityReport]:
    report = {}
    df = df.copy()
    if df.empty:
        report['total_issues'] = 0
        return df, report

    now = pd.Timestamp.now()

    df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')

    n_future = df['timestamp'].gt(now).sum()
    report['future_timestamps'] = n_future
    df = df[df['timestamp'] <= now]

    n_missing_id = df['application_id'].isna().sum()
    report['missing_ids'] = n_missing_id
    df = df.dropna(subset=['application_id'])

    n_unknown = (df['source'] == 'unknown').sum()
    report['unknown_source'] = n_unknown

    report['total_issues'] = n_future + n_missing_id + n_unknown
    return df, report


def compute_application_metrics(df: pd.DataFrame, config: Dict[str, Any]) -> Tuple[AppMetrics, pd.Series]:
    metrics = {}
    df = df.copy()
    if df.empty:
        return _empty_app_metrics(), pd.Series(dtype=float)

    df['date'] = df['timestamp'].dt.date

    metrics['total_applications'] = len(df)

    stage_counts = df['stage'].value_counts()
    for stage in STAGE_ORDER + ['rejected']:
        metrics[f'{stage}_count'] = int(stage_counts.get(stage, 0))

    accepted = df[df['stage'] == 'accepted']
    metrics['accepted_count'] = len(accepted)
    metrics['conversion_rate'] = round(len(accepted) / len(df) * 100, 1) if len(df) > 0 else 0.0

    rejected_count = stage_counts.get('rejected', 0)
    non_rejected = len(df) - rejected_count

    funnel_data = []
    cumulative_stages = {
        'applied': non_rejected,
        'screened': stage_counts.get('screened', 0) + stage_counts.get('interviewed', 0) + stage_counts.get('offered', 0) + stage_counts.get('accepted', 0),
        'interviewed': stage_counts.get('interviewed', 0) + stage_counts.get('offered', 0) + stage_counts.get('accepted', 0),
        'offered': stage_counts.get('offered', 0) + stage_counts.get('accepted', 0),
        'accepted': stage_counts.get('accepted', 0),
    }
    prev_count = non_rejected
    for stage in STAGE_ORDER:
        count = cumulative_stages[stage]
        conversion = round(count / prev_count * 100, 1) if prev_count > 0 else 0.0
        funnel_data.append({'stage': stage, 'count': count, 'from_previous_pct': conversion})
        prev_count = count
    metrics['funnel'] = funnel_data

    daily_counts = df.groupby('date').size()
    metrics['daily_avg'] = round(daily_counts.mean(), 1)
    metrics['volume_trend'] = round(week_over_week_change(daily_counts), 1)

    source_dist = df['source'].value_counts()
    metrics['source_distribution'] = source_dist.to_dict()
    if len(source_dist) > 0:
        top_source = source_dist.index[0]
        metrics['top_source'] = top_source
        metrics['top_source_pct'] = round(source_dist[top_source] / len(df) * 100, 1)

    role_dist = df['role'].value_counts()
    metrics['role_distribution'] = role_dist.to_dict()

    time_to_hire = df[df['stage'] == 'accepted']['days_in_stage']
    metrics['avg_time_to_hire'] = round(time_to_hire.mean(), 1) if len(time_to_hire) > 0 else None

    metrics['stage_dropout'] = _compute_dropout(df)

    return metrics, daily_counts


def _compute_dropout(df):
    stage_order_with_rejected = STAGE_ORDER + ['rejected']
    total = len(df)
    dropouts = []
    for stage in stage_order_with_rejected:
        count = len(df[df['stage'] == stage])
        dropouts.append({'stage': stage, 'count': count, 'pct_of_total': round(count / total * 100, 1)})
    return dropouts


def _empty_app_metrics() -> AppMetrics:
    return {
        'total_applications': 0, 'conversion_rate': 0.0, 'accepted_count': 0,
        'applied_count': 0, 'screened_count': 0, 'interviewed_count': 0,
        'offered_count': 0, 'accepted_count': 0, 'rejected_count': 0,
        'funnel': [{'stage': s, 'count': 0, 'from_previous_pct': 0.0} for s in STAGE_ORDER],
        'daily_avg': 0, 'volume_trend': 0.0,
        'source_distribution': {}, 'role_distribution': {},
        'top_source': None, 'top_source_pct': 0,
        'avg_time_to_hire': None,
        'stage_dropout': [{'stage': s, 'count': 0, 'pct_of_total': 0.0} for s in STAGE_ORDER + ['rejected']],
    }


def compute_source_effectiveness(df):
    results = []
    if df.empty or 'source' not in df.columns:
        return pd.DataFrame(results)
    for source in df['source'].unique():
        sdf = df[df['source'] == source]
        total = len(sdf)
        accepted = len(sdf[sdf['stage'] == 'accepted'])
        conv = round(accepted / total * 100, 1) if total > 0 else 0
        avg_days = round(sdf[sdf['stage'] == 'accepted']['days_in_stage'].mean(), 1) if accepted > 0 else None
        results.append({
            'source': source,
            'applications': total,
            'accepted': accepted,
            'conversion_pct': conv,
            'avg_days_to_hire': avg_days,
        })
    return pd.DataFrame(results).sort_values('applications', ascending=False)
