import pandas as pd
import numpy as np
from scipy import stats
from typing import Dict, List, Any, Union, Optional, Tuple


def detect_anomalies(series: pd.Series, z_threshold: float = 2.0) -> pd.Series:
    """Return a boolean mask aligned to the input series index."""
    if len(series) < 4:
        return pd.Series(False, index=series.index)
    z = np.abs(stats.zscore(series.fillna(series.mean())))
    return pd.Series(z > z_threshold, index=series.index)


def week_over_week_change(series: pd.Series) -> float:
    if len(series) < 14:
        return 0.0
    recent = series.iloc[-7:].mean()
    prior = series.iloc[-14:-7].mean()
    if prior == 0:
        return 0.0
    return ((recent - prior) / prior) * 100


def rag_status(
    value: Union[int, float, None],
    warning_threshold: float,
    critical_threshold: float,
    higher_is_better: bool = True
) -> str:
    if value is None or not isinstance(value, (int, float)):
        return 'red'
    if higher_is_better:
        if value >= warning_threshold:
            return 'green'
        elif value >= critical_threshold:
            return 'amber'
        return 'red'
    else:
        if value <= warning_threshold:
            return 'green'
        elif value <= critical_threshold:
            return 'amber'
        return 'red'



