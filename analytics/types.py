from typing import TypedDict, List, Dict, Optional
import pandas as pd


class TicketMetrics(TypedDict):
    total_tickets: int
    open_tickets: int
    avg_resolution_hours: float
    median_resolution_hours: float
    p95_resolution_hours: float
    sla_breach_rate: float
    sla_compliance_pct: float
    avg_csat: float
    csat_trend: float
    daily_avg_volume: float
    volume_trend: float
    volume_anomalies: int
    _volume_anomaly_mask: pd.Series
    _daily_counts_index: pd.Index
    category_distribution: Dict[str, int]
    priority_distribution: Dict[str, int]
    resolution_trend: float


class ServiceMetrics(TypedDict):
    uptime_pct: float
    degraded_pct: float
    total_incidents: int
    avg_mttr_minutes: float
    max_mttr_minutes: int
    avg_response_time_ms: float
    p95_response_time_ms: float
    response_trend: float
    uptime_response_ms: float


class FunnelStage(TypedDict):
    stage: str
    count: int
    from_previous_pct: float


class StageDropout(TypedDict):
    stage: str
    count: int
    pct_of_total: float


class AppMetrics(TypedDict):
    total_applications: int
    conversion_rate: float
    accepted_count: int
    applied_count: int
    screened_count: int
    interviewed_count: int
    offered_count: int
    rejected_count: int
    funnel: List[FunnelStage]
    daily_avg: float
    volume_trend: float
    source_distribution: Dict[str, int]
    role_distribution: Dict[str, int]
    top_source: Optional[str]
    top_source_pct: float
    avg_time_to_hire: Optional[float]
    stage_dropout: List[StageDropout]


class QualityReport(TypedDict, total=False):
    total_issues: int
    rows_before: int
    future_timestamps: int
    missing_csat: int
    negative_resolution: int
    category_typos: int
    duplicates_removed: int
    missing_response: int
    negative_response: int
    duplicates: int
    out_of_order: int
    missing_ids: int
    unknown_source: int
