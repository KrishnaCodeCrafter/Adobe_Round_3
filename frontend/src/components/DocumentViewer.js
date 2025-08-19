import React, { useEffect, useRef, forwardRef, useImperativeHandle } from 'react';

// IMPORTANT: Replace with your actual Adobe PDF Embed API Client ID
const ADOBE_CLIENT_ID = "YOUR_ADOBE_CLIENT_ID_HERE";

const DocumentViewer = forwardRef(({ activeDoc }, ref) => {
    const viewerRef = useRef(null);

    useEffect(() => {
        if (activeDoc && viewerRef.current) {
            const adobeDCView = new window.AdobeDC.View({
                clientId: ADOBE_CLIENT_ID,
                divId: viewerRef.current.id,
            });

            adobeDCView.previewFile({
                content: { location: { url: `http://localhost:5000/files/${activeDoc}` } },
                metaData: { fileName: activeDoc }
            }, { 
                embedMode: "SIZED_CONTAINER",
                showLeftHandPanel: false,
                showAnnotationTools: false,
             });
        }
    }, [activeDoc]);

    useImperativeHandle(ref, () => ({
        gotoPage: (page) => {
            // The Adobe Viewer SDK is complex; this navigation is a best-effort.
            // A more robust implementation might require digging into the SDK's event listeners.
            console.log(`Requesting navigation to page: ${page}`);
        }
    }));

    // The empty state when no document is selected
    if (!activeDoc) {
        return (
            <div className="panel">
                <div className="empty-state">
                    <div className="empty-state-icon">📖</div>
                    <h3>Document Viewer</h3>
                    <p>Select a section from the ranked list to view its document here.</p>
                </div>
            </div>
        );
    }

    return (
        <div className="panel" style={{ padding: 0 }}>
            <div id="adobe-dc-view" ref={viewerRef} style={{ height: "100%" }}></div>
        </div>
    );
});

export default DocumentViewer;
