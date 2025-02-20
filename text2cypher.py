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
    Generate a **Cypher statement** to answer the following question: {question}.
    Strictly use only words present in this schema: {schema}.
    Keep the answer **short** and use **only** the relationships provided in the schema: `ACTED_IN`, `DIRECTED`, `PRODUCED`, `WROTE`, `REVIEWED`. 
    Do not introduce other relationships or entities. 
    Do not use HAS_SKILL or other schema terms outside of the ones provided. 
    In the Cypher query, find people who acted in a movie specifically titled "The Matrix".
    Return only the Cypher query without any explanation.
    """

    # Generate response using Ollama
    try:
        print("Generating response...")
        response = ollama.chat(
            model="hf.co/lakkeo/stable-cypher-instruct-3b:Q8_0",
            messages=[
                {"role": "system", "content": "Create a Cypher statement to answer the following question."},
                {"role": "user", "content": full_prompt}
            ]
        )
        
        # Return the generated response as JSON
        return jsonify({
            'cypher_query': response.message.content
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if name == '__main__':
    app.run(debug=True)