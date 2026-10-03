import pandas as pd
import streamlit as st
from sqlalchemy import desc
from utils.models import (
    Incident, Resource, AgentExecution, AuditLog,
    IncidentEvidence, ResourceAssignment
)
from utils.services import (
    create_incident, change_status, propose_resource
)
from utils.agents import orchestrate, resource_agent
from utils.data import load_demo_dataset
from utils.ui import page_hero, severity_badge, status_badge

STATUSES = ["Pending", "Under Review", "Approved", "Assigned", "In Progress", "Resolved"]


def dashboard_page(db):
    page_hero(
        "OPERATIONS / COMMAND CENTER",
        "Emergency Command Center",
        "AI-assisted incident intelligence with human-controlled operational decisions.",
    )

    incidents = db.query(Incident).order_by(desc(Incident.created_at)).all()
    resources = db.query(Resource).all()

    metrics = {
        "Total Incidents": len(incidents),
        "Pending Review": sum(i.status in ("Pending", "Under Review") for i in incidents),
        "Urgent": sum(i.severity in ("High", "Critical") for i in incidents),
        "Active": sum(i.status in ("Assigned", "In Progress") for i in incidents),
        "Resolved": sum(i.status == "Resolved" for i in incidents),
    }

    cols = st.columns(5, gap="small")
    for col, (label, value) in zip(cols, metrics.items()):
        col.metric(label, value)

    st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
    left, right = st.columns([1.55, 1], gap="large")

    with left:
        st.markdown('<div class="section-title">LIVE INCIDENT MAP</div>', unsafe_allow_html=True)
        rows = [
            {"lat": i.latitude, "lon": i.longitude}
            for i in incidents
            if i.latitude is not None and i.longitude is not None
        ]
        if rows:
            st.map(pd.DataFrame(rows), height=410)
        else:
            st.info("No coordinates available. RescueMind AI never invents coordinates.")

    with right:
        st.markdown('<div class="section-title">RECENT INCIDENTS</div>', unsafe_allow_html=True)
        if incidents:
            for incident in incidents[:7]:
                st.markdown(
                    f"""
                    <div class="incident-card">
                        <div style="display:flex;justify-content:space-between;gap:8px;align-items:center;">
                            <span class="incident-code">{incident.incident_code}</span>
                            {severity_badge(incident.severity)}
                        </div>
                        <div class="incident-meta">{incident.category} · {incident.status}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
        else:
            st.info("No incidents have been reported yet.")

    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
    st.markdown('<div class="section-title">OPERATIONAL SNAPSHOT</div>', unsafe_allow_html=True)
    a, b = st.columns(2, gap="large")
    with a:
        st.markdown(
            f"""
            <div class="panel">
                <div class="mini-label">Resource readiness</div>
                <h3 style="margin:5px 0;color:#f8fafc;">{sum(r.status == 'Available' for r in resources)} available</h3>
                <div style="color:#8194aa;font-size:.76rem;">of {len(resources)} simulated resources currently tracked</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with b:
        st.markdown(
            """
            <div class="safe-notice">
                <b>Human-in-the-loop:</b> AI outputs are unverified recommendations.
                Coordinators must review supporting information before operational action.
            </div>
            """,
            unsafe_allow_html=True,
        )


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
        submitted = st.form_submit_button("🚨 Submit Emergency Report", use_container_width=True)

    if submitted:
        if len(description.strip()) < 10:
            st.error("Please provide a more detailed description.")
            return

        incident, report = create_incident(
            db,
            description,
            "Other" if category == "Auto Detect" else category,
            location,
            image.name if image else None,
        )

        if image:
            db.add(IncidentEvidence(
                incident_id=incident.id,
                evidence_type="image",
                file_name=image.name,
            ))

        result = orchestrate(db, incident, category)
        db.commit()

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
            st.markdown('<div class="panel">', unsafe_allow_html=True)
            st.markdown("**Detected signals**")
            detected = explanation.get("detected", [])
            st.write(" · ".join(map(str, detected)) if detected else "No explicit signals returned.")
            st.markdown("**Missing information**")
            missing = explanation.get("missing", [])
            st.write(" · ".join(map(str, missing)) if missing else "No missing information reported.")
            st.markdown('</div>', unsafe_allow_html=True)
        with y:
            st.markdown('<div class="panel">', unsafe_allow_html=True)
            st.markdown("**Reasoning**")
            st.write(explanation.get("reasoning", "Not available"))
            st.caption(f"Provider: {explanation.get('provider', 'Unknown')}")
            st.markdown('</div>', unsafe_allow_html=True)

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

    selected = st.selectbox(
        "Select incident",
        incidents,
        format_func=lambda x: f"{x.incident_code} — {x.category} — {x.severity}",
    )

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
            st.markdown('<div class="panel">', unsafe_allow_html=True)
            st.markdown("**Detected signals**")
            st.write(explanation.get("detected", []) or "No signals available")
            st.markdown("**Missing information**")
            st.write(explanation.get("missing", []) or "None reported")
            st.markdown("**Warnings**")
            st.write(explanation.get("warnings", []) or "None")
            st.markdown('</div>', unsafe_allow_html=True)
        with y:
            st.markdown('<div class="panel">', unsafe_allow_html=True)
            st.markdown("**Reasoning**")
            st.write(explanation.get("reasoning", "Not available"))
            st.caption(f"Provider: {explanation.get('provider', 'Unknown')}")
            st.markdown('</div>', unsafe_allow_html=True)

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

    resources = db.query(Resource).order_by(Resource.id).all()
    available = sum(r.status == "Available" for r in resources)
    busy = len(resources) - available

    a, b, c = st.columns(3, gap="small")
    a.metric("Total Resources", len(resources))
    b.metric("Available", available)
    c.metric("Unavailable / Busy", busy)

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

    with st.expander("＋ Add simulated resource"):
        with st.form("add_resource"):
            name = st.text_input("Name")
            resource_type = st.selectbox(
                "Type",
                ["Ambulance", "Rescue Team", "Rescue Boat", "Medical Unit", "Supplies"],
            )
            capacity = st.number_input("Capacity", min_value=1, max_value=1000, value=1)
            location = st.text_input("Location")
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
                    status="Available",
                ))
                db.commit()
                st.success("Resource added.")
                st.rerun()


def ai_activity_page(db):
    page_hero(
        "TRANSPARENCY / AI ACTIVITY",
        "AI Agent Activity",
        "Transparent execution history for the specialized RescueMind analysis agents.",
    )

    executions = (
        db.query(AgentExecution)
        .order_by(AgentExecution.id.desc())
        .limit(100)
        .all()
    )

    if not executions:
        st.info("No agent executions have been recorded yet.")
        return

    success_count = sum(x.status == "success" for x in executions)
    failure_count = len(executions) - success_count
    a, b, c = st.columns(3, gap="small")
    a.metric("Executions", len(executions))
    b.metric("Successful", success_count)
    c.metric("Other Status", failure_count)

    st.markdown('<div class="section-title">EXECUTION LOG</div>', unsafe_allow_html=True)
    for execution in executions:
        status_class = "badge-green" if execution.status == "success" else "badge-orange"
        with st.expander(
            f"{execution.agent_name}  ·  {execution.status}  ·  {execution.duration_ms or 0} ms"
        ):
            st.markdown(
                f'<span class="badge {status_class}">{execution.status}</span>',
                unsafe_allow_html=True,
            )
            st.json(execution.output_json or {})


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
