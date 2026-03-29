import { useState, useRef } from 'react';
import { parsePortfolio } from '../lib/api';
import { HoldingsTable } from './HoldingsTable';

export function PortfolioUploader({ data, onDataParsed }) {
  const [loading, setLoading] = useState(false);
  const fileInputRef = useRef(null);

  const handleFile = async (file) => {
    if (!file) return;
    setLoading(true);
    try {
      const result = await parsePortfolio(file);
      onDataParsed(result);
    } catch (e) {
      alert("Error parsing CSV: " + e.message);
    }
    setLoading(false);
    if(fileInputRef.current) fileInputRef.current.value = "";
  };

  const handleDrop = (e) => {
    e.preventDefault();
    if(e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFile(e.dataTransfer.files[0]);
    }
  };

  const loadFallback = () => {
    const fallbackData = {
      holdings: [
        { ticker: "RELIANCE.NS", quantity: 50, avg_buy_price: 2400.0, current_price: 2950.2, pnl_abs: 27510.0, pnl_pct: 22.92, value: 147510.0 },
        { ticker: "INFY.NS", quantity: 100, avg_buy_price: 1450.0, current_price: 1680.5, pnl_abs: 23050.0, pnl_pct: 15.9, value: 168050.0 },
        { ticker: "HDFCBANK.NS", quantity: 30, avg_buy_price: 1600.0, current_price: 1420.0, pnl_abs: -5400.0, pnl_pct: -11.25, value: 42600.0 },
        { ticker: "TCS.NS", quantity: 20, avg_buy_price: 3500.0, current_price: 4100.0, pnl_abs: 12000.0, pnl_pct: 17.14, value: 82000.0 },
        { ticker: "WIPRO.NS", quantity: 75, avg_buy_price: 420.0, current_price: 510.0, pnl_abs: 6750.0, pnl_pct: 21.43, value: 38250.0 }
      ],
      summary: {
        total_invested: 414500.0,
        total_current_value: 478410.0,
        total_pnl_abs: 63910.0,
        total_pnl_pct: 15.42,
        holdings_count: 5
      }
    };
    onDataParsed(fallbackData);
  };

  if (data) {
    return (
      <div style={{ padding: 14 }}>
        <BacktestStats summary={data.summary} holdings={data.holdings} />
        <div style={{ marginTop: 14 }}>
            <span style={{ fontFamily: 'var(--mono)', fontSize: 10, color: 'var(--text-muted)', letterSpacing: '0.10em' }}>HOLDINGS BREAKDOWN</span>
        </div>
        <div style={{ marginTop: 8 }}>
            <HoldingsTable holdings={data.holdings} />
        </div>
      </div>
    );
  }

  return (
    <div style={{ padding: 14, display: 'flex', flexDirection: 'column', gap: 12 }}>
        <div 
          onDragOver={e => e.preventDefault()}
          onDrop={handleDrop}
          style={{
            border: '1px dashed var(--border-dark)',
            background: 'var(--bg-zebra)',
            padding: '24px',
            textAlign: 'center',
            cursor: 'pointer'
          }}
          onClick={() => fileInputRef.current?.click()}
        >
          <span style={{ fontFamily: 'var(--mono)', fontSize: 11, color: 'var(--text-secondary)' }}>
            {loading ? 'PROCESSING CSV...' : 'DRAG AND DROP PORTFOLIO CSV HERE'}
          </span>
          <input type="file" ref={fileInputRef} onChange={e => handleFile(e.target.files[0])} style={{ display: 'none' }} accept=".csv" />
        </div>

        <button 
          onClick={loadFallback}
          style={{
            background: 'var(--bg-white)',
            border: '1px solid var(--border)',
            padding: '12px',
            fontFamily: 'var(--mono)',
            fontSize: 10,
            cursor: 'pointer',
            textAlign: 'center',
            color: 'var(--text-primary)',
            letterSpacing: '0.05em'
          }}
          onMouseEnter={e => e.currentTarget.style.background = 'var(--bg-hover)'}
          onMouseLeave={e => e.currentTarget.style.background = 'var(--bg-white)'}
        >
          [ FAILSAFE ] LOAD DEMO PORTFOLIO
        </button>
    </div>
  );
}

function BacktestStats({ summary, holdings }) {
  const isPositive = summary.total_pnl_pct >= 0;
  const pnlColor = isPositive ? 'var(--green)' : 'var(--red)';

  const stats = [
    { label: "HOLDINGS", value: summary.holdings_count, color: 'var(--text-primary)' },
    { label: "INVESTED", value: `₹${(summary.total_invested / 1000).toFixed(1)}K`, color: 'var(--text-primary)' },
    { label: "CURRENT", value: `₹${(summary.total_current_value / 1000).toFixed(1)}K`, color: 'var(--text-primary)' },
    { label: "P&L (%)", value: `${isPositive ? '+' : ''}${summary.total_pnl_pct.toFixed(2)}%`, color: pnlColor },
  ];

  if (holdings && holdings.length > 0 && summary.total_current_value > 0) {
    const sorted = [...holdings].sort((a, b) => b.value - a.value);
    const top2Value = (sorted[0]?.value || 0) + (sorted[1]?.value || 0);
    const concentration = (top2Value / summary.total_current_value) * 100;
    stats.push({ 
      label: "CONC. RISK", 
      value: `${concentration.toFixed(1)}%`, 
      color: concentration > 50 ? 'var(--amber)' : 'var(--text-primary)' 
    });
  }

  return (
    <div style={{ display: 'grid', gridTemplateColumns: `repeat(${stats.length}, 1fr)`, border: '1px solid var(--border)' }}>
      {stats.map((s, i) => (
        <div key={i} style={{
          padding: '10px 12px',
          borderRight: i < stats.length - 1 ? '1px solid var(--border)' : 'none',
          background: i % 2 === 0 ? '#fff' : 'var(--bg)',
        }}>
          <div style={{ fontFamily: 'var(--mono)', fontSize: 9, color: 'var(--text-muted)', letterSpacing: '0.10em', marginBottom: 4 }}>
            {s.label}
          </div>
          <div style={{ fontFamily: 'var(--mono)', fontSize: 16, fontWeight: 600, color: s.color }}>
            {s.value}
          </div>
        </div>
      ))}
    </div>
  );
}
