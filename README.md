# Persona-Driven Document Intelligence Engine

### Adobe India Hackathon 2025 - "Connecting the Dots"

This project is an intelligent web application designed to analyze a collection of PDF documents and extract the most relevant information based on a user's specific persona and goals. It transforms passive reading into an active, insightful, and personalized research experience.

*The application interface in light mode, showcasing the three-panel layout.*

## Features

* **Persona-Driven Analysis**: Simply define a user persona (e.g., "Travel Planner") and a "job-to-be-done" (e.g., "find family-friendly activities"). The engine will read through all documents and rank sections based on their relevance to your specific needs.
* **Hybrid Relevance Scoring**: Combines traditional keyword matching with advanced semantic similarity (using `sentence-transformers`) to understand the context and meaning behind the text, ensuring highly accurate results.
* **Interactive PDF Viewer**: Click on any ranked section, and the integrated Adobe PDF viewer instantly navigates to the corresponding page, seamlessly connecting insights to their source.
* **Automated Insight Generation**: For each relevant section, the app automatically generates:
    * **Concise Summaries**: A quick preview of the section's content.
    * **Extracted Keywords**: At-a-glance tags of the most important topics.
* **Layout-Aware Sectioning**: A smart algorithm that detects visual gaps in the document layout to accurately determine where sections begin and end, preventing unrelated content from being grouped together.
* **Light & Dark Mode**: A sleek, modern interface with a user-toggleable dark mode for comfortable reading in any environment.

*The application interface in dark mode.*

## Architecture

The application is built with a modern full-stack architecture, separating the frontend and backend for scalability and maintainability.

* **Frontend**: A responsive web application built with **React.js**, providing a dynamic and interactive user experience.
* **Backend**: A powerful API built with **Python** and the **Flask** web framework. It handles all the heavy lifting, including PDF parsing, text analysis, and relevance scoring.
* **PDF Rendering**: Powered by the **Adobe PDF Embed API** for a robust and feature-rich document viewing experience.
* **Containerization**: The entire application is containerized using **Docker**, ensuring a consistent and easy-to-deploy environment.

## Getting Started

You can run this project either locally for development or using the provided Docker container for a production-like setup.

### Prerequisites

* Node.js and npm
* Python 3.7+ and pip
* Docker Desktop (for containerized setup)
* An **Adobe PDF Embed API Key**. You can get one for free from the [Adobe website](https://www.adobe.io/document-services/apis/pdf-embed/).

### 1. Local Development Setup

**A. Start the Backend Server:**

1.  Navigate to the `backend` directory:
    ```bash
    cd backend
    ```
2.  (Recommended) Create and activate a virtual environment:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On macOS/Linux
    venv\Scripts\activate    # On Windows
    ```
3.  Install the required Python packages:
    ```bash
    pip install -r requirements.txt
    ```
4.  Run the Flask API server:
    ```bash
    python api.py
    ```
    The backend will now be running on `http://localhost:5000`.

**B. Start the Frontend App:**

1.  Open a **new terminal** and navigate to the `frontend` directory:
    ```bash
    cd frontend
    ```
2.  Install the required Node.js packages:
    ```bash
    npm install
    ```
3.  **Important:** Add your Adobe API key to `frontend/src/components/DocumentViewer.js`.
4.  Run the React development server:
    ```bash
    npm start
    ```
    Your browser will automatically open to `http://localhost:3000`.

### 2. Docker Setup

1.  **Important:** Add your Adobe API key to `frontend/src/components/DocumentViewer.js`.
2.  From the project's root directory, build the Docker image:
    ```bash
    docker build -t adobe-hackathon-solution .
    ```
3.  Run the Docker container:
    ```bash
    docker run -p 3000:80 -p 5000:5000 -v $(pwd)/uploads:/app/uploads -v $(pwd)/output:/app/output adobe-hackathon-solution
    ```
4.  Access the application in your browser at `http://localhost:3000`.

## Screenshot
<img width="1913" height="863" alt="image" src="https://github.com/user-attachments/assets/0b285953-abb5-44c4-9eda-bab624f299df" />

## How It Works

### Persona-Driven Ranking

The core of the application is its ability to understand user intent. When you provide a persona and a job-to-be-done, the backend constructs a rich query. This query is then compared against every section of every document using a hybrid scoring model:

1.  **Keyword Score**: A baseline score is given for direct matches of keywords from the persona's "focus areas."
2.  **Semantic Score**: Using the `all-MiniLM-L6-v2` sentence transformer model, the engine calculates the contextual similarity between your query and the document text. This allows it to find relevant sections even if they don't use the exact same keywords.

### Challenge & Solution: Layout-Aware Sectioning

A significant challenge in PDF analysis is accurately determining where a section ends. Our initial implementation was too "greedy," sometimes grouping unrelated text into the previous section.

**Solution:** We implemented a **"Gap Detection" heuristic**. The engine now analyzes the physical layout of the PDF, measures the vertical whitespace between text blocks, and uses large gaps as implicit boundaries to intelligently segment sections. This dramatically improved the accuracy of our analysis.

*The Insight Panel provides a concise summary and extracted keywords for the selected section.*
