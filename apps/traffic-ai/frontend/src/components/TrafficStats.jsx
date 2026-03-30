import {
  Bar,
  BarChart,
  Cell,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis
} from 'recharts';

const palette = ['#2de2e6', '#ff3cac', '#b6ff3a', '#ff9f1c', '#ff4d6d'];

export default function TrafficStats({ vehicleCounts, loading }) {
  const hasData = vehicleCounts && Object.values(vehicleCounts).some((value) => value > 0);

  if (loading && !hasData) {
    return (
      <div className="glass rounded-2xl p-6 text-white/70">
        Syncing vehicle telemetry...
      </div>
    );
  }

  const stats = [
    { label: 'Total Vehicles', value: vehicleCounts.total_vehicles, accent: 'text-neon-cyan' },
    { label: 'Cars', value: vehicleCounts.cars, accent: 'text-neon-lime' },
    { label: 'Buses', value: vehicleCounts.buses, accent: 'text-neon-amber' },
    { label: 'Trucks', value: vehicleCounts.trucks, accent: 'text-neon-magenta' },
    { label: 'Motorcycles', value: vehicleCounts.motorcycles, accent: 'text-neon-red' }
  ];

  const chartData = stats.slice(1).map((item) => ({
    name: item.label,
    value: item.value
  }));

  return (
    <section className="space-y-6">
      <div className="grid gap-4 lg:grid-cols-5">
        {stats.map((stat) => (
          <div key={stat.label} className="glass rounded-2xl p-5 shadow-glow">
            <p className="card-title">{stat.label}</p>
            <p className={`stat-value ${stat.accent}`}>{stat.value}</p>
          </div>
        ))}
      </div>

      <div className="glass rounded-2xl p-6">
        <div className="flex items-center justify-between">
          <div>
            <p className="card-title">Vehicle Mix</p>
            <h3 className="text-lg font-semibold text-white">Category Breakdown</h3>
          </div>
          <span className="badge badge-success">
            {loading ? 'Updating…' : 'Live Telemetry'}
          </span>
        </div>
        <div className="mt-4 h-56">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={chartData}>
              <XAxis dataKey="name" stroke="#5c6b8a" fontSize={12} />
              <YAxis stroke="#5c6b8a" fontSize={12} />
              <Tooltip
                contentStyle={{
                  background: '#0a1222',
                  border: '1px solid rgba(255,255,255,0.1)',
                  borderRadius: '12px',
                  fontSize: '12px'
                }}
              />
              <Bar dataKey="value" radius={[8, 8, 0, 0]}>
                {chartData.map((entry, index) => (
                  <Cell key={entry.name} fill={palette[index % palette.length]} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </section>
  );
}
