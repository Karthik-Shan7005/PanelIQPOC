export default function MetricCards({ columns, rows }) {
    if (!rows || rows.length !== 1) return null;
  
    const colors = [
      { bg: '#0d1e35', color: '#00d4ff' },
      { bg: '#1a1535', color: '#a78bfa' },
      { bg: '#0d2e1e', color: '#00e5a0' },
      { bg: '#2a1f0a', color: '#f59e0b' },
    ];
  
    return (
      <div style={{
        display: 'flex', gap: '12px', flexWrap: 'wrap', marginTop: '8px'
      }}>
        {columns.map((col, i) => (
          <div key={i} style={{
            background: colors[i % colors.length].bg,
            border: `1px solid ${colors[i % colors.length].color}33`,
            borderRadius: '10px',
            padding: '14px 20px',
            minWidth: '140px',
            flex: 1,
          }}>
            <div style={{
              fontSize: '10px', color: '#6b7a99',
              textTransform: 'uppercase', letterSpacing: '1px',
              marginBottom: '6px'
            }}>
              {col}
            </div>
            <div style={{
              fontSize: '24px', fontWeight: '700',
              color: colors[i % colors.length].color
            }}>
              {rows[0][i]}
            </div>
          </div>
        ))}
      </div>
    );
  }