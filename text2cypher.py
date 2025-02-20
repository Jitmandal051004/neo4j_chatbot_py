from flask import Flask, request, jsonify
import ollama

app = Flask(__name__)

@app.route('/generate-cypher', methods=['POST'])
def generate_cypher():
    # Get the question from the incoming request
    data = request.get_json()
    question = data.get('question', '')

    # Define schema and the prompt
    schema = "(:Person)-[:ACTED_IN]->(:Movie)", "(:Person)-[:DIRECTED]->(:Movie)", "(:Person)-[:PRODUCED]->(:Movie)", "(:Person)-[:WROTE]->(:Movie)", "(:Person)-[:REVIEWED]->(:Movie)"
    
    full_prompt = f"""
    Generate a **Cypher MATCH query** to answer the following question: {question}.
    Strictly use only words present in this schema: {schema}.
    Keep the answer **short** and use **only** the relationships provided in the schema: `ACTED_IN`, `DIRECTED`, `PRODUCED`, `WROTE`, `REVIEWED`. 
    Do not introduce other relationships or entities. 
    The Cypher query **must start with MATCH and contain only the MATCH clause**. No RETURN, WHERE, or other clauses are allowed.
    **Example format**:
    MATCH (p:Person)-[r]->(m) RETURN p, r, m LIMIT 10;
    MATCH (p:Person) RETURN count(p);
    MATCH (p) RETURN p;
    Now generate the MATCH query following the rules strictly.
    """

    # Generate response using Ollama
    try:
        print("Generating response...")
        response = ollama.chat(
            model="hf.co/lakkeo/stable-cypher-instruct-3b:Q5_K_M",
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
