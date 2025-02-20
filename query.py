import streamlit as st
from pyvis.network import Network
from neo4j import GraphDatabase
import neo4j
import pandas as pd
import tempfile
import os

# Set Streamlit page config
st.set_page_config(page_title="Neo4j ChatBot", layout="wide")

# Custom header
st.markdown("""
    <h1 style='text-align: center; color: #00cc66; font-size: 2.5rem;'>Neo4j ChatBot</h1>
    <p style='text-align: center; font-size: 1.2rem;'>Write your question in the Sidebar and get the visual result.</p>
""", unsafe_allow_html=True)

# Neo4j connection details
URI = "bolt://localhost:7687"
AUTH = ("neo4j", "12345678")

def get_graph_data(user_query):
    with GraphDatabase.driver(URI, auth=AUTH) as driver:
        try:
            result, summary, _ = driver.execute_query(user_query)
            return result
        except Exception as e:
            st.error(f"Error executing query: {e}")
            return None

def visualize_result(query_graph):
    if not query_graph:
        return None

    visual_graph = Network(height="700px", width="100%", directed=True)
    visual_graph.toggle_physics(True)
    visual_graph.force_atlas_2based(gravity=-50, central_gravity=0.01)

    node_ids = set()
    edge_count = 0  # Track if edges exist

    # Define colors for different node types
    color_map = {
        "Person": "#00cc66",  # Green for Person
        "Movie": "#1f78b4",  # Blue for Movie
        "Default": "#ffcc00"  # Yellow for unknown types
    }

    # Add Nodes with Colors
    for record in query_graph:
        for item in record:
            if isinstance(item, neo4j.graph.Node):
                node_id = item.element_id
                node_labels = list(item.labels)  # Extract node labels
                node_type = node_labels[0] if node_labels else "Default"  # Use first label or default
                node_text = item.get("name", item.get("title", "Unknown"))

                node_color = color_map.get(node_type, color_map["Default"])  # Get color based on type

                node_ids.add(node_id)
                visual_graph.add_node(node_id, label=node_text, color=node_color, size=15)

    # Add Edges (only if nodes exist)
    for record in query_graph:
        for item in record:
            if isinstance(item, neo4j.graph.Relationship):
                start_id = item.start_node.element_id
                end_id = item.end_node.element_id
                
                if start_id in node_ids and end_id in node_ids:
                    visual_graph.add_edge(start_id, end_id, title=item.type, width=2)
                    edge_count += 1  # Increase edge count

    return visual_graph if edge_count > 0 else None  # Return graph only if edges exist

def save_and_display_pyvis(net):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".html") as tmpfile:
        net.save_graph(tmpfile.name)
        return tmpfile.name

# Sidebar for user input
st.sidebar.title("Graph Query Input")
default_query = "MATCH (p:Person)-[r]->(m) RETURN p, r, m LIMIT 10"
user_query = st.sidebar.text_area("Enter your question", default_query)

if st.sidebar.button("Run Query"):
    with st.spinner("Fetching data... Please wait"):
        query_result = get_graph_data(user_query)

    if query_result:
        # Try creating a graph visualization
        graph = visualize_result(query_result)

        if graph:
            st.subheader("Graph Visualization")
            html_file = save_and_display_pyvis(graph)
            with open(html_file, "r", encoding="utf-8") as f:
                html_code = f.read()
            st.components.v1.html(html_code, height=700, scrolling=True)
        else:
            if query_result:  # Ensure there's data
                column_names = query_result[0].keys() if query_result else []  # Extract column names
                records = [list(record.values()) for record in query_result]  # Extract row values
                
                df = pd.DataFrame(records, columns=column_names) if column_names else pd.DataFrame(records) 

                st.subheader("Query Result")
                st.dataframe(df)  # Display the table properly

        st.success("Query executed successfully!")
    else:
        st.error("No results found. Try a different query.")
