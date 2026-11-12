import json
import os

import streamlit as st
from agentic_workflow import run_analysis, run_offline_analysis

st.title("SPECTRUM — AI Analyst")
st.caption("The planner selects an analysis, Python computes it, a validator checks it, and the reporter explains the result.")

# Offline mode toggle
offline_mode = st.checkbox("Use offline mode (no API key needed)")

# Session history initialisation
if "history" not in st.session_state:
    st.session_state["history"] = []

# Check for dataset
dataset = st.session_state.get("dataset")
analysis_data = st.session_state.get("analysis_data")

if dataset is None or analysis_data is None:
    st.info("Upload a dataset on the Explore page first.")
else:
    history = st.session_state["history"]

    # Analysis history panel
    with st.expander(f"History ({len(history)} analyses)"):
        if history:
            for i, entry in enumerate(history, 1):
                st.markdown(f"**{i}. {entry['question']}**")
                st.write(entry["explanation"])
                st.divider()
        else:
            st.write("No analyses yet.")

    question = st.text_input("Ask a question about this dataset", key="agent_question")

    if offline_mode:
        if st.button("Analyze question", disabled=not question.strip()):
            try:
                with st.spinner("Running offline analysis…"):
                    result = run_offline_analysis(question, analysis_data)

                st.session_state["history"].append(
                    {
                        "question": question,
                        "explanation": result["explanation"],
                        "plan": result["plan"],
                        "result": result["result"],
                    }
                )

                st.markdown("#### Agent explanation")
                st.write(result["explanation"])

                with st.status("Agent activity", state="complete", expanded=True):
                    for step in result["trace"]:
                        st.write(f"**{step['step']}:** {step['detail']}")
                    st.write("**Plan selected:**")
                    st.json(result["plan"])

                st.markdown("#### Verified calculation")
                st.json(result["result"])

                st.download_button(
                    "Download result JSON",
                    data=json.dumps(result["result"], indent=2),
                    file_name="result.json",
                    mime="application/json",
                )

                if result.get("figure") is not None:
                    st.plotly_chart(result["figure"], width="stretch")

            except Exception as error:
                st.error(f"The analyst could not complete this question: {error}")
    else:
        api_key = os.environ.get("GROQ_API_KEY", "")
        if not api_key:
            st.info("To enable the Groq analyst, set the GROQ_API_KEY environment variable and restart the app.")

        if st.button("Analyze question", disabled=not api_key or not question.strip()):
            try:
                with st.spinner("Planner, analyst, validator, and reporter are working…"):
                    result = run_analysis(
                        question,
                        analysis_data,
                        api_key,
                        model=os.environ.get("GROQ_MODEL", "openai/gpt-oss-20b"),
                    )

                st.session_state["history"].append(
                    {
                        "question": question,
                        "explanation": result["explanation"],
                        "plan": result["plan"],
                        "result": result["result"],
                    }
                )

                st.markdown("#### Agent explanation")
                st.write(result["explanation"])

                with st.status("Agent activity", state="complete", expanded=True):
                    for step in result["trace"]:
                        st.write(f"**{step['step']}:** {step['detail']}")
                    st.write("**Plan selected:**")
                    st.json(result["plan"])

                st.markdown("#### Verified calculation")
                st.json(result["result"])

                st.download_button(
                    "Download result JSON",
                    data=json.dumps(result["result"], indent=2),
                    file_name="result.json",
                    mime="application/json",
                )

                if result.get("figure") is not None:
                    st.plotly_chart(result["figure"], width="stretch")

            except Exception as error:
                st.error(f"The analyst could not complete this question: {error}")
