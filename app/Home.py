"""
NOAH Knowledge Graph - Home Page
"""
import streamlit as st
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Page config
st.set_page_config(
    page_title="NOAH Knowledge Graph",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        color: #1E88E5;
        text-align: center;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.2rem;
        text-align: center;
        color: #666;
        margin-bottom: 2rem;
    }
    .stat-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 10px;
        color: white;
        text-align: center;
    }
    .stat-number {
        font-size: 2.5rem;
        font-weight: bold;
        margin: 0.5rem 0;
    }
    .stat-label {
        font-size: 0.9rem;
        opacity: 0.9;
    }
    .feature-box {
        background: #f8f9fa;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 4px solid #1E88E5;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown('<div class="main-header">🏠 NOAH Knowledge Graph</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="sub-header">Naturally Occurring Affordable Housing - NYC Data Explorer</div>',
    unsafe_allow_html=True
)

# Introduction
st.markdown("---")
col1, col2 = st.columns([2, 1])

with col1:
    st.markdown("### 📖 What is NOAH?")
    st.markdown("""
    The **NOAH (Naturally Occurring Affordable Housing) Knowledge Graph** transforms NYC housing data
    from a traditional relational database into a powerful graph database, enabling:

    - 🔍 **Intuitive natural language queries** - Ask questions in plain English
    - ⚡ **Fast relationship traversals** - Find neighbors, patterns, and connections instantly
    - 📊 **Complex pattern matching** - Discover housing affordability trends
    - 🎯 **Multi-hop queries** - Explore neighborhood networks easily
    """)

    st.markdown("### 🎯 Why Neo4j?")
    st.markdown("""
    Traditional SQL databases struggle with relationship-heavy queries. Neo4j excels at:
    - **Multi-hop traversals** (neighbors of neighbors) - simple instead of complex JOINs
    - **Pattern matching** - find complex housing patterns in one query
    - **Graph algorithms** - shortest paths, community detection, centrality analysis
    """)

with col2:
    st.markdown("### 🚀 Quick Start")

    with st.container():
        st.markdown('<div class="feature-box">', unsafe_allow_html=True)
        st.markdown("**Step 1:** Set up your API key")
        st.markdown("Go to ⚙️ Settings")
        st.markdown("</div>", unsafe_allow_html=True)

    with st.container():
        st.markdown('<div class="feature-box">', unsafe_allow_html=True)
        st.markdown("**Step 2:** Try a query")
        st.markdown("Go to 🔍 Query")
        st.markdown("</div>", unsafe_allow_html=True)

    with st.container():
        st.markdown('<div class="feature-box">', unsafe_allow_html=True)
        st.markdown("**Step 3:** Explore!")
        st.markdown("Ask questions in plain English")
        st.markdown("</div>", unsafe_allow_html=True)

# Statistics
st.markdown("---")
st.markdown("### 📊 Database Statistics")

# Get stats from session state or use defaults
if 'db_stats' not in st.session_state:
    st.session_state.db_stats = {
        'zipcodes': 16,
        'buildings': 0,
        'projects': 20,
        'neighbors': 140,
        'located_in': 20
    }

stats = st.session_state.db_stats

col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.markdown(f"""
    <div class="stat-card">
        <div class="stat-label">ZIP Codes</div>
        <div class="stat-number">{stats['zipcodes']}</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div class="stat-card" style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);">
        <div class="stat-label">Buildings</div>
        <div class="stat-number">{stats['buildings']}</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown(f"""
    <div class="stat-card" style="background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);">
        <div class="stat-label">Housing Projects</div>
        <div class="stat-number">{stats['projects']}</div>
    </div>
    """, unsafe_allow_html=True)

with col4:
    st.markdown(f"""
    <div class="stat-card" style="background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);">
        <div class="stat-label">Neighbor Links</div>
        <div class="stat-number">{stats['neighbors']}</div>
    </div>
    """, unsafe_allow_html=True)

with col5:
    st.markdown(f"""
    <div class="stat-card" style="background: linear-gradient(135deg, #fa709a 0%, #fee140 100%);">
        <div class="stat-label">Location Links</div>
        <div class="stat-number">{stats['located_in']}</div>
    </div>
    """, unsafe_allow_html=True)

# Example Queries
st.markdown("---")
st.markdown("### 💡 Example Questions You Can Ask")

example_col1, example_col2 = st.columns(2)

with example_col1:
    st.markdown("**🔍 Simple Queries:**")
    st.code("Which ZIP codes are in Brooklyn?")
    st.code("Show me all housing projects in Manhattan")
    st.code("How many projects are in each borough?")

    st.markdown("**🔗 Relationship Queries:**")
    st.code("Which ZIP codes are neighbors of 10001?")
    st.code("Find housing projects in ZIPs neighboring 11106")

with example_col2:
    st.markdown("**📍 Spatial Queries:**")
    st.code("Find ZIP codes within 5km of 10001")
    st.code("Which ZIPs are closest to 10002?")

    st.markdown("**🎯 Complex Queries:**")
    st.code("Find all ZIP codes within 2 hops of 10001")
    st.code("Show housing projects in high rent burden neighborhoods")

# Features
st.markdown("---")
st.markdown("### ✨ Key Features")

feat_col1, feat_col2, feat_col3 = st.columns(3)

with feat_col1:
    st.markdown("#### 🗣️ Natural Language")
    st.markdown("""
    Ask questions in plain English. Our AI-powered Text2Cypher translator
    converts your questions into optimized graph queries automatically.
    """)

with feat_col2:
    st.markdown("#### 🧑‍💻 Expert Mode")
    st.markdown("""
    Write Cypher queries directly for full control. Includes syntax highlighting,
    auto-completion, and example query library.
    """)

with feat_col3:
    st.markdown("#### 📊 Rich Results")
    st.markdown("""
    View results as tables, charts, or interactive network visualizations.
    Export data in multiple formats (CSV, JSON).
    """)

# Technology Stack
st.markdown("---")
st.markdown("### 🛠️ Technology Stack")

tech_col1, tech_col2, tech_col3 = st.columns(3)

with tech_col1:
    st.markdown("**Database:**")
    st.markdown("- 🗄️ Neo4j 5.15.0")
    st.markdown("- 🐘 PostgreSQL + PostGIS")

with tech_col2:
    st.markdown("**AI/ML:**")
    st.markdown("- 🤖 OpenAI GPT-4")
    st.markdown("- 🧠 Anthropic Claude")
    st.markdown("- 📝 Few-shot Learning")

with tech_col3:
    st.markdown("**Frontend:**")
    st.markdown("- 🎨 Streamlit")
    st.markdown("- 🐍 Python 3.11+")
    st.markdown("- 🐳 Docker")

# Footer
st.markdown("---")
footer_col1, footer_col2, footer_col3 = st.columns(3)

with footer_col1:
    st.markdown("**📚 Documentation**")
    st.markdown("[User Guide](https://github.com)")
    st.markdown("[API Reference](https://github.com)")

with footer_col2:
    st.markdown("**🔗 Links**")
    st.markdown("[GitHub Repository](https://github.com)")
    st.markdown("[Report Issues](https://github.com)")

with footer_col3:
    st.markdown("**👥 About**")
    st.markdown("NYU Capstone Project 2026")
    st.markdown("Digital Forge Lab")

# Sidebar
with st.sidebar:
    st.markdown("### 🎯 Navigation")
    st.info("""
    👈 Use the sidebar to navigate between pages:

    - 🏠 **Home**: Overview and introduction
    - 🔍 **Query**: Ask questions and run queries
    - ⚙️ **Settings**: Configure API keys and connections
    """)

    st.markdown("---")
    st.markdown("### 📊 Connection Status")

    # Check if configured
    if 'api_key' in st.session_state and st.session_state.get('api_key'):
        st.success("✅ API Key configured")
    else:
        st.warning("⚠️ API Key not set")
        st.markdown("[Go to Settings →](Settings)")

    if 'neo4j_connected' in st.session_state and st.session_state.get('neo4j_connected'):
        st.success("✅ Neo4j connected")
    else:
        st.info("ℹ️ Neo4j not connected")
