import numpy as np
import pandas as pd
from datetime import datetime, timedelta


SERVICE_CATEGORY_MAP = {
    'database': ['bug', 'performance'],
    'auth-service': ['account', 'security'],
    'web-server': ['bug', 'performance'],
    'api-gateway': ['bug', 'performance'],
    'cache': ['performance'],
    'dns': ['performance'],
    'file-storage': ['bug'],
    'monitoring': ['bug'],
}


def generate_services(config):
    cfg = config['data']['services']
    dq = cfg['data_quality']
    end_date = datetime.now()
    start_date = end_date - timedelta(days=cfg['days'])
    interval_minutes = cfg['check_interval_minutes']

    timestamps = pd.date_range(start=start_date, end=end_date, freq=f'{interval_minutes}min', inclusive='left')
    services = cfg['names']
    np.random.seed(None)

    rows = []
    incidents = []

    for service in services:
        n_incidents = np.random.randint(cfg['incidents_per_service_min'], cfg['incidents_per_service_max'] + 1)
        idxs = np.random.choice(len(timestamps), size=n_incidents, replace=False)
        incident_times = sorted([pd.Timestamp(timestamps[i]) for i in idxs])

        incident_dfs_by_service = []
        for t in incident_times:
            duration = np.random.randint(5, 121)
            cause_category = list(SERVICE_CATEGORY_MAP[service])[np.random.randint(0, len(SERVICE_CATEGORY_MAP[service]))]
            incident_end = t + timedelta(minutes=duration)
            incident_dfs_by_service.append({
                'service': service,
                'start_time': t,
                'end_time': incident_end,
                'duration_minutes': duration,
                'cause_category': cause_category,
            })

        incidents.extend(incident_dfs_by_service)

        for idx, t in enumerate(timestamps):
            ts = pd.Timestamp(t)
            status = 'up'
            response_time = np.random.normal(cfg['response_time_ms_mean'], cfg['response_time_ms_std'])

            for inc in incident_dfs_by_service:
                if inc['start_time'] <= ts <= inc['end_time']:
                    status = 'down'
                    response_time = np.random.normal(500, 200)
                    break
                elif inc['end_time'] < ts < inc['end_time'] + timedelta(hours=2):
                    if status == 'up':
                        status = 'degraded'
                        response_time = np.random.normal(200, 100)

            response_time = max(0, response_time)
            rows.append({'service': service, 'timestamp': ts, 'status': status, 'response_time_ms': round(response_time, 1)})

    df = pd.DataFrame(rows)
    incidents_df = pd.DataFrame(incidents)

    df, dq_issues = _inject_data_quality(df, dq)

    return df, incidents_df, dq_issues


def _inject_data_quality(df, dq):
    issues = []

    df = df.sort_values('timestamp').reset_index(drop=True)

    n_missing = int(len(df) * dq['missing_rate'])
    if n_missing > 0:
        idxs = np.random.choice(len(df), size=n_missing, replace=False)
        df.loc[idxs, 'response_time_ms'] = np.nan
        issues.append(f"{n_missing} missing response_time values")

    n_neg = int(len(df) * dq['negative_response_rate'])
    if n_neg > 0:
        idxs = np.random.choice(len(df), size=n_neg, replace=False)
        df.loc[idxs, 'response_time_ms'] = -abs(df.loc[idxs, 'response_time_ms'])
        issues.append(f"{n_neg} negative response_time values")

    n_dup = int(len(df) * dq['duplicate_rate'])
    if n_dup > 0:
        idxs = np.random.choice(len(df), size=n_dup, replace=False)
        dup_rows = df.iloc[idxs].copy()
        df = pd.concat([df, dup_rows], ignore_index=True)
        df = df.sort_values('timestamp').reset_index(drop=True)
        issues.append(f"{n_dup} duplicate entries")

    n_out_of_order = int(len(df) * dq['out_of_order_rate'])
    if n_out_of_order > 0:
        dfs_reordered = []
        swapped = 0
        for service in df['service'].unique():
            sdf = df[df['service'] == service].copy()
            idxs = list(range(len(sdf)))
            i = 0
            while i < len(idxs) - 1 and swapped < n_out_of_order:
                if np.random.random() < 0.5:
                    idxs[i], idxs[i + 1] = idxs[i + 1], idxs[i]
                    swapped += 1
                    i += 2
                else:
                    i += 1
            dfs_reordered.append(sdf.iloc[idxs].reset_index(drop=True))
        df = pd.concat(dfs_reordered, ignore_index=True)
        issues.append(f"{swapped} out-of-order timestamps")

    return df, issues
