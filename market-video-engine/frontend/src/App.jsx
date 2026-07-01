import React, { useState } from 'react';
import './styles.css';

const API_BASE = 'http://127.0.0.1:8004';

export default function App() {
  const [customTickers, setCustomTickers] = useState('');
  const [isGenerating, setIsGenerating] = useState(false);
  const [videoUrl, setVideoUrl] = useState(null);
  const [error, setError] = useState(null);

  const handleGenerate = async () => {
    setIsGenerating(true);
    setError(null);
    setVideoUrl(null);

    try {
      const tickersArray = customTickers
        .split(',')
        .map(t => t.trim())
        .filter(t => t.length > 0);

      const response = await fetch(`${API_BASE}/video/generate`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          video_type: 'full_overview',
          custom_tickers: tickersArray
        }),
      });

      if (!response.ok) {
        throw new Error(`Server returned ${response.status}`);
      }

      const data = await response.json();
      
      if (data.video_url) {
        setVideoUrl(`${API_BASE}${data.video_url}`);
      } else {
        throw new Error("No video URL returned from server.");
      }
    } catch (err) {
      setError(err.message || 'An error occurred during generation.');
    } finally {
      setIsGenerating(false);
    }
  };

  return (
    <div className="dashboard">
      
      {/* Top Header */}
      <header className="top-header">
        <div className="brand">
          <i className="fa-solid fa-film"></i>
          AI MARKET VIDEO ENGINE
        </div>
      </header>

      <div className="main-layout">
        {/* Sidebar Control Panel */}
        <aside className="sidebar">
          <div className="sidebar-header">
            Render Controls
          </div>
          <div className="sidebar-content">
            
            <label className="input-label">Custom Tickers (Optional)</label>
            <input 
              type="text" 
              className="input-field" 
              placeholder="e.g. RELIANCE, TCS"
              value={customTickers}
              onChange={(e) => setCustomTickers(e.target.value)}
              disabled={isGenerating}
            />

            <button 
              className="generate-btn" 
              onClick={handleGenerate} 
              disabled={isGenerating}
            >
              {isGenerating ? (
                <>
                  <i className="fa-solid fa-spinner fa-spin"></i> GENERATING...
                </>
              ) : (
                <>
                  <i className="fa-solid fa-play"></i> GENERATE VIDEO
                </>
              )}
            </button>

            {error && (
              <div className="error-msg">
                <i className="fa-solid fa-circle-exclamation"></i> {error}
              </div>
            )}
          </div>
        </aside>

        {/* Main Stage */}
        <main className="main-stage">
          <div className="video-container">
            
            {isGenerating && (
              <div className="loading-state">
                <div className="spinner"></div>
                <div>RENDERING VIDEO...</div>
              </div>
            )}

            {!isGenerating && !videoUrl && (
              <div className="placeholder-content">
                <i className="fa-regular fa-file-video"></i>
                <div style={{ fontSize: '16px', fontWeight: '500', marginBottom: '4px', fontFamily: 'var(--sans)' }}>No Video Loaded</div>
                <div>Enter tickers and click Generate</div>
              </div>
            )}

            {!isGenerating && videoUrl && (
              <video 
                className="video-player" 
                controls 
                autoPlay
                src={videoUrl}
              >
                Your browser does not support the video tag.
              </video>
            )}
            
          </div>

          {videoUrl && !isGenerating && (
            <div className="download-bar">
              <a href={videoUrl} download className="download-btn">
                <i className="fa-solid fa-download"></i> Download MP4
              </a>
            </div>
          )}
        </main>
      </div>

    </div>
  );
}
