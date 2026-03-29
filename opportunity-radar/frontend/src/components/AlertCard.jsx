import React from 'react';
import SignalBadge from './SignalBadge';
import { signalBg, signalColor } from '../utils/theme';

const AlertCard = ({ alert, isSelected, onClick }) => {
  const { ticker, alert_type, title, source_label, created_at, signal_strength } = alert;
  
  const timeStr = new Date(created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

  return (
    <div 
      onClick={onClick}
      style={{
        padding: '12px',
        borderBottom: '1px solid var(--border)',
        background: isSelected ? 'var(--green-bg)' : '#fff',
        borderLeft: isSelected ? '2px solid var(--green)' : '2px solid transparent',
        cursor: 'pointer',
        transition: 'background 0s, border-left 0s', // No transition delay, instant
      }}
      onMouseEnter={e => !isSelected && (e.currentTarget.style.background = 'var(--bg-hover)')}
      onMouseLeave={e => !isSelected && (e.currentTarget.style.background = '#fff')}
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 6 }}>
        <span style={{ fontFamily: 'var(--mono)', fontSize: 13, fontWeight: 600, color: 'var(--text-primary)', letterSpacing: '0.04em' }}>
          {ticker}
        </span>
        <span style={{ fontFamily: 'var(--mono)', fontSize: 10, color: 'var(--text-muted)' }}>
          {timeStr}
        </span>
      </div>
      
      <div style={{ marginBottom: 8 }}>
        <SignalBadge type={alert_type} name={alert_type.replace('_', ' ').toUpperCase()} small />
      </div>

      <div style={{ fontSize: 13, color: 'var(--text-secondary)', marginBottom: 6, lineHeight: 1.4 }}>
        {title}
      </div>

      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <span style={{ fontFamily: 'var(--mono)', fontSize: 10, color: 'var(--text-muted)' }}>
          {source_label}
        </span>
        {signal_strength && (
          <span style={{ 
            fontFamily: 'var(--mono)', 
            fontSize: 9, 
            color: signalColor(signal_strength), 
            background: signalBg(signal_strength), 
            padding: '2px 4px', 
            fontWeight: 600,
            border: `1px solid ${signalColor(signal_strength)}`
          }}>
            {signal_strength.toUpperCase()}
          </span>
        )}
      </div>
    </div>
  );
};

export default AlertCard;
