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

STATUSES = ["Pending", "Under Review", "Approved", "Assigned", "In Progress", "Resolved"]

def dashboard_page(db):
    st.markdown(
        '<div class="hero"><h1>🚨 Emergency Command Center</h1>'
        '<p>AI-assisted incident intelligence with human-controlled decisions.</p></div>',
        unsafe_allow_html=True,
    )

    incidents = db.query(Incident).order_by(desc(Incident.created_at)).all()
    metrics = {
        "Total": len(incidents),
        "Pending": sum(i.status in ("Pending", "Under Review") for i in incidents),
        "Urgent": sum(i.severity in ("High", "Critical") for i in incidents),
        "Assigned": sum(i.status in ("Assigned", "In Progress") for i in incidents),
        "Resolved": sum(i.status == "Resolved" for i in incidents),
    }

    cols = st.columns(5)
    for col, (label, value) in zip(cols, metrics.items()):
        col.metric(label, value)

    st.divider()
    left, right = st.columns([1.5, 1])

    with left:
        st.subheader("Incident Map")
        rows = [
            {"lat": i.latitude, "lon": i.longitude}
            for i in incidents
            if i.latitude is not None and i.longitude is not None
        ]
        if rows:
            st.map(pd.DataFrame(rows))
        else:
            st.info("No coordinates available. RescueMind AI never invents coordinates.")

    with right:
        st.subheader("Recent Incidents")
        for incident in incidents[:7]:
            icon = {
                "Critical": "🔴",
                "High": "🟠",
                "Medium": "🟡",
                "Low": "🟢",
            }.get(incident.severity, "⚪")
            st.write(f"{icon} **{incident.incident_code}**")
            st.caption(f"{incident.category} · {incident.status} · {incident.severity}")

    st.divider()
    st.markdown(
        '<div class="notice">⚠️ <b>Human-in-the-loop:</b> AI output is an unverified '
        'recommendation. Coordinators must review before operational action.</div>',
        unsafe_allow_html=True,
    )

def report_page(db):
    st.markdown(
        '<div class="hero"><h1>📣 Report Emergency</h1>'
        '<p>Submit a simulated emergency report for AI-assisted triage.</p></div>',
        unsafe_allow_html=True,
    )

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
        location = st.text_input(
            "Location or coordinates",
            placeholder="Example: Lahore or 31.5204, 74.3587",
        )
        image = st.file_uploader("Optional evidence image", type=["png", "jpg", "jpeg"])
        submitted = st.form_submit_button("🚨 Submit Emergency", use_container_width=True)

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
            f"Report **{report.report_code}** received. "
            f"Incident **{incident.incident_code}** created."
        )

        a, b, c = st.columns(3)
        a.metric("Category", incident.category)
        b.metric("Severity", incident.severity)
        c.metric("Score", incident.severity_score)

        st.subheader("AI Explainability")
        st.write("**Detected:**", result["explanation"].get("detected", []))
        st.write("**Missing:**", result["explanation"].get("missing", []))
        st.write("**Reasoning:**", result["explanation"].get("reasoning"))
        st.warning("Human verification is required before operational action.")

        if result["duplicates"]:
            st.subheader("Potential Duplicate Reports")
            st.dataframe(pd.DataFrame(result["duplicates"]), use_container_width=True)
        else:
            st.success("No potential duplicate found above the similarity threshold.")

def incidents_page(db):
    st.markdown(
        '<div class="hero"><h1>📋 Incident Management</h1>'
        '<p>Review findings and make human-controlled operational decisions.</p></div>',
        unsafe_allow_html=True,
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

    a, b, c, d = st.columns(4)
    a.metric("Category", selected.category)
    b.metric("Severity", selected.severity)
    c.metric("Score", selected.severity_score)
    d.metric("Status", selected.status)

    st.write(selected.description)

    tab1, tab2, tab3 = st.tabs(["AI Explanation", "Resources", "Coordinator Action"])

    with tab1:
        explanation = selected.ai_explanation or {}
        st.write("**Detected:**", explanation.get("detected", []))
        st.write("**Missing:**", explanation.get("missing", []))
        st.write("**Reasoning:**", explanation.get("reasoning", "Not available"))
        st.caption(f"Provider: {explanation.get('provider', 'Unknown')}")
        st.warning("Human verification required.")

    with tab2:
        resources = db.query(Resource).all()
        recommendations = resource_agent(selected, resources)

        if not recommendations:
            st.info("No matching available resources.")
        else:
            for rec in recommendations:
                st.write(f"**{rec['name']}** · {rec['type']}")
                st.caption(rec["reason"])
                if st.button(
                    f"Propose {rec['resource_code']}",
                    key=f"resource_{selected.id}_{rec['resource_id']}",
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
        approved = st.checkbox(
            "I reviewed the AI recommendation and supporting information.",
            key=f"review_{selected.id}",
        )
        new_status = st.selectbox(
            "Status",
            STATUSES,
            index=STATUSES.index(selected.status)
            if selected.status in STATUSES else 0,
            key=f"status_{selected.id}",
        )

        if st.button("Save Coordinator Decision", type="primary"):
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

def resources_page(db):
    st.markdown(
        '<div class="hero"><h1>🚑 Resource Management</h1>'
        '<p>Simulated rescue resources available for coordinator review.</p></div>',
        unsafe_allow_html=True,
    )

    resources = db.query(Resource).order_by(Resource.id).all()
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

    with st.expander("Add simulated resource"):
        with st.form("add_resource"):
            name = st.text_input("Name")
            resource_type = st.selectbox(
                "Type",
                ["Ambulance", "Rescue Team", "Rescue Boat", "Medical Unit", "Supplies"],
            )
            capacity = st.number_input("Capacity", min_value=1, max_value=1000, value=1)
            location = st.text_input("Location")
            submit = st.form_submit_button("Add Resource")

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
    st.markdown(
        '<div class="hero"><h1>🤖 AI Agent Activity</h1>'
        '<p>Transparent execution history for specialized agents.</p></div>',
        unsafe_allow_html=True,
    )

    executions = (
        db.query(AgentExecution)
        .order_by(AgentExecution.id.desc())
        .limit(100)
        .all()
    )

    for execution in executions:
        with st.expander(
            f"{execution.agent_name} · {execution.status} · {execution.duration_ms or 0} ms"
        ):
            st.json(execution.output_json or {})

def audit_page(db):
    st.markdown(
        '<div class="hero"><h1>📝 Audit Trail</h1>'
        '<p>Traceable records of coordinator and system actions.</p></div>',
        unsafe_allow_html=True,
    )

    logs = db.query(AuditLog).order_by(AuditLog.id.desc()).limit(200).all()

    if not logs:
        st.info("No audit events yet.")
        return

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
