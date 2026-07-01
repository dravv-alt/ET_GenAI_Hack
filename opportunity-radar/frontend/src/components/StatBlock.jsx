import React from 'react';

const StatBlock = ({ stats }) => {
  return (
    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(0, 1fr))', border: '1px solid var(--border)' }}>
      {stats.map((s, i) => (
        <div key={i} style={{
          padding: '10px 12px',
          borderRight: i < stats.length - 1 ? '1px solid var(--border)' : 'none',
          background: i % 2 === 0 ? '#fff' : 'var(--bg-zebra)',
        }}>
          <div style={{ 
            fontFamily: 'var(--mono)', 
            fontSize: 9, 
            color: 'var(--text-muted)', 
            letterSpacing: '0.10em', 
            marginBottom: 4,
            whiteSpace: 'nowrap',
            overflow: 'hidden',
            textOverflow: 'ellipsis'
          }}>
            {s.label}
          </div>
          <div style={{ 
            fontFamily: 'var(--mono)', 
            fontSize: 16, 
            fontWeight: 600, 
            color: s.color || 'var(--text-primary)' 
          }}>
            {s.value}
          </div>
        </div>
      ))}
    </div>
  );
};

export default StatBlock;
