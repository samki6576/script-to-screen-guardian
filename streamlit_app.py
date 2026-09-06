"""Streamlit entry point for Script-to-Screen Guardian."""

from __future__ import annotations

import asyncio
import os
from datetime import date, timedelta

import streamlit as st


def _load_streamlit_secrets() -> None:
    """Expose Streamlit Cloud secrets to the existing settings loader."""
    for key in (
        "GOOGLE_CLOUD_PROJECT",
        "GEMINI_API_KEY",
        "GEMINI_MODEL",
        "CLICKHOUSE_HOST",
        "CLICKHOUSE_PORT",
        "CLICKHOUSE_NATIVE_PORT",
        "CLICKHOUSE_DATABASE",
        "CLICKHOUSE_USER",
        "CLICKHOUSE_PASSWORD",
        "APP_ENV",
    ):
        if key in st.secrets:
            os.environ[key] = str(st.secrets[key])


_load_streamlit_secrets()

from app.models import ProductionRiskReport
from app.orchestrator import get_orchestrator


st.set_page_config(
    page_title="Script-to-Screen Guardian",
    page_icon="SG",
    layout="wide",
)

st.title("Script-to-Screen Guardian")
st.caption("Production risk analysis powered by a multi-agent workflow")

with st.sidebar:
    st.header("Production setup")
    shoot_date = st.date_input(
        "Shoot start date",
        value=date.today() + timedelta(days=7),
        min_value=date.today(),
    )
    st.info(
        "Add GEMINI_API_KEY to Streamlit Cloud secrets for live analysis. "
        "Without it, the built-in fallback responses keep the demo usable."
    )

uploaded_file = st.file_uploader("Upload a script", type=["txt", "fdx", "md"])
script_text = st.text_area(
    "Or paste the script here",
    height=260,
    placeholder="INT. LOCATION - DAY\n\nA short scene description...",
)

if st.button("Analyze production risks", type="primary", use_container_width=True):
    if uploaded_file is not None:
        script_text = uploaded_file.getvalue().decode("utf-8", errors="replace")

    if not script_text.strip():
        st.error("Upload a script or paste script text before starting the analysis.")
    else:
        with st.spinner("Agents are assessing locations, logistics, and production risk..."):
            try:
                reports = asyncio.run(
                    get_orchestrator().run(script_text, shoot_date.isoformat())
                )
                st.session_state["reports"] = reports
            except Exception as exc:
                st.error(f"Analysis failed: {exc}")


reports: list[ProductionRiskReport] = st.session_state.get("reports", [])
if reports:
    high = sum(r.decision.overall_risk.value == "HIGH" for r in reports)
    medium = sum(r.decision.overall_risk.value == "MEDIUM" for r in reports)
    low = len(reports) - high - medium

    metric_columns = st.columns(4)
    metric_columns[0].metric("Scenes analyzed", len(reports))
    metric_columns[1].metric("High risk", high)
    metric_columns[2].metric("Medium risk", medium)
    metric_columns[3].metric("Low risk", low)

    st.subheader("Scene risk report")
    for report in reports:
        decision = report.decision
        risk = decision.overall_risk.value
        with st.expander(
            f"{report.scene.id} · {report.scene.location} · {risk}",
            expanded=risk == "HIGH",
        ):
            left, right = st.columns(2)
            with left:
                st.write(f"**Weather:** {report.location.weather_forecast}")
                st.write(f"**Permit:** {report.location.permit_status}")
                st.write(f"**Weather risk:** {report.location.weather_risk.value}")
                st.write(f"**Crew available:** {report.logistics.crew_available}")
            with right:
                st.write(f"**Cost impact:** {decision.cost_impact}")
                st.write(f"**Action required:** {decision.action_required}")
                equipment = report.logistics.equipment_needed or ["None listed"]
                st.write("**Equipment:** " + ", ".join(equipment))
                if decision.recommendations:
                    st.write("**Recommendations**")
                    for recommendation in decision.recommendations:
                        st.write(f"- {recommendation}")
else:
    st.info("Run an analysis to see scene-level production risks.")