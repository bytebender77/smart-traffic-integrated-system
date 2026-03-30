import { useEffect, useMemo } from 'react';
import TrafficStats from '../components/TrafficStats.jsx';
import TrafficMap from '../components/TrafficMap.jsx';
import SignalControlPanel from '../components/SignalControlPanel.jsx';
import EmergencyAlert from '../components/EmergencyAlert.jsx';
import CameraFeed from '../components/CameraFeed.jsx';
import VideoUploadPanel from '../components/VideoUploadPanel.jsx';
import useTrafficStore from '../store/trafficStore.js';

const getSourceLabel = (source) => {
  if (!source) return 'No Feed Connected';
  if (source.startsWith('camera:') || /^[0-9]+$/.test(source)) {
    return 'USB Camera';
  }
  if (source.startsWith('rtsp://')) return 'RTSP Stream';
  if (source.startsWith('http://') || source.startsWith('https://')) return 'HTTP Stream';
  return 'Video File';
};

export default function Dashboard() {
  const {
    loading,
    error,
    statusMessage,
    liveSource,
    selectedIntersection,
    vehicleCounts,
    signalPlan,
    emergencyStatus,
    intersectionData,
    roadNetwork,
    systemStatus,
    lastUpdated,
    simulationMode,
    fetchSystemStatus,
    fetchIntersectionData,
    fetchTrafficData,
    fetchSimulationData
  } = useTrafficStore();

  const envVideoPath = useMemo(
    () => import.meta.env.VITE_TRAFFIC_VIDEO_PATH || '',
    []
  );

  const videoPath = liveSource || envVideoPath;
  const sourceLabel = getSourceLabel(videoPath);

  // Determine feed mode label and badge class
  const isSimMode = simulationMode && !videoPath;
  const feedModeLabel = isSimMode
    ? '🎲 Simulation Mode'
    : videoPath
      ? 'Live Feed Active'
      : 'Awaiting Feed';
  const feedModeClass = isSimMode
    ? 'badge-info'
    : videoPath
      ? 'badge-success'
      : 'badge-warning';

  useEffect(() => {
    fetchSystemStatus();
    fetchIntersectionData();

    if (videoPath) {
      // Real video feed mode
      fetchTrafficData({ videoPath });
      const interval = setInterval(() => {
        fetchTrafficData({ videoPath });
      }, 5000);
      return () => clearInterval(interval);
    } else {
      // Simulation mode — fetch simulated data every 5 seconds
      fetchSimulationData();
      const interval = setInterval(() => {
        fetchSimulationData();
      }, 5000);
      return () => clearInterval(interval);
    }
  }, [fetchIntersectionData, fetchSystemStatus, fetchTrafficData, fetchSimulationData, videoPath]);

  const emergencyType = emergencyStatus?.vehicleType;
  const emergencyIcon = emergencyType === 'fire' ? '🚒' : '🚑';
  const emergencyLabel = emergencyType === 'fire' ? 'Fire Service' : 'Ambulance';

  return (
    <div className="mx-auto flex max-w-7xl flex-col gap-8">
      {emergencyStatus?.active && (
        <div className="rounded-2xl border border-neon-red/50 bg-neon-red/20 px-6 py-4 text-sm font-semibold uppercase tracking-[0.3em] text-neon-red">
          {emergencyIcon} {emergencyLabel} Mode Active – Priority Corridor Enabled
        </div>
      )}

      <VideoUploadPanel />

      {error && (
        <div className="rounded-xl border border-neon-red/50 bg-neon-red/10 px-4 py-3 text-sm text-neon-red">
          {error}
        </div>
      )}

      {!error && statusMessage && (
        <div className="rounded-xl border border-neon-cyan/40 bg-neon-cyan/5 px-4 py-3 text-sm text-neon-cyan">
          {statusMessage}
        </div>
      )}

      <div className="glass rounded-2xl p-5 text-sm text-white/70">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <p className="card-title">System Status</p>
            <p className="text-lg font-semibold text-white">
              {systemStatus?.traffic_state || 'Coordinating...'}
            </p>
            <div className="mt-2 flex flex-wrap gap-2">
              <span className={`badge ${feedModeClass}`}>{feedModeLabel}</span>
              {isSimMode ? (
                <span className="badge badge-info">Dynamic Simulation</span>
              ) : (
                <span className="badge badge-warning">{sourceLabel}</span>
              )}
            </div>
          </div>
          <div className="flex flex-wrap gap-4 text-xs uppercase tracking-[0.3em] text-white/40">
            <span>Active Intersections: {systemStatus?.active_intersections ?? '--'}</span>
            <span>Emergency Mode: {systemStatus?.emergency_mode ? 'ON' : 'OFF'}</span>
            <span>
              Last Updated: {lastUpdated ? new Date(lastUpdated).toLocaleTimeString() : '--'}
            </span>
          </div>
        </div>
      </div>

      <TrafficStats vehicleCounts={vehicleCounts} loading={loading} />

      <div className="grid gap-6 xl:grid-cols-[1.4fr_0.9fr]">
        <TrafficMap
          intersections={intersectionData}
          roadNetwork={roadNetwork}
          emergencyRoute={emergencyStatus?.route}
          emergencyActive={emergencyStatus?.active}
          emergencyType={emergencyType}
          selectedIntersection={selectedIntersection}
          simulationMode={simulationMode}
        />
        <div className="space-y-6">
          <SignalControlPanel
            signalPlan={signalPlan}
            loading={loading}
            intersections={intersectionData}
          />
          <EmergencyAlert emergencyStatus={emergencyStatus} />
        </div>
      </div>

      <CameraFeed />
    </div>
  );
}
