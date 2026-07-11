import numpy as np
import pandas as pd
from datetime import datetime, timedelta


ASSIGNEES = ['alice', 'bob', 'charlie', 'diana', 'eve']


def generate_tickets(config, incidents_df=None):
    cfg = config['data']['tickets']
    dq = cfg['data_quality']
    end_date = datetime.now()
    start_date = end_date - timedelta(days=cfg['days'])

    np.random.seed(None)

    categories = cfg['categories']
    priorities = list(cfg['priority_weights'].keys())
    priority_weights = list(cfg['priority_weights'].values())
    statuses = ['open', 'in_progress', 'resolved', 'closed']

    hour_weights = {h: 3 if 9 <= h <= 17 else 1 for h in range(24)}
    weekday_weights = {d: 5 if d < 5 else 1 for d in range(7)}

    n = np.random.randint(cfg['count_min'], cfg['count_max'])
    timestamps = []
    used_categories = []

    for _ in range(n):
        t = _random_timestamp(start_date, end_date, hour_weights, weekday_weights)
        timestamps.append(t)

        cat = _pick_category(t, categories, incidents_df)
        used_categories.append(cat)

    timestamps = sorted(timestamps)

    ticket_ids = [f"TKT-{i:05d}" for i in range(n)]

    priorities_list = np.random.choice(priorities, size=n, p=priority_weights)
    assignees = np.random.choice(ASSIGNEES, size=n)

    resolution_hours = np.random.lognormal(
        mean=np.log(cfg['resolution_hours_mean']),
        sigma=0.6,
        size=n
    )

    csat = np.random.normal(cfg['csat_mean'], cfg['csat_std'], size=n)
    csat = np.clip(csat, 1, 5).round(1)

    now_ts = pd.Timestamp.now()
    status_list = []
    for i, t in enumerate(timestamps):
        age_hours = (now_ts - t).total_seconds() / 3600
        res_h = resolution_hours[i]
        if age_hours < 1:
            status_list.append('open')
        elif age_hours < res_h * 0.5:
            status_list.append('in_progress')
        else:
            status_list.append(np.random.choice(['resolved', 'closed'], p=[0.4, 0.6]))

    df = pd.DataFrame({
        'ticket_id': ticket_ids,
        'timestamp': timestamps,
        'category': used_categories,
        'priority': priorities_list,
        'status': status_list,
        'assignee': assignees,
        'resolution_time_hours': resolution_hours.round(1),
        'customer_satisfaction': csat,
    })

    df, issues = _inject_data_quality(df, dq, cfg['dirty_categories'])

    return df, issues


def _random_timestamp(start, end, hour_weights, weekday_weights):
    while True:
        t = start + timedelta(
            days=np.random.randint(0, (end - start).days),
            hours=np.random.randint(0, 24),
            minutes=np.random.randint(0, 60)
        )
        w = weekday_weights.get(t.weekday(), 1) * hour_weights.get(t.hour, 1)
        if np.random.random() < w / 5.0:
            return pd.Timestamp(t)


def _pick_category(timestamp, categories, incidents_df):
    if incidents_df is not None and len(incidents_df) > 0 and np.random.random() < 0.15:
        nearby = incidents_df[
            (incidents_df['start_time'] <= timestamp + timedelta(hours=48)) &
            (incidents_df['end_time'] >= timestamp - timedelta(hours=24))
        ]
        if len(nearby) > 0:
            chosen = nearby.sample(1).iloc[0]
            return chosen['cause_category']

    return np.random.choice(categories)


def _inject_data_quality(df, dq, dirty_categories):
    issues = []

    n_missing = int(len(df) * dq['missing_csat_rate'])
    if n_missing > 0:
        idxs = np.random.choice(len(df), size=n_missing, replace=False)
        df.loc[idxs, 'customer_satisfaction'] = np.nan
        issues.append(f"{n_missing} tickets with missing CSAT scores")

    n_neg = int(len(df) * dq['negative_resolution_rate'])
    if n_neg > 0:
        idxs = np.random.choice(len(df), size=n_neg, replace=False)
        df.loc[idxs, 'resolution_time_hours'] = -abs(df.loc[idxs, 'resolution_time_hours'])
        issues.append(f"{n_neg} tickets with negative resolution times")

    n_dup = int(len(df) * dq['duplicate_rate'])
    if n_dup > 0:
        idxs = np.random.choice(len(df), size=n_dup, replace=False)
        dup_rows = df.iloc[idxs].copy()
        df = pd.concat([df, dup_rows], ignore_index=True)
        issues.append(f"{n_dup} duplicate ticket entries")

    n_typo = int(len(df) * dq['typo_rate'])
    if n_typo > 0:
        idxs = np.random.choice(len(df), size=n_typo, replace=False)
        for idx in idxs:
            df.loc[idx, 'category'] = np.random.choice(dirty_categories)
        issues.append(f"{n_typo} tickets with inconsistent category names")

    n_future = int(len(df) * dq['future_timestamp_rate'])
    if n_future > 0:
        idxs = np.random.choice(len(df), size=n_future, replace=False)
        for idx in idxs:
            df.loc[idx, 'timestamp'] = pd.Timestamp.now() + timedelta(days=np.random.randint(1, 30))
        issues.append(f"{n_future} tickets with future timestamps")

    df = df.sort_values('timestamp').reset_index(drop=True)
    return df, issues
