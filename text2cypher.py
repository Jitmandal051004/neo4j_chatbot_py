from flask import Flask, request, jsonify
import ollama

app = Flask(__name__)

@app.route('/generate-cypher', methods=['POST'])
def generate_cypher():
    # Get the question from the incoming request
    data = request.get_json()
    question = data.get('question', '')
    model = data.get('model', '')

    # Define schema and the prompt
    schema = "(:Person)-[:ACTED_IN]->(:Movie)", "(:Person)-[:DIRECTED]->(:Movie)", "(:Person)-[:PRODUCED]->(:Movie)", "(:Person)-[:WROTE]->(:Movie)", "(:Person)-[:REVIEWED]->(:Movie)"
    
    full_prompt = f"""
        Generate a **Cypher MATCH query** that strictly follows these rules:
        1. The query **must start with MATCH**.
        2. Use **only** the relationships provided in the schema: `ACTED_IN`, `DIRECTED`, `PRODUCED`, `WROTE`, `REVIEWED`.
        3. Do **not** introduce any other relationships or entities.
        4. Ensure **all nodes have variables** (e.g., `(p:Person)`, `(m:Movie)`).
        5. **All brackets must be correctly closed**.
        6. **No RETURN, WHERE, or other clauses**—only the `MATCH` clause is allowed.

        ### **Schema**:
        {schema}

        ### **Example Format**:
        MATCH (p:Person)-[r:ACTED_IN]->(m:Movie);
        MATCH (p:Person)-[r:DIRECTED]->(m:Movie);
        MATCH (p:Person)-[r]->(m:Movie);

        Now, generate the **correct Cypher MATCH query** for this question:  
        **{question}**
    """

    # Generate response using Ollama
    try:
        print("Generating response...")
        response = ollama.chat(
            model=f"hf.co/lakkeo/{model}",
            messages=[
                {"role": "system", "content": "Create a Cypher MATCH query to answer the following question."},
                {"role": "user", "content": full_prompt}
            ]
        )
        
        # Return the generated response as JSON
        return jsonify({
            'cypher_query': response.message.content
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
