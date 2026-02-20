"""
NOAH Knowledge Graph - Query Interface
"""
import streamlit as st
import sys
from pathlib import Path
import json
import time

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

# Page config
st.set_page_config(
    page_title="Query - NOAH KG",
    page_icon="🔍",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    .query-box {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #1E88E5;
    }
    .result-box {
        background: white;
        padding: 1.5rem;
        border-radius: 8px;
        border: 1px solid #e0e0e0;
        margin: 1rem 0;
    }
    .cypher-code {
        background: #282c34;
        color: #abb2bf;
        padding: 1rem;
        border-radius: 8px;
        font-family: 'Courier New', monospace;
    }
    .success-box {
        background: #d4edda;
        border: 1px solid #c3e6cb;
        color: #155724;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
    }
    .error-box {
        background: #f8d7da;
        border: 1px solid #f5c6cb;
        color: #721c24;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'query_history' not in st.session_state:
    st.session_state.query_history = []

if 'current_result' not in st.session_state:
    st.session_state.current_result = None

# Header
st.title("🔍 Query Interface")
st.markdown("Ask questions about NYC housing data in plain English or write Cypher queries directly.")

# Check if API key is configured
if 'api_key' not in st.session_state or not st.session_state.get('api_key'):
    st.warning("⚠️ Please configure your API key in the Settings page first.")
    if st.button("Go to Settings"):
        st.switch_page("pages/2_⚙️_Settings.py")
    st.stop()

# Tabs
tab1, tab2 = st.tabs(["🗣️ Natural Language", "🧑‍💻 Cypher Expert"])

# ========================================
# Tab 1: Natural Language Query
# ========================================
with tab1:
    st.markdown("### Ask Your Question")

    # Example questions
    st.markdown("**💡 Try these examples:**")
    example_cols = st.columns(3)

    with example_cols[0]:
        if st.button("Which ZIPs are neighbors of 10001?", use_container_width=True):
            st.session_state.nl_query = "Which ZIP codes are neighbors of 10001?"

    with example_cols[1]:
        if st.button("Find housing projects in Brooklyn", use_container_width=True):
            st.session_state.nl_query = "Show me all housing projects in Brooklyn"

    with example_cols[2]:
        if st.button("How many projects per borough?", use_container_width=True):
            st.session_state.nl_query = "How many housing projects are in each borough?"

    # Query input
    question = st.text_area(
        "Your question:",
        value=st.session_state.get('nl_query', ''),
        placeholder="Example: Which ZIP codes have the highest rent burden?",
        height=100,
        key="nl_input"
    )

    col1, col2, col3 = st.columns([1, 1, 4])

    with col1:
        submit_btn = st.button("🚀 Submit Query", type="primary", use_container_width=True)

    with col2:
        clear_btn = st.button("🗑️ Clear", use_container_width=True)
        if clear_btn:
            st.session_state.nl_query = ""
            st.session_state.current_result = None
            st.rerun()

    # Process query
    if submit_btn and question:
        with st.spinner("🤖 Generating Cypher query..."):
            try:
                # Import Text2Cypher
                from noah_converter.text2cypher import Text2CypherTranslator
                from noah_converter.utils.db_connection import Neo4jConnection
                from noah_converter.utils.config import load_config

                # Get config
                config = load_config()
                neo4j_conn = Neo4jConnection(config.target_db)

                # Create translator
                provider = st.session_state.get('llm_provider', 'openai')
                api_key = st.session_state.get('api_key')
                model = st.session_state.get('model', 'gpt-3.5-turbo' if provider == 'openai' else 'claude-sonnet-4-5-20250929')

                translator = Text2CypherTranslator(
                    neo4j_conn=neo4j_conn,
                    llm_provider=provider,
                    api_key=api_key,
                    model=model,
                    temperature=0
                )

                # Execute query
                start_time = time.time()
                result = translator.query(
                    question=question,
                    execute=True,
                    explain=True
                )
                execution_time = time.time() - start_time

                result['execution_time'] = execution_time
                st.session_state.current_result = result

                # Add to history
                st.session_state.query_history.append({
                    'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
                    'type': 'Natural Language',
                    'question': question,
                    'cypher': result['cypher'],
                    'success': not result['error'],
                    'execution_time': execution_time
                })

                neo4j_conn.close()

            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
                st.session_state.current_result = {
                    'error': str(e),
                    'question': question
                }

    # Display results
    if st.session_state.current_result:
        result = st.session_state.current_result

        st.markdown("---")

        if result.get('error'):
            st.markdown(f'<div class="error-box">❌ <b>Error:</b> {result["error"]}</div>', unsafe_allow_html=True)
        else:
            # Success message
            st.markdown(
                f'<div class="success-box">✅ Query executed successfully in {result["execution_time"]:.2f}s</div>',
                unsafe_allow_html=True
            )

            # Generated Cypher
            with st.expander("📝 Generated Cypher Query", expanded=True):
                st.code(result['cypher'], language='cypher')

                col1, col2 = st.columns([1, 5])
                with col1:
                    if st.button("📋 Copy"):
                        st.toast("Copied to clipboard!")

            # Results
            st.markdown("### 📊 Query Results")

            if result['results']:
                st.dataframe(
                    result['results'],
                    use_container_width=True,
                    height=300
                )

                # Download button
                csv_data = ""
                if result['results']:
                    import pandas as pd
                    df = pd.DataFrame(result['results'])
                    csv_data = df.to_csv(index=False)

                st.download_button(
                    label="📥 Download as CSV",
                    data=csv_data,
                    file_name="query_results.csv",
                    mime="text/csv"
                )

                st.metric("Total Results", len(result['results']))
            else:
                st.info("ℹ️ No results found.")

            # AI Explanation
            if result.get('explanation'):
                st.markdown("### 💬 AI Explanation")
                st.info(result['explanation'])

# ========================================
# Tab 2: Cypher Expert Mode
# ========================================
with tab2:
    st.markdown("### Write Cypher Query")

    # Example queries
    st.markdown("**💡 Example Queries:**")
    example_cypher_cols = st.columns(2)

    with example_cypher_cols[0]:
        if st.button("Simple: All Zipcodes", use_container_width=True, key="ex1"):
            st.session_state.cypher_query = "MATCH (z:Zipcode)\nRETURN z.zipcode, z.borough\nORDER BY z.zipcode\nLIMIT 10"

        if st.button("Neighbors Query", use_container_width=True, key="ex2"):
            st.session_state.cypher_query = "MATCH (z:Zipcode {zipcode: '10001'})-[:NEIGHBORS]->(neighbor)\nRETURN neighbor.zipcode, neighbor.borough\nORDER BY neighbor.zipcode"

    with example_cypher_cols[1]:
        if st.button("Aggregation: Projects per Borough", use_container_width=True, key="ex3"):
            st.session_state.cypher_query = "MATCH (p:HousingProject)-[:LOCATED_IN]->(z:Zipcode)\nRETURN z.borough, count(p) AS numProjects\nORDER BY numProjects DESC"

        if st.button("Multi-hop: 2-hop Neighbors", use_container_width=True, key="ex4"):
            st.session_state.cypher_query = "MATCH path = (z:Zipcode {zipcode: '10001'})-[:NEIGHBORS*1..2]->(neighbor)\nWITH DISTINCT neighbor, min(length(path)) AS hops\nRETURN neighbor.zipcode, hops\nORDER BY hops, neighbor.zipcode\nLIMIT 20"

    # Cypher editor
    cypher_query = st.text_area(
        "Cypher Query:",
        value=st.session_state.get('cypher_query', ''),
        placeholder="MATCH (z:Zipcode)\nRETURN z.zipcode, z.borough\nLIMIT 10",
        height=200,
        key="cypher_input"
    )

    col1, col2, col3 = st.columns([1, 1, 4])

    with col1:
        run_btn = st.button("▶️ Run Query", type="primary", use_container_width=True)

    with col2:
        clear_cypher_btn = st.button("🗑️ Clear", use_container_width=True, key="clear_cypher")
        if clear_cypher_btn:
            st.session_state.cypher_query = ""
            st.session_state.current_result = None
            st.rerun()

    # Execute Cypher
    if run_btn and cypher_query:
        with st.spinner("⚙️ Executing query..."):
            try:
                from noah_converter.utils.db_connection import Neo4jConnection
                from noah_converter.utils.config import load_config

                config = load_config()
                neo4j_conn = Neo4jConnection(config.target_db)

                start_time = time.time()
                results = neo4j_conn.execute_query(cypher_query)
                execution_time = time.time() - start_time

                st.session_state.current_result = {
                    'cypher': cypher_query,
                    'results': results,
                    'execution_time': execution_time,
                    'error': None
                }

                # Add to history
                st.session_state.query_history.append({
                    'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
                    'type': 'Cypher',
                    'question': cypher_query[:100] + '...' if len(cypher_query) > 100 else cypher_query,
                    'cypher': cypher_query,
                    'success': True,
                    'execution_time': execution_time
                })

                neo4j_conn.close()

            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
                st.session_state.current_result = {
                    'error': str(e),
                    'cypher': cypher_query
                }

    # Display results
    if st.session_state.current_result and st.session_state.current_result.get('cypher') == cypher_query:
        result = st.session_state.current_result

        st.markdown("---")

        if result.get('error'):
            st.markdown(f'<div class="error-box">❌ <b>Error:</b> {result["error"]}</div>', unsafe_allow_html=True)
        else:
            st.markdown(
                f'<div class="success-box">✅ Query executed successfully in {result["execution_time"]:.2f}s</div>',
                unsafe_allow_html=True
            )

            st.markdown("### 📊 Query Results")

            if result['results']:
                st.dataframe(
                    result['results'],
                    use_container_width=True,
                    height=300
                )

                import pandas as pd
                df = pd.DataFrame(result['results'])
                csv_data = df.to_csv(index=False)

                st.download_button(
                    label="📥 Download as CSV",
                    data=csv_data,
                    file_name="cypher_results.csv",
                    mime="text/csv"
                )

                st.metric("Total Results", len(result['results']))
            else:
                st.info("ℹ️ No results found.")

# Sidebar - Query History
with st.sidebar:
    st.markdown("### 📜 Recent Queries")

    if st.session_state.query_history:
        # Show last 5 queries
        for i, query in enumerate(reversed(st.session_state.query_history[-5:])):
            with st.expander(f"{query['type']} - {query['timestamp']}", expanded=False):
                st.text(query['question'][:100])
                if query['success']:
                    st.success(f"✅ {query['execution_time']:.2f}s")
                else:
                    st.error("❌ Failed")

        if st.button("🗑️ Clear History"):
            st.session_state.query_history = []
            st.rerun()
    else:
        st.info("No queries yet")
