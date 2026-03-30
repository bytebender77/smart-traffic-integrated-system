import { useState } from 'react';
import useTrafficStore from '../store/trafficStore.js';
import { getLaneLabel } from '../data/laneOptions.js';

export default function LiveFeedMonitor() {
  const {
    streamUrl,
    streamSource,
    selectedIntersection,
    selectedLane,
    clearLiveSource,
    clearStreamInfo
  } = useTrafficStore();
  const [collapsed, setCollapsed] = useState(false);

  if (!streamUrl) return null;

  const handleStop = () => {
    clearLiveSource();
    clearStreamInfo();
  };

  return (
    <section className="glass rounded-2xl p-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <p className="card-title">Live Monitor</p>
          <h3 className="text-lg font-semibold text-white">Vehicle Detection Stream</h3>
          <div className="mt-2 flex flex-wrap gap-3 text-xs uppercase tracking-[0.2em] text-white/40">
            <span>Intersection: {selectedIntersection || '--'}</span>
            <span>Lane: {getLaneLabel(selectedLane)}</span>
          </div>
        </div>
        <div className="flex flex-wrap gap-3">
          <button
            type="button"
            onClick={() => setCollapsed((prev) => !prev)}
            className="rounded-full border border-white/10 bg-white/5 px-4 py-2 text-xs font-semibold uppercase tracking-[0.3em] text-white/70 transition hover:bg-white/10"
          >
            {collapsed ? 'Show Preview' : 'Hide Preview'}
          </button>
          <button
            type="button"
            onClick={handleStop}
            className="rounded-full border border-neon-red/50 bg-neon-red/10 px-4 py-2 text-xs font-semibold uppercase tracking-[0.3em] text-neon-red transition hover:bg-neon-red/20"
          >
            Stop Stream
          </button>
        </div>
      </div>

      <div className="mt-3 text-xs uppercase tracking-[0.3em] text-white/40">
        Source: {streamSource || 'Unknown'}
      </div>

      {!collapsed && (
        <div className="mt-4 overflow-hidden rounded-2xl border border-white/10 bg-abyss/70">
          <div className="flex h-56 items-center justify-center bg-black/40 sm:h-72 md:h-80">
            <img
              src={streamUrl}
              alt="Live vehicle detection stream"
              className="h-full w-full object-contain"
            />
          </div>
        </div>
      )}
    </section>
  );
}
