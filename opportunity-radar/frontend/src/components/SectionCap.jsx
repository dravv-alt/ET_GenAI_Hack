import React from 'react';

const SectionCap = ({ label, count }) => {
  return (
    <div style={{
      padding: '6px 12px',
      background: 'var(--header-sub)',
      borderBottom: '1px solid var(--border-header)',
      display: 'flex',
      justifyContent: 'space-between',
      alignItems: 'center',
    }}>
      <span style={{ fontFamily: 'var(--mono)', fontSize: 10, color: '#aaa', letterSpacing: '0.10em' }}>
        {label}
      </span>
      {count !== undefined && (
        <span style={{ fontFamily: 'var(--mono)', fontSize: 10, color: 'var(--green)' }}>
          {count}
        </span>
      )}
    </div>
  );
};

export default SectionCap;
