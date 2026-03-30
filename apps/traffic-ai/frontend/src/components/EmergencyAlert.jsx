import useTrafficStore from '../store/trafficStore.js';

export default function EmergencyAlert({ emergencyStatus }) {
  const {
    triggerEmergencyRoute,
    clearEmergencyRoute,
    selectedIntersection,
    loading
  } = useTrafficStore();
  const isActive = emergencyStatus?.active;
  const route = emergencyStatus?.route || [];
  const etaSeconds = emergencyStatus?.etaSeconds;
  const totalDistance = emergencyStatus?.totalDistance;
  const vehicleType = emergencyStatus?.vehicleType;
  const typeLabel = vehicleType === 'fire' ? 'Fire service' : 'Ambulance';
  const typeIcon = vehicleType === 'fire' ? '🚒' : '🚑';

  const handleTrigger = (type) => {
    triggerEmergencyRoute(selectedIntersection || 'A', 'Hospital', type);
  };

  const handleClear = () => {
    clearEmergencyRoute();
  };

  return (
    <div className="glass rounded-2xl p-6">
      <div className="flex items-center justify-between">
        <div>
          <p className="card-title">Emergency Channel</p>
          <h3 className="text-lg font-semibold text-white">Priority Alerts</h3>
        </div>
        <div className="flex flex-col items-end gap-2">
          <span className={`badge ${isActive ? 'badge-danger' : 'badge-success'}`}>
            {isActive ? 'Emergency Active' : 'All Clear'}
          </span>
          <span className="badge badge-warning">Prototype Detection (Ambulance)</span>
        </div>
      </div>

      <div className="mt-5 space-y-4">
        <div className="rounded-xl border border-white/10 bg-white/5 p-4">
          <p className="text-xs uppercase tracking-[0.3em] text-white/50">Status</p>
          <h4 className="mt-2 text-lg font-semibold text-white">
            {isActive ? `${typeIcon} ${typeLabel} detected` : 'No emergency vehicle detected'}
          </h4>
          <p className="mt-2 text-sm text-white/70">
            {emergencyStatus?.message || 'Awaiting emergency scan...'}
          </p>
          <p className="mt-2 text-xs text-white/50">
            Fire service is simulated for demo (manual trigger).
          </p>
          <div className="mt-3 flex flex-wrap gap-3 text-xs uppercase tracking-[0.2em] text-white/50">
            <span>Source: {selectedIntersection || 'A'}</span>
            <span>Destination: Hospital</span>
            {etaSeconds !== undefined && (
              <span>ETA: {Math.round(etaSeconds)}s</span>
            )}
            {totalDistance !== undefined && (
              <span>Distance: {Math.round(totalDistance)}m</span>
            )}
          </div>
          <div className="mt-4 flex flex-wrap gap-3">
            <button
              type="button"
              onClick={() => handleTrigger('ambulance')}
              disabled={loading}
              className="rounded-full border border-neon-red/60 bg-neon-red/10 px-4 py-2 text-xs font-semibold uppercase tracking-[0.3em] text-neon-red transition hover:bg-neon-red/20 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {loading ? 'Activating…' : 'Trigger Ambulance'}
            </button>
            <button
              type="button"
              onClick={() => handleTrigger('fire')}
              disabled={loading}
              className="rounded-full border border-neon-amber/60 bg-neon-amber/10 px-4 py-2 text-xs font-semibold uppercase tracking-[0.3em] text-neon-amber transition hover:bg-neon-amber/20 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {loading ? 'Activating…' : 'Trigger Fire Service'}
            </button>
            {isActive && (
              <button
                type="button"
                onClick={handleClear}
                disabled={loading}
                className="rounded-full border border-white/10 bg-white/5 px-4 py-2 text-xs font-semibold uppercase tracking-[0.3em] text-white/70 transition hover:bg-white/10 disabled:cursor-not-allowed disabled:opacity-50"
              >
                Clear Emergency
              </button>
            )}
          </div>
        </div>

        {isActive && (
          <div className="rounded-xl border border-white/10 bg-abyss/70 p-4">
            <p className="card-title">Green Corridor Route</p>
            <div className="mt-3 flex flex-wrap gap-2">
              {route.map((node) => (
                <span
                  key={node}
                  className="rounded-full border border-neon-cyan/40 bg-neon-cyan/10 px-3 py-1 text-xs font-semibold uppercase tracking-widest text-neon-cyan"
                >
                  {node}
                </span>
              ))}
            </div>
            <p className="mt-3 text-sm text-white/60">
              Corridor intersections are highlighted on the map in cyan.
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
