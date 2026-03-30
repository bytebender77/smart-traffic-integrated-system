import { useEffect, useMemo, useState } from 'react';
import { MapContainer, TileLayer, CircleMarker, Popup, Polyline } from 'react-leaflet';

const congestionColor = {
  low: '#b6ff3a',
  medium: '#ff9f1c',
  high: '#ff4d6d'
};

export default function TrafficMap({
  intersections = [],
  emergencyRoute = [],
  emergencyActive = false,
  emergencyType = null,
  selectedIntersection = '',
  roadNetwork = [],
  simulationMode = false
}) {
  if (!intersections.length) {
    return (
      <div className="glass rounded-2xl p-6 text-white/70">
        Loading intersection map...
      </div>
    );
  }

  const selectedNode = intersections.find(
    (intersection) => intersection.id === selectedIntersection
  );
  const center = selectedNode ? selectedNode.position : intersections[0].position;
  const bounds = useMemo(() => {
    if (!intersections.length) return null;
    const lats = intersections.map((i) => i.position[0]);
    const lons = intersections.map((i) => i.position[1]);
    const minLat = Math.min(...lats);
    const maxLat = Math.max(...lats);
    const minLon = Math.min(...lons);
    const maxLon = Math.max(...lons);
    return [
      [minLat, minLon],
      [maxLat, maxLon],
    ];
  }, [intersections]);
  const [animatedRoute, setAnimatedRoute] = useState([]);

  const routeKey = useMemo(() => emergencyRoute.join('|'), [emergencyRoute]);

  useEffect(() => {
    if (!emergencyActive || emergencyRoute.length === 0) {
      setAnimatedRoute([]);
      return undefined;
    }

    let index = 1;
    setAnimatedRoute(emergencyRoute.slice(0, 1));

    const interval = setInterval(() => {
      index += 1;
      setAnimatedRoute(emergencyRoute.slice(0, index));
      if (index >= emergencyRoute.length) {
        clearInterval(interval);
      }
    }, 600);

    return () => clearInterval(interval);
  }, [emergencyActive, routeKey, emergencyRoute]);

  const visibleRoute = emergencyActive && emergencyRoute.length ? animatedRoute : [];
  const visibleNodeSet = useMemo(() => new Set(visibleRoute), [visibleRoute]);
  const corridorLabel = emergencyType === 'fire' ? '🚒 Fire Corridor' : '🚑 Emergency Corridor';

  const routeEdgeKeys = useMemo(() => {
    if (!emergencyActive || emergencyRoute.length < 2) return new Set();
    const keys = new Set();
    for (let i = 0; i < emergencyRoute.length - 1; i += 1) {
      const a = emergencyRoute[i];
      const b = emergencyRoute[i + 1];
      if (!visibleNodeSet.has(a) || !visibleNodeSet.has(b)) continue;
      const key = [a, b].sort().join('|');
      keys.add(key);
    }
    return keys;
  }, [emergencyActive, emergencyRoute, visibleNodeSet]);

  return (
    <div className="glass relative rounded-2xl p-4">
      <div className="flex items-center justify-between pb-4">
        <div>
          <p className="card-title">Live City Map</p>
          <h3 className="text-lg font-semibold text-white">Intersection Congestion</h3>
        </div>
        <div className="flex flex-wrap gap-2">
          {simulationMode && (
            <span className="badge badge-info">Simulation Mode Active</span>
          )}
          {emergencyActive && (
            <span className="badge badge-danger">
              {emergencyType === 'fire' ? 'Fire Corridor Active' : 'Green Corridor Active'}
            </span>
          )}
        </div>
      </div>
      <div className="map-shell">
        <MapContainer
          center={center}
          zoom={14}
          bounds={bounds || undefined}
          scrollWheelZoom={false}
        >
          <TileLayer
            attribution="© OpenStreetMap contributors"
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />
          {roadNetwork.map((edge) => {
            const a = edge.from;
            const b = edge.to;
            const key = [a, b].sort().join('|');
            const coords = edge.coordinates || [];
            if (!coords.length) return null;

            const isOnCorridor = routeEdgeKeys.has(key);

            return (
              <Polyline
                key={`${a}-${b}`}
                positions={coords}
                pathOptions={{
                  color: isOnCorridor ? '#2de2e6' : 'rgba(148,163,184,0.35)',
                  weight: isOnCorridor ? 4 : 2,
                  opacity: isOnCorridor ? 0.95 : 1,
                }}
              />
            );
          })}

          {intersections.map((intersection) => {
            const congestion = intersection.congestion || 'medium';
            const isOnRoute = visibleRoute?.includes(intersection.id);
            const isSelected = intersection.id === selectedIntersection;
            const vc = intersection.vehicleCounts;
            const densityPct = intersection.densityPercent;
            const avgSpeed = intersection.avgSpeedKmph;
            const isMidNode = String(intersection.id || '').includes('_mid');
            const baseRadius = isMidNode ? 8 : 12;
            const routeRadius = isMidNode ? 12 : 16;
            const selectedRadius = 18;
            const fillColor = congestionColor[congestion] || congestionColor.medium;
            return (
              <CircleMarker
                key={intersection.id}
                center={intersection.position}
                radius={isSelected ? selectedRadius : isOnRoute ? routeRadius : baseRadius}
                pathOptions={{
                  // Use outline to indicate the emergency corridor,
                  // but keep marker fill as the true congestion state.
                  color: isSelected
                    ? '#ff3cac'
                    : isOnRoute
                      ? '#2de2e6'
                      : fillColor,
                  weight: isSelected ? 4 : isOnRoute ? 3 : 2,
                  fillColor: isSelected ? '#ff3cac' : fillColor,
                  fillOpacity: isSelected ? 0.95 : 0.85
                }}
              >
                <Popup>
                  <div className="text-xs text-midnight" style={{ minWidth: '120px' }}>
                    <p className="font-semibold" style={{ fontSize: '14px', marginBottom: '4px' }}>
                      Node {intersection.name}
                    </p>
                    <p>
                      Congestion:{' '}
                      <span style={{
                        fontWeight: 'bold',
                        color: congestion === 'high' ? '#ff4d6d' : congestion === 'medium' ? '#ff9f1c' : '#4ade80'
                      }}>
                        {congestion.toUpperCase()}
                      </span>
                    </p>
                    {densityPct !== undefined && (
                      <p>Density: {Math.round(densityPct)}%</p>
                    )}
                    {avgSpeed !== undefined && avgSpeed !== null && (
                      <p>Avg Speed: {Math.round(avgSpeed)} km/h</p>
                    )}
                    {vc && (
                      <div style={{ marginTop: '4px', borderTop: '1px solid #ddd', paddingTop: '4px' }}>
                        <p>🚗 Cars: {vc.cars}</p>
                        <p>🚌 Buses: {vc.buses}</p>
                        <p>🚛 Trucks: {vc.trucks}</p>
                        <p>🏍️ Motorcycles: {vc.motorcycles}</p>
                        <p style={{ fontWeight: 'bold', marginTop: '2px' }}>
                          Total: {vc.total_vehicles}
                        </p>
                      </div>
                    )}
                    {isSelected && <p style={{ marginTop: '4px', color: '#ff3cac' }}>📹 Assigned Feed</p>}
                    {isOnRoute && <p style={{ marginTop: '4px', color: '#2de2e6' }}>{corridorLabel}</p>}
                  </div>
                </Popup>
              </CircleMarker>
            );
          })}
        </MapContainer>
      </div>
    </div>
  );
}
