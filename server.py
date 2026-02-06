from flask import Flask, request, jsonify
from flask_cors import CORS
from verbecc import CompleteConjugator
import os

app = Flask(__name__)
CORS(app)

# Initialize the Verbecc Conjugator
# This loads the dictionary and ML models.
conjugator = CompleteConjugator(lang='ro')

def extract_conjugations(data):
    """
    Smart extraction that navigates verbecc's nested dictionary structure.
    It looks specifically for the list of conjugated strings.
    """
    results = []
    
    if isinstance(data, dict):
        # 1. CHECK FOR THE TREASURE: 
        # Does this dict contain the actual conjugations?
        # 'conjugations' is the standard key, 'c' is the minified key.
        if 'conjugations' in data:
            return extract_conjugations(data['conjugations'])
        if 'c' in data:
            return extract_conjugations(data['c'])
            
        # 2. DIG DEEPER:
        # If not, it's a Mood or Tense container. Iterate through values.
        for value in data.values():
            results.extend(extract_conjugations(value))
            
    elif isinstance(data, list):
        # 3. COLLECT DATA:
        # If we found a list, check the items inside.
        for item in data:
            if isinstance(item, str):
                results.append(item)
            elif isinstance(item, dict):
                # If the list contains dictionaries (rare but possible), recurse
                results.extend(extract_conjugations(item))
            elif isinstance(item, list):
                # Flatten nested lists
                results.extend(extract_conjugations(item))
                 
    return results

@app.route('/conjugate', methods=['POST'])
def conjugate_verb():
    data = request.get_json()
    raw_verb = data.get('verb', '').strip().lower()

    if not raw_verb:
        return jsonify({"error": "Please enter a verb."}), 400

    verb_to_try = raw_verb

    try:
        # 1. Get the complex conjugation object
        conjugation = conjugator.conjugate(verb_to_try)
        conjugation_data = conjugation.get_data()
        
        # 2. Extract only the strings
        all_forms = extract_conjugations(conjugation_data)
        
        # 3. Clean and Sort
        cleaned_results = set()
        for form in all_forms:
            clean_form = str(form).strip()
            # We keep 'e' (valid for "el e") but remove empty strings
            if len(clean_form) > 0:
                cleaned_results.add(clean_form)

        final_list = sorted(list(cleaned_results))
        
        if not final_list:
            return jsonify({"error": f"Could not conjugate '{verb_to_try}'."}), 404

        return jsonify({"results": final_list})

    except Exception as e:
        print(f"Server Error: {e}")
        return jsonify({"error": "Server error processing verb."}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
