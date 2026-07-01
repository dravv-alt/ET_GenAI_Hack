import React, { useState, useEffect } from 'react';
import HeaderBar from './components/HeaderBar';
import SectionCap from './components/SectionCap';
import AlertCard from './components/AlertCard';
import ChartArea from './components/ChartArea';
import ScoreHero from './components/ScoreHero';
import BreakdownBar from './components/BreakdownBar';
import StatBlock from './components/StatBlock';
import DataTable from './components/DataTable';
import AiExplanation from './components/AiExplanation';

const API_BASE = 'http://localhost:8001';

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null, info: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, info) {
    this.setState({ info });
    console.error("ErrorBoundary caught an error", error, info);
  }

  render() {
    if (this.state.hasError) {
      return (
         <div style={{ padding: 20, whiteSpace: 'pre-wrap', color: 'red', fontFamily: 'monospace' }}>
            <h2>Something went wrong.</h2>
            {this.state.error && this.state.error.toString()}
            <br />
            {this.state.info && this.state.info.componentStack}
         </div>
      );
    }
    return this.props.children;
  }
}

function AppContent() {
  const [alerts, setAlerts] = useState([]);
  const [selectedTicker, setSelectedTicker] = useState(null);
  const [isScanning, setIsScanning] = useState(false);
  const [error, setError] = useState(null);

  // Fetch alerts on load
  const fetchAlerts = async () => {
    try {
      setError(null);
      const res = await fetch(`${API_BASE}/alerts`);
      if (!res.ok) throw new Error('Failed to fetch alerts.');
      const data = await res.json();
      setAlerts(data.alerts || []);
      
      // Auto-select first ticker if none selected
      if (data.alerts && data.alerts.length > 0 && !selectedTicker) {
        setSelectedTicker(data.alerts[0].ticker);
      }
    } catch (err) {
      console.error(err);
      setError(err.message);
    }
  };

  useEffect(() => {
    fetchAlerts();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleScan = async () => {
    setIsScanning(true);
    setError(null);
    try {
      const res = await fetch(`${API_BASE}/scan`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify([]) // Empty array uses default watchlist
      });
      if (!res.ok) throw new Error('Scan failed.');
      const data = await res.json();
      setAlerts(data.alerts || []);
      
      if (data.alerts && data.alerts.length > 0) {
        setSelectedTicker(data.alerts[0].ticker);
      }
    } catch (err) {
      console.error(err);
      setError('Scan error: server might be unreachable.');
    } finally {
      setIsScanning(false);
    }
  };

  const handleSearch = (ticker) => {
    setSelectedTicker(ticker);
  };

  // Derived state for the selected ticker
  const tickerAlerts = alerts.filter(a => a.ticker === selectedTicker);
  const selectedAlert = tickerAlerts[0]; // Usually the highest ranked for this ticker

  // Calculate some dummy stats for the Score Panel based on the selected ticker's alerts
  // In a real app this would come from the backend.
  const topScore = selectedAlert 
    ? (selectedAlert.signal_strength === 'high' ? 85 : selectedAlert.signal_strength === 'medium' ? 65 : 45) + Math.random() * 10 
    : 0;

  const stats = [
    { label: 'WIN RATE', value: '68%', color: 'var(--green)' },
    { label: 'AVG RET', value: '+4.2%', color: 'var(--green)' },
    { label: 'MAX DD', value: '-2.1%', color: 'var(--red)' },
    { label: 'OCCURS', value: '14', color: 'var(--text-primary)' },
  ];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100vh', overflow: 'hidden' }}>
      {/* 1. Header (Topbar) */}
      <HeaderBar 
        onSearch={handleSearch} 
        onScan={handleScan} 
        isScanning={isScanning} 
      />

      {error && (
        <div style={{ background: 'var(--red-bg)', color: 'var(--red)', padding: '8px 16px', fontFamily: 'var(--mono)', fontSize: 12, borderBottom: '1px solid var(--red-dim)' }}>
          ERROR: {error}
        </div>
      )}

      {/* 2. Main Terminal Content (3 columns) */}
      <div style={{ display: 'flex', flex: 1, overflow: 'hidden' }}>
        
        {/* LEFT: Alert Feed */}
        <div style={{ 
          width: 220, 
          flexShrink: 0, 
          borderRight: '1px solid var(--border)', 
          display: 'flex', 
          flexDirection: 'column',
          background: '#fff'
        }}>
          <SectionCap label="LIVE ALERTS" count={alerts.length} />
          <div style={{ flex: 1, overflowY: 'auto' }} className={isScanning ? 'pulse' : 'animate-in'}>
            {alerts.length === 0 && !isScanning && (
              <div style={{ padding: 16, color: 'var(--text-muted)', fontFamily: 'var(--mono)', fontSize: 11, textAlign: 'center' }}>
                NO ALERTS FOUND. CLICK SCAN.
              </div>
            )}
            {alerts.map((a, i) => (
              <AlertCard 
                key={`${a.id}-${i}`} 
                alert={a} 
                isSelected={selectedTicker === a.ticker}
                onClick={() => setSelectedTicker(a.ticker)}
              />
            ))}
          </div>
        </div>

        {/* CENTER: Main Chart Area */}
        <div style={{ 
          flex: 1, 
          display: 'flex', 
          flexDirection: 'column', 
          overflowY: 'auto',
          background: 'var(--bg-white)',
        }}>
          <div style={{ flexShrink: 0, borderBottom: '1px solid var(--border)' }}>
            {selectedTicker ? (
              <ChartArea ticker={selectedTicker} alerts={tickerAlerts} />
            ) : (
              <div style={{ height: 430, display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-muted)', fontFamily: 'var(--mono)', fontSize: 12 }}>
                SELECT A TICKER TO VIEW CHART
              </div>
            )}
          </div>

          <div style={{ flexShrink: 0 }}>
             {selectedAlert && <AiExplanation alert={selectedAlert} />}
          </div>

          <div style={{ flex: 1 }}>
             <DataTable alerts={alerts} />
          </div>
        </div>

        {/* RIGHT: Score Panel */}
        <div style={{ 
          width: 200, 
          flexShrink: 0, 
          borderLeft: '1px solid var(--border)', 
          background: 'var(--bg-white)',
          display: 'flex',
          flexDirection: 'column'
        }}>
          <SectionCap label="SIGNAL LOGIC" />
          
          <div style={{ padding: '0 0 16px 0', borderBottom: '1px solid var(--border)' }}>
            <ScoreHero score={topScore} label={selectedAlert ? selectedAlert.signal_strength : 'N/A'} />
          </div>

          <div style={{ padding: '16px 14px', borderBottom: '1px solid var(--border)' }}>
            <div style={{ fontFamily: 'var(--mono)', fontSize: 10, color: 'var(--text-muted)', letterSpacing: '0.10em', marginBottom: 12 }}>
              BREAKDOWN
            </div>
            
            <BreakdownBar label="TECHNICAL" val={selectedAlert && topScore > 60 ? 8 : 4} max={10} color="var(--green)" />
            <BreakdownBar label="FUNDAMENTAL" val={selectedAlert && ['earnings_beat', 'capex_announcement'].includes(selectedAlert.alert_type) ? 9 : 2} max={10} color="var(--amber)" />
            <BreakdownBar label="SENTIMENT" val={selectedAlert && ['insider_buy', 'sentiment_shift'].includes(selectedAlert.alert_type) ? 8 : 5} max={10} color={topScore > 60 ? "var(--green)" : "var(--amber)"} />
          </div>

          <div style={{ padding: '16px 14px' }}>
            <div style={{ fontFamily: 'var(--mono)', fontSize: 10, color: 'var(--text-muted)', letterSpacing: '0.10em', marginBottom: 12 }}>
              HISTORICAL EDGE
            </div>
            <StatBlock stats={stats} />
          </div>

        </div>

      </div>
    </div>
  );
}

export default function App() {
  return (
    <ErrorBoundary>
      <AppContent />
    </ErrorBoundary>
  );
}
