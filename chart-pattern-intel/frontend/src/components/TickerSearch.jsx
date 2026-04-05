import { useEffect, useMemo, useState } from 'react';

export default function TickerSearch({ value, tickers, onSelect, marketSuffix, aliases, placeholder }) {
  const [query, setQuery] = useState(value || '');
  const [show, setShow] = useState(false);

  const resolvedAliases = useMemo(() => aliases || {}, [aliases]);

  useEffect(() => {
    setQuery(value || '');
  }, [value]);

  const matches = useMemo(() => {
    const q = query.trim().toUpperCase();
    if (!q) return [];
    return tickers.filter((t) => t.symbol.includes(q) || t.name.toUpperCase().includes(q)).slice(0, 6);
  }, [query, tickers]);

  function normalizeSymbol(input) {
    const trimmed = (input || '').trim().toUpperCase();
    if (!trimmed) return '';
    let normalized = trimmed;
    if (marketSuffix && normalized.endsWith(marketSuffix)) {
      normalized = normalized.slice(0, -marketSuffix.length);
    }
    if (resolvedAliases[normalized]) return resolvedAliases[normalized];
    if (tickers.some((item) => item.symbol === normalized)) return normalized;
    return normalized;
  }

  function submit(symbol) {
    const final = normalizeSymbol(symbol || query);
    if (!final) return;
    onSelect(final);
    setShow(false);
  }

  return (
    <div style={{ position: 'relative' }}>
      <div style={{ display: 'flex', alignItems: 'center', background: '#2c2c2c', border: '1px solid #444', height: 28 }}>
        <span style={{ color: '#888', fontSize: 11, padding: '0 8px', fontFamily: 'var(--mono)', flexShrink: 0 }}>
          TICKER
        </span>
        <input
          value={query}
          onChange={(e) => {
            setQuery(e.target.value);
            setShow(true);
          }}
          onFocus={() => setShow(true)}
          onBlur={() => setTimeout(() => setShow(false), 120)}
          onKeyDown={(e) => {
            if (e.key === 'Enter') submit();
          }}
          style={{
            flex: 1,
            background: 'transparent',
            border: 'none',
            outline: 'none',
            color: '#fff',
            fontSize: 12,
            fontFamily: 'var(--mono)',
            caretColor: 'var(--green)',
          }}
          placeholder={placeholder || 'RELIANCE'}
        />
        <button
          onClick={() => submit()}
          style={{
            background: 'var(--green)',
            border: 'none',
            color: '#fff',
            width: 28,
            height: 28,
            cursor: 'pointer',
            fontSize: 14,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
          }}
        >
          ›
        </button>
      </div>
      {show && matches.length > 0 && (
        <div
          className="card"
          style={{ position: 'absolute', top: 30, left: 0, right: 0, zIndex: 10 }}
        >
          {matches.map((item) => (
            <div
              key={item.symbol}
              onMouseDown={(event) => {
                event.preventDefault();
                setQuery(item.symbol);
                submit(item.symbol);
              }}
              style={{
                padding: '6px 8px',
                borderBottom: '1px solid var(--border)',
                cursor: 'pointer',
                background: 'var(--bg-white)',
              }}
            >
              <div style={{ fontFamily: 'var(--mono)', fontSize: 11, letterSpacing: '0.06em' }}>{item.symbol}</div>
              <div style={{ fontFamily: 'var(--sans)', fontSize: 11, color: 'var(--text-secondary)' }}>{item.name}</div>
            </div>
          ))}
        </div>
      )}
      {show && matches.length === 0 && query.trim() && (
        <div
          className="card"
          style={{ position: 'absolute', top: 30, left: 0, right: 0, zIndex: 10 }}
        >
          <div style={{ padding: '8px 10px', fontFamily: 'var(--mono)', fontSize: 11, color: 'var(--text-muted)' }}>
            NO MATCHES
          </div>
        </div>
      )}
    </div>
  );
}
