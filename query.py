import streamlit as st
from pyvis.network import Network
from neo4j import GraphDatabase
import neo4j
import pandas as pd
import tempfile

st.set_page_config(page_title="Neo4j ChatBot", layout="wide")

st.markdown("""
    <h1 style='text-align: center; color: #00cc66; font-size: 2.5rem;'>Neo4j ChatBot</h1>
    <p style='text-align: center; font-size: 1.2rem;'>Enter your Neo4j credentials below to connect.</p>
""", unsafe_allow_html=True)

st.sidebar.title("Neo4j Connection Settings")

neo4j_url = st.sidebar.text_input("Neo4j URL", "bolt://localhost:7687")
neo4j_username = st.sidebar.text_input("Username", "neo4j")
neo4j_password = st.sidebar.text_input("Password", type="password")

def check_credentials():
    return all([neo4j_url, neo4j_username, neo4j_password])

def get_graph_data(user_query):
    if not check_credentials():
        return None
    try:
        with GraphDatabase.driver(neo4j_url, auth=(neo4j_username, neo4j_password)) as driver:
            result, summary, _ = driver.execute_query(user_query)
            return result
    except Exception as e:
        st.error(f"Connection failed: {e}")
        return None

def visualize_result(query_graph):
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
    with tempfile.NamedTemporaryFile(delete=False, suffix=".html") as tmpfile:
        net.save_graph(tmpfile.name)
        return tmpfile.name

user_query = st.text_area("Enter your question below:", "MATCH (p:Person)-[r]->(m) RETURN p, r, m LIMIT 10")

run_query = st.button("Run Query")

if run_query:
    if not check_credentials():
        st.error("Please enter valid Neo4j credentials before running a query.")
    else:
        with st.spinner("Fetching data... Please wait"):
            query_result = get_graph_data(user_query)

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
