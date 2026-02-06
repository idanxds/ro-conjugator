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

    # STRATEGY 1: Clean the input
    # Remove 'a ' from the start if present (e.g. "a face" -> "face")
    if raw_verb.startswith("a "):
        verb_to_try = raw_verb[2:].strip()
    else:
        verb_to_try = raw_verb

    try:
        # STRATEGY 2: Try conjugating
        conjugation_object = conjugator.conjugate(verb_to_try)
        
        results = []
        for mood, tense, person, form in conjugation_object.iterate():
            # Clean up the output to look nice
            results.append(f"{mood} {tense} ({person}): {form}")
            
        return jsonify({"results": results})

    except ValueError:
        # If standard conjugation fails, it might be an unknown verb.
        # mlconjug3 is actually good at guessing new verbs, but sometimes the "lookup" fails.
        return jsonify({"error": f"Verb '{verb_to_try}' not found in the model. Try checking accents (ă, â, î, ș, ț)."}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
