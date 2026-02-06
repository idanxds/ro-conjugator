from flask import Flask, request, jsonify
from flask_cors import CORS
from verbecc import CompleteConjugator
import os

app = Flask(__name__)
CORS(app)

# Initialize the Verbecc Conjugator for Romanian
# This loads the dictionary and ML models.
conjugator = CompleteConjugator(lang='ro')

def extract_conjugations(data):
    """
    Recursive function to dig through the complex dictionary returned by verbecc
    and extract only the final conjugated strings.
    """
    results = []
    
    if isinstance(data, dict):
        # If it's a dictionary (like 'Mood' or 'Tense'), dig deeper
        for key, value in data.items():
            results.extend(extract_conjugations(value))
    elif isinstance(data, list):
        # If it's a list, these are the actual conjugations!
        for item in data:
            # verbecc sometimes returns full objects or strings depending on version.
            # We treat them as strings.
            if isinstance(item, str):
                results.append(item)
            elif isinstance(item, list):
                 # Sometimes it returns [pronoun, verb], we join them
                 results.append(" ".join(item))
            elif hasattr(item, '__iter__'):
                 # Handle older versions where it might be a tuple
                 results.append(" ".join([str(x) for x in item]))
                 
    return results

@app.route('/conjugate', methods=['POST'])
def conjugate_verb():
    data = request.get_json()
    raw_verb = data.get('verb', '').strip().lower()

    if not raw_verb:
        return jsonify({"error": "Please enter a verb."}), 400

    # Clean input: verbecc expects the infinitive (e.g., 'fi' or 'a fi')
    # It handles 'a ' well, but we can strip it to be safe.
    verb_to_try = raw_verb

    try:
        # 1. Get the complex conjugation object
        conjugation = conjugator.conjugate(verb_to_try)
        
        # 2. Get the data as a dictionary
        # verbecc 2.x returns a wrapper, .get_data() gives the raw dict
        conjugation_data = conjugation.get_data()
        
        # 3. Flatten the dictionary into a simple list of verbs
        all_forms = extract_conjugations(conjugation_data)
        
        # 4. Filter and Clean
        # - Remove duplicates
        # - Remove empty strings
        # - Filter out "random stuff" (e.g., if a result is just 1 letter and not 'e')
        cleaned_results = set()
        for form in all_forms:
            clean_form = str(form).strip()
            # We keep 'e' (as in 'el e') but discard obvious garbage if any
            if len(clean_form) > 0:
                cleaned_results.add(clean_form)

        # 5. Sort alphabetically
        final_list = sorted(list(cleaned_results))
        
        if not final_list:
            return jsonify({"error": f"Could not conjugate '{verb_to_try}'."}), 404

        return jsonify({"results": final_list})

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": "Server error. The verb might be invalid."}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
