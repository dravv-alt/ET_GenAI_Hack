import React from 'react';
import SignalBadge from './SignalBadge';
import { signalColor, signalBg, scoreColor } from '../utils/theme';

const DataTable = ({ alerts }) => {
  if (!alerts || alerts.length === 0) return null;

  return (
    <div style={{ padding: '0 16px', background: '#fff' }}>
      <div style={{ fontFamily: 'var(--mono)', fontSize: 10, color: 'var(--text-muted)', letterSpacing: '0.10em', padding: '12px 0 8px', borderBottom: '1px solid var(--border)' }}>
        LATEST SCAN RESULTS
      </div>
      <div style={{ overflowX: 'auto' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', fontFamily: 'var(--mono)', fontSize: 11 }}>
          <thead>
            <tr style={{ background: '#f0f0f0', borderBottom: '2px solid var(--border-dark)' }}>
              <th style={{ padding: '6px 10px', textAlign: 'left', fontWeight: 500, fontSize: 10, color: 'var(--text-muted)', letterSpacing: '0.08em', whiteSpace: 'nowrap', borderRight: '1px solid var(--border)' }}>TICKER</th>
              <th style={{ padding: '6px 10px', textAlign: 'left', fontWeight: 500, fontSize: 10, color: 'var(--text-muted)', letterSpacing: '0.08em', whiteSpace: 'nowrap', borderRight: '1px solid var(--border)' }}>STRENGTH</th>
              <th style={{ padding: '6px 10px', textAlign: 'left', fontWeight: 500, fontSize: 10, color: 'var(--text-muted)', letterSpacing: '0.08em', whiteSpace: 'nowrap', borderRight: '1px solid var(--border)' }}>ALERT TYPE</th>
              <th style={{ padding: '6px 10px', textAlign: 'left', fontWeight: 500, fontSize: 10, color: 'var(--text-muted)', letterSpacing: '0.08em', whiteSpace: 'nowrap', borderRight: '1px solid var(--border)' }}>HEADLINE</th>
              <th style={{ padding: '6px 10px', textAlign: 'left', fontWeight: 500, fontSize: 10, color: 'var(--text-muted)', letterSpacing: '0.08em', whiteSpace: 'nowrap' }}>TIMESTAMP</th>
            </tr>
          </thead>
          <tbody>
            {alerts.map((a, i) => (
              <tr 
                key={i} 
                style={{ borderBottom: '1px solid var(--border)', background: i % 2 === 0 ? '#fff' : 'var(--bg-zebra)' }}
                onMouseEnter={e => e.currentTarget.style.background = 'var(--bg-hover)'}
                onMouseLeave={e => e.currentTarget.style.background = i % 2 === 0 ? '#fff' : 'var(--bg-zebra)'}
              >
                <td style={{ padding: '5px 10px', borderRight: '1px solid var(--border)', fontWeight: 600 }}>{a.ticker}</td>
                <td style={{ padding: '5px 10px', borderRight: '1px solid var(--border)' }}>
                  <span style={{ 
                    color: signalColor(a.signal_strength), 
                    fontWeight: 600,
                  }}>{a.signal_strength.toUpperCase()}</span>
                </td>
                <td style={{ padding: '5px 10px', borderRight: '1px solid var(--border)' }}>
                  <SignalBadge type={a.alert_type} name={a.alert_type.replace('_', ' ').toUpperCase()} small />
                </td>
                <td style={{ padding: '5px 10px', borderRight: '1px solid var(--border)', fontFamily: 'var(--sans)' }}>{a.title}</td>
                <td style={{ padding: '5px 10px', color: 'var(--text-muted)' }}>
                  {new Date(a.created_at).toLocaleString([], { dateStyle: 'short', timeStyle: 'short' })}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default DataTable;
