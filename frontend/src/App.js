import React, { useState, useRef, useEffect } from 'react';
import axios from 'axios';
import DocumentViewer from './components/DocumentViewer';
import ResultsDisplay from './components/ResultsDisplay';
import InsightPanel from './components/InsightPanel';
import './App.css';

function App() {
    // State for dark mode
    const [isDarkMode, setIsDarkMode] = useState(false);

    // Existing states for application logic
    const [persona, setPersona] = useState(JSON.stringify({ "role": "PhD Researcher", "focus_areas": "methodologies, datasets" }, null, 2));
    const [job, setJob] = useState("Prepare a literature review.");
    const [documents, setDocuments] = useState(null);
    const [results, setResults] = useState(null);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState('');
    const [activeSection, setActiveSection] = useState(null);

    // States for the "Find Similar" feature
    const [similarResults, setSimilarResults] = useState(null);
    const [isFindingSimilar, setIsFindingSimilar] = useState(false);

    const viewerRef = useRef(null);

    // Effect to toggle the 'dark-mode' class on the body
    useEffect(() => {
        document.body.classList.toggle('dark-mode', isDarkMode);
    }, [isDarkMode]);

    const handleSubmit = async (e) => {
        e.preventDefault();
        setIsLoading(true);
        setError('');
        setResults(null);
        setActiveSection(null);
        setSimilarResults(null);

        const formData = new FormData();
        formData.append('persona', persona);
        formData.append('job_to_be_done', job);
        for (let i = 0; i < documents.length; i++) {
            formData.append('documents', documents[i]);
        }

        try {
            const response = await axios.post('http://localhost:5000/process', formData, {
                headers: { 'Content-Type': 'multipart/form-data' }
            });
            setResults(response.data);
            if (response.data.extracted_sections && response.data.extracted_sections.length > 0) {
                handleSectionSelect(response.data.extracted_sections[0]);
            }
        } catch (err) {
            setError('Failed to process documents. Please check the backend server and your inputs.');
            console.error(err);
        } finally {
            setIsLoading(false);
        }
    };

    const handleSectionSelect = (section) => {
        setActiveSection(section);
        setSimilarResults(null); // Clear previous similar results
        if (viewerRef.current) {
            viewerRef.current.gotoPage(section.page_number + 1);
        }
    };

    // --- THIS FUNCTION MAKES THE BUTTON WORK ---
    const handleFindSimilar = async (section) => {
        setIsFindingSimilar(true);
        setSimilarResults(null);
        try {
            const response = await axios.post('http://localhost:5000/find_similar', {
                text: section.section_text_raw
            });
            setSimilarResults(response.data);
        } catch (err) {
            console.error("Failed to find similar sections", err);
        } finally {
            setIsFindingSimilar(false);
        }
    };

    const getActiveDoc = () => {
        return activeSection ? activeSection.document : null;
    }

    return (
        <div className="App">
            <header className="header">
                <h1>Persona-Driven Document Intelligence</h1>
                <div className="toggle-container">
                    <span>💡</span>
                    <label className="toggle-switch">
                        <input
                            type="checkbox"
                            checked={isDarkMode}
                            onChange={() => setIsDarkMode(!isDarkMode)}
                        />
                        <span className="slider"></span>
                    </label>
                    <span>🌙</span>
                </div>
            </header>
            <div className="main-container">
                {isLoading && (
                    <div className="loading-overlay">
                        <div className="spinner"></div>
                    </div>
                )}
                <div className="form-container">
                    <h2>1. Define Your Context</h2>
                    <form onSubmit={handleSubmit}>
                        <div className="form-group">
                            <label>Persona (JSON or Plain Text)</label>
                            <textarea rows="5" value={persona} onChange={(e) => setPersona(e.target.value)} />
                        </div>
                        <div className="form-group">
                            <label>Job to be Done</label>
                            <textarea rows="3" value={job} onChange={(e) => setJob(e.target.value)} />
                        </div>
                        <div className="form-group">
                            <label>Upload PDF Documents</label>
                            <input type="file" multiple required onChange={(e) => setDocuments(e.target.files)} />
                        </div>
                        <button type="submit" disabled={isLoading}>{isLoading ? 'Processing...' : 'Analyze Documents'}</button>
                        {error && <div className="error-message">{error}</div>}
                    </form>
                </div>
                <main className="content-area">
                    <div className="content-area-grid">
                        <ResultsDisplay
                            results={results}
                            activeSection={activeSection}
                            onSectionSelect={handleSectionSelect}
                        />
                        <InsightPanel
                            section={activeSection}
                            onFindSimilar={handleFindSimilar}
                            similarResults={similarResults}
                            isFindingSimilar={isFindingSimilar}
                        />
                        <DocumentViewer activeDoc={getActiveDoc()} ref={viewerRef} />
                    </div>
                </main>
            </div>
        </div>
    );
}

export default App;