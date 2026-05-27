import {
    BarChart, Bar, LineChart, Line,
    PieChart, Pie, Cell,
    XAxis, YAxis, CartesianGrid,
    Tooltip, Legend, ResponsiveContainer
  } from 'recharts';
  
  const COLORS = [
    '#00d4ff', '#7c6af7', '#00e5a0', '#f59e0b',
    '#ff6b6b', '#a78bfa', '#34d399', '#fb923c'
  ];
  
  export default function ResultChart({ chartType, columns, rows }) {
    if (!rows || rows.length === 0) return null;
    if (chartType === 'metric_cards' || chartType === 'table') return null;
  
    // Convert rows to recharts format
    const data = rows.slice(0, 20).map(row => {
      const obj = {};
      columns.forEach((col, i) => {
        // Convert formatted numbers back to numeric
        const val = row[i];
        const num = typeof val === 'string'
          ? parseFloat(val.replace(/,/g, ''))
          : val;
        obj[col] = isNaN(num) ? val : num;
      });
      return obj;
    });
  
    const categoryCol = columns[0];
    const valueColumns = columns.slice(1);
  
    const tooltipStyle = {
      backgroundColor: '#111520',
      border: '1px solid #1e2a40',
      borderRadius: '8px',
      color: '#e8edf5',
      fontSize: '12px'
    };
  
    if (chartType === 'line_chart') {
      return (
        <div style={{
          background: '#111520', border: '1px solid #1e2a40',
          borderRadius: '10px', padding: '16px', marginTop: '8px'
        }}>
          <div style={{
            fontSize: '11px', color: '#00d4ff',
            fontFamily: 'monospace', marginBottom: '12px'
          }}>
            📈 {columns.join(' · ')}
          </div>
          <ResponsiveContainer width="100%" height={240}>
            <LineChart data={data}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e2a40" />
              <XAxis dataKey={categoryCol}
                tick={{ fill: '#6b7a99', fontSize: 11 }}
                axisLine={{ stroke: '#1e2a40' }} />
              <YAxis
                tick={{ fill: '#6b7a99', fontSize: 11 }}
                axisLine={{ stroke: '#1e2a40' }} />
              <Tooltip contentStyle={tooltipStyle} />
              <Legend wrapperStyle={{ color: '#6b7a99', fontSize: 12 }} />
              {valueColumns.map((col, i) => (
                <Line key={col} type="monotone" dataKey={col}
                  stroke={COLORS[i % COLORS.length]}
                  strokeWidth={2} dot={{ r: 4 }} />
              ))}
            </LineChart>
          </ResponsiveContainer>
        </div>
      );
    }
  
    if (chartType === 'pie_chart') {
      const pieData = data.map(d => ({
        name: d[categoryCol],
        value: d[valueColumns[0]]
      }));
      return (
        <div style={{
          background: '#111520', border: '1px solid #1e2a40',
          borderRadius: '10px', padding: '16px', marginTop: '8px'
        }}>
          <div style={{
            fontSize: '11px', color: '#00d4ff',
            fontFamily: 'monospace', marginBottom: '12px'
          }}>
            🥧 {valueColumns[0]} Distribution
          </div>
          <ResponsiveContainer width="100%" height={240}>
            <PieChart>
              <Pie data={pieData} dataKey="value" nameKey="name"
                cx="50%" cy="50%" outerRadius={90} label>
                {pieData.map((_, i) => (
                  <Cell key={i} fill={COLORS[i % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip contentStyle={tooltipStyle} />
              <Legend wrapperStyle={{ color: '#6b7a99', fontSize: 12 }} />
            </PieChart>
          </ResponsiveContainer>
        </div>
      );
    }
  
    // Default — Bar chart
    return (
      <div style={{
        background: '#111520', border: '1px solid #1e2a40',
        borderRadius: '10px', padding: '16px', marginTop: '8px'
      }}>
        <div style={{
          fontSize: '11px', color: '#00d4ff',
          fontFamily: 'monospace', marginBottom: '12px'
        }}>
          📊 {columns.join(' · ')}
          {rows.length > 20 && (
            <span style={{ color: '#6b7a99' }}> (Top 20 shown)</span>
          )}
        </div>
        <ResponsiveContainer width="100%" height={240}>
          <BarChart data={data} margin={{ bottom: 40 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#1e2a40" />
            <XAxis dataKey={categoryCol}
              tick={{ fill: '#6b7a99', fontSize: 10 }}
              axisLine={{ stroke: '#1e2a40' }}
              angle={-35} textAnchor="end" interval={0} />
            <YAxis
              tick={{ fill: '#6b7a99', fontSize: 11 }}
              axisLine={{ stroke: '#1e2a40' }} />
            <Tooltip contentStyle={tooltipStyle} />
            <Legend wrapperStyle={{ color: '#6b7a99', fontSize: 12 }} />
            {valueColumns.map((col, i) => (
              <Bar key={col} dataKey={col}
                fill={COLORS[i % COLORS.length]}
                radius={[4, 4, 0, 0]} />
            ))}
          </BarChart>
        </ResponsiveContainer>
      </div>
    );
  }