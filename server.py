from flask import Flask, request, jsonify
from flask_cors import CORS
import mlconjug3
import requests
from bs4 import BeautifulSoup
import os

app = Flask(__name__)
CORS(app)

# Initialize the AI conjugator
conjugator = mlconjug3.Conjugator(language='ro')

def scrape_wiktionary_clean(verb):
    """Scrapes ONLY the conjugated words, ignoring labels."""
    try:
        url = f"https://en.wiktionary.org/api/rest_v1/page/html/{verb}?redirect=true"
        response = requests.get(url)
        if response.status_code != 200:
            return None

        soup = BeautifulSoup(response.content, 'html.parser')
        tables = soup.find_all('table', class_='inflection-table')
        
        clean_words = []
        for table in tables:
            data_cells = table.find_all('td')
            for cell in data_cells:
                word = cell.get_text(" ", strip=True)
                # Filter out garbage/labels
                if word and not any(x in word.lower() for x in ["subjunctive", "imperative", "person", "singular", "plural"]):
                    clean_words.append(word)
                    
        return clean_words if len(clean_words) > 0 else None
    except:
        return None

@app.route('/conjugate', methods=['POST'])
def conjugate_verb():
    data = request.get_json()
    raw_verb = data.get('verb', '').strip().lower()

    if not raw_verb:
        return jsonify({"error": "Please enter a verb."}), 400

    # Clean input
    verb_to_try = raw_verb[2:].strip() if raw_verb.startswith("a ") else raw_verb

    results = []

    # --- ATTEMPT 1: MLCONJUG3 (AI) ---
    try:
        conjugation_object = conjugator.conjugate(verb_to_try)
        if conjugation_object:
            # We ONLY want 'form' (the 4th item)
            for _, _, _, form in conjugation_object.iterate():
                results.append(form)
    except:
        pass

    # --- ATTEMPT 2: WIKTIONARY (Backup) ---
    if not results:
        print(f"AI failed for '{verb_to_try}', trying Wiktionary...")
        wiki_results = scrape_wiktionary_clean(verb_to_try)
        if wiki_results:
            results = wiki_results
        else:
            return jsonify({"error": f"Verb '{verb_to_try}' not found."}), 404

    # --- FINAL CLEANUP: Remove Duplicates & Sort ---
    # set() removes duplicates
    # sorted() puts them in alphabetical order
    final_results = sorted(list(set(results)))

    return jsonify({"results": final_results})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
