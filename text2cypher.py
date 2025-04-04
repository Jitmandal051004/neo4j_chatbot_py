from flask import Flask, request, jsonify
import ollama

app = Flask(__name__)

@app.route('/generate-cypher', methods=['POST'])
def generate_cypher():
    data = request.get_json()
    question = data.get('question', '')
    model = data.get('model', '')

    if not model:
        model = "hf.co/lakkeo/stable-cypher-instruct-3b:Q5_K_M"

    print("Using model:", model)

    schema = '''"(:Person)-[:ACTED_IN]->(:Movie)", 
            "(:Person)-[:DIRECTED]->(:Movie)", 
            "(:Person)-[:PRODUCED]->(:Movie)", 
            "(:Person)-[:WROTE]->(:Movie)", 
            "(:Person)-[:REVIEWED]->(:Movie)", 
            "(:Person)-[:FOLLOWS]->(:Person)"'''

    examples = """
    Example Queries:
    1. Movies between 1990-2000 with >5000 votes:
        MATCH (m:Movie) WHERE m.released >= 1990 AND m.released <= 2000 AND m.votes > 5000 RETURN m;

    2. Movie with highest budget:
        MATCH (m:Movie) RETURN m ORDER BY m.budget DESC LIMIT 1;

    3. Top 5 actors with most roles before 1980:
        MATCH (a:Actor)-[r:ACTED_IN]->(m:Movie) WHERE m.year < 1980 RETURN a, r, m LIMIT 5;

    4. Give me Person who acted in movies and their relation:
        MATCH (a:Actor)-[r:ACTED_IN]->(m:Movie) WHERE a, r, m
    """

    full_prompt = f"""
        Generate a **Cypher MATCH query** following these rules:
	- Must start with **MATCH**.
	- Use **only** relationships: `ACTED_IN`, `DIRECTED`, `PRODUCED`, `WROTE`, `REVIEWED`.
	- The **RETURN clause must return only variables (e.g., RETURN p, m, r) without aliasing**.
	- **Do not explain** your reasoning, just return the Cypher query.

        ### **Schema**:
        {schema}

        {examples}

        **Question:** {question}
    """

    try:
        print("Generating response...")
        response = ollama.chat(
            model=model,  # Directly pass the model name without "hf.co/"
            messages=[
                {"role": "system", "content": "Create a Cypher MATCH query to answer the following question."},
                {"role": "user", "content": full_prompt}
            ]
        )

        cypher_query = response['message']['content']
        cypher_start = cypher_query.find("MATCH")

        if cypher_start != -1:
            cypher_query = cypher_query[cypher_start:].strip()

        print(f"Generated Cypher Query: {cypher_query}")

        return jsonify({'cypher_query': cypher_query})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)

