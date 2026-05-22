import streamlit as st
import sys
import os
import re
import contextlib
from io import StringIO

# Add the current directory to path so we can import our agents
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agents.manager import Manager

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Trace AI Engine",
    page_icon="🤖",
    layout="wide"
)

# --- CUSTOM CSS (Optional Polish) ---
st.markdown("""
<style>
    .stTextArea textarea { font-size: 14px; font-family: monospace; }
    .main { background-color: #f9f9f9; }
</style>
""", unsafe_allow_html=True)

# --- HEADER ---
col1, col2 = st.columns([1, 5])
with col1:
    st.image("https://cdn-icons-png.flaticon.com/512/2103/2103633.png", width=80)
with col2:
    st.title("Trace AI: QA Automation Engine")
    st.caption("Auto-generate robust Test Cases from User Stories using Multi-Agent AI.")

# --- SIDEBAR (CONTROLS) ---
with st.sidebar:
    st.header("⚙️ Controls")
    
    if st.button("🔄 Reset Agents", help="Clear memory and reload agents"):
        st.cache_resource.clear()
        st.toast("Agents have been reset!", icon="✅")
    
    st.markdown("---")
    st.info("""
    **Active Agents:**
    - 👨‍💼 **Manager:** Team Lead
    - 🏛️ **Archivist:** Legacy Data
    - ✍️ **Author:** Test Writer
    - 🔍 **Auditor:** Reviewer
    - 📝 **Scribe:** File Publisher
    """)

# --- AGENT INITIALIZATION (Cached) ---
@st.cache_resource
def get_manager():
    return Manager()

# --- MAIN UI ---
st.subheader("1. Input Requirements")
user_input = st.text_area(
    "Paste Feature, Context, and Scenarios:",
    height=300,
    placeholder="Feature: Search...\n\nAcceptance Criteria:\n1. ...\n\nScenarios:\n- Search by ID..."
)

col_run, col_status = st.columns([1, 4])
with col_run:
    run_btn = st.button("🚀 Generate Tests", type="primary", use_container_width=True)

# --- EXECUTION LOGIC ---
if run_btn:
    if not user_input.strip():
        st.error("Please provide input first.")
    else:
        # Create a container for the logs
        st.subheader("2. Agent Workflow Logs")
        log_box = st.empty()
        
        # Capture the terminal output
        output_buffer = StringIO()
        manager = get_manager()
        
        try:
            with st.spinner("Agents are collaborating..."):
                with contextlib.redirect_stdout(output_buffer):
                    # --- CALL THE MANAGER ---
                    result = manager.process_request(user_input)
                
                # Display logs in a code block
                log_box.code(output_buffer.getvalue(), language="text")

            # --- DISPLAY RESULTS ---
            st.subheader("3. Final Output")
            
            if "CRITICAL FAILURE" in result:
                st.error(result)
            else:
                st.success("Test Cases Generated Successfully!")
                st.text(result)
                
                # Check for CSV file creation to show download button
                match = re.search(r"saved: (.*\.csv)", result)
                if match:
                    csv_path = match.group(1)
                    if os.path.exists(csv_path):
                        with open(csv_path, "rb") as file:
                            st.download_button(
                                label="📥 Download CSV File",
                                data=file,
                                file_name=os.path.basename(csv_path),
                                mime="text/csv"
                            )

        except Exception as e:
            st.error(f"System Error: {e}")