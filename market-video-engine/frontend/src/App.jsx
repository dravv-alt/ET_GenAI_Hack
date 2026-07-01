import React, { useState } from 'react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell, CartesianGrid } from 'recharts';
import { TrendingUp, TrendingDown, Activity, Info } from 'lucide-react';
import './styles.css';

const API_BASE = 'http://127.0.0.1:8004';

export default function App() {
  const [targetDate, setTargetDate] = useState(() => new Date().toISOString().split('T')[0]);
  const [isGenerating, setIsGenerating] = useState(false);
  const [loadingStep, setLoadingStep] = useState('');
  const [videoUrl, setVideoUrl] = useState(null);
  const [marketData, setMarketData] = useState(null);
  const [revealedData, setRevealedData] = useState({ nifty: false, sectors: false, movers: false });
  const [error, setError] = useState(null);

  const handleGenerate = async () => {
    setIsGenerating(true);
    setLoadingStep('FETCHING LIVE MARKET DATA...');
    setError(null);
    setVideoUrl(null);
    setMarketData(null);
    setRevealedData({ nifty: false, sectors: false, movers: false });

    try {
      // STEP 1: Fetch Market Data Sequentially
      const dataResponse = await fetch(`${API_BASE}/video/market-data`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          video_type: 'full_overview',
          date: targetDate
        }),
      });

      if (!dataResponse.ok) {
        throw new Error(`Data fetch failed: ${dataResponse.status}`);
      }
      
      const dataJson = await dataResponse.json();
      setMarketData(dataJson.snapshot);
      
      // STEP 2: Staggered reveal to keep user engaged while video generates
      setTimeout(() => {
        setRevealedData(prev => ({ ...prev, nifty: true }));
        setLoadingStep('SCANNING SECTOR ROTATION...');
      }, 500);

      setTimeout(() => {
        setRevealedData(prev => ({ ...prev, sectors: true }));
        setLoadingStep('IDENTIFYING TOP MOVERS...');
      }, 2500);

      setTimeout(() => {
        setRevealedData(prev => ({ ...prev, movers: true }));
        setLoadingStep('WRITING AI NARRATIVE SCRIPT & RENDERING VIDEO...');
      }, 4500);
      
      const videoResponse = await fetch(`${API_BASE}/video/generate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          video_type: 'full_overview',
          date: targetDate
        }),
      });

      if (!videoResponse.ok) {
        throw new Error(`Video generation failed: ${videoResponse.status}`);
      }

      const videoJson = await videoResponse.json();
      
      if (videoJson.video_url) {
        setVideoUrl(`${API_BASE}${videoJson.video_url}`);
      } else {
        throw new Error("No video URL returned from server.");
      }
    } catch (err) {
      setError(err.message || 'An error occurred during generation.');
    } finally {
      setIsGenerating(false);
      setLoadingStep('');
      // Reveal everything in case of quick finish or error
      setRevealedData({ nifty: true, sectors: true, movers: true });
    }
  };

  const renderDataPanel = () => {
    if (!marketData) return null;

    const { nifty, movers, sectors } = marketData;
    
    // Format data for Recharts
    const topGainers = movers?.gainers?.slice(0, 5) || [];
    const topLosers = movers?.losers?.slice(0, 5) || [];
    const allMovers = [...topGainers, ...topLosers].sort((a, b) => b.change_pct - a.change_pct);

    return (
      <div className="data-panel animate-in">
        <div className="data-header">
          <Info size={16} /> 
          <span>LIVE MARKET DATA CROSS-VERIFICATION</span>
        </div>
        
        <div className="data-grid">
          {/* Nifty 50 Table */}
          {revealedData.nifty ? (
            <div className="data-card animate-in">
              <h3>Nifty 50 Snapshot</h3>
              <table className="data-table">
                <tbody>
                  <tr><td>Open</td><td className="text-right">{nifty?.open?.toLocaleString()}</td></tr>
                  <tr><td>High</td><td className="text-right">{nifty?.high?.toLocaleString()}</td></tr>
                  <tr><td>Low</td><td className="text-right">{nifty?.low?.toLocaleString()}</td></tr>
                  <tr>
                    <td>Close</td>
                    <td className="text-right font-bold">{nifty?.close?.toLocaleString()}</td>
                  </tr>
                  <tr>
                    <td>Change</td>
                    <td className={`text-right font-bold ${nifty?.change_pct >= 0 ? 'text-green' : 'text-red'}`}>
                      {nifty?.change_abs > 0 ? '+' : ''}{nifty?.change_abs} ({nifty?.change_pct}%)
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          ) : <div className="data-card"><div className="placeholder-content"><div className="spinner" style={{width: 20, height: 20, borderColor: 'var(--text-muted)', borderTopColor: 'var(--blue)', margin: '0 auto', marginBottom: 10}}></div>Analyzing Nifty...</div></div>}

          {/* Sector Chart */}
          {revealedData.sectors ? (
            <div className="data-card animate-in">
              <h3>Sector Rotation (Day % Change)</h3>
              <div className="chart-wrapper">
                <ResponsiveContainer width="100%" height={200}>
                  <BarChart data={sectors} margin={{ top: 10, right: 10, left: -20, bottom: 25 }}>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="var(--border)" />
                    <XAxis dataKey="sector" tick={{fontSize: 10}} interval={0} angle={-45} textAnchor="end" height={50} />
                    <YAxis tick={{fontSize: 10}} />
                    <Tooltip cursor={{fill: 'var(--bg-hover)'}} contentStyle={{borderRadius: 2, border: '1px solid var(--border-dark)', fontSize: '12px'}} />
                    <Bar dataKey="change_pct" radius={[2, 2, 0, 0]}>
                      {sectors?.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.change_pct >= 0 ? 'var(--green)' : 'var(--red)'} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>
          ) : <div className="data-card"><div className="placeholder-content"><div className="spinner" style={{width: 20, height: 20, borderColor: 'var(--text-muted)', borderTopColor: 'var(--blue)', margin: '0 auto', marginBottom: 10}}></div>Scanning Sectors...</div></div>}

          {/* Top Movers Chart */}
          {revealedData.movers ? (
            <div className="data-card span-full animate-in">
              <h3>Top Movers {targetDate && `(${targetDate})`}</h3>
              <div className="chart-wrapper">
                <ResponsiveContainer width="100%" height={200}>
                  <BarChart data={allMovers} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="var(--border)" />
                    <XAxis dataKey="ticker" tick={{fontSize: 11}} />
                    <YAxis tick={{fontSize: 10}} />
                    <Tooltip cursor={{fill: 'var(--bg-hover)'}} contentStyle={{borderRadius: 2, border: '1px solid var(--border-dark)', fontSize: '12px'}} />
                    <Bar dataKey="change_pct" radius={[2, 2, 0, 0]}>
                      {allMovers.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.change_pct >= 0 ? 'var(--green)' : 'var(--red)'} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>
          ) : <div className="data-card span-full"><div className="placeholder-content"><div className="spinner" style={{width: 20, height: 20, borderColor: 'var(--text-muted)', borderTopColor: 'var(--blue)', margin: '0 auto', marginBottom: 10}}></div>Identifying Movers...</div></div>}

        </div>
      </div>
    );
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
            
            <label className="input-label">Select Historic Date</label>
            <input 
              type="date" 
              className="input-field"
              value={targetDate}
              onChange={(e) => setTargetDate(e.target.value)}
              disabled={isGenerating}
              max={new Date().toISOString().split('T')[0]}
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
                <div>{loadingStep}</div>
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

          {/* Verification Data Panel */}
          {renderDataPanel()}

        </main>
      </div>

    </div>
  );
}
