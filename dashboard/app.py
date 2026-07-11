import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from data.generate_all import generate_all
from analytics.metrics import (
    rag_status, detect_anomalies,
)
from analytics.ticket_metrics import (
    compute_ticket_metrics, compute_sla_table, clean_tickets,
)
from analytics.service_metrics import (
    compute_service_metrics, compute_per_service_uptime,
    compute_incident_timeline, clean_services,
)
from analytics.application_metrics import (
    compute_application_metrics, compute_source_effectiveness, clean_applications,
)
from analytics.insights import (
    compute_dq_score, compute_dq_rag, generate_alerts, generate_insights,
)
from dashboard.style import (
    get_css, get_chart_template, SN_TEAL, RAG_GREEN, RAG_AMBER, RAG_RED, rag_hex,
    CHART_BLUES, CHART_REDS, CHART_RDYLGN, CHART_RDBU,
)


@st.cache_data(ttl=3600)
def load_data():
    data = generate_all()
    return data


def _safe_chart(fig, container_width=True):
    try:
        if fig is not None:
            st.plotly_chart(fig, use_container_width=container_width)
    except Exception:
        st.caption('This chart could not be rendered.')


def apply_chart_theme(fig):
    tmpl = get_chart_template(st.session_state.get('dark_mode', False))
    fig.update_layout(**tmpl['layout'])
    return fig


def main():
    st.set_page_config(page_title='Digital Operations Analytics', layout='wide')

    dark_mode = st.session_state.get('dark_mode', False)
    st.markdown(get_css(dark_mode), unsafe_allow_html=True)

    data = load_data()
    config = data['config']

    tickets_raw = data['tickets']
    services_raw = data['services']
    applications_raw = data['applications']
    incidents_df = data['incidents']
    tickets_clean, tickets_dq = clean_tickets(tickets_raw, config)
    services_clean, services_dq = clean_services(services_raw)
    applications_clean, apps_dq = clean_applications(applications_raw, config)

    total_records = len(tickets_raw) + len(services_raw) + len(applications_raw)

    st.sidebar.title('Filters')
    st.sidebar.checkbox('Dark Mode', key='dark_mode')
    st.sidebar.markdown('<hr style="margin:0 0 1rem 0">', unsafe_allow_html=True)

    ts_min = pd.Timestamp.min.to_pydatetime()
    ts_max = pd.Timestamp.now()
    d_min = min(
        tickets_clean['timestamp'].min() if not tickets_clean.empty else ts_max,
        services_clean['timestamp'].min() if not services_clean.empty else ts_max,
        applications_clean['timestamp'].min() if not applications_clean.empty else ts_max,
    )
    d_max = max(
        tickets_clean['timestamp'].max() if not tickets_clean.empty else ts_min,
        services_clean['timestamp'].max() if not services_clean.empty else ts_min,
        applications_clean['timestamp'].max() if not applications_clean.empty else ts_min,
    )
    date_range = st.sidebar.date_input('Date Range', [d_min.date(), d_max.date()])

    all_categories = sorted(tickets_clean['category'].unique())
    selected_categories = st.sidebar.multiselect('Ticket Categories', all_categories, default=all_categories)

    all_services = sorted(services_clean['service'].unique())
    selected_services = st.sidebar.multiselect('Services', all_services, default=all_services)

    tickets_filtered = tickets_clean[
        (tickets_clean['timestamp'].dt.date >= date_range[0]) &
        (tickets_clean['timestamp'].dt.date <= date_range[1]) &
        (tickets_clean['category'].isin(selected_categories))
    ]

    services_filtered = services_clean[
        (services_clean['timestamp'].dt.date >= date_range[0]) &
        (services_clean['timestamp'].dt.date <= date_range[1]) &
        (services_clean['service'].isin(selected_services))
    ]

    applications_filtered = applications_clean[
        (applications_clean['timestamp'].dt.date >= date_range[0]) &
        (applications_clean['timestamp'].dt.date <= date_range[1])
    ]

    if incidents_df is not None and len(incidents_df) > 0:
        incidents_filtered = incidents_df[
            (incidents_df['start_time'].dt.date >= date_range[0]) &
            (incidents_df['start_time'].dt.date <= date_range[1]) &
            (incidents_df['service'].isin(selected_services))
        ].copy()
    else:
        incidents_filtered = pd.DataFrame()

    st.title('Digital Operations Analytics')
    st.markdown('<p style="color:#6b7280;margin-top:-0.5rem">Support Operations · Service Health · Talent Pipeline</p>', unsafe_allow_html=True)

    ticket_metrics, daily_tickets, daily_resolution = compute_ticket_metrics(tickets_filtered, config)
    service_metrics = compute_service_metrics(services_filtered, incidents_filtered, config)
    app_metrics, daily_apps = compute_application_metrics(applications_filtered, config)

    tabs = st.tabs(['Executive Summary', 'Support Operations', 'Service Health', 'Talent Pipeline', 'Insights'])

    # ─── TAB 1: EXECUTIVE SUMMARY ───────────────────────────────────────────────

    with tabs[0]:
        st.header('Executive Summary')

        th = config['analytics'].get('thresholds', {})
        kpis = [
            {'label': 'Service Health', 'value': f'{service_metrics["uptime_pct"]}%', 'rag': rag_status(service_metrics['uptime_pct'], config['analytics']['uptime_warning'], config['analytics']['uptime_critical'], True)},
            {'label': 'Support SLA', 'value': f'{ticket_metrics["sla_compliance_pct"]}%', 'rag': rag_status(ticket_metrics['sla_compliance_pct'], th.get('sla_compliance', {}).get('warning', 95), th.get('sla_compliance', {}).get('critical', 90), True)},
            {'label': 'Conversion Rate', 'value': f'{app_metrics["conversion_rate"]}%', 'rag': rag_status(app_metrics['conversion_rate'], th.get('conversion', {}).get('warning', 15), th.get('conversion', {}).get('critical', 10), True)},
            {'label': 'Data Quality', 'value': compute_dq_score(tickets_dq, services_dq, apps_dq, total_records), 'rag': compute_dq_rag(tickets_dq, services_dq, apps_dq, total_records, config)},
        ]

        cols = st.columns(4)
        for i, kpi in enumerate(kpis):
            with cols[i]:
                color = rag_hex(kpi['rag'])
                st.markdown(
                    f'<div class="sn-metric-card" style="border-left:4px solid {color}">'
                    f'<div class="sn-card-header">'
                    f'<span class="sn-card-label">{kpi["label"]}</span>'
                    f'<span class="sn-card-rag" style="background:{color}"></span>'
                    f'</div>'
                    f'<div class="sn-card-value" style="color:{color}">{kpi["value"]}</div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )

        st.markdown('<div class="sn-section-header">Key Alerts</div>', unsafe_allow_html=True)
        alerts = generate_alerts(ticket_metrics, service_metrics, app_metrics, tickets_dq, services_dq, apps_dq, config)
        for alert in alerts:
            color = {'high': RAG_RED, 'medium': RAG_AMBER, 'low': SN_TEAL}.get(alert['severity'], SN_TEAL)
            st.markdown(
                f'<div class="sn-alert" style="border-left-color:{color}">'
                f'<span class="sn-alert-severity" style="color:{color}">{alert["severity"]}</span> '
                f'{alert["message"]}'
                f'</div>',
                unsafe_allow_html=True,
            )

        st.markdown('<div class="sn-section-header">Trend Overview</div>', unsafe_allow_html=True)
        col1, col2 = st.columns(2)

        with col1:
            if len(daily_tickets) > 1:
                fig = px.line(
                    x=daily_tickets.index, y=daily_tickets.values,
                    title='Daily Ticket Volume',
                    labels={'x': 'Date', 'y': 'Tickets'},
                    color_discrete_sequence=[SN_TEAL],
                )
                fig.update_layout(height=250, margin=dict(l=20, r=20, t=30, b=20), showlegend=False)
                apply_chart_theme(fig)
                _safe_chart(fig)

        with col2:
            if services_filtered is not None and len(services_filtered) > 0:
                daily_resp = services_filtered.groupby(services_filtered['timestamp'].dt.date)['response_time_ms'].mean()
                if len(daily_resp) > 1:
                    fig = px.line(
                        x=daily_resp.index, y=daily_resp.values,
                        title='Avg Response Time (ms)',
                        labels={'x': 'Date', 'y': 'ms'},
                        color_discrete_sequence=[SN_TEAL],
                    )
                    fig.update_layout(height=250, margin=dict(l=20, r=20, t=30, b=20), showlegend=False)
                    apply_chart_theme(fig)
                    _safe_chart(fig)

        st.markdown('<div style="margin-top:1rem;">', unsafe_allow_html=True)
        ecc = st.columns(2)
        with ecc[0]:
            _csv_download(tickets_filtered, 'tickets_export.csv', 'Download Tickets CSV')
        with ecc[1]:
            _csv_download(services_filtered, 'services_export.csv', 'Download Services CSV')

    # ─── TAB 2: SUPPORT OPERATIONS ──────────────────────────────────────────────

    with tabs[1]:
        st.header('Support Operations')

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.markdown(f'<div class="sn-metric-card"><div class="sn-card-label">Total Tickets</div><div class="sn-card-value">{ticket_metrics["total_tickets"]}</div></div>', unsafe_allow_html=True)
        with col2:
            st.markdown(f'<div class="sn-metric-card"><div class="sn-card-label">Open / In Progress</div><div class="sn-card-value">{ticket_metrics["open_tickets"]}</div></div>', unsafe_allow_html=True)
        with col3:
            st.markdown(f'<div class="sn-metric-card"><div class="sn-card-label">Avg Resolution</div><div class="sn-card-value">{ticket_metrics["avg_resolution_hours"]}h</div></div>', unsafe_allow_html=True)
        with col4:
            csat_delta = ticket_metrics["csat_trend"]
            delta_color = '#22c55e' if csat_delta >= 0 else '#f2514d'
            delta = f'{csat_delta:+.1f}% WoW'
            st.markdown(f'<div class="sn-metric-card"><div class="sn-card-label">Avg CSAT</div><div class="sn-card-value">{ticket_metrics["avg_csat"]}</div><div style="font-size:0.8rem;color:{delta_color};font-weight:600">{delta}</div></div>', unsafe_allow_html=True)

        col1, col2 = st.columns(2)

        with col1:
            if len(daily_tickets) > 1:
                anomaly_mask = ticket_metrics.get('_volume_anomaly_mask', detect_anomalies(daily_tickets, config['analytics']['anomaly_z_threshold']))
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=daily_tickets.index, y=daily_tickets.values,
                    mode='lines+markers', name='Volume',
                    line=dict(color=    SN_TEAL, width=2),
                    marker=dict(size=4, color=    SN_TEAL),
                ))
                anomaly_dates = daily_tickets.index[anomaly_mask]
                anomaly_vals = daily_tickets.values[anomaly_mask]
                if len(anomaly_dates) > 0:
                    fig.add_trace(go.Scatter(
                        x=anomaly_dates, y=anomaly_vals,
                        mode='markers', name='Anomalies',
                        marker=dict(color=RAG_RED, size=8, symbol='x', line=dict(width=1, color=RAG_RED)),
                    ))
                fig.update_layout(title='Daily Ticket Volume', height=350)
                apply_chart_theme(fig)
                _safe_chart(fig)

        with col2:
            cats = ticket_metrics['category_distribution']
            if cats:
                cat_df = pd.DataFrame({'Category': list(cats.keys()), 'Count': list(cats.values())})
                fig = px.bar(cat_df, x='Category', y='Count', title='Tickets by Category', color='Count',
                             color_continuous_scale=CHART_BLUES)
                fig.update_layout(height=350)
                apply_chart_theme(fig)
                _safe_chart(fig)

        col1, col2 = st.columns(2)

        with col1:
            if len(daily_resolution) > 1:
                fig = px.line(
                    x=daily_resolution.index, y=daily_resolution.values,
                    title='Avg Resolution Time Trend',
                    labels={'x': 'Date', 'y': 'Hours'},
                    color_discrete_sequence=[SN_TEAL],
                )
                fig.add_hline(y=config['analytics']['sla_hours'], line_dash='dash', line_color=RAG_RED,
                              annotation_text=f'SLA ({config["analytics"]["sla_hours"]}h)')
                fig.update_layout(height=350)
                apply_chart_theme(fig)
                _safe_chart(fig)

        with col2:
            sla_table = compute_sla_table(tickets_filtered, config['analytics']['sla_hours'])
            if len(sla_table) > 0:
                fig = px.bar(sla_table, x='category', y='compliance_pct',
                             title='SLA Compliance by Category', color='compliance_pct',
                             color_continuous_scale=CHART_RDYLGN, range_color=[80, 100])
                sla_ref = th.get('sla_compliance', {}).get('warning', 95)
                fig.add_hline(y=sla_ref, line_dash='dash', line_color=RAG_GREEN)
                fig.update_layout(height=350)
                apply_chart_theme(fig)
                _safe_chart(fig)

        st.markdown('<div style="margin-top:1rem;">', unsafe_allow_html=True)
        ecc2 = st.columns(3)
        with ecc2[0]:
            _csv_download(tickets_filtered, 'support_tickets.csv', 'Download Tickets CSV')
        with ecc2[1]:
            ecc2_sla = compute_sla_table(tickets_filtered, config['analytics']['sla_hours'])
            _csv_download(ecc2_sla, 'sla_compliance.csv', 'Download SLA CSV')
        with ecc2[2]:
            ecc2_daily = daily_tickets.to_frame('count').reset_index()
            _csv_download(ecc2_daily, 'daily_volume.csv', 'Download Volume CSV')

    # ─── TAB 3: SERVICE HEALTH ──────────────────────────────────────────────────

    with tabs[2]:
        st.header('Service Health')

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            uptime_color = rag_hex(rag_status(service_metrics['uptime_pct'], config['analytics']['uptime_warning'], config['analytics']['uptime_critical'], True))
            st.markdown(f'<div class="sn-metric-card" style="border-left:4px solid {uptime_color}"><div class="sn-card-label">Uptime</div><div class="sn-card-value" style="color:{uptime_color}">{service_metrics["uptime_pct"]}%</div></div>', unsafe_allow_html=True)
        with col2:
            st.markdown(f'<div class="sn-metric-card"><div class="sn-card-label">Avg Response</div><div class="sn-card-value">{service_metrics["avg_response_time_ms"]}ms</div></div>', unsafe_allow_html=True)
        with col3:
            st.markdown(f'<div class="sn-metric-card"><div class="sn-card-label">Total Incidents</div><div class="sn-card-value">{service_metrics["total_incidents"]}</div></div>', unsafe_allow_html=True)
        with col4:
            st.markdown(f'<div class="sn-metric-card"><div class="sn-card-label">Avg MTTR</div><div class="sn-card-value">{service_metrics["avg_mttr_minutes"]}m</div></div>', unsafe_allow_html=True)

        per_service = compute_per_service_uptime(services_filtered)
        if len(per_service) > 0:
            fig = px.bar(
                per_service, x='service', y='uptime_pct',
                title='Uptime by Service',
                color='uptime_pct',
                color_continuous_scale=CHART_RDYLGN,
                range_color=[95, 100],
                text=per_service['uptime_pct'].apply(lambda x: f'{x}%'),
            )
            fig.add_hline(y=config['analytics']['uptime_warning'], line_dash='dash', line_color=RAG_AMBER,
                          annotation_text=f'Warning ({config["analytics"]["uptime_warning"]}%)')
            fig.add_hline(y=config['analytics']['uptime_critical'], line_dash='dash', line_color=RAG_RED,
                          annotation_text=f'Critical ({config["analytics"]["uptime_critical"]}%)')
            fig.update_layout(height=400)
            apply_chart_theme(fig)
            _safe_chart(fig)

        col1, col2 = st.columns(2)

        with col1:
            daily_resp = services_filtered.groupby(services_filtered['timestamp'].dt.date)['response_time_ms'].mean()
            if len(daily_resp) > 1:
                fig = px.line(
                    x=daily_resp.index, y=daily_resp.values,
                    title='Avg Response Time (All Services)',
                    labels={'x': 'Date', 'y': 'ms'},
                    color_discrete_sequence=[SN_TEAL],
                )
                fig.update_layout(height=350)
                apply_chart_theme(fig)
                _safe_chart(fig)

        with col2:
            timeline = compute_incident_timeline(incidents_filtered)
            if len(timeline) > 0:
                fig = px.bar(
                    timeline, x='date', y='incidents',
                    title='Incidents Over Time',
                    labels={'x': 'Date', 'y': 'Incidents'},
                    color='incidents',
                    color_continuous_scale=CHART_REDS,
                )
                fig.update_layout(height=350)
                apply_chart_theme(fig)
                _safe_chart(fig)

        if len(per_service) > 0:
            fig = px.scatter(
                per_service, x='avg_response_ms', y='uptime_pct',
                size='total_checks', text='service',
                title='Service Health Scatter: Uptime vs Response Time',
                labels={'avg_response_ms': 'Avg Response (ms)', 'uptime_pct': 'Uptime %'},
                color='uptime_pct',
                color_continuous_scale=CHART_RDYLGN,
            )
            fig.update_traces(textposition='top center')
            fig.update_layout(height=450)
            apply_chart_theme(fig)
            _safe_chart(fig)

        st.markdown('<div style="margin-top:1rem;">', unsafe_allow_html=True)
        ecc3 = st.columns(3)
        with ecc3[0]:
            _csv_download(services_filtered, 'service_health.csv', 'Download Services CSV')
        with ecc3[1]:
            _csv_download(per_service, 'per_service_uptime.csv', 'Download Uptime CSV')
        with ecc3[2]:
            _csv_download(timeline if len(timeline) > 0 else None, 'incident_timeline.csv', 'Download Incidents CSV')

    # ─── TAB 4: TALENT PIPELINE ─────────────────────────────────────────────────

    with tabs[3]:
        st.header('Talent Pipeline')

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.markdown(f'<div class="sn-metric-card"><div class="sn-card-label">Total Applications</div><div class="sn-card-value">{app_metrics["total_applications"]}</div></div>', unsafe_allow_html=True)
        with col2:
            conv_color = rag_hex(rag_status(app_metrics['conversion_rate'], th.get('conversion', {}).get('warning', 15), th.get('conversion', {}).get('critical', 10), True))
            st.markdown(f'<div class="sn-metric-card" style="border-left:4px solid {conv_color}"><div class="sn-card-label">Conversion Rate</div><div class="sn-card-value" style="color:{conv_color}">{app_metrics["conversion_rate"]}%</div></div>', unsafe_allow_html=True)
        with col3:
            st.markdown(f'<div class="sn-metric-card"><div class="sn-card-label">Accepted</div><div class="sn-card-value">{app_metrics.get("accepted_count", 0)}</div></div>', unsafe_allow_html=True)
        with col4:
            ath = app_metrics.get('avg_time_to_hire')
            hire = f'{ath}d' if ath is not None else 'N/A'
            st.markdown(f'<div class="sn-metric-card"><div class="sn-card-label">Avg Time-to-Hire</div><div class="sn-card-value">{hire}</div></div>', unsafe_allow_html=True)

        col1, col2 = st.columns(2)

        with col1:
            funnel = app_metrics['funnel']
            if funnel:
                funnel_df = pd.DataFrame(funnel)
                fig = px.funnel(
                    funnel_df, x='count', y='stage',
                    title='Application Funnel',
                )
                fig.update_layout(height=400)
                apply_chart_theme(fig)
                _safe_chart(fig)

        with col2:
            source_eff = compute_source_effectiveness(applications_filtered)
            if len(source_eff) > 0:
                fig = px.bar(
                    source_eff, x='source', y='applications',
                    title='Applications by Source',
                    color='conversion_pct',
                    color_continuous_scale=CHART_RDYLGN,
                    text='applications',
                )
                fig.update_layout(height=400)
                apply_chart_theme(fig)
                _safe_chart(fig)

        col1, col2 = st.columns(2)

        with col1:
            dropout = app_metrics['stage_dropout']
            if dropout:
                dd = pd.DataFrame(dropout)
                fig = px.bar(
                    dd, x='stage', y='pct_of_total',
                    title='Stage Distribution (% of Total)',
                    color='pct_of_total',
                    color_continuous_scale=CHART_BLUES,
                    text=dd['pct_of_total'].apply(lambda x: f'{x}%'),
                )
                fig.update_layout(height=350)
                apply_chart_theme(fig)
                _safe_chart(fig)

        with col2:
            roles = app_metrics['role_distribution']
            if roles:
                rd = pd.DataFrame({'Role': list(roles.keys()), 'Count': list(roles.values())})
                fig = px.pie(rd, values='Count', names='Role', title='Applications by Role')
                fig.update_layout(height=350)
                apply_chart_theme(fig)
                _safe_chart(fig)

        if len(source_eff) > 0:
            fig = px.bar(
                source_eff, x='source', y='conversion_pct',
                title='Conversion Rate by Source',
                color='conversion_pct',
                color_continuous_scale=CHART_RDYLGN,
                text=source_eff['conversion_pct'].apply(lambda x: f'{x}%'),
            )
            fig.update_layout(height=350)
            apply_chart_theme(fig)
            _safe_chart(fig)

        st.markdown('<div style="margin-top:1rem;">', unsafe_allow_html=True)
        ecc4 = st.columns(3)
        with ecc4[0]:
            _csv_download(applications_filtered, 'applications.csv', 'Download Applications CSV')
        with ecc4[1]:
            _csv_download(source_eff if len(source_eff) > 0 else None, 'source_effectiveness.csv', 'Download Source CSV')
        with ecc4[2]:
            ecc4_funnel = pd.DataFrame(app_metrics['funnel']) if app_metrics['funnel'] else pd.DataFrame()
            _csv_download(ecc4_funnel, 'funnel.csv', 'Download Funnel CSV')

    # ─── TAB 5: INSIGHTS ────────────────────────────────────────────────────────

    with tabs[4]:
        st.header('Insights & Analysis')

        dq_total = sum([
            tickets_dq.get('total_issues', 0),
            services_dq.get('total_issues', 0),
            apps_dq.get('total_issues', 0),
        ])
        dq_score = compute_dq_score(tickets_dq, services_dq, apps_dq, total_records)
        dq_rag = compute_dq_rag(tickets_dq, services_dq, apps_dq, total_records, config)
        dq_color = rag_hex(dq_rag)

        st.markdown(
            f'<div class="sn-metric-card" style="border-left:4px solid {dq_color}">'
            f'<span class="sn-card-label">Overall Data Quality</span>'
            f'<div class="sn-card-value" style="color:{dq_color}">{dq_score}</div>'
            f'<div style="font-size:0.85rem;color:#6b7280;margin-top:0.25rem">{dq_total} issues found across {total_records} records</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

        st.markdown('<div class="sn-section-header">Data Quality Issues</div>', unsafe_allow_html=True)

        col1, col2, col3 = st.columns(3)
        with col1:
            if tickets_dq:
                dq_items = [
                    ('Missing CSAT', tickets_dq.get('missing_csat', 0)),
                    ('Negative Hours', tickets_dq.get('negative_resolution', 0)),
                    ('Category Typos', tickets_dq.get('category_typos', 0)),
                    ('Future Timestamps', tickets_dq.get('future_timestamps', 0)),
                    ('Duplicates', tickets_dq.get('duplicates_removed', 0)),
                ]
                dq_df = pd.DataFrame(dq_items, columns=['Issue', 'Count'])
                dq_df = dq_df[dq_df['Count'] > 0]
                if len(dq_df) > 0:
                    fig = px.bar(dq_df, x='Issue', y='Count', title='Ticket Data Quality Issues', color='Count', color_continuous_scale=CHART_REDS)
                    fig.update_layout(height=250)
                    apply_chart_theme(fig)
                    _safe_chart(fig)

        with col2:
            if services_dq:
                dq_items = [
                    ('Missing Response', services_dq.get('missing_response', 0)),
                    ('Negative Resp. (ms)', services_dq.get('negative_response', 0)),
                    ('Out of Order', services_dq.get('out_of_order', 0)),
                    ('Duplicates', services_dq.get('duplicates', 0)),
                ]
                dq_df = pd.DataFrame(dq_items, columns=['Issue', 'Count'])
                dq_df = dq_df[dq_df['Count'] > 0]
                if len(dq_df) > 0:
                    fig = px.bar(dq_df, x='Issue', y='Count', title='Service Data Quality Issues', color='Count', color_continuous_scale=CHART_REDS)
                    fig.update_layout(height=250)
                    apply_chart_theme(fig)
                    _safe_chart(fig)

        with col3:
            if apps_dq:
                dq_items = [
                    ('Future Timestamps', apps_dq.get('future_timestamps', 0)),
                    ('Missing IDs', apps_dq.get('missing_ids', 0)),
                    ('Unknown Source', apps_dq.get('unknown_source', 0)),
                ]
                dq_df = pd.DataFrame(dq_items, columns=['Issue', 'Count'])
                dq_df = dq_df[dq_df['Count'] > 0]
                if len(dq_df) > 0:
                    fig = px.bar(dq_df, x='Issue', y='Count', title='Application Data Quality Issues', color='Count', color_continuous_scale=CHART_REDS)
                    fig.update_layout(height=250)
                    apply_chart_theme(fig)
                    _safe_chart(fig)

        st.markdown('<div class="sn-section-header">Anomaly Detection</div>', unsafe_allow_html=True)

        col1, col2 = st.columns(2)
        with col1:
            ticket_anomalies = ticket_metrics.get('_volume_anomaly_mask', detect_anomalies(daily_tickets, config['analytics']['anomaly_z_threshold']))
            n_anom = ticket_anomalies.sum()
            st.markdown(f'<div class="sn-metric-card"><strong>Ticket Volume Anomalies:</strong> {int(n_anom)} days with unusual activity (z > {config["analytics"]["anomaly_z_threshold"]})</div>', unsafe_allow_html=True)
            if n_anom > 0:
                anom_dates = daily_tickets.index[ticket_anomalies]
                st.markdown('Affected dates: ' + ', '.join(str(d) for d in anom_dates[:5]))
                if n_anom > 5:
                    st.markdown(f'... and {int(n_anom) - 5} more')

        with col2:
            daily_resp = services_filtered.groupby(services_filtered['timestamp'].dt.date)['response_time_ms'].mean()
            if len(daily_resp) > 1:
                resp_anomalies = detect_anomalies(daily_resp, config['analytics']['anomaly_z_threshold'])
                n_resp_anom = resp_anomalies.sum()
                st.markdown(f'<div class="sn-metric-card"><strong>Response Time Anomalies:</strong> {int(n_resp_anom)} days with unusual latency</div>', unsafe_allow_html=True)
                if n_resp_anom > 0:
                    anom_dates = daily_resp.index[resp_anomalies]
                    st.markdown('Affected dates: ' + ', '.join(str(d) for d in anom_dates[:5]))
                    if n_resp_anom > 5:
                        st.markdown(f'... and {int(n_resp_anom) - 5} more')

        st.markdown('<div class="sn-section-header">Cross-Source Correlation</div>', unsafe_allow_html=True)

        daily_incidents = _safe_groupby_size(incidents_filtered, 'start_time')
        daily_ticket_counts = tickets_filtered.groupby(tickets_filtered['timestamp'].dt.date).size()
        combined = None

        if len(daily_incidents) > 0 and len(daily_ticket_counts) > 0:
            combined = pd.DataFrame({
                'incidents': daily_incidents,
                'tickets': daily_ticket_counts,
            }).fillna(0)

            corr = combined['incidents'].corr(combined['tickets'])

            st.markdown(
                f'<div class="sn-metric-card" style="border-left:4px solid {    SN_TEAL}">'
                f'<strong>Correlation: Incidents vs. Ticket Volume — r = {corr:.2f}</strong><br/>'
                f'When services experience incidents, there is a {"strong" if abs(corr) > 0.5 else "moderate" if abs(corr) > 0.3 else "weak"} '
                f'{"positive" if corr > 0 else "negative"} correlation with support ticket volume.'
                f'</div>',
                unsafe_allow_html=True,
            )

            fig = go.Figure()
            fig.add_trace(go.Bar(
                x=combined.index, y=combined['incidents'],
                name='Incidents',
                marker_color=RAG_RED,
                opacity=0.7,
                yaxis='y',
            ))
            fig.add_trace(go.Scatter(
                x=combined.index, y=combined['tickets'],
                name='Ticket Volume',
                mode='lines+markers',
                line=dict(color=    SN_TEAL, width=2),
                marker=dict(size=4, color=    SN_TEAL),
                yaxis='y2',
            ))
            fig.update_layout(
                title='Incidents vs. Ticket Volume',
                xaxis=dict(title='Date'),
                yaxis=dict(title='Incidents', side='left', showgrid=False),
                yaxis2=dict(title='Tickets', side='right', overlaying='y', showgrid=False),
                legend=dict(x=1.05, y=1),
                height=400,
            )
            apply_chart_theme(fig)
            _safe_chart(fig)

            service_corrs = []
            for service in incidents_filtered['service'].unique():
                svc_incidents = incidents_filtered[incidents_filtered['service'] == service]
                daily_svc = _safe_groupby_size(svc_incidents, 'start_time')
                if len(daily_svc) > 0 and len(daily_ticket_counts) > 0:
                    c = pd.DataFrame({'incidents': daily_svc, 'tickets': daily_ticket_counts}).fillna(0)
                    r = c['incidents'].corr(c['tickets'])
                    service_corrs.append({'service': service, 'correlation': round(r, 2), 'incidents': len(daily_svc)})

            if service_corrs:
                sc_df = pd.DataFrame(service_corrs).sort_values('correlation', ascending=False)
                fig = px.bar(sc_df, x='service', y='correlation', title='Correlation by Service: Incidents → Ticket Volume',
                            color='correlation', color_continuous_scale=CHART_RDBU, range_color=[-1, 1],
                            text=sc_df['correlation'].apply(lambda x: f'{x:.2f}'))
                fig.update_layout(height=350)
                apply_chart_theme(fig)
                _safe_chart(fig)

        st.markdown('<div class="sn-section-header">Automated Insights</div>', unsafe_allow_html=True)
        insights = generate_insights(ticket_metrics, service_metrics, app_metrics)
        for insight in insights:
            st.markdown(f'<div style="padding:0.5rem 0;border-bottom:1px solid #f3f4f6">• {insight}</div>', unsafe_allow_html=True)


def _csv_download(df, filename, label):
    if df is not None and len(df) > 0:
        st.download_button(label=label, data=df.to_csv(index=False), file_name=filename, mime='text/csv')


def _safe_groupby_size(df, date_col):
    if df is None or df.empty or date_col not in df.columns:
        return pd.Series(dtype=int)
    return df.groupby(df[date_col].dt.date).size()


if __name__ == '__main__':
    main()
