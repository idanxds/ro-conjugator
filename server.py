from flask import Flask, request, jsonify
from flask_cors import CORS
import mlconjug3
import os

app = Flask(__name__)
CORS(app)  # Allows your HTML file to talk to this Python server

# Initialize the conjugator once (it's faster)
conjugator = mlconjug3.Conjugator(language='ro')

@app.route('/conjugate', methods=['POST'])
def conjugate_verb():
    data = request.get_json()
    verb_input = data.get('verb', '').strip()

    if not verb_input:
        return jsonify({"error": "Please enter a verb."}), 400

    try:
        # Conjugate the verb
        conjugation_object = conjugator.conjugate(verb_input)
        
        # Flatten the results into a clean list of strings
        # Format: "Indicativ Prezent (1s): vorbesc"
        results = []
        for mood, tense, person, form in conjugation_object.iterate():
            results.append(f"{mood} {tense} ({person}): {form}")
            
        return jsonify({"results": results})

    except ValueError:
        return jsonify({"error": f"Verb '{verb_input}' not found."}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
