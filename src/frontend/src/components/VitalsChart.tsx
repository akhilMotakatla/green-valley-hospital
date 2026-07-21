import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';

interface LineConfig {
  key: string;
  label: string;
  color: string;
  strokeDasharray?: string;
}

interface VitalsChartProps {
  data: Record<string, unknown>[];
  xKey: string;
  lines: LineConfig[];
  unit: string;
  title: string;
  ariaLabel: string;
}

export function VitalsChart({ data, xKey, lines, unit, title, ariaLabel }: VitalsChartProps) {
  if (data.length < 2) {
    return (
      <div className="card" style={{ textAlign: 'center', padding: '2rem' }}>
        <h4 style={{ marginBottom: '0.5rem' }}>{title}</h4>
        <p className="muted">Only one reading on record — minimum 2 readings required for trend display.</p>
      </div>
    );
  }

  return (
    <div className="card" style={{ paddingBottom: '1rem' }}>
      <h4 style={{ marginBottom: '1rem' }}>{title}</h4>
      <div role="img" aria-label={ariaLabel}>
        <ResponsiveContainer width="100%" height={220}>
          <LineChart data={data} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(0,0,0,0.08)" />
            <XAxis
              dataKey={xKey}
              tick={{ fontSize: 11 }}
              tickFormatter={(val: string) => val?.slice(0, 10)}
            />
            <YAxis
              tick={{ fontSize: 11 }}
              unit={unit ? ` ${unit}` : undefined}
            />
            <Tooltip
              formatter={(value: unknown, name: string) => [`${value} ${unit}`, name]}
            />
            <Legend />
            {lines.map((line) => (
              <Line
                key={line.key}
                type="monotone"
                dataKey={line.key}
                stroke={line.color}
                strokeDasharray={line.strokeDasharray}
                name={line.label}
                dot={{ r: 4 }}
                activeDot={{ r: 6 }}
              />
            ))}
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
