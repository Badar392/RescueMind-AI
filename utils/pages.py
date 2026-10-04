import pandas as pd
import streamlit as st
from sqlalchemy import desc
from utils.models import (
    Incident, Resource, AgentExecution, AuditLog, ResourceOptimizationRun,
    IncidentEvidence, ResourceAssignment
)
from utils.services import (
    create_incident, change_status, propose_resource
)
from utils.event_bus import publish_event
from utils.agents import orchestrate, resource_agent
from utils.resource_optimizer import optimize_resources
from utils.ai import transcribe_audio
from utils.data import load_demo_dataset
import plotly.express as px
from utils.ui import (page_hero, severity_badge, status_badge, kpi_row, section,
                      style_fig, SEV_COLORS)

STATUSES = ["Pending", "Under Review", "Approved", "Assigned", "In Progress", "Resolved"]


def dashboard_page(db):
    page_hero("OPERATIONS / COMMAND CENTER", "Emergency Command Center",
              "AI-assisted incident intelligence with human-controlled operational decisions.")
    incidents = db.query(Incident).order_by(desc(Incident.created_at)).all()
    resources = db.query(Resource).all()
    n = lambda f: sum(1 for i in incidents if f(i))
    avail = sum(r.status == "Available" for r in resources)
    kpi_row([
        ("Total Incidents", len(incidents), "☰", "blue", "All reported"),
        ("Pending Review", n(lambda i: i.status in ("Pending", "Under Review")), "⏳", "orange", "Awaiting coordinator"),
        ("Urgent", n(lambda i: i.severity in ("High", "Critical")), "⚠", "red", "High / Critical"),
        ("Active", n(lambda i: i.status in ("Assigned", "In Progress")), "⚡", "cyan", "In operation"),
        ("Resolved", n(lambda i: i.status == "Resolved"), "✔", "green", "Closed cases"),
    ])
    st.write("")
    left, right = st.columns([1.6, 1], gap="large")
    with left:
        section("LIVE INCIDENT MAP")
        rows = [{"lat": i.latitude, "lon": i.longitude, "Incident": i.incident_code, "Severity": i.severity or "Medium"}
                for i in incidents if i.latitude is not None and i.longitude is not None]
        if rows:
            fig = px.scatter_map(pd.DataFrame(rows), lat="lat", lon="lon", color="Severity", hover_name="Incident",
                                 color_discrete_map=SEV_COLORS, zoom=9, map_style="carto-darkmatter")
            fig.update_traces(marker=dict(size=15))
            st.plotly_chart(style_fig(fig, 400), use_container_width=True)
        else:
            st.info("No coordinates available. RescueMind AI never invents coordinates.")
    with right:
        section("RECENT INCIDENTS")
        if not incidents:
            st.info("No incidents have been reported yet.")
        for i in incidents[:6]:
            st.markdown(
                f'<div class="incident-card"><div style="display:flex;justify-content:space-between;align-items:center">'
                f'<span class="incident-code">{i.incident_code}</span>{severity_badge(i.severity)}</div>'
                f'<div class="incident-meta">{i.category} · {status_badge(i.status)}</div></div>', unsafe_allow_html=True)

    if incidents:
        c1, c2, c3 = st.columns([1, 1, 1], gap="large")
        df = pd.DataFrame([{"Severity": i.severity or "Medium", "Category": i.category, "Status": i.status} for i in incidents])
        with c1:
            section("SEVERITY MIX")
            fig = px.pie(df, names="Severity", hole=.6, color="Severity", color_discrete_map=SEV_COLORS)
            st.plotly_chart(style_fig(fig, 260), use_container_width=True)
        with c2:
            section("BY CATEGORY")
            d = df["Category"].value_counts().reset_index()
            fig = px.bar(d, x="count", y="Category", orientation="h", color_discrete_sequence=["#6366f1"])
            st.plotly_chart(style_fig(fig, 260), use_container_width=True)
        with c3:
            section("WORKFLOW STATUS")
            d = df["Status"].value_counts().reset_index()
            fig = px.bar(d, x="Status", y="count", color_discrete_sequence=["#06b6d4"])
            st.plotly_chart(style_fig(fig, 260), use_container_width=True)

    a, b = st.columns(2, gap="large")
    with a:
        pct = round(100 * avail / len(resources)) if resources else 0
        st.markdown(f'<div class="panel"><div class="mini-label">Resource readiness</div>'
                    f'<h2 style="margin:6px 0;color:#fff">{avail} / {len(resources)} available</h2>'
                    f'<div style="height:8px;border-radius:6px;background:#1b2740"><div style="width:{pct}%;height:100%;'
                    f'border-radius:6px;background:linear-gradient(90deg,#22c55e,#06b6d4)"></div></div></div>',
                    unsafe_allow_html=True)
    with b:
        st.markdown('<div class="safe-notice"><b>Human-in-the-loop:</b> AI outputs are unverified recommendations. '
                    'Coordinators must review supporting information before operational action.</div>',
                    unsafe_allow_html=True)


def report_page(db):
    page_hero(
        "INTAKE / NEW REPORT",
        "Report Emergency",
        "Submit a simulated emergency report for AI-assisted triage and coordination.",
    )

    st.markdown('<div class="section-title">INCIDENT INFORMATION</div>', unsafe_allow_html=True)
    with st.form("report"):
        category = st.selectbox(
            "Emergency category",
            ["Auto Detect", "Flood", "Earthquake", "Fire", "Road Accident", "Medical Emergency", "Other"],
        )
        description = st.text_area(
            "Emergency description",
            height=160,
            placeholder="Example: Several people are trapped in rising flood water near the bridge...",
        )
        c1, c2 = st.columns([1.3, 1], gap="large")
        with c1:
            location = st.text_input(
                "Location or coordinates",
                placeholder="Example: Lahore or 31.5204, 74.3587",
            )
        with c2:
            image = st.file_uploader("Optional evidence image", type=["png", "jpg", "jpeg"])
        voice = st.audio_input("Optional voice report") if hasattr(st, "audio_input") else st.file_uploader("Optional voice report", type=["wav", "mp3", "m4a", "webm"])
        submitted = st.form_submit_button("🚨 Submit Emergency Report", use_container_width=True)

    if submitted:
        # Optional voice becomes an additional evidence channel. The user can still edit the text before submission.
        voice_text = ""
        voice_note = ""
        if voice:
            try:
                voice_bytes = voice.getvalue()
                voice_result = transcribe_audio(voice_bytes, getattr(voice, "name", None) or "report.wav")
                voice_text = (voice_result.get("text") or "").strip()
                if voice_text:
                    st.info(f"🎙 Voice transcribed: {voice_text}")
                    description = voice_text if not description.strip() else f"{description.strip()}\n\nVoice evidence: {voice_text}"
                else:
                    voice_note = voice_result.get("note") or voice_result.get("error") or "No speech was detected in the recording."
            except Exception as exc:
                voice_note = f"{type(exc).__name__}: {exc}"

        if voice and not voice_text:
            st.warning(f"Voice report could not be transcribed. {voice_note} Please type the description instead.")

        if len(description.strip()) < 10:
            st.error("Please type a description (at least 10 characters), or record again once voice transcription is available.")
            return

        incident, report = create_incident(
            db, description, "Other" if category == "Auto Detect" else category, location, image.name if image else None,
        )

        image_bytes = image.getvalue() if image else None
        if image:
            db.add(IncidentEvidence(incident_id=incident.id, evidence_type="image", file_name=image.name))
        if voice:
            db.add(IncidentEvidence(incident_id=incident.id, evidence_type="voice", file_name=getattr(voice, "name", "voice-report"), extracted_text=voice_text or None))

        result = orchestrate(db, incident, category, image_bytes=image_bytes, image_name=image.name if image else None)
        db.commit()

        # Streamlit reports must enter the same event-driven monitoring path as API reports.
        publish_event("incident.created", incident.id, {"source": "streamlit_report"})

        st.success(
            f"Report **{report.report_code}** received. Incident **{incident.incident_code}** created."
        )

        a, b, c = st.columns(3, gap="small")
        a.metric("Detected Category", incident.category)
        b.metric("Severity", incident.severity)
        c.metric("Severity Score", incident.severity_score)

        st.markdown("<div class='section-title'>AI EXPLAINABILITY</div>", unsafe_allow_html=True)
        x, y = st.columns([1, 1], gap="large")
        explanation = result["explanation"]
        with x:
            with st.container(border=True):
                st.markdown("**Detected signals**")
                detected = explanation.get("detected", [])
                st.write(" · ".join(map(str, detected)) if detected else "No explicit signals returned.")
                st.markdown("**Missing information**")
                missing = explanation.get("missing", [])
                st.write(" · ".join(map(str, missing)) if missing else "No missing information reported.")
        with y:
            with st.container(border=True):
                st.markdown("**Reasoning**")
                st.write(explanation.get("reasoning", "Not available"))
                st.caption(f"Provider: {explanation.get('provider', 'Unknown')}")

        vision = result.get("agent_context", {}).get("data", {}).get("vision", {}) if isinstance(result.get("agent_context"), dict) else {}
        if vision:
            st.markdown('<div class="section-title">VISION EVIDENCE</div>', unsafe_allow_html=True)
            st.write(vision.get("findings", []) or "No visible findings returned.")
            if vision.get("hazards"): st.write("Hazards:", vision.get("hazards"))

        st.warning("Human verification is required before operational action.")

        if result["duplicates"]:
            st.markdown('<div class="section-title">POTENTIAL DUPLICATE REPORTS</div>', unsafe_allow_html=True)
            st.dataframe(pd.DataFrame(result["duplicates"]), use_container_width=True, hide_index=True)
        else:
            st.success("No potential duplicate found above the similarity threshold.")


def incidents_page(db):
    page_hero(
        "OPERATIONS / INCIDENTS",
        "Incident Management",
        "Review AI findings and make human-controlled operational decisions.",
    )

    incidents = db.query(Incident).order_by(Incident.id.desc()).all()
    if not incidents:
        st.info("No incidents available.")
        return

    by_id = {i.id: i for i in incidents}
    selected_id = st.selectbox(
        "Select incident",
        list(by_id),
        format_func=lambda i: f"{by_id[i].incident_code} — {by_id[i].category} — {by_id[i].severity}",
    )
    selected = db.get(Incident, selected_id)  # live session object so status edits persist

    st.markdown(
        f"""
        <div class="panel" style="margin:10px 0 18px;">
            <div class="mini-label">SELECTED INCIDENT</div>
            <div style="display:flex;justify-content:space-between;gap:12px;align-items:center;margin-top:5px;">
                <div>
                    <div style="font-size:1.1rem;font-weight:800;color:#f8fafc;">{selected.incident_code}</div>
                    <div style="font-size:.76rem;color:#8194aa;margin-top:3px;">{selected.category} · {selected.location_text or 'Location not verified'}</div>
                </div>
                <div>{severity_badge(selected.severity)} &nbsp; {status_badge(selected.status)}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    a, b, c, d = st.columns(4, gap="small")
    a.metric("Category", selected.category)
    b.metric("Severity", selected.severity)
    c.metric("Score", selected.severity_score)
    d.metric("Status", selected.status)

    with st.expander("View original emergency description", expanded=True):
        st.write(selected.description)

    tab1, tab2, tab3, tab4 = st.tabs(["🧠 AI Intelligence", "🚑 Resources", "🛡 Coordinator Action", "🤖 Agent Timeline"])

    with tab1:
        explanation = selected.ai_explanation or {}
        x, y = st.columns(2, gap="large")
        with x:
            with st.container(border=True):
                st.markdown("**Detected signals**")
                st.write(explanation.get("detected", []) or "No signals available")
                st.markdown("**Missing information**")
                st.write(explanation.get("missing", []) or "None reported")
                st.markdown("**Warnings**")
                st.write(explanation.get("warnings", []) or "None")
        with y:
            with st.container(border=True):
                st.markdown("**Reasoning**")
                st.write(explanation.get("reasoning", "Not available"))
                st.caption(f"Provider: {explanation.get('provider', 'Unknown')}")

        agent_context = explanation.get("agent_context", {})
        response_plan = agent_context.get("data", {}).get("response_plan", {})
        if response_plan:
            st.markdown('<div class="section-title">RESPONSE PLAN</div>', unsafe_allow_html=True)
            p1, p2, p3 = st.columns(3, gap="small")
            p1.metric("Priority", response_plan.get("priority_label", "Review"))
            p2.metric("Candidates", len(response_plan.get("matched_resources", [])))
            p3.metric("Approval", "Required" if response_plan.get("human_approval_required", True) else "Not required")
            st.markdown("**Recommended actions**")
            for action in response_plan.get("recommended_actions", []):
                st.write(f"• {action}")
            if response_plan.get("risks"):
                st.markdown("**Operational risks / uncertainty**")
                for risk in response_plan["risks"]:
                    st.write(f"⚠ {risk}")

        st.warning("Human verification is required before operational action.")

    with tab2:
        resources = db.query(Resource).all()
        recommendations = resource_agent(selected, resources)

        if not recommendations:
            st.info("No matching available resources.")
        else:
            for rec in recommendations:
                distance_text = f"{rec['distance_km']} km" if rec.get("distance_km") is not None else "unknown"
                r1, r2 = st.columns([3, 1], gap="large")
                with r1:
                    st.markdown(
                        f"""
                        <div class="incident-card">
                            <div class="incident-code">{rec['name']}</div>
                            <div class="incident-meta">{rec['type']} · {rec['resource_code']}</div>
                            <div style="color:#a9b8c9;font-size:.78rem;margin-top:7px;">{rec['reason']}</div>
                            <div style="color:#8fd3ff;font-size:.75rem;margin-top:6px;">Match score: {rec.get('match_score', '—')} · Distance: {distance_text}</div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
                with r2:
                    st.write("")
                    if st.button(
                        f"Propose {rec['resource_code']}",
                        key=f"resource_{selected.id}_{rec['resource_id']}",
                        use_container_width=True,
                    ):
                        propose_resource(
                            db,
                            selected.id,
                            rec["resource_id"],
                            rec["reason"],
                        )
                        db.commit()
                        st.success("Resource proposal recorded. No automatic dispatch occurred.")

    with tab3:
        st.markdown(
            '<div class="notice">Review the AI recommendation and supporting information before moving an incident into an operational state.</div>',
            unsafe_allow_html=True,
        )
        approved = st.checkbox(
            "I reviewed the AI recommendation and supporting information.",
            key=f"review_{selected.id}",
        )
        new_status = st.selectbox(
            "Status",
            STATUSES,
            index=STATUSES.index(selected.status) if selected.status in STATUSES else 0,
            key=f"status_{selected.id}",
        )

        if st.button("Save Coordinator Decision", type="primary", use_container_width=True):
            if new_status in {"Approved", "Assigned", "In Progress", "Resolved"} and not approved:
                st.error("Review confirmation is required.")
            else:
                change_status(
                    db,
                    selected,
                    new_status,
                    actor="coordinator",
                    note="Coordinator reviewed the incident.",
                )
                db.commit()
                publish_event("incident.updated", selected.id, {"source": "coordinator_streamlit", "new_status": new_status})
                st.success("Incident updated.")
                st.rerun()

    with tab4:
        st.markdown('<div class="section-title">AGENT EXECUTION TIMELINE</div>', unsafe_allow_html=True)
        executions = (
            db.query(AgentExecution)
            .filter(AgentExecution.incident_id == selected.id)
            .order_by(AgentExecution.id.asc())
            .all()
        )
        if not executions:
            st.info("No agent execution records are available for this incident.")
        else:
            for execution in executions:
                output = execution.output_json or {}
                confidence = output.get("confidence")
                confidence_text = f" · confidence {round(confidence * 100)}%" if isinstance(confidence, (int, float)) else ""
                icon = "✓" if execution.status == "success" else "!"
                st.markdown(
                    f"""
                    <div class="incident-card" style="margin-bottom:8px;">
                        <div style="display:flex;justify-content:space-between;align-items:center;gap:10px;">
                            <div class="incident-code">{icon} {execution.agent_name}</div>
                            <div class="incident-meta">{execution.duration_ms or 0} ms{confidence_text}</div>
                        </div>
                        <div class="incident-meta" style="margin-top:6px;">Status: {execution.status}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                with st.expander(f"View {execution.agent_name} output", expanded=False):
                    st.json(output)



def resources_page(db):
    page_hero(
        "OPERATIONS / RESOURCES",
        "Resource Management",
        "Track simulated rescue resources and review availability for coordinator decisions.",
    )

    if st.session_state.get("resource_flash"):
        st.success("Resource status updated — " + st.session_state.pop("resource_flash"))
    resources = db.query(Resource).order_by(Resource.id).all()
    available = sum(r.status == "Available" for r in resources)
    busy = len(resources) - available

    a, b, c = st.columns(3, gap="small")
    a.metric("Total Resources", len(resources))
    b.metric("Available", available)
    c.metric("Unavailable / Busy", busy)

    st.markdown('<div class="section-title">AI RESOURCE OPTIMIZATION</div>', unsafe_allow_html=True)
    active_incidents = db.query(Incident).filter(Incident.status.in_(["Pending", "Under Review", "Approved", "Assigned", "In Progress"])).all()
    if active_incidents and resources:
        recommendations = optimize_resources(active_incidents, resources, 3)
        st.caption("Recommendations balance capability, availability, proximity, capacity, incident severity, and resource competition. Human approval is required.")
        if recommendations:
            st.dataframe(pd.DataFrame([{
                "Incident": x["incident_code"], "Severity": x["severity"], "Resource": x["resource_code"],
                "Type": x["resource_type"], "Distance (km)": round(x["distance_km"], 1) if x["distance_km"] is not None else None,
                "Optimized Score": x["optimized_score"], "Competition Penalty": x["competition_penalty"],
                "Decision": "Human review"
            } for x in recommendations]), use_container_width=True, hide_index=True)
        else:
            st.info("No feasible resource recommendations for active incidents.")
    else:
        st.info("Create an active incident to generate optimization recommendations.")

    st.markdown('<div class="section-title">RESOURCE INVENTORY</div>', unsafe_allow_html=True)
    st.dataframe(
        pd.DataFrame([
            {
                "Code": r.resource_code,
                "Name": r.name,
                "Type": r.resource_type,
                "Status": r.status,
                "Capacity": r.capacity,
                "Location": r.location,
            }
            for r in resources
        ]),
        use_container_width=True,
        hide_index=True,
    )

    STATUS_OPTIONS = ["Available", "Busy", "Maintenance", "Offline"]
    with st.expander("↻ Update resource availability"):
        if resources:
            # NOTE: st.selectbox returns a detached copy of ORM objects, so edits to it are silently lost.
            # Select by ID and re-fetch the row from the live DB session instead.
            by_id = {r.id: r for r in resources}
            resource_id = st.selectbox(
                "Resource", list(by_id),
                format_func=lambda i: f"{by_id[i].resource_code} — {by_id[i].name}  ({by_id[i].status})",
            )
            selected_resource = db.get(Resource, resource_id)
            current = selected_resource.status if selected_resource.status in STATUS_OPTIONS else "Available"
            new_status = st.selectbox(
                "New status", STATUS_OPTIONS, index=STATUS_OPTIONS.index(current),
                key=f"res_status_{resource_id}_{current}",
            )
            if st.button("Save Resource Status", use_container_width=True):
                if new_status == current:
                    st.info(f"{selected_resource.resource_code} is already {current}.")
                else:
                    old_status = selected_resource.status
                    selected_resource.status = new_status
                    db.add(AuditLog(action="resource_status_changed", actor="coordinator", entity_type="resource", entity_id=str(selected_resource.id), details={"old": old_status, "new": new_status}))
                    db.commit()
                    publish_event("resource.updated", None, {"resource_id": selected_resource.id, "old_status": old_status, "new_status": new_status, "source": "coordinator_streamlit"})
                    st.session_state["resource_flash"] = f"{selected_resource.resource_code} changed: {old_status} → {new_status}"
                    st.rerun()

    with st.expander("＋ Add simulated resource"):
        with st.form("add_resource"):
            name = st.text_input("Name")
            resource_type = st.selectbox(
                "Type",
                ["Ambulance", "Rescue Team", "Rescue Boat", "Medical Unit", "Supplies"],
            )
            capacity = st.number_input("Capacity", min_value=1, max_value=1000, value=1)
            location = st.text_input("Location")
            initial_status = st.selectbox("Initial status", STATUS_OPTIONS)
            submit = st.form_submit_button("Add Resource", use_container_width=True)

        if submit:
            if not name or not location:
                st.error("Name and location are required.")
            else:
                from utils.services import make_code
                db.add(Resource(
                    resource_code=make_code("RES"),
                    name=name,
                    resource_type=resource_type,
                    capacity=capacity,
                    location=location,
                    status=initial_status,
                ))
                db.commit()
                st.success("Resource added.")
                st.rerun()


def audit_page(db):
    page_hero(
        "TRANSPARENCY / AUDIT",
        "Audit Trail",
        "Traceable records of coordinator and system actions across the incident workflow.",
    )

    logs = db.query(AuditLog).order_by(AuditLog.id.desc()).limit(200).all()

    if not logs:
        st.info("No audit events yet.")
        return

    st.markdown('<div class="section-title">SYSTEM ACTIVITY</div>', unsafe_allow_html=True)
    st.dataframe(
        pd.DataFrame([
            {
                "Action": x.action,
                "Actor": x.actor,
                "Entity": x.entity_type,
                "Entity ID": x.entity_id,
                "Time": x.created_at,
                "Details": str(x.details or {}),
            }
            for x in logs
        ]),
        use_container_width=True,
        hide_index=True,
    )


def _agent_activity_view(db):
    executions = db.query(AgentExecution).order_by(AgentExecution.id.desc()).limit(100).all()
    if not executions:
        st.info("No agent executions have been recorded yet.")
        return
    st.markdown('<div class="section-title">AGENT EXECUTION LOG</div>', unsafe_allow_html=True)
    st.caption("What each AI agent analysed and decided. Monitoring-agent runs are triggered by the events in the Event Stream tab.")
    for execution in executions:
        status_class = "badge-green" if execution.status == "success" else "badge-orange"
        with st.expander(f"{execution.agent_name}  ·  {execution.status}  ·  {execution.duration_ms or 0} ms"):
            st.markdown(f'<span class="badge {status_class}">{execution.status}</span>', unsafe_allow_html=True)
            st.json(execution.output_json or {})


def _event_stream_view(db):
    from utils.models import EventRecord
    st.markdown('<div class="safe-notice"><b>Control rule:</b> events can trigger analysis and recommendations, but never autonomous field dispatch. A coordinator remains the approval authority.</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-title">EVENT STREAM</div>', unsafe_allow_html=True)
    events = db.query(EventRecord).order_by(desc(EventRecord.id)).limit(30).all()
    if not events:
        st.info("No events have been emitted yet. Submit an emergency report to start the stream.")
        return
    for event in events:
        with st.expander(f"#{event.id} · {event.event_type} · {event.status} · incident {event.incident_id or 'system'}"):
            st.json({"payload": event.payload or {}, "error": event.error, "created_at": str(event.created_at)})


def ai_monitoring_page(db):
    """Single page for AI agent activity + live event monitoring (two views of one pipeline:
    event -> monitoring handler -> agent execution)."""
    from utils.models import EventRecord
    page_hero(
        "TRANSPARENCY / AI MONITORING",
        "AI Monitoring Center",
        "Live event stream and the AI agent executions it triggers, in one auditable view.",
    )
    executions = db.query(AgentExecution).order_by(AgentExecution.id.desc()).limit(100).all()
    events = db.query(EventRecord).order_by(desc(EventRecord.id)).limit(80).all()
    ok = sum(x.status == "success" for x in executions)
    kpi_row([
        ("Agent runs", len(executions), "✦", "blue", "Last 100 executions"),
        ("Successful", ok, "✔", "green", f"{len(executions) - ok} other status"),
        ("Stream events", len(events), "◉", "cyan", f"{sum(e.status == 'queued' for e in events)} queued"),
        ("Failed events", sum(e.status == "failed" for e in events), "⚠", "red", "Needs attention"),
    ])
    st.write("")
    tab_agents, tab_events = st.tabs(["🤖 Agent Activity", "📡 Live Event Stream"])
    with tab_agents:
        _agent_activity_view(db)
    with tab_events:
        _event_stream_view(db)
