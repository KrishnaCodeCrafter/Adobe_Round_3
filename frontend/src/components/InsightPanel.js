import React from 'react';

const InsightPanel = ({ section, similarResults, isFindingSimilar }) => {
    return (
        <div className="panel">
            <h3 className="panel-header">Insights</h3>
            <div className="panel-content">
                {!section ? (
                    <div className="empty-state">
                        <div className="empty-state-icon">💡</div>
                        <h3>Insights Appear Here</h3>
                        <p>Select a ranked section to see a summary and keywords.</p>
                    </div>
                ) : (
                    <>
                        <div className="insight-block">
                            <h4>Summary for "{section.section_title}"</h4>
                            <p>{section.refined_text || "No summary available."}</p>
                        </div>

                        <div className="insight-block">
                            <h4>Keywords</h4>
                            {section.keywords && section.keywords.length > 0 ? (
                                <div className="keywords-container">
                                    {section.keywords.map((kw, i) => <span key={i} className="keyword-tag">{kw}</span>)}
                                </div>
                            ) : <p>No keywords extracted.</p>}
                        </div>

                        {/* The "Discover" block has been removed from here */}

                        {/* This part for displaying results is kept in case you want to trigger it from somewhere else in the future */}
                        {similarResults && (
                            <div className="insight-block">
                                <h4>Related Content</h4>
                                {similarResults.length > 0 ? (
                                    similarResults.map((res, i) => (
                                        <div key={i} className="similar-item">
                                            <h5>{res.section_title}</h5>
                                            <p>Source: {res.document} (Page: {res.page_number})</p>
                                        </div>
                                    ))
                                ) : <p>No other similar sections found.</p>}
                            </div>
                        )}
                    </>
                )}
            </div>
        </div>
    );
};

export default InsightPanel;