import numpy as np
import pandas as pd
from datetime import datetime, timedelta


ROLE_WEIGHTS = {
    'software-engineer': 0.35,
    'devops-engineer': 0.20,
    'data-scientist': 0.15,
    'product-manager': 0.15,
    'designer': 0.15,
}


def generate_applications(config):
    cfg = config['data']['applications']
    dq = cfg['data_quality']
    end_date = datetime.now()
    start_date = end_date - timedelta(days=cfg['days'])

    np.random.seed(None)

    n = np.random.randint(cfg['count_min'], cfg['count_max'])
    roles = list(cfg['role_weights'].keys())
    role_weights = list(cfg['role_weights'].values())
    sources = list(cfg['source_weights'].keys())
    source_weights = list(cfg['source_weights'].values())

    timestamps = []
    for _ in range(n):
        t = start_date + timedelta(
            days=np.random.randint(0, cfg['days']),
            hours=np.random.randint(0, 24),
            minutes=np.random.randint(0, 60)
        )
        timestamps.append(pd.Timestamp(t))

    timestamps = sorted(timestamps)

    app_ids = [f"APP-{i:05d}" for i in range(n)]
    assigned_roles = np.random.choice(roles, size=n, p=role_weights)
    assigned_sources = np.random.choice(sources, size=n, p=source_weights)

    now_ts = pd.Timestamp.now()
    stages = []
    days_in_stage = []
    offer_amounts = []

    for i, t in enumerate(timestamps):
        age_days = (now_ts - t).days
        stage, days = _assign_stage(age_days)
        stages.append(stage)
        days_in_stage.append(days)

        if stage == 'accepted':
            amount = np.random.normal(120000, 30000)
            amount = max(50000, round(amount / 10000) * 10000)
            offer_amounts.append(int(amount))
        else:
            offer_amounts.append(None)

    df = pd.DataFrame({
        'application_id': app_ids,
        'timestamp': timestamps,
        'role': assigned_roles,
        'source': assigned_sources,
        'stage': stages,
        'days_in_stage': days_in_stage,
        'offer_amount': offer_amounts,
    })

    df, issues = _inject_data_quality(df, dq)

    return df, issues


def _assign_stage(age_days):
    if age_days < 7:
        stage = np.random.choice(['applied', 'screened'], p=[0.7, 0.3])
        days = np.random.randint(0, age_days + 1)
    elif age_days < 21:
        stage = np.random.choice(['applied', 'screened', 'interviewed', 'rejected'],
                                  p=[0.1, 0.3, 0.4, 0.2])
        days = np.random.randint(0, min(14, age_days + 1))
    elif age_days < 45:
        stage = np.random.choice(['screened', 'interviewed', 'offered', 'rejected'],
                                  p=[0.05, 0.3, 0.25, 0.4])
        days = np.random.randint(0, min(21, age_days + 1))
    else:
        stage = np.random.choice(['interviewed', 'offered', 'accepted', 'rejected'],
                                  p=[0.05, 0.15, 0.2, 0.6])
        days = np.random.randint(0, min(30, age_days + 1))

    return stage, days


def _inject_data_quality(df, dq):
    issues = []

    n_impossible = int(len(df) * dq['impossible_transition_rate'])
    if n_impossible > 0:
        idxs = np.random.choice(len(df), size=n_impossible, replace=False)
        for idx in idxs:
            df.loc[idx, 'stage'] = 'accepted'
            df.loc[idx, 'days_in_stage'] = 0
        issues.append(f"{n_impossible} applications with impossible stage transitions")

    n_missing = int(len(df) * dq['missing_id_rate'])
    if n_missing > 0:
        idxs = np.random.choice(len(df), size=n_missing, replace=False)
        df.loc[idxs, 'application_id'] = np.nan
        issues.append(f"{n_missing} applications with missing IDs")

    n_future = int(len(df) * dq['future_timestamp_rate'])
    if n_future > 0:
        idxs = np.random.choice(len(df), size=n_future, replace=False)
        for idx in idxs:
            df.loc[idx, 'timestamp'] = pd.Timestamp.now() + timedelta(days=np.random.randint(1, 14))
        issues.append(f"{n_future} applications with future timestamps")

    n_unknown = int(len(df) * dq['unknown_source_rate'])
    if n_unknown > 0:
        idxs = np.random.choice(len(df), size=n_unknown, replace=False)
        df.loc[idxs, 'source'] = 'unknown'
        issues.append(f"{n_unknown} applications with unknown source")

    return df, issues
