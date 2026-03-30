import { useEffect } from 'react';
import TrafficMap from '../components/TrafficMap.jsx';
import useTrafficStore from '../store/trafficStore.js';

const densityBadge = {
  low: 'badge badge-success',
  medium: 'badge badge-warning',
  high: 'badge badge-danger'
};

export default function Intersections() {
  const {
    intersectionData,
    emergencyStatus,
    roadNetwork,
    fetchIntersectionData,
    error,
    simulationMode
  } = useTrafficStore();

  useEffect(() => {
    fetchIntersectionData();
  }, [fetchIntersectionData]);

  return (
    <div className="mx-auto grid max-w-7xl gap-6 lg:grid-cols-[0.85fr_1.15fr]">
      {error && (
        <div className="col-span-full rounded-xl border border-neon-red/50 bg-neon-red/10 px-4 py-3 text-sm text-neon-red">
          {error}
        </div>
      )}
      <div className="glass rounded-2xl p-6">
        <div className="flex items-center justify-between">
          <div>
            <p className="card-title">Intersection Grid</p>
            <h3 className="text-lg font-semibold text-white">Priority Nodes</h3>
          </div>
          <span className="badge badge-success">{intersectionData.length} Nodes</span>
        </div>

        <div className="mt-5 space-y-4">
          {intersectionData.map((intersection) => (
            <div
              key={intersection.id}
              className="rounded-xl border border-white/10 bg-abyss/70 px-4 py-3"
            >
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-semibold text-white">
                    {intersection.name}
                  </p>
                  <p className="text-xs text-white/50">{intersection.id}</p>
                </div>
                <span className={densityBadge[intersection.congestion] || densityBadge.medium}>
                  {intersection.congestion}
                </span>
              </div>
            </div>
          ))}
        </div>
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
