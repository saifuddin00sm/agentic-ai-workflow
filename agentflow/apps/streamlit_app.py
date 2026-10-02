"""Streamlit web demo for AgentFlow."""

from __future__ import annotations

import asyncio
import json
from datetime import datetime
from typing import Any

import streamlit as st

st.set_page_config(
    page_title="AgentFlow - Multi-Agent Research",
    page_icon="🔬",
    layout="wide",
)


def run_async(coro: Any) -> Any:
    """Run an async coroutine in Streamlit."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


def get_mock_client() -> Any:
    """Get mock LLM client for demo."""
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from apps.cli import _create_mock_client
    return _create_mock_client()


def render_event_timeline(events: list[dict[str, Any]]) -> None:
    """Render the event timeline."""
    st.subheader("📊 Pipeline Timeline")

    for event in events:
        event_type = event.get("type", "")
        stage = event.get("stage", "")
        data = event.get("data", {})
        latency = event.get("latency_ms", 0)

        if event_type == "stage_started":
            st.markdown(f"▶ **{stage}** started")
        elif event_type == "stage_completed":
            st.success(f"✓ **{stage}** completed ({latency}ms)")
        elif event_type == "tool_called":
            tool = data.get("tool", "?")
            st.code(f"🔧 {tool}(...)", language=None)
        elif event_type == "tool_result":
            tool = data.get("tool", "?")
            st.text(f"  ✓ {tool}")
        elif event_type == "tool_failed":
            tool = data.get("tool", "?")
            st.warning(f"  ✗ {tool}")
        elif event_type == "warning":
            st.warning(f"⚠ {data.get('message', '')}")
        elif event_type == "stage_retry":
            st.info(f"↻ Revision: {stage}")
        elif event_type == "run_completed":
            st.balloons()
            st.success(f"🏁 Pipeline completed ({latency}ms)")
        elif event_type == "run_failed":
            st.error(f"💥 Failed: {data.get('error', '')}")


def main() -> None:
    """Main Streamlit app."""
    st.title("🔬 AgentFlow")
    st.markdown("*Multi-Agent Research & Analysis Workflow*")

    with st.sidebar:
        st.header("Settings")
        mode = st.radio("Mode", ["Mock (Offline)", "Live (API)"], index=0)
        st.markdown("---")
        st.markdown("### Pipeline Stages\n1. **Plan** - Decompose query\n2. **Research** - Parallel tools\n3. **Analyze** - Synthesize\n4. **Write** - Report\n5. **Validate** - Quality check")

    query = st.text_input("Research Query", value="Company due-diligence brief on Acme Corp")

    if st.button("🚀 Run Pipeline", type="primary"):
        with st.spinner("Running research pipeline..."):
            from agentflow.pipeline import Pipeline

            if mode.startswith("Mock"):
                llm = get_mock_client()
            else:
                try:
                    from agentflow.llm.anthropic_client import AnthropicClient
                    llm = AnthropicClient()
                except Exception as e:
                    st.error(f"Failed to initialize LLM: {e}")
                    return

            pipeline = Pipeline(llm=llm)

            async def collect_events() -> list[dict[str, Any]]:
                result = []
                async for event in pipeline.run(query):
                    result.append(event.model_dump(mode="json"))
                return result

            events = run_async(collect_events())
            st.session_state["events"] = events

    if "events" in st.session_state:
        render_event_timeline(st.session_state["events"])

        st.markdown("---")
        with st.expander("🔍 Raw Stage Outputs"):
            for event in st.session_state["events"]:
                if event.get("type") == "stage_completed":
                    st.json(event)

        trace_json = json.dumps(st.session_state["events"], indent=2, default=str)
        st.download_button(
            "📥 Download Run Trace",
            data=trace_json,
            file_name=f"agentflow_trace_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json",
        )


if __name__ == "__main__":
    main()
