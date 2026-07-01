import React, { useState } from 'react';
import './styles.css';

const API_BASE = 'http://localhost:8004';

export default function App() {
  const [videoType, setVideoType] = useState('market_wrap');
  const [customTickers, setCustomTickers] = useState('');
  const [isGenerating, setIsGenerating] = useState(false);
  const [videoUrl, setVideoUrl] = useState(null);
  const [error, setError] = useState(null);

  const videoOptions = [
    { id: 'market_wrap', label: 'Market Wrap', icon: 'fa-earth-americas' },
    { id: 'sector_rotation', label: 'Sector Rotation', icon: 'fa-chart-pie' },
    { id: 'race_chart', label: 'Race Chart', icon: 'fa-flag-checkered' },
    { id: 'ipo_tracker', label: 'IPO Tracker', icon: 'fa-rocket' },
    { id: 'full_overview', label: 'Full Overview', icon: 'fa-globe' }
  ];

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
          video_type: videoType,
          custom_tickers: tickersArray
        }),
      });

      if (!response.ok) {
        throw new Error(`Server returned ${response.status}`);
      }

      const data = await response.json();
      
      // Backend returns video_url like "/video/download/mve_2026...mp4"
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
      
      {/* Sidebar Control Panel */}
      <aside className="sidebar">
        <div className="brand">
          <i className="fa-solid fa-video"></i>
          Market Video Engine
        </div>

        <div className="section-title">Video Format</div>
        <div className="type-selector">
          {videoOptions.map(opt => (
            <button 
              key={opt.id}
              className={`type-pill ${videoType === opt.id ? 'active' : ''}`}
              onClick={() => setVideoType(opt.id)}
              disabled={isGenerating}
            >
              <i className={`fa-solid ${opt.icon}`}></i>
              {opt.label}
            </button>
          ))}
        </div>

        <div className="section-title">Custom Tickers (Optional)</div>
        <div className="input-group">
          <input 
            type="text" 
            className="input-field" 
            placeholder="e.g. RELIANCE, TCS, INFY"
            value={customTickers}
            onChange={(e) => setCustomTickers(e.target.value)}
            disabled={isGenerating}
          />
        </div>

        <button 
          className="generate-btn" 
          onClick={handleGenerate} 
          disabled={isGenerating}
        >
          {isGenerating ? (
            <>
              <i className="fa-solid fa-spinner fa-spin"></i> Generating...
            </>
          ) : (
            <>
              <i className="fa-solid fa-wand-magic-sparkles"></i> Generate Video
            </>
          )}
        </button>

        {error && (
          <div style={{ marginTop: '20px', color: '#ef4444', fontSize: '13px', textAlign: 'center' }}>
            <i className="fa-solid fa-triangle-exclamation"></i> {error}
          </div>
        )}
      </aside>

      {/* Main Stage */}
      <main className="main-stage">
        <div className="video-container">
          
          {isGenerating && (
            <div className="loading-state">
              <div className="spinner"></div>
              <div className="status-text">AI is rendering your video...</div>
            </div>
          )}

          {!isGenerating && !videoUrl && (
            <div className="placeholder-content">
              <i className="fa-regular fa-circle-play"></i>
              <h2>No Video Generated</h2>
              <p style={{ marginTop: '10px', fontSize: '14px', color: 'var(--text-muted)' }}>
                Select your format and hit Generate to start.
              </p>
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
              <i className="fa-solid fa-download"></i> Download .mp4
            </a>
          </div>
        )}
      </main>

    </div>
  );
}
