import os
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename
from pathlib import Path
import json
import main_round1b # Assuming your Round 1B logic is in this file
import pickle
import numpy as np
from sentence_transformers import util

app = Flask(__name__)
CORS(app) # Allows the frontend to communicate with the backend

# Configuration
UPLOAD_FOLDER = Path('../uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
UPLOAD_FOLDER.mkdir(exist_ok=True)

@app.route('/process', methods=['POST'])
def process_documents():
    """
    Main endpoint to process documents based on persona and job.
    """
    if 'persona' not in request.form or 'job_to_be_done' not in request.form:
        return jsonify({"error": "Missing persona or job_to_be_done"}), 400

    persona_str = request.form['persona']
    job_to_be_done = request.form['job_to_be_done']
    files = request.files.getlist('documents')

    if not files:
        return jsonify({"error": "No documents provided"}), 400

    # --- Create a temporary test case structure for your Round 1B script ---
    case_dir = UPLOAD_FOLDER / "temp_case"
    docs_dir = case_dir / "documents"
    docs_dir.mkdir(parents=True, exist_ok=True)

    # Clean up previous files
    for f in docs_dir.glob('*'):
        os.remove(f)

    # Save new files and persona/job definitions
    doc_paths = []
    for file in files:
        filename = secure_filename(file.filename)
        file_path = docs_dir / filename
        file.save(file_path)
        doc_paths.append(file_path)

    with open(case_dir / 'persona_definition.json', 'w') as f:
        f.write(persona_str)

    with open(case_dir / 'job_to_be_done.txt', 'w') as f:
        f.write(job_to_be_done)

    # --- Run your Round 1B logic ---
    # Note: You might need to adapt your Round 1B script to be callable like this
    # and to return the data instead of just writing to a file.
    # For now, we assume it writes to a known location.
    output_dir = Path('../output') # Assuming your script outputs here
    output_dir.mkdir(exist_ok=True)
    main_round1b.process_single_test_case(case_dir, output_dir)

    # --- Read the result and return it ---
    result_file = output_dir / "temp_case_output.json"
    if result_file.exists():
        with open(result_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return jsonify(data)
    else:
        return jsonify({"error": "Processing failed, output not found."}), 500

@app.route('/files/<filename>')
def get_file(filename):
    """Endpoint to serve the uploaded PDF files to the frontend viewer."""
    return send_from_directory(app.config['UPLOAD_FOLDER'] / "temp_case" / "documents", filename)

@app.route('/find_similar', methods=['POST'])
def find_similar():
    data = request.get_json()
    query_text = data.get('text')
    case_name = "temp_case" # We are using a fixed name from the /process endpoint

    output_dir = Path('../output')
    sections_data_path = output_dir / f"{case_name}_sections_data.pkl"
    embeddings_path = output_dir / f"{case_name}_embeddings.npy"

    if not main_round1b.semantic_model or not sections_data_path.exists() or not embeddings_path.exists():
        return jsonify({"error": "Model or data not available for similarity search."}), 500

    # Load pre-computed data
    all_embeddings = np.load(embeddings_path)
    with open(sections_data_path, "rb") as f_in:
        all_sections = pickle.load(f_in)
    
    # Compute similarity
    query_embedding = main_round1b.semantic_model.encode(query_text, convert_to_tensor=True)
    cos_scores = util.pytorch_cos_sim(query_embedding, all_embeddings)[0]
    
    # Get top 5 most similar sections
    top_results = np.argsort(-cos_scores)[:5]

    similar_sections = []
    for idx in top_results:
        # Don't include the query section itself
        if all_sections[idx]["section_text_raw"] != query_text:
            similar_sections.append({
                "document": all_sections[idx]["document"],
                "page_number": all_sections[idx]["page_number"],
                "section_title": all_sections[idx]["section_title"],
                "score": cos_scores[idx].item()
            })

    return jsonify(similar_sections)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)