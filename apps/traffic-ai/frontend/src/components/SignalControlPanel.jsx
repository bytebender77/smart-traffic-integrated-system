import { laneOptions, getLaneLabel } from '../data/laneOptions.js';

const laneLabels = laneOptions.map((lane) => lane.id);

const congestionBadge = {
  LOW: 'badge badge-success',
  MEDIUM: 'badge badge-warning',
  HIGH: 'badge badge-danger',
  SEVERE: 'badge badge-danger'
};

export default function SignalControlPanel({ signalPlan, loading, intersections = [] }) {
  if (loading && !signalPlan) {
    return (
      <div className="glass rounded-2xl p-6 text-white/70">
        Loading signal optimization...
      </div>
    );
  }

  const signals = signalPlan?.signals || {};
  const intersectionById = intersections.reduce((acc, node) => {
    acc[node.id] = node;
    return acc;
  }, {});

  return (
    <div className="glass rounded-2xl p-6">
      <div className="flex items-center justify-between">
        <div>
          <p className="card-title">Signal Control</p>
          <h3 className="text-lg font-semibold text-white">Optimized Green Times</h3>
        </div>
        <div className="flex flex-col items-end gap-2">
          <span className="badge badge-success">Cycle {signalPlan?.cycle_time ?? '--'}s</span>
          {loading && (
            <span className="badge badge-warning">Updating…</span>
          )}
        </div>
      </div>

      <div className="mt-6 space-y-4">
        {laneLabels.map((lane) => {
          const laneSignal = signals[lane];
          const congestion = laneSignal?.congestion_level || 'MEDIUM';
          const nodeId = lane.replace('lane_', '');
          const nodeData = intersectionById[nodeId];
          const densityPct = laneSignal?.density_percent ?? nodeData?.densityPercent;
          const speedKmph = laneSignal?.speed_kmph ?? nodeData?.avgSpeedKmph;
          const effectiveDensity = laneSignal?.effective_density;
          const totalVehicles = nodeData?.vehicleCounts?.total_vehicles;
          return (
            <div key={lane} className="flex items-center justify-between">
              <div>
                <p className="text-sm font-semibold text-white">
                  {getLaneLabel(lane)}
                </p>
                <span className={congestionBadge[congestion] || 'badge badge-warning'}>
                  {congestion}
                </span>
                <p className="mt-2 text-xs text-white/50">
                  {totalVehicles !== undefined ? `${totalVehicles} vehicles · ` : ''}
                  Density {densityPct !== undefined ? `${Math.round(densityPct)}%` : '--'}
                  {speedKmph !== undefined && speedKmph !== null ? ` · Speed ${Math.round(speedKmph)} km/h` : ''}
                  {effectiveDensity !== undefined && effectiveDensity !== null ? ` · Pressure ${Math.round(effectiveDensity)}%` : ''}
                  {' '}→ Green {laneSignal?.green_time ?? '--'}s
                </p>
              </div>
              <div className="text-right">
                <p className="text-2xl font-semibold text-neon-cyan">
                  {laneSignal?.green_time ?? '--'}s
                </p>
                <p className="text-xs uppercase tracking-[0.3em] text-white/40">
                  Green Time
                </p>
              </div>
            </div>
          );
        })}
      </div>

      <div className="mt-6 rounded-xl border border-white/10 bg-white/5 p-4">
        <p className="text-xs uppercase tracking-[0.3em] text-white/50">AI Notes</p>
        <p className="mt-2 text-sm text-white/70">
          Speed-weighted adaptive signal control (density × slowdown).
        </p>
      </div>
    </div>
  );
}
