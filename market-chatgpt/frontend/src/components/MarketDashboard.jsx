import { useState, useEffect } from 'react';
import { fetchMarketData } from '../lib/api';

export function MarketDashboard({ onContextChange }) {
  const [marketData, setMarketData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  const [search, setSearch] = useState('');
  const [filter, setFilter] = useState('ALL'); // ALL, GAINERS, LOSERS

  useEffect(() => {
    let unmounted = false;
    const loadData = async () => {
      try {
        const res = await fetchMarketData();
        if (!unmounted) {
          setMarketData(res.data);
          setLoading(false);
          setError(res.error || null);
        }
      } catch (err) {
        if (!unmounted) {
          setError(err.message);
          setLoading(false);
        }
      }
    };
    loadData();
    // Poll every 60 seconds
    const interval = setInterval(loadData, 60000);
    return () => {
      unmounted = true;
      clearInterval(interval);
    };
  }, []);

  // Filter the data based on search and tabs
  const filteredData = marketData.filter(item => {
    if (search && !item.ticker.toLowerCase().includes(search.toLowerCase())) return false;
    if (filter === 'GAINERS' && item.pnl_pct <= 0) return false;
    if (filter === 'LOSERS' && item.pnl_pct >= 0) return false;
    return true;
  });

  // Whenever filteredData changes, we need to bubble it up to the Chat context
  useEffect(() => {
    onContextChange(filteredData);
  }, [search, filter, marketData]);

  if (loading) {
    return (
      <div style={{ padding: 24, textAlign: 'center', fontFamily: 'var(--mono)', fontSize: 11, color: 'var(--text-muted)' }}>
        [ CONNECTING TO LIVE MARKET FEED... ]
      </div>
    );
  }

  if (error && marketData.length === 0) {
    return (
      <div style={{ padding: 24, textAlign: 'center', fontFamily: 'var(--mono)', fontSize: 11, color: 'var(--red)' }}>
        [ FEED ERROR ]<br/>{error}
      </div>
    );
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      
      {/* Search and Filter Ribbon */}
      <div style={{ padding: '12px', borderBottom: '1px solid var(--border)', background: 'var(--bg-white)', display: 'flex', gap: 12, alignItems: 'center' }}>
        <input
          placeholder="SEARCH TICKERS..."
          value={search}
          onChange={e => setSearch(e.target.value)}
          style={{
            flex: 1, padding: '6px 8px', border: '1px solid var(--border)',
            fontFamily: 'var(--mono)', fontSize: 11, background: 'var(--bg)',
            outline: 'none'
          }}
        />

        <div style={{ display: 'flex', gap: 1, background: 'var(--border)' }}>
          {['ALL', 'GAINERS', 'LOSERS'].map(f => (
            <button
              key={f}
              onClick={() => setFilter(f)}
              style={{
                border: 'none', padding: '6px 10px', fontFamily: 'var(--mono)', fontSize: 10, cursor: 'pointer',
                background: filter === f ? 'var(--header-sub)' : 'var(--bg-white)',
                color: filter === f ? '#fff' : 'var(--text-secondary)'
              }}
            >
              {f}
            </button>
          ))}
        </div>
      </div>

      {/* Feed Table */}
      <div style={{ flex: 1, overflowY: 'auto' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', fontFamily: 'var(--mono)', fontSize: 11 }}>
          <thead>
            <tr style={{ background: '#f0f0f0', borderBottom: '2px solid var(--border-dark)', borderTop: 'none' }}>
              <th style={{ padding: '6px 10px', textAlign: 'left', fontWeight: 500, fontSize: 10, color: 'var(--text-muted)', letterSpacing: '0.08em', whiteSpace: 'nowrap', borderRight: '1px solid var(--border)' }}>TICKER</th>
              <th style={{ padding: '6px 10px', textAlign: 'right', fontWeight: 500, fontSize: 10, color: 'var(--text-muted)', letterSpacing: '0.08em', whiteSpace: 'nowrap', borderRight: '1px solid var(--border)' }}>LTP</th>
              <th style={{ padding: '6px 10px', textAlign: 'right', fontWeight: 500, fontSize: 10, color: 'var(--text-muted)', letterSpacing: '0.08em', whiteSpace: 'nowrap', borderRight: '1px solid var(--border)' }}>CHG%</th>
              <th style={{ padding: '6px 10px', textAlign: 'right', fontWeight: 500, fontSize: 10, color: 'var(--text-muted)', letterSpacing: '0.08em', whiteSpace: 'nowrap', borderRight: 'none' }}>VOL</th>
            </tr>
          </thead>
          <tbody>
            {filteredData.map((d, i) => {
              const isPos = d.pnl_pct >= 0;
              return (
                <tr key={i} style={{ borderBottom: '1px solid var(--border)', background: i % 2 === 0 ? '#fff' : 'var(--bg-zebra)' }}
                    onMouseEnter={e => e.currentTarget.style.background = 'var(--bg-hover)'}
                    onMouseLeave={e => e.currentTarget.style.background = i % 2 === 0 ? '#fff' : 'var(--bg-zebra)'}>
                  <td style={{ padding: '5px 10px', borderRight: '1px solid var(--border)', fontWeight: 600, color: 'var(--text-primary)' }}>
                    {d.ticker}
                  </td>
                  <td style={{ padding: '5px 10px', borderRight: '1px solid var(--border)', textAlign: 'right', color: 'var(--text-primary)' }}>
                    {d.current_price.toFixed(1)}
                  </td>
                  <td style={{ padding: '5px 10px', borderRight: '1px solid var(--border)', textAlign: 'right', color: isPos ? 'var(--green)' : 'var(--red)' }}>
                    {isPos ? '+' : ''}{d.pnl_pct.toFixed(2)}%
                  </td>
                  <td style={{ padding: '5px 10px', borderRight: 'none', textAlign: 'right', color: 'var(--text-secondary)' }}>
                    {d.volume > 0 ? (d.volume / 1000000).toFixed(2) + 'M' : '-'}
                  </td>
                </tr>
              );
            })}
            {filteredData.length === 0 && (
              <tr>
                <td colSpan={4} style={{ padding: 24, textAlign: 'center', color: 'var(--text-muted)' }}>
                  NO DATA MATCHING FILTER
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
