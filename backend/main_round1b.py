import os
import json
import re
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime
import numpy as np
import pickle
import fitz

from pdf_parser import extract_outline_from_pdf, extract_title_from_pdf

try:
    from sentence_transformers import SentenceTransformer, util

    MODEL_NAME = 'all-MiniLM-L6-v2'
    # NOTE: Path updated to work with local execution and Docker
    MODEL_PATH_IN_CONTAINER = Path("models") / MODEL_NAME

    semantic_model = None

    if MODEL_PATH_IN_CONTAINER.exists():
        semantic_model = SentenceTransformer(str(MODEL_PATH_IN_CONTAINER))
        print(f"Loaded SentenceTransformer model from {MODEL_PATH_IN_CONTAINER}")
    else:
        print(f"Warning: SentenceTransformer model not found at {MODEL_PATH_IN_CONTAINER}.")
        print(f"Attempting to download '{MODEL_NAME}'. This will fail if no internet during runtime.")
        try:
            semantic_model = SentenceTransformer(MODEL_NAME)
            # Ensure the models directory exists before saving
            MODEL_PATH_IN_CONTAINER.parent.mkdir(parents=True, exist_ok=True)
            semantic_model.save(str(MODEL_PATH_IN_CONTAINER))
            print(f"Downloaded and loaded SentenceTransformer model '{MODEL_NAME}'.")
        except Exception as dl_e:
            print(f"Error during model download: {dl_e}. Semantic similarity will be disabled.")

except ImportError:
    print("Error: 'sentence-transformers' not found. Please install it (`pip install sentence-transformers`).")
    print("Falling back to keyword-only relevance scoring.")
    semantic_model = None
except Exception as e:
    print(f"Generic error during SentenceTransformer setup: {e}. Falling back to keyword-only relevance scoring.")
    semantic_model = None

# --- NEW: Keyword Extraction Function ---
# A simple set of common English stop words
STOP_WORDS = set("""
a about above after again against all am an and any are aren't as at be because
been before being below between both but by can't cannot could couldn't did didn't
do does doesn't doing don't down during each few for from further had hadn't has
hasn't have haven't having he he'd he'll he's her here here's hers herself him
himself his how how's i i'd i'll i'm i've if in into is isn't it it's its itself
let's me more most mustn't my myself no nor not of off on once only or other
ought our ours ourselves out over own same shan't she she'd she'll she's should
shouldn't so some such than that that's the their theirs them themselves then there
there's these they they'd they'll they're they've this those through to too under
until up very was wasn't we we'd we'll we're we've were weren't what what's when
when's where where's which while who who's whom why why's with won't would
wouldn't you you'd you'll you're you've your yours yourself yourselves
""".split())

def extract_keywords(text: str, num_keywords=5) -> List[str]:
    """A simple keyword extraction function."""
    # Find words that are 3 to 15 characters long
    words = re.findall(r'\b\w{3,15}\b', text.lower())
    # Filter out stop words and non-alphabetic words
    words = [word for word in words if word.isalpha() and word not in STOP_WORDS]
    
    # Get frequency distribution using collections.Counter
    from collections import Counter
    word_freq = Counter(words)
    
    # Return the most common keywords
    return [word for word, freq in word_freq.most_common(num_keywords)]

# ---------------------- Document Sectioning ----------------------

def extract_document_sections(pdf_path: Path) -> List[Dict]:
    """
    Extracts text content from a PDF and associates it with the nearest preceding heading.
    [MODIFIED] Now includes gap detection to prevent overly greedy sectioning.
    """
    doc_sections = []
    outline = extract_outline_from_pdf(pdf_path)
    doc = fitz.open(pdf_path)
    
    all_content_items = []
    avg_line_height = 12  # A default line height

    for page_num, page in enumerate(doc):
        text_dict = page.get_text("dict")
        line_heights = []

        # First, gather all text blocks and calculate average line height for the page
        blocks = [b for b in text_dict.get("blocks", []) if b["type"] == 0]
        for block in blocks:
            for line in block.get("lines", []):
                line_heights.append(line['bbox'][3] - line['bbox'][1])
        
        if line_heights:
            avg_line_height = np.mean(line_heights)

        # Add text blocks to our list of items
        for block in blocks:
            block_text = "".join(span["text"] for line in block.get("lines", []) for span in line.get("spans", []))
            if block_text.strip():
                all_content_items.append({
                    "type": "text", "text": block_text.strip(), "page": page_num + 1,
                    "bbox": block["bbox"]
                })

    # Add heading markers to the list of items
    for h in outline:
        all_content_items.append({
            "type": "heading_marker", "text": h["text"], "level": h["level"],
            "page": h["page"], "bbox": (0,0,0,0) # Placeholder bbox
        })

    # Sort all items by page and then by vertical position
    all_content_items.sort(key=lambda x: (x["page"], x["bbox"][1]))

    # --- Sectioning Logic ---
    current_section_title = "Document Start"
    current_section_level = "H0"
    current_section_text_parts = []
    current_section_start_page = 1
    
    # Define a threshold for what constitutes a large gap
    # A gap of 2.5 times the average line height is a robust choice
    gap_threshold = avg_line_height * 2.5

    for i, item in enumerate(all_content_items):
        is_section_break = False

        # Condition 1: The item is a heading
        if item.get("type") == "heading_marker":
            is_section_break = True
        
        # Condition 2: Detect a large vertical gap between text blocks
        if i > 0 and item.get("type") == "text":
            prev_item = all_content_items[i-1]
            if prev_item.get("type") == "text" and prev_item["page"] == item["page"]:
                prev_bottom = prev_item["bbox"][3]
                current_top = item["bbox"][1]
                if (current_top - prev_bottom) > gap_threshold:
                    is_section_break = True

        if is_section_break and current_section_text_parts:
            # End the current section and save it
            doc_sections.append({
                "document": pdf_path.name, "page_number": current_section_start_page,
                "section_title": current_section_title,
                "section_text": "\n".join(current_section_text_parts),
                "level": current_section_level
            })
            current_section_text_parts = []

        # Start a new section if it was a heading break
        if item.get("type") == "heading_marker":
            current_section_title = item["text"]
            current_section_level = item["level"]
            current_section_start_page = item["page"]
        
        # Always add the current item's text if it's a text block
        if item.get("type") == "text":
             # If a gap forced a break, the title should be the first line of the new text
            if is_section_break and item.get("type") != "heading_marker":
                current_section_title = "Content" # Assign a generic title
                current_section_start_page = item["page"]
            current_section_text_parts.append(item["text"])

    # Add the last section
    if current_section_text_parts:
        doc_sections.append({
            "document": pdf_path.name, "page_number": current_section_start_page,
            "section_title": current_section_title,
            "section_text": "\n".join(current_section_text_parts),
            "level": current_section_level
        })

    doc.close()
    return doc_sections

# ---------------------- Persona & Job-to-be-Done Processing ----------------------
def load_persona_and_job(input_case_dir: Path) -> Dict[str, Any]:
    # This function remains unchanged
    persona = {}
    job_to_be_done = ""
    persona_path_json = input_case_dir / "persona_definition.json"
    persona_path_txt = input_case_dir / "persona_definition.txt"
    if persona_path_json.exists():
        with open(persona_path_json, 'r', encoding='utf-8') as f:
            persona = json.load(f)
        print(f"  Loaded persona from {persona_path_json.name}")
    elif persona_path_txt.exists():
        with open(persona_path_txt, 'r', encoding='utf-8') as f:
            persona_desc = f.read().strip()
            persona = {"description": persona_desc, "role": "Unspecified Role", "focus_areas": ""}
        print(f"  Loaded persona from {persona_path_txt.name} (as text description)")
    else:
        raise FileNotFoundError(f"Neither persona_definition.json nor persona_definition.txt found in {input_case_dir}")
    job_path = input_case_dir / "job_to_be_done.txt"
    if job_path.exists():
        with open(job_path, 'r', encoding='utf-8') as f:
            job_to_be_done = f.read().strip()
        print(f"  Loaded job-to-be-done from {job_path.name}")
    else:
        raise FileNotFoundError(f"job_to_be_done.txt not found in {input_case_dir}")
    return {"persona": persona, "job_to_be_done": job_to_be_done}

# ---------------------- Relevance Scoring ----------------------
def calculate_relevance(text: str, persona_info: Dict, job_text: str, nlp_model: Any = None) -> float:
    # This function remains unchanged
    score = 0.0
    all_keywords = set()
    job_keywords_raw = re.findall(r'\b\w+\b', job_text.lower())
    all_keywords.update(job_keywords_raw)
    if persona_info.get("focus_areas"):
        persona_focus_keywords_raw = re.findall(r'\b\w+\b', persona_info["focus_areas"].lower())
        all_keywords.update(persona_focus_keywords_raw)
    text_tokens_lower = re.findall(r'\b\w+\b', text.lower())
    for kw in all_keywords:
        if kw in text_tokens_lower:
            score += 2.0
    if nlp_model:
        try:
            query_parts = [job_text]
            if persona_info.get("description"):
                query_parts.append(f"Persona description: {persona_info['description']}")
            if persona_info.get("role"):
                query_parts.append(f"Role: {persona_info['role']}")
            if persona_info.get("focus_areas"):
                query_parts.append(f"Focus areas: {persona_info['focus_areas']}")
            combined_query = ". ".join(query_parts)
            query_embedding = nlp_model.encode(combined_query, convert_to_tensor=True)
            text_embedding = nlp_model.encode(text, convert_to_tensor=True)
            cosine_score = util.pytorch_cos_sim(query_embedding, text_embedding).item()
            normalized_cosine = (cosine_score + 1) / 2
            score += normalized_cosine * 10.0
        except Exception as e:
            print(f"Semantic similarity failed for a section. Error: {e}")
            pass 
    if len(text.split()) < 10 and any(kw in text.lower() for kw in all_keywords):
        score += 1.0
    return score

# ---------------------- Main Round 1B Processor ----------------------
def process_single_test_case(input_case_dir: Path, output_dir: Path):
    case_name = input_case_dir.name
    print(f"\n--- Processing Test Case: {case_name} ---")

    try:
        persona_job_data = load_persona_and_job(input_case_dir)
        persona_info = persona_job_data["persona"]
        job_to_be_done = persona_job_data["job_to_be_done"]
    except FileNotFoundError as e:
        print(f"  Skipping test case {case_name} due to missing input file: {e}")
        return None
    except Exception as e:
        print(f"  Skipping test case {case_name} due to error loading persona/job data: {e}")
        return None

    documents_dir = input_case_dir / "documents"
    pdf_files = list(documents_dir.glob("*.pdf"))
    if not pdf_files:
        print(f"  No PDF files found in {documents_dir}. Skipping test case {case_name}.")
        return None

    all_extracted_sections = []
    input_document_names = [f.name for f in pdf_files]

    print("  Starting section extraction from documents...")
    for pdf_file in pdf_files:
        print(f"    Processing document: {pdf_file.name}")
        sections = extract_document_sections(pdf_file)
        all_extracted_sections.extend(sections)
    print(f"  Extracted {len(all_extracted_sections)} potential sections for {case_name}.")

    # --- MODIFIED: Score, Rank, and Augment Sections ---
    print("  Calculating relevance, extracting keywords, and ranking sections...")
    ranked_sections = []
    all_embeddings = [] # To store embeddings for similarity search

    if not all_extracted_sections:
        print(f"  No sections extracted to rank for {case_name}.")
    
    for section in all_extracted_sections:
        relevance_score = calculate_relevance(
            section["section_text"], persona_info, job_to_be_done, nlp_model=semantic_model
        )
        
        # NEW: Generate and store embedding for each section
        if semantic_model:
            embedding = semantic_model.encode(section["section_text"], convert_to_tensor=False)
            all_embeddings.append(embedding)

        # NEW: Extract keywords
        keywords = extract_keywords(section["section_text"])

        ranked_sections.append({
            "document": section["document"],
            "page_number": section["page_number"],
            "section_title": section["section_title"],
            "importance_rank": relevance_score, 
            "section_text_raw": section["section_text"],
            "keywords": keywords  # Add keywords to the data
        })

    # NEW: Save the embeddings and the section data for the new API
    if semantic_model and all_embeddings:
        # Save section data for use in the /find_similar endpoint
        with open(output_dir / f"{case_name}_sections_data.pkl", "wb") as f_out:
            pickle.dump(ranked_sections, f_out)
        # Save embeddings as a numpy array
        np.save(output_dir / f"{case_name}_embeddings.npy", np.array(all_embeddings))

    ranked_sections.sort(key=lambda x: x["importance_rank"], reverse=True)

    # --- MODIFIED: Streamlined final output generation ---
    final_extracted_sections_output = []
    for i, section in enumerate(ranked_sections):
        full_text = section["section_text_raw"]
        sentences = re.split(r'(?<=[.!?])\s+', full_text)
        refined_text = " ".join(sentences[:min(3, len(sentences))])

        final_extracted_sections_output.append({
            "document": section["document"],
            "page_number": section["page_number"],
            "section_title": section["section_title"],
            "importance_rank": i + 1,
            "section_text_raw": section["section_text_raw"],
            "refined_text": refined_text,
            "keywords": section.get("keywords", [])
        })

    output_data = {
        "metadata": {
            "input_documents": input_document_names,
            "persona": persona_info,
            "job_to_be_done": job_to_be_done,
            "processing_timestamp": datetime.now().isoformat()
        },
        "extracted_sections": final_extracted_sections_output
        # The separate 'sub_section_analysis' is now integrated above
    }

    output_file_name = f"{case_name}_output.json"
    output_file_path = output_dir / output_file_name
    try:
        with open(output_file_path, "w", encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        print(f"  Test Case '{case_name}' complete. Output saved to {output_file_path.name}")
        return output_data # Return data for direct use in the API
    except Exception as e:
        print(f"  Error saving output JSON for {case_name} to {output_file_path.name}: {e}")
        return None

# ---------------------- Main Entry Point ----------------------
if __name__ == "__main__":
    print("--- Starting Round 1B: Persona-Driven Document Intelligence (Multiple Test Cases) ---")
    
    # Use relative paths for better portability
    base_input_root = Path("input")
    base_output_root = Path("output")
    base_output_root.mkdir(parents=True, exist_ok=True)
    Path("models").mkdir(parents=True, exist_ok=True) 

    test_case_dirs = []
    if base_input_root.exists():
        for entry in base_input_root.iterdir():
            if entry.is_dir() and (entry / "documents").is_dir():
                test_case_dirs.append(entry)
    
    if not test_case_dirs:
        print(f"No test case directories found in {base_input_root}. Please structure inputs as: input/test_case_name/documents/...")
    else:
        for tc_dir in test_case_dirs:
            process_single_test_case(tc_dir, base_output_root)

    print("--- Finished processing all available test cases ---")