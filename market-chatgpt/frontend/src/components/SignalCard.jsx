export function SignalCard({ signal }) {
  const type = signal.signal.toLowerCase();
  
  const signalColor = 
    type === 'bullish' ? 'var(--green)' :
    type === 'bearish' ? 'var(--red)'   : 'var(--amber)';

  const signalBg = 
    type === 'bullish' ? 'var(--green-bg)' :
    type === 'bearish' ? 'var(--red-bg)'   : 'var(--amber-bg)';

  const icon = 
    type === 'bullish' ? '▲' : 
    type === 'bearish' ? '▼' : '◆';

  return (
    <div style={{
      border: `1px solid ${signalColor}`,
      background: signalBg,
      display: 'flex',
      flexDirection: 'column',
    }}>
      <div style={{
        padding: '6px 10px',
        borderBottom: `1px solid ${signalColor}`,
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        background: '#fff'
      }}>
        <span style={{ fontFamily: 'var(--mono)', fontSize: 13, fontWeight: 600, color: 'var(--text-primary)', letterSpacing: '0.04em' }}>
          {signal.ticker.replace('.NS', '')}
        </span>
        <span style={{
          fontSize: 11,
          fontFamily: 'var(--mono)',
          fontWeight: 600,
          color: signalColor,
          letterSpacing: '0.06em',
        }}>
          {icon} {type.toUpperCase()}
        </span>
      </div>

      <div style={{ padding: '8px 10px', fontFamily: 'var(--sans)' }}>
        <ul style={{ paddingLeft: 16, margin: 0, color: 'var(--text-secondary)', fontSize: 12 }}>
          {signal.reasons && signal.reasons.map((r, i) => (
            <li key={i} style={{ marginBottom: 4 }}>{r}</li>
          ))}
        </ul>
      </div>
    </div>
  );
}
