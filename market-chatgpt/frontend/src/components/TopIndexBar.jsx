import { useState, useEffect } from 'react';
import { fetchMarketData } from '../lib/api';

export function TopIndexBar() {
  const [indices, setIndices] = useState([]);

  useEffect(() => {
    let unmounted = false;
    const load = async () => {
      try {
        const res = await fetchMarketData('INDICES');
        if (!unmounted) setIndices(res.data);
      } catch (e) {
        // fail silently for indices bar
      }
    };
    load();
    const int = setInterval(load, 60000);
    return () => {
      unmounted = true;
      clearInterval(int);
    };
  }, []);

  if (indices.length === 0) return null;

  return (
    <div style={{
      display: 'flex',
      alignItems: 'center',
      background: 'var(--header-sub)', // Dark theme matching header
      borderBottom: '1px solid var(--border-header)',
      height: 28,
      padding: '0 16px',
      overflowX: 'auto',
      whiteSpace: 'nowrap',
      gap: 24,
      fontFamily: 'var(--mono)',
      fontSize: 10,
    }}>
      {indices.filter(idx => idx.ticker !== '^VIX').map((idx, i) => {
        const isPos = idx.pnl_pct >= 0;
        return (
          <div key={i} style={{ display: 'flex', gap: 6 }}>
            <span style={{ color: 'var(--text-header-dim)', fontWeight: 600 }}>{idx.ticker.replace('^', '')}</span>
            <span style={{ color: '#fff' }}>{idx.current_price.toLocaleString(undefined, { maximumFractionDigits: 1 })}</span>
            <span style={{ color: isPos ? 'var(--green)' : 'var(--red)' }}>
              {isPos ? '▲' : '▼'}{Math.abs(idx.pnl_pct).toFixed(2)}%
            </span>
          </div>
        );
      })}
      
      {(() => {
        const vix = indices.find(i => i.ticker === '^VIX');
        if (!vix) return null;
        const val = vix.current_price;
        const state = val > 30 ? 'FEAR 🔴' : val > 20 ? 'NEUTRAL 🟡' : 'GREED 🟢';
        return (
          <div style={{ marginLeft: 'auto', display: 'flex', gap: 6, alignItems: 'center', background: '#000', padding: '2px 8px', borderRadius: 12, border: '1px solid #444' }}>
            <span style={{ color: '#aaa', fontWeight: 600 }}>VIX INDEX:</span>
            <span style={{ color: val > 30 ? 'var(--red)' : val > 20 ? 'var(--amber)' : 'var(--green)' }}>{state} ({val.toFixed(2)})</span>
          </div>
        );
      })()}
    </div>
  );
}
