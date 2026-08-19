import React from 'react';
import { Download, Info } from 'lucide-react';
import { 
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  Tooltip, 
  ResponsiveContainer,
  Cell,
  LabelList,
  CartesianGrid
} from 'recharts';

const formatLkrCurrency = (value) => {
  if (value === null || value === undefined || value === '') return value;
  const numericValue = Number(value);
  if (Number.isNaN(numericValue)) return value;

  return new Intl.NumberFormat('en-LK', {
    style: 'currency',
    currency: 'LKR',
    maximumFractionDigits: 0,
  }).format(numericValue).replace('LKR', 'Rs. ');
};

const formatCompactCurrency = (value) => {
  const numericValue = Number(value);
  if (!Number.isFinite(numericValue)) return value;

  const formatter = new Intl.NumberFormat('en-LK', {
    notation: 'compact',
    maximumFractionDigits: 1,
    style: 'currency',
    currency: 'LKR',
  });

  return formatter.format(numericValue).replace('LKR', 'Rs.');
};

const isMoneyColumn = (columnName = '') => {
  const column = columnName.toLowerCase();
  // Quantity/count columns are NOT money
  if (/(?:quantity|qty|count|units|number)/.test(column)) {
    return false;
  }
  return /(?:revenue|sales|amount|price|profit|cost|total|value|spend|earn|income)/.test(column);
};

export default function VisualizationComponents({ resultJson, sql, question, onExportCSV, theme }) {
  let columns = [];
  let rows = [];
  try {
    const data = JSON.parse(resultJson);
    columns = data.columns || [];
    rows = data.rows || [];
  } catch (err) {
    console.error('Error parsing resultJson:', err);
    return null;
  }

  if (columns.length === 0 || rows.length === 0) return null;

  // Format Recharts-compatible data
  const chartData = rows.map((row) => {
    let item = {};
    columns.forEach((col, cIdx) => {
      const rawValue = row[cIdx];
      if (typeof rawValue === 'number') {
        item[col] = rawValue;
      } else {
        const num = Number(rawValue);
        item[col] = Number.isNaN(num) ? rawValue : num;
      }
    });
    return item;
  });

  // Smartly identify X and Y axis keys
  // xKey is always the first column (grouped entity name / product name)
  let xKey = columns[0];
  let yKey = columns[columns.length - 1];

  // Find all numeric columns for Y Axis selection
  let numericColumns = [];
  columns.forEach((col, idx) => {
    const sampleVal = rows[0][idx];
    if (typeof sampleVal === 'number' || !Number.isNaN(Number(sampleVal))) {
      numericColumns.push({ col, idx });
    }
  });

  if (numericColumns.length > 0) {
    const lastNumCol = numericColumns[numericColumns.length - 1];
    // Check if the default column is all zeroes
    const allZero = rows.every(row => {
      const val = Number(row[lastNumCol.idx]);
      return val === 0 || Number.isNaN(val);
    });
    
    if (allZero && numericColumns.length > 1) {
      // Fallback to the previous numeric column (e.g., total_revenue) which has values
      yKey = numericColumns[numericColumns.length - 2].col;
    } else {
      yKey = lastNumCol.col;
    }
  }

  const yIdx = columns.indexOf(yKey);
  const isNumeric = yIdx !== -1;
  const moneyYAxis = isMoneyColumn(yKey);

  // Gradient colors for Recharts
  const COLORS = ['#38bdf8', '#818cf8', '#a78bfa', '#f472b6', '#34d399', '#fbbf24'];

  const rowsFetched = rows.length;
  const statusLabel = rowsFetched > 0 ? "SUCCESS" : "EMPTY";

  return (
    <div style={{ width: '100%', display: 'flex', flexDirection: 'column', gap: '16px', marginTop: '16px' }}>
      
      {/* 4 Metadata Metrics Cards */}
      <div className="metrics-row" style={{ margin: 0 }}>
        <div className="metric-card">
          <div className="metric-card-val" style={{ color: 'var(--accent-cyan)' }}>{rowsFetched}</div>
          <div className="metric-card-lbl">Rows Fetched</div>
        </div>
        <div className="metric-card">
          <div className="metric-card-val" style={{ color: '#818cf8' }}>Groq 70B</div>
          <div className="metric-card-lbl">Agent Engine</div>
        </div>
        <div className="metric-card">
          <div className="metric-card-val" style={{ color: '#34d399' }}>{statusLabel}</div>
          <div className="metric-card-lbl">Agent Status</div>
        </div>
        <div className="metric-card">
          <div className="metric-card-val" style={{ color: '#f472b6' }}>ACTIVE</div>
          <div className="metric-card-lbl">Guardrails</div>
        </div>
      </div>

      <div className="results-columns">
        
        {/* Left Column: Data Grid table */}
        <div className="result-card-panel">
          <div className="panel-header">
            <span>📋 Raw Query Results</span>
            <button 
              className="csv-export-btn"
              onClick={() => onExportCSV(question, sql, columns, rows)}
            >
              <Download size={13} />
              Export CSV
            </button>
          </div>
          <div className="table-wrapper">
            <table className="data-table">
              <thead>
                <tr>
                  {columns.map((col, idx) => <th key={idx}>{col}</th>)}
                </tr>
              </thead>
              <tbody>
                {rows.map((row, rIdx) => (
                  <tr key={rIdx}>
                    {row.map((val, cIdx) => {
                      const columnName = columns[cIdx] || '';
                      const isMoney = isMoneyColumn(columnName);
                      const displayValue = val !== null && val !== undefined 
                        ? (isMoney && typeof val === 'number' ? formatLkrCurrency(val) : String(val)) 
                        : 'NULL';
                      return <td key={cIdx}>{displayValue}</td>;
                    })}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Right Column: Dynamic Recharts bar graph */}
        <div className="result-card-panel">
          <div className="panel-header">
            <span>📊 Interactive Visualization</span>
          </div>
          <div style={{ width: '100%', height: 240, position: 'relative' }}>
            {isNumeric ? (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={chartData} margin={{ top: 20, right: 10, left: 4, bottom: 8 }} barCategoryGap="20%">
                  <CartesianGrid 
                    strokeDasharray="3 3" 
                    vertical={false} 
                    stroke={theme === 'dark' ? 'rgba(255,255,255,0.06)' : 'rgba(0,0,0,0.06)'} 
                  />
                  <XAxis 
                    dataKey={xKey} 
                    stroke={theme === 'dark' ? '#94a3b8' : '#64748b'} 
                    fontSize={11} 
                    tickLine={false} 
                    axisLine={false}
                    dy={8}
                  />
                  <YAxis 
                    stroke={theme === 'dark' ? '#94a3b8' : '#64748b'} 
                    fontSize={11} 
                    tickLine={false} 
                    axisLine={false}
                    tickFormatter={moneyYAxis ? formatCompactCurrency : (value) => value}
                  />
                  <Tooltip 
                    formatter={(value) => [moneyYAxis ? formatLkrCurrency(value) : value, yKey]}
                    labelFormatter={(label) => `${label}`}
                    contentStyle={{ 
                      backgroundColor: theme === 'dark' ? '#1d212a' : '#ffffff', 
                      border: `1px solid ${theme === 'dark' ? '#262c36' : '#cbd5e1'}`, 
                      borderRadius: '8px', 
                      color: theme === 'dark' ? '#f1f5f9' : '#0f172a', 
                      fontSize: '12px' 
                    }}
                    itemStyle={{ color: '#38bdf8' }}
                  />
                  <Bar dataKey={yKey} radius={[6, 6, 0, 0]} maxBarSize={52}>
                    {chartData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                    <LabelList 
                      dataKey={yKey} 
                      position="top" 
                      fill={theme === 'dark' ? '#f1f5f9' : '#0f172a'} 
                      fontSize={10} 
                      offset={8} 
                      formatter={moneyYAxis ? (value) => formatCompactCurrency(value) : (value) => value}
                    />
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <div style={{ color: 'var(--text-muted)', fontSize: '13px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Info size={16} />
                No numeric chart available for this result structure.
              </div>
            )}
          </div>
        </div>

      </div>
    </div>
  );
}
