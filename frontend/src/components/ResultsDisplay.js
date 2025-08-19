import React from 'react';

const ResultsDisplay = ({ results, activeSection, onSectionSelect }) => {
    return (
        <div className="panel">
            <h3 className="panel-header">Ranked Sections</h3>
            <div className="panel-content results-list">
                {!results ? (
                    <div className="empty-state">
                        <div className="empty-state-icon">📄</div>
                        <h3>Ready for Analysis</h3>
                        <p>Your ranked document sections will appear here once you submit.</p>
                    </div>
                ) : (
                    results.extracted_sections.map((section, index) => (
                        <div
                            key={index}
                            className={`section-item ${activeSection && activeSection.section_title === section.section_title && activeSection.document === section.document ? 'active' : ''}`}
                            onClick={() => onSectionSelect(section)}
                        >
                            <h4>{section.importance_rank}. {section.section_title}</h4>
                            <p>Source: {section.document} (Page: {section.page_number + 1})</p>
                        </div>
                    ))
                )}
            </div>
        </div>
    );
};

export default ResultsDisplay;