import React from 'react';

const BreakdownBar = ({ label, val, max, color }) => {
  const percentage = max > 0 ? (val / max) * 100 : 0;
  
  return (
    <div style={{ marginBottom: 12 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
        <span style={{ fontFamily: 'var(--mono)', fontSize: 10, color: 'var(--text-muted)', letterSpacing: '0.06em' }}>
          {label}
        </span>
        <span style={{ fontFamily: 'var(--mono)', fontSize: 10, fontWeight: 500 }}>
          {val}/{max}
        </span>
      </div>
      <div style={{ height: 3, background: 'var(--border)', position: 'relative' }}>
        <div style={{ 
          position: 'absolute', 
          left: 0, 
          top: 0, 
          bottom: 0, 
          width: `${percentage}%`, 
          background: color, 
          transition: 'width 0.5s ease' 
        }} />
      </div>
    </div>
  );
};

export default BreakdownBar;
