import { useEffect } from 'react';
import TrafficMap from '../components/TrafficMap.jsx';
import EmergencyAlert from '../components/EmergencyAlert.jsx';
import useTrafficStore from '../store/trafficStore.js';

export default function EmergencyMode() {
  const {
    emergencyStatus,
    intersectionData,
    roadNetwork,
    fetchIntersectionData,
    error,
    simulationMode
  } = useTrafficStore();

  useEffect(() => {
    fetchIntersectionData();
  }, [fetchIntersectionData]);

  return (
    <div className="mx-auto flex max-w-7xl flex-col gap-6">
      {emergencyStatus?.active && (
        <div className="rounded-2xl border border-neon-red/50 bg-neon-red/20 px-6 py-4 text-sm font-semibold uppercase tracking-[0.3em] text-neon-red">
          🚑 Emergency Mode Active – Priority Corridor Enabled
        </div>
      )}
      {error && (
        <div className="rounded-xl border border-neon-red/50 bg-neon-red/10 px-4 py-3 text-sm text-neon-red">
          {error}
        </div>
      )}
      <div className="grid gap-6 lg:grid-cols-[1.1fr_0.9fr]">
        <div className="glass rounded-2xl p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="card-title">Emergency Command</p>
              <h3 className="text-lg font-semibold text-white">Green Corridor</h3>
            </div>
            <span
              className={`badge ${
                emergencyStatus?.active ? 'badge-danger' : 'badge-success'
              }`}
            >
              {emergencyStatus?.active ? 'Priority Active' : 'Standby'}
            </span>
          </div>

          <div className="mt-6 rounded-xl border border-white/10 bg-white/5 p-4 text-sm text-white/70">
            Emergency corridor mode pre-emptively extends green phases along
            the fastest route and coordinates adjacent intersections.
          </div>
        </div>

        <EmergencyAlert emergencyStatus={emergencyStatus} />
      </div>

      <TrafficMap
        intersections={intersectionData}
        roadNetwork={roadNetwork}
        emergencyRoute={emergencyStatus?.route}
        emergencyActive={emergencyStatus?.active}
        simulationMode={simulationMode}
      />
    </div>
  );
}
