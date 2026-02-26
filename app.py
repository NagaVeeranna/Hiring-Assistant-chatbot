"""
Main Streamlit application for TalentScout Hiring Assistant
"""

import streamlit as st
import os
import time
from datetime import datetime
from dotenv import load_dotenv

# Import local modules
from chatbot import HiringAssistant
from utils import ExportManager, SentimentAnalyzer

load_dotenv()

# Page configuration
st.set_page_config(
    page_title="TalentScout AI | Hiring Assistant",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Consolidated Premium CSS
st.markdown("""
<style>
    /* Premium "Real Product" Design System */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=Outfit:wght@600;700&display=swap');

    .stApp {
        background: radial-gradient(circle, #EFF6FF 0%, #F8FAFC 60%, #FFFFFF 100%);
        color: #1A1F2B;
        font-family: 'Inter', -apple-system, system-ui, sans-serif;
    }

    /* Executive Header */
    .main-header {
        text-align: center;
        padding: 5rem 2rem 4rem 2rem;
        background: transparent;
        margin-bottom: 3rem;
    }

    h1 {
        font-family: 'Outfit', sans-serif;
        font-weight: 700;
        letter-spacing: -0.04em;
        color: #1e293b;
        font-size: 3.5rem !important;
        margin-bottom: 0.5rem;
    }

    h1 span { color: #2563EB; }

    .title-divider {
        width: 80px;
        height: 3px;
        background: #2563EB;
        border-radius: 10px;
        margin: 15px auto 28px auto; /* Increased margin-bottom */
    }

    .subtitle {
        color: #64748B;
        font-size: 1.25rem;
        font-weight: 400;
        max-width: 600px;
        margin: 0 auto;
        line-height: 1.5;
    }

    /* Elevated Chat Cards */
    .stChatMessage {
        background-color: #FFFFFF !important;
        border-radius: 14px !important;
        padding: 1.25rem 1.75rem !important;
        margin-bottom: 1.5rem !important;
        max-width: 85%;
        border: 1px solid #E6ECF5 !important;
        box-shadow: 0 6px 18px rgba(0, 0, 0, 0.05) !important;
        transition: transform 0.2s ease;
    }

    .stChatMessage:hover {
        transform: translateY(-2px);
    }

    .stChatMessage[data-testid="user-message"] {
        margin-left: auto;
        background-color: #F8FAFF !important;
        border: 1px solid #DBEAFE !important;
    }

    /* SaaS Dashboard Sidebar */
    section[data-testid="stSidebar"] {
        background-color: #FAFBFF !important;
        border-right: 1px solid #E6ECF5 !important;
    }

    .info-box {
        background-color: #FFFFFF;
        padding: 1.5rem;
        border-radius: 12px;
        margin: 1.25rem 0;
        border: 1px solid #DBEAFE;
        border-left: 4px solid #2563EB;
        box-shadow: 0 4px 14px rgba(37, 99, 235, 0.12);
    }

    .info-box h4 {
        margin-top: 0;
        margin-bottom: 1.25rem;
        color: #1E293B;
        font-family: 'Outfit', sans-serif;
    }

    .sidebar-label { 
        color: #94A3B8; 
        font-size: 0.70rem; 
        font-weight: 700; 
        text-transform: uppercase; 
        letter-spacing: 0.08em;
        margin-bottom: 0.2rem;
        margin-top: 0.75rem;
    }

    .sidebar-value { 
        color: #1E293B; 
        font-size: 0.95rem; 
        font-weight: 500;
        margin-bottom: 0;
    }

    /* Product Action Buttons */
    .stButton button {
        border-radius: 10px;
        background: #2563EB;
        color: white;
        height: 3rem;
        font-weight: 600;
        font-size: 1rem;
        border: none;
        transition: all 0.2s ease;
        padding: 0 2rem;
        box-shadow: 0 4px 12px rgba(37, 99, 235, 0.25);
    }

    .stButton button:hover {
        transform: translateY(-1px);
        background: #1D4ED8;
        box-shadow: 0 8px 20px rgba(37, 99, 235, 0.35);
    }

    /* Input Focus State - FORCED BLUE */
    [data-testid="stTextInput"] input:focus, 
    .stChatInputContainer:focus-within,
    [data-testid="stChatInput"] {
        border-color: #3B82F6 !important;
        box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.15) !important;
        outline: none !important;
    }

    /* Ensure no red borders from Streamlit defaults */
    .stChatInputContainer {
        border: 1px solid #E6ECF5 !important;
    }

    /* Metric Display */
    [data-testid="stMetricValue"] {
        color: #2563EB !important;
        font-weight: 700 !important;
        font-size: 1.75rem !important;
        font-family: 'Outfit', sans-serif !important;
    }
    
    [data-testid="stMetricLabel"] {
        color: #64748B !important;
        font-weight: 500 !important;
    }

    .main .block-container {
        padding-top: 2rem;
        max-width: 950px;
    }

    /* Warning Message Style */
    .warning-message {
        background-color: #FEF2F2;
        color: #991B1B;
        padding: 1.5rem;
        border-radius: 8px;
        border: 1px solid #FEE2E2;
        margin-bottom: 2rem;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if "assistant" not in st.session_state:
    try:
        st.session_state.assistant = HiringAssistant()
        st.session_state.messages = []
        st.session_state.initialized = False
        st.session_state.typing = False
        st.session_state.export_data = None
    except ValueError as e:
        st.error(f"Error: {str(e)}")
        st.stop()

# Executive Header
st.markdown("""
<div class="main-header">
    <h1>TalentScout <span>AI</span></h1>
    <div class="title-divider"></div>
    <p class="subtitle">Intelligent Hiring Assistant for Technology Placements</p>
</div>
""", unsafe_allow_html=True)

# API Key check
if not os.getenv("GOOGLE_API_KEY"):
    st.markdown("""
    <div class="warning-message">
        GOOGLE_API_KEY not found. Please add it to your .env file.
    </div>
    """, unsafe_allow_html=True)
    
    with st.expander("How to fix this"):
        st.markdown("""
        1. Create a `.env` file in your project root
        2. Add: `GOOGLE_API_KEY=your_api_key_here`
        3. Get your API key from [Google AI Studio](https://makersuite.google.com/app/apikey)
        
        **Example .env file:**
        ```
        GOOGLE_API_KEY=AIzaSyBxxxxxxxxxxxxxxxxxxxxx
        ```
        """)
    st.stop()

# Sidebar
with st.sidebar:
    st.markdown("### Session Overview")
    
    # Candidate profile card
    info = st.session_state.assistant.candidate_data
    
    st.markdown(f"""
    <div class="info-box">
        <h4>Candidate Profile</h4>
        <p class='sidebar-label'>Full Name</p>
        <p class='sidebar-value'>{info.full_name or '---'}</p>
        <p class='sidebar-label'>Email</p>
        <p class='sidebar-value'>{info.email or '---'}</p>
        <p class='sidebar-label'>Experience</p>
        <p class='sidebar-value'>{info.experience_years or '---'} Years</p>
        <p class='sidebar-label'>Location</p>
        <p class='sidebar-value'>{info.location or '---'}</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Progress Metric
    completion = info.completion_percentage()
    st.metric(label="Profile Readiness", value=f"{completion}%")
    
    st.markdown("---")
    
    # Sentiment analysis (bonus feature)
    if len(st.session_state.messages) > 2:
        st.markdown("### Conversation Insight")
        insight = st.session_state.assistant.get_sentiment_insight()
        st.caption(insight)
    
    # Session summary
    if st.session_state.assistant.conversation_phase != "Greeting":
        summary = st.session_state.assistant.get_session_summary()
        st.markdown("### Session Stats")
        st.caption(f"Duration: {summary['duration_minutes']} min")
        st.caption(f"Messages: {summary['message_count']}")
        st.caption(f"Phase: {summary['phase']}")
    
    st.markdown("---")
    
    # Export functionality
    if st.button("Export Session", use_container_width=True):
        export_data = ExportManager.prepare_export_data(
            st.session_state.assistant, 
            st.session_state.messages
        )
        st.session_state.export_data = export_data
        
        # JSON download
        json_str = ExportManager.to_json(export_data)
        st.download_button(
            label="Download JSON",
            data=json_str,
            file_name=f"interview_{export_data['export_id']}.json",
            mime="application/json",
            use_container_width=True
        )
        
        # CSV Q&A download
        csv_qa = ExportManager.to_csv_qa(export_data)
        st.download_button(
            label="Download Q&A CSV",
            data=csv_qa,
            file_name=f"qa_{export_data['export_id']}.csv",
            mime="text/csv",
            use_container_width=True
        )
        
        # CSV Candidate download
        csv_candidate = ExportManager.to_csv_candidate(export_data)
        st.download_button(
            label="Download Candidate CSV",
            data=csv_candidate,
            file_name=f"candidate_{export_data['export_id']}.csv",
            mime="text/csv",
            use_container_width=True
        )
    
    st.markdown("---")
    
    # Reset conversation
    if st.button("Reset Conversation", use_container_width=True):
        st.session_state.assistant = HiringAssistant()
        st.session_state.messages = []
        st.session_state.initialized = False
        st.session_state.export_data = None
        st.rerun()
    
    # Footer
    st.caption("Powered by **Gemini 2.5 Flash**")
    st.caption("© 2025 TalentScout AI")

# Main chat area
chat_container = st.container()

with chat_container:
    # Initial greeting
    if not st.session_state.initialized:
        with st.spinner("Initializing TalentScout AI..."):
            greeting = st.session_state.assistant.start_chat()
            st.session_state.messages.append({"role": "assistant", "content": greeting})
            st.session_state.initialized = True
    
    # Display chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Chat input
    if prompt := st.chat_input("Type your response here...", key="chat_input"):
        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Show typing indicator
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            
            # Show typing animation
            with st.spinner(""):
                # Get response
                response = st.session_state.assistant.process_message(prompt)
                message_placeholder.markdown(response)
            
            st.session_state.messages.append({"role": "assistant", "content": response})
        
        # Rerun to update sidebar
        st.rerun()

# Footer with additional info
st.markdown("---")
col1, col2, col3 = st.columns(3)
with col1:
    st.caption("🔒 GDPR Compliant")
with col2:
    st.caption("⚡ Powered by Gemini 2.5 Flash")
with col3:
    st.caption("🎯 For TalentScout Recruitment")