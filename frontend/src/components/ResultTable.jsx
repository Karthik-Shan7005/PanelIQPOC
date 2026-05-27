import { useState } from 'react';

export default function ResultTable({ columns, rows, rowCount }) {
  const [page, setPage] = useState(0);
  const pageSize = 10;
  const totalPages = Math.ceil(rows.length / pageSize);
  const visibleRows = rows.slice(page * pageSize, (page + 1) * pageSize);

  const exportCSV = () => {
    const lines = [
      columns.join(','),
      ...rows.map(r => r.map(v => `"${v}"`).join(','))
    ];
    const blob = new Blob([lines.join('\n')], { type: 'text/csv' });
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = 'paneliq_export.csv';
    a.click();
  };

  return (
    <div style={{
      background: '#111520', border: '1px solid #1e2a40',
      borderRadius: '10px', overflow: 'hidden', marginTop: '8px'
    }}>
      {/* Header */}
      <div style={{
        display: 'flex', justifyContent: 'space-between',
        alignItems: 'center', padding: '10px 16px',
        borderBottom: '1px solid #1e2a40',
        fontSize: '11px', color: '#6b7a99',
        fontFamily: 'monospace'
      }}>
        <span style={{ color: '#00d4ff' }}>
          📋 {rowCount} rows returned
        </span>
        <button onClick={exportCSV} style={{
          background: 'none', border: '1px solid #1e2a40',
          color: '#6b7a99', padding: '3px 10px', borderRadius: '5px',
          cursor: 'pointer', fontSize: '11px',
        }}>
          Export CSV
        </button>
      </div>

      {/* Table */}
      <div style={{ overflowX: 'auto' }}>
        <table style={{
          width: '100%', borderCollapse: 'collapse', fontSize: '12.5px'
        }}>
          <thead>
            <tr>
              {columns.map((col, i) => (
                <th key={i} style={{
                  background: '#0d1220', color: '#6b7a99',
                  padding: '9px 14px', textAlign: 'left',
                  fontSize: '10px', fontWeight: '700',
                  textTransform: 'uppercase', letterSpacing: '0.8px',
                  borderBottom: '1px solid #1e2a40',
                  whiteSpace: 'nowrap'
                }}>
                  {col}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {visibleRows.map((row, i) => (
              <tr key={i} style={{
                borderBottom: '1px solid #151e30',
                transition: 'background 0.1s'
              }}
                onMouseEnter={e => e.currentTarget.style.background = '#13192a'}
                onMouseLeave={e => e.currentTarget.style.background = 'transparent'}
              >
                {row.map((cell, j) => (
                  <td key={j} style={{
                    padding: '9px 14px', color: '#e8edf5'
                  }}>
                    {cell}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div style={{
          display: 'flex', justifyContent: 'center',
          alignItems: 'center', gap: '12px',
          padding: '10px', borderTop: '1px solid #1e2a40',
          fontSize: '12px', color: '#6b7a99'
        }}>
          <button
            onClick={() => setPage(p => Math.max(0, p - 1))}
            disabled={page === 0}
            style={{
              background: 'none', border: '1px solid #1e2a40',
              color: page === 0 ? '#333' : '#6b7a99',
              padding: '3px 10px', borderRadius: '5px',
              cursor: page === 0 ? 'default' : 'pointer'
            }}
          >
            ← Prev
          </button>
          <span>Page {page + 1} of {totalPages}</span>
          <button
            onClick={() => setPage(p => Math.min(totalPages - 1, p + 1))}
            disabled={page === totalPages - 1}
            style={{
              background: 'none', border: '1px solid #1e2a40',
              color: page === totalPages - 1 ? '#333' : '#6b7a99',
              padding: '3px 10px', borderRadius: '5px',
              cursor: page === totalPages - 1 ? 'default' : 'pointer'
            }}
          >
            Next →
          </button>
        </div>
      )}
    </div>
  );
}