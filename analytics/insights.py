from typing import Dict, Any, List, Optional
from analytics.types import TicketMetrics, ServiceMetrics, AppMetrics, QualityReport


def compute_dq_score(
    tickets_dq: QualityReport,
    services_dq: QualityReport,
    apps_dq: QualityReport,
    total_records: int,
) -> str:
    total_issues = sum([
        tickets_dq.get('total_issues', 0),
        services_dq.get('total_issues', 0),
        apps_dq.get('total_issues', 0),
    ])
    if total_issues == 0 or total_records == 0:
        return '100%'
    score = max(0, 100 - (total_issues / total_records * 100))
    return f'{score:.0f}%'


def compute_dq_rag(
    tickets_dq: QualityReport,
    services_dq: QualityReport,
    apps_dq: QualityReport,
    total_records: int,
    config: Optional[Dict[str, Any]] = None,
) -> str:
    total_issues = sum([
        tickets_dq.get('total_issues', 0),
        services_dq.get('total_issues', 0),
        apps_dq.get('total_issues', 0),
    ])
    if total_issues == 0 or total_records == 0:
        return 'green'
    rate = total_issues / total_records
    if config:
        th = config.get('analytics', {}).get('thresholds', {}).get('data_quality', {})
        warn = th.get('warning', 0.02)
        crit = th.get('critical', 0.05)
    else:
        warn, crit = 0.02, 0.05
    if rate < warn:
        return 'green'
    elif rate < crit:
        return 'amber'
    return 'red'


def generate_alerts(
    ticket_m: TicketMetrics,
    service_m: ServiceMetrics,
    app_m: AppMetrics,
    tickets_dq: QualityReport,
    services_dq: QualityReport,
    apps_dq: QualityReport,
    config: Dict[str, Any],
) -> List[Dict[str, Any]]:
    alerts = []
    al = config['analytics'].get('alerts', {})
    uptime_critical = config['analytics']['uptime_critical']
    uptime_warning = config['analytics']['uptime_warning']
    sla_high = al.get('sla_breach_percent', {}).get('high', 10)
    sla_warn = al.get('sla_breach_percent', {}).get('warning', 5)
    incidents_max = al.get('incidents', 20)
    conv_min = al.get('conversion_critical', 5)
    dq_max = al.get('dq_issues', 50)

    sla_breach = ticket_m.get('sla_breach_rate', 0)
    if sla_breach > sla_high:
        alerts.append({'severity': 'high', 'message': f'SLA breach rate at {sla_breach}% — above {sla_high}% threshold'})
    elif sla_breach > sla_warn:
        alerts.append({'severity': 'medium', 'message': f'SLA breach rate at {sla_breach}% — monitor closely'})
    if ticket_m.get('volume_anomalies', 0) > 0:
        alerts.append({'severity': 'medium', 'message': f'{ticket_m["volume_anomalies"]} anomalous days detected in ticket volume'})
    if service_m.get('uptime_pct', 100) < uptime_critical:
        alerts.append({'severity': 'high', 'message': f'Overall uptime at {service_m["uptime_pct"]}% — below critical threshold'})
    elif service_m.get('uptime_pct', 100) < uptime_warning:
        alerts.append({'severity': 'medium', 'message': f'Overall uptime at {service_m["uptime_pct"]}% — below warning threshold'})
    if service_m.get('total_incidents', 0) > incidents_max:
        alerts.append({'severity': 'medium', 'message': f'{service_m["total_incidents"]} total incidents recorded in this period'})
    if app_m.get('conversion_rate', 100) < conv_min:
        alerts.append({'severity': 'high', 'message': f'Conversion rate at {app_m["conversion_rate"]}% — critically low'})
    for dq in [tickets_dq, services_dq, apps_dq]:
        if dq.get('total_issues', 0) > dq_max:
            alerts.append({'severity': 'medium', 'message': 'High data quality issue count detected — review data pipelines'})
    return alerts


def generate_insights(
    ticket_m: TicketMetrics,
    service_m: ServiceMetrics,
    app_m: AppMetrics,
) -> List[str]:
    insights = []
    insights.append(f'Ticket volume averaged {ticket_m["daily_avg_volume"]:.0f} tickets/day '
                    f'with a {ticket_m["volume_trend"]:+.1f}% WoW trend.')
    insights.append(f'Average resolution time is {ticket_m["avg_resolution_hours"]}h '
                    f'({ticket_m["resolution_trend"]:+.1f}% WoW).')
    cat_dist = ticket_m.get('category_distribution', {})
    if cat_dist:
        top_cat = max(cat_dist, key=cat_dist.get)
        top_cat_pct = cat_dist[top_cat] / max(ticket_m['total_tickets'], 1) * 100
        insights.append(f'Most common ticket category: "{top_cat}" ({top_cat_pct:.0f}% of all tickets).')
    if service_m.get('total_incidents', 0) > 0:
        insights.append(f'Infrastructure experienced {service_m["total_incidents"]} incidents with '
                        f'MTTR averaging {service_m["avg_mttr_minutes"]}m (max {service_m["max_mttr_minutes"]}m).')
    if app_m.get('avg_time_to_hire'):
        insights.append(f'Average time-to-hire is {app_m["avg_time_to_hire"]} days at a '
                        f'{app_m["conversion_rate"]}% conversion rate.')
    if app_m.get('top_source'):
        insights.append(f'"{app_m["top_source"]}" is the most common application source '
                        f'({app_m["top_source_pct"]}% of all applications).')
    return insights
