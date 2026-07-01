import React from 'react';

const AiExplanation = ({ alert }) => {
  if (!alert) return null;

  return (
    <div style={{
      margin: '16px',
      padding: '12px',
      background: 'var(--amber-bg)',
      border: '1px solid var(--amber-dim)',
    }}>
      <div style={{
        fontFamily: 'var(--mono)',
        fontSize: 10,
        fontWeight: 600,
        color: 'var(--amber)',
        letterSpacing: '0.10em',
        marginBottom: 8
      }}>
        AI ANALYSIS // {alert.ticker}
      </div>
      
      <div style={{
        fontFamily: 'var(--sans)', // Specs say mono text for AI Explanation, let's use mono.
        fontSize: 12,
        color: 'var(--text-primary)',
        lineHeight: 1.5,
      }}>
        <div style={{ fontFamily: 'var(--mono)', marginBottom: 8 }}>
           {alert.why_it_matters}
        </div>
        <div style={{ fontFamily: 'var(--mono)', color: 'var(--text-muted)' }}>
           › {alert.action_hint}
        </div>
      </div>
    </div>
  );
};

export default AiExplanation;
