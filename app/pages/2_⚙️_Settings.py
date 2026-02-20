"""
NOAH Knowledge Graph - Settings Page
"""
import streamlit as st
import sys
from pathlib import Path
import os

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

# Page config
st.set_page_config(
    page_title="Settings - NOAH KG",
    page_icon="⚙️",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    .setting-section {
        background: #f8f9fa;
        padding: 1.5rem;
        border-radius: 10px;
        margin: 1rem 0;
    }
    .status-ok {
        color: #28a745;
        font-weight: bold;
    }
    .status-error {
        color: #dc3545;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

st.title("⚙️ Settings & Configuration")
st.markdown("Configure API keys, database connections, and LLM parameters.")

# Initialize session state
if 'api_key' not in st.session_state:
    st.session_state.api_key = os.getenv('OPENAI_API_KEY', '') or os.getenv('ANTHROPIC_API_KEY', '')

if 'llm_provider' not in st.session_state:
    # Auto-detect based on available key
    if os.getenv('OPENAI_API_KEY'):
        st.session_state.llm_provider = 'openai'
    elif os.getenv('ANTHROPIC_API_KEY'):
        st.session_state.llm_provider = 'claude'
    else:
        st.session_state.llm_provider = 'openai'

if 'model' not in st.session_state:
    st.session_state.model = 'gpt-3.5-turbo'

if 'temperature' not in st.session_state:
    st.session_state.temperature = 0.0

# ========================================
# 1. API Key Configuration
# ========================================
st.markdown("## 🔑 API Key Configuration")

with st.container():
    st.markdown('<div class="setting-section">', unsafe_allow_html=True)

    # Provider selection
    provider = st.selectbox(
        "LLM Provider",
        options=['openai', 'claude', 'gemini'],
        index=['openai', 'claude', 'gemini'].index(st.session_state.llm_provider) if st.session_state.llm_provider in ['openai', 'claude', 'gemini'] else 0,
        help="Choose your preferred LLM provider"
    )

    st.session_state.llm_provider = provider

    # API Key input
    if provider == 'openai':
        api_key_label = "OpenAI API Key"
        api_key_placeholder = "sk-..."
    elif provider == 'claude':
        api_key_label = "Anthropic API Key"
        api_key_placeholder = "sk-ant-..."
    else:  # gemini
        api_key_label = "Google API Key"
        api_key_placeholder = "AIza..."

    api_key = st.text_input(
        api_key_label,
        value=st.session_state.get('api_key', ''),
        type="password",
        placeholder=api_key_placeholder,
        help=f"Your {api_key_label} - will be stored in session only (not saved to disk)"
    )

    if api_key != st.session_state.get('api_key', ''):
        st.session_state.api_key = api_key

    # Verify button
    col1, col2 = st.columns([1, 3])

    with col1:
        verify_btn = st.button("🔍 Verify Key", type="primary")

    if verify_btn:
        if not api_key:
            st.error("❌ Please enter an API key")
        else:
            with st.spinner("Verifying API key..."):
                try:
                    if provider == 'openai':
                        from openai import OpenAI
                        client = OpenAI(api_key=api_key)
                        # Test with minimal request
                        response = client.chat.completions.create(
                            model="gpt-3.5-turbo",
                            messages=[{"role": "user", "content": "Hi"}],
                            max_tokens=5
                        )
                        st.success("✅ OpenAI API key is valid!")
                    elif provider == 'claude':
                        from anthropic import Anthropic
                        client = Anthropic(api_key=api_key)
                        # Test with minimal request
                        response = client.messages.create(
                            model="claude-sonnet-4-5-20250929",
                            max_tokens=5,
                            messages=[{"role": "user", "content": "Hi"}]
                        )
                        st.success("✅ Anthropic API key is valid!")
                    else:  # gemini
                        import google.generativeai as genai
                        genai.configure(api_key=api_key)
                        model = genai.GenerativeModel('gemini-1.5-pro')
                        # Test with minimal request
                        response = model.generate_content("Hi")
                        st.success("✅ Google Gemini API key is valid!")

                except Exception as e:
                    st.error(f"❌ API key verification failed: {str(e)}")

    # Status
    if st.session_state.get('api_key'):
        st.markdown('<p class="status-ok">✅ API Key configured</p>', unsafe_allow_html=True)
    else:
        st.markdown('<p class="status-error">❌ API Key not set</p>', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

# ========================================
# 2. LLM Parameters
# ========================================
st.markdown("## 🤖 LLM Parameters")

with st.container():
    st.markdown('<div class="setting-section">', unsafe_allow_html=True)

    # Model selection
    if provider == 'openai':
        model_options = ['gpt-3.5-turbo', 'gpt-4', 'gpt-4-turbo-preview', 'gpt-4o']
        default_model = 'gpt-3.5-turbo'
    elif provider == 'claude':
        model_options = ['claude-sonnet-4-5-20250929', 'claude-opus-4-6', 'claude-haiku-4-5-20251001']
        default_model = 'claude-sonnet-4-5-20250929'
    else:  # gemini
        model_options = ['gemini-1.5-pro', 'gemini-1.5-flash', 'gemini-1.0-pro']
        default_model = 'gemini-1.5-pro'

    model = st.selectbox(
        "Model",
        options=model_options,
        index=model_options.index(st.session_state.get('model', default_model)) if st.session_state.get('model', default_model) in model_options else 0,
        help="Choose the LLM model to use for Text2Cypher translation"
    )

    st.session_state.model = model

    # Temperature
    temperature = st.slider(
        "Temperature",
        min_value=0.0,
        max_value=1.0,
        value=st.session_state.get('temperature', 0.0),
        step=0.1,
        help="0 = Deterministic (recommended for Cypher generation), 1 = Creative"
    )

    st.session_state.temperature = temperature

    # Max tokens
    max_tokens = st.number_input(
        "Max Tokens",
        min_value=100,
        max_value=4000,
        value=st.session_state.get('max_tokens', 2000),
        step=100,
        help="Maximum tokens in LLM response"
    )

    st.session_state.max_tokens = max_tokens

    st.markdown('</div>', unsafe_allow_html=True)

# ========================================
# 3. Neo4j Connection
# ========================================
st.markdown("## 🗄️ Neo4j Connection")

with st.container():
    st.markdown('<div class="setting-section">', unsafe_allow_html=True)

    # Connection info from config
    try:
        from noah_converter.utils.config import load_config
        config = load_config()

        st.info(f"""
        **Connection Details:**
        - URI: `{config.target_db.uri}`
        - Database: `{config.target_db.database}`
        - User: `{config.target_db.user}`
        """)

        # Test connection
        if st.button("🔍 Test Connection"):
            with st.spinner("Testing Neo4j connection..."):
                try:
                    from noah_converter.utils.db_connection import Neo4jConnection

                    neo4j_conn = Neo4jConnection(config.target_db)

                    # Get stats
                    stats = {}

                    # Count nodes
                    result = neo4j_conn.execute_query("MATCH (z:Zipcode) RETURN count(z) AS count")
                    stats['zipcodes'] = result[0]['count'] if result else 0

                    result = neo4j_conn.execute_query("MATCH (b:Building) RETURN count(b) AS count")
                    stats['buildings'] = result[0]['count'] if result else 0

                    result = neo4j_conn.execute_query("MATCH (p:HousingProject) RETURN count(p) AS count")
                    stats['projects'] = result[0]['count'] if result else 0

                    # Count relationships
                    result = neo4j_conn.execute_query("MATCH ()-[r:NEIGHBORS]->() RETURN count(r) AS count")
                    stats['neighbors'] = result[0]['count'] if result else 0

                    result = neo4j_conn.execute_query("MATCH ()-[r:LOCATED_IN]->() RETURN count(r) AS count")
                    stats['located_in'] = result[0]['count'] if result else 0

                    neo4j_conn.close()

                    st.success("✅ Successfully connected to Neo4j!")

                    # Update session state
                    st.session_state.neo4j_connected = True
                    st.session_state.db_stats = stats

                    # Show stats
                    st.markdown("**Database Statistics:**")
                    col1, col2, col3, col4, col5 = st.columns(5)
                    with col1:
                        st.metric("Zipcodes", stats['zipcodes'])
                    with col2:
                        st.metric("Buildings", stats['buildings'])
                    with col3:
                        st.metric("Projects", stats['projects'])
                    with col4:
                        st.metric("NEIGHBORS", stats['neighbors'])
                    with col5:
                        st.metric("LOCATED_IN", stats['located_in'])

                except Exception as e:
                    st.error(f"❌ Connection failed: {str(e)}")
                    st.session_state.neo4j_connected = False

        # Connection status
        if st.session_state.get('neo4j_connected'):
            st.markdown('<p class="status-ok">✅ Neo4j connected</p>', unsafe_allow_html=True)
        else:
            st.markdown('<p class="status-error">❌ Not connected</p>', unsafe_allow_html=True)

    except Exception as e:
        st.error(f"❌ Error loading config: {str(e)}")

    st.markdown('</div>', unsafe_allow_html=True)

# ========================================
# 4. Advanced Options
# ========================================
st.markdown("## 🔧 Advanced Options")

with st.container():
    st.markdown('<div class="setting-section">', unsafe_allow_html=True)

    enable_history = st.checkbox(
        "Enable Query History",
        value=st.session_state.get('enable_history', True),
        help="Store query history in session"
    )
    st.session_state.enable_history = enable_history

    auto_explain = st.checkbox(
        "Auto-generate Explanations",
        value=st.session_state.get('auto_explain', True),
        help="Automatically generate natural language explanations for query results"
    )
    st.session_state.auto_explain = auto_explain

    show_schema = st.checkbox(
        "Include Schema in Prompts",
        value=st.session_state.get('show_schema', True),
        help="Include database schema context in LLM prompts for better accuracy"
    )
    st.session_state.show_schema = show_schema

    st.markdown('</div>', unsafe_allow_html=True)

# ========================================
# Save/Reset
# ========================================
st.markdown("---")

col1, col2, col3 = st.columns([1, 1, 3])

with col1:
    if st.button("💾 Save Settings", type="primary"):
        st.success("✅ Settings saved to session!")

with col2:
    if st.button("🔄 Reset to Defaults"):
        # Reset to defaults
        st.session_state.api_key = ''
        st.session_state.llm_provider = 'openai'
        st.session_state.model = 'gpt-3.5-turbo'
        st.session_state.temperature = 0.0
        st.session_state.max_tokens = 2000
        st.session_state.enable_history = True
        st.session_state.auto_explain = True
        st.session_state.show_schema = True
        st.success("✅ Reset to defaults!")
        st.rerun()

# Sidebar - Current Settings Summary
with st.sidebar:
    st.markdown("### 📋 Current Settings")

    st.markdown("**LLM Configuration:**")
    st.code(f"""
Provider: {st.session_state.get('llm_provider', 'Not set')}
Model: {st.session_state.get('model', 'Not set')}
Temperature: {st.session_state.get('temperature', 0.0)}
Max Tokens: {st.session_state.get('max_tokens', 2000)}
    """)

    st.markdown("**Features:**")
    st.markdown(f"- Query History: {'✅' if st.session_state.get('enable_history') else '❌'}")
    st.markdown(f"- Auto Explain: {'✅' if st.session_state.get('auto_explain') else '❌'}")
    st.markdown(f"- Schema Context: {'✅' if st.session_state.get('show_schema') else '❌'}")
