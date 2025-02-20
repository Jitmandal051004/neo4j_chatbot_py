import streamlit as st
from pyvis.network import Network
from neo4j import GraphDatabase
import neo4j
import pandas as pd
import tempfile
import requests

st.set_page_config(page_title="Neo4j ChatBot", layout="wide")

st.markdown("""
    <h1 style='text-align: center; color: #00cc66; font-size: 2.5rem;'>Neo4j ChatBot</h1>
    <p style='text-align: center; font-size: 1.2rem;'>Enter your Neo4j credentials below to connect.</p>
""", unsafe_allow_html=True)

st.sidebar.title("Neo4j Connection Settings")

neo4j_url = st.sidebar.text_input("Neo4j URL", "bolt://localhost:7687")
neo4j_username = st.sidebar.text_input("Username", "neo4j")
neo4j_password = st.sidebar.text_input("Password", type="password")
ollama_model = st.sidebar.text_input("HuggingFace Model", "lakkeo/stable-cypher-instruct-3b:Q_K_M")

flask_server_url = "http://127.0.0.1:5000/generate-cypher"  # Update with your Flask server URL

def check_credentials():
    return all([neo4j_url, neo4j_username, neo4j_password])

def fetch_cypher_query(user_question):
    """Fetches the Cypher query from the Flask server."""
    try:
        response = requests.post(flask_server_url, json={"question": user_question,"model": ollama_model})
        response_json = response.json()
        return response_json.get("cypher_query", None)
    except Exception as e:
        st.error(f"Failed to fetch Cypher query: {e}")
        return None

def get_graph_data(cypher_query):
    """Executes the Cypher query in Neo4j and returns results."""
    if not check_credentials() or not cypher_query:
        return None
    try:
        with GraphDatabase.driver(neo4j_url, auth=(neo4j_username, neo4j_password)) as driver:
            result, summary, _ = driver.execute_query(cypher_query)
            return result
    except Exception as e:
        st.error(f"Neo4j connection failed: {e}")
        return None

def visualize_result(query_graph):
    """Generates a Pyvis visualization from the Neo4j query result."""
    if not query_graph:
        return None
    
    visual_graph = Network(height="700px", width="100%", directed=True)
    visual_graph.toggle_physics(True)
    visual_graph.force_atlas_2based(gravity=-50, central_gravity=0.01)
    
    color_map = {"Person": "#00cc66", "Movie": "#1f78b4", "Default": "#ffcc00"}
    node_ids = set()
    has_nodes = False
    
    for record in query_graph:
        for item in record:
            if isinstance(item, neo4j.graph.Node):
                has_nodes = True
                node_id = item.element_id
                node_labels = list(item.labels)
                node_type = node_labels[0] if node_labels else "Default"
                node_text = item.get("name", item.get("title", "Unknown"))
                node_color = color_map.get(node_type, color_map["Default"])
                
                node_ids.add(node_id)
                visual_graph.add_node(node_id, label=node_text, color=node_color, size=15)
    
    for record in query_graph:
        for item in record:
            if isinstance(item, neo4j.graph.Relationship):
                start_id = item.start_node.element_id
                end_id = item.end_node.element_id
                
                visual_graph.add_edge(start_id, end_id, title=item.type, width=2)
    
    return visual_graph if has_nodes else None

def save_and_display_pyvis(net):
    """Saves and embeds the Pyvis graph in Streamlit."""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".html") as tmpfile:
        net.save_graph(tmpfile.name)
        return tmpfile.name

user_question = st.text_area("Enter your question below:", "Who acted in The Matrix?")

run_query = st.button("Get Answer")

if run_query:
    if not check_credentials():
        st.error("Please enter valid Neo4j credentials before running a query.")
    else:
        with st.spinner("Fetching Cypher query from the server..."):
            cypher_query = fetch_cypher_query(user_question)

        if cypher_query:
            st.subheader("Generated Cypher Query")
            st.code(cypher_query, language="cypher")

            with st.spinner("Executing Cypher query in Neo4j..."):
                query_result = get_graph_data(cypher_query)

            if query_result:
                records = []
                column_names = set()
                for record in query_result:
                    row_data = {}
                    for key, value in record.items():
                        row_data[key] = value
                        column_names.add(key)
                    records.append(row_data)
                
                graph = visualize_result(query_result)
                df = pd.DataFrame(records, columns=list(column_names)) if records else None
                
                st.subheader("Graph Visualization")
                if graph:
                    graph_path = save_and_display_pyvis(graph)
                    with open(graph_path, "r", encoding="utf-8") as f:
                        html_content = f.read()
                    st.components.v1.html(html_content, height=700, scrolling=True)
                else:
                    st.write("Graph Visualization Not Possible")
                
                if df is not None and not df.empty:
                    st.subheader("Query Result")
                    st.dataframe(df, use_container_width=True)
                else:
                    st.error("No results found. Try a different query.")
        else:
            st.error("Failed to generate a Cypher query. Try again.")
