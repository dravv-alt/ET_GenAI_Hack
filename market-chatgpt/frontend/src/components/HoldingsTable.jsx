export function HoldingsTable({ holdings }) {
  return (
    <table style={{ width: '100%', borderCollapse: 'collapse', fontFamily: 'var(--mono)', fontSize: 11 }}>
      <thead>
        <tr style={{ background: '#f0f0f0', borderBottom: '2px solid var(--border-dark)', borderTop: '1px solid var(--border)' }}>
          <th style={{ padding: '6px 10px', textAlign: 'left', fontWeight: 500, fontSize: 10, color: 'var(--text-muted)', letterSpacing: '0.08em', whiteSpace: 'nowrap', borderRight: '1px solid var(--border)', borderLeft: '1px solid var(--border)' }}>TICKER</th>
          <th style={{ padding: '6px 10px', textAlign: 'right', fontWeight: 500, fontSize: 10, color: 'var(--text-muted)', letterSpacing: '0.08em', whiteSpace: 'nowrap', borderRight: '1px solid var(--border)' }}>QTY</th>
          <th style={{ padding: '6px 10px', textAlign: 'right', fontWeight: 500, fontSize: 10, color: 'var(--text-muted)', letterSpacing: '0.08em', whiteSpace: 'nowrap', borderRight: '1px solid var(--border)' }}>LTP</th>
          <th style={{ padding: '6px 10px', textAlign: 'right', fontWeight: 500, fontSize: 10, color: 'var(--text-muted)', letterSpacing: '0.08em', whiteSpace: 'nowrap', borderRight: '1px solid var(--border)' }}>P&L%</th>
        </tr>
      </thead>
      <tbody>
        {holdings.map((h, i) => {
          const isPos = h.pnl_pct >= 0;
          return (
            <tr key={i} style={{ borderBottom: '1px solid var(--border)', background: i % 2 === 0 ? '#fff' : 'var(--bg-zebra)' }}
                onMouseEnter={e => e.currentTarget.style.background = 'var(--bg-hover)'}
                onMouseLeave={e => e.currentTarget.style.background = i % 2 === 0 ? '#fff' : 'var(--bg-zebra)'}>
              <td style={{ padding: '5px 10px', borderLeft: '1px solid var(--border)', borderRight: '1px solid var(--border)', fontWeight: 600, color: 'var(--text-primary)' }}>
                {h.ticker.replace('.NS', '')}
              </td>
              <td style={{ padding: '5px 10px', borderRight: '1px solid var(--border)', textAlign: 'right', color: 'var(--text-secondary)' }}>
                {h.quantity}
              </td>
              <td style={{ padding: '5px 10px', borderRight: '1px solid var(--border)', textAlign: 'right', color: 'var(--text-primary)' }}>
                {h.current_price.toFixed(1)}
              </td>
              <td style={{ padding: '5px 10px', borderRight: '1px solid var(--border)', textAlign: 'right', color: isPos ? 'var(--green)' : 'var(--red)' }}>
                {isPos ? '+' : ''}{h.pnl_pct.toFixed(2)}%
              </td>
            </tr>
          );
        })}
      </tbody>
    </table>
  );
}
