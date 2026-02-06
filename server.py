from flask import Flask, request, jsonify
from flask_cors import CORS
import mlconjug3
import os

app = Flask(__name__)
CORS(app)

# Initialize the conjugator
conjugator = mlconjug3.Conjugator(language='ro')

@app.route('/conjugate', methods=['POST'])
def conjugate_verb():
    data = request.get_json()
    raw_verb = data.get('verb', '').strip().lower()

    if not raw_verb:
        return jsonify({"error": "Please enter a verb."}), 400

    # Clean input: Remove 'a ' prefix if present
    verb_to_try = raw_verb[2:].strip() if raw_verb.startswith("a ") else raw_verb

    try:
        # Attempt conjugation
        conjugation_object = conjugator.conjugate(verb_to_try)
        
        # --- THE FIX IS HERE ---
        # Sometimes the library returns 'None' instead of raising an error.
        # We must check for this before trying to loop through it.
        if conjugation_object is None:
            return jsonify({"error": f"Verb '{verb_to_try}' could not be conjugated by the AI model."}), 404

        # Format results
        results = []
        for mood, tense, person, form in conjugation_object.iterate():
            results.append(f"{mood} {tense} ({person}): {form}")
            
        return jsonify({"results": results})

    except Exception as e:
        # Catch any other unexpected crashes
        return jsonify({"error": f"Server Error: {str(e)}"}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
