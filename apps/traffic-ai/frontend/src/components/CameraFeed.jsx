import useTrafficStore from '../store/trafficStore.js';
import { getTrafficStreamUrl } from '../services/api.js';

export default function CameraFeed() {
  const { streamUrl, liveSource } = useTrafficStore();
  const derivedStreamUrl = streamUrl || (liveSource ? getTrafficStreamUrl(liveSource, { frame_skip: 2 }) : '');
  const hasStream = Boolean(derivedStreamUrl);

  return (
    <div className="glass rounded-2xl p-6">
      <div className="flex items-center justify-between">
        <div>
          <p className="card-title">Camera Feed</p>
          <h3 className="text-lg font-semibold text-white">Intersection Vision</h3>
        </div>
        <span className={`badge ${hasStream ? 'badge-success' : 'badge-warning'}`}>
          {hasStream ? 'Live MJPEG Stream' : 'No Live Feed'}
        </span>
      </div>

      <div className="relative mt-4 h-64 overflow-hidden rounded-xl border border-white/10 bg-abyss">
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_top,rgba(45,226,230,0.2),transparent_55%)]" />
        <div className="absolute inset-0 bg-[linear-gradient(135deg,rgba(255,255,255,0.04)_25%,transparent_25%,transparent_50%,rgba(255,255,255,0.04)_50%,rgba(255,255,255,0.04)_75%,transparent_75%,transparent)] bg-[length:18px_18px] opacity-20" />
        <div className="absolute left-6 top-5 rounded-full border border-neon-cyan/40 bg-neon-cyan/10 px-3 py-1 text-xs uppercase tracking-[0.3em] text-neon-cyan">
          Cam 07 · Sector B
        </div>

        {hasStream ? (
          <img
            src={derivedStreamUrl}
            alt="Live vehicle detection stream"
            className="absolute inset-0 h-full w-full object-contain"
          />
        ) : (
          <div className="absolute inset-0 flex items-center justify-center text-sm text-white/60">
            Start a live feed or video stream to view real detections.
          </div>
        )}

        <div className="absolute bottom-5 right-6 rounded-full bg-white/10 px-3 py-1 text-xs uppercase tracking-[0.3em] text-white/70">
          YOLOv8 Vision
        </div>
      </div>

      <p className="mt-4 text-sm text-white/60">
        This panel mirrors the same annotated MJPEG feed used by the dashboard.
        Connect RTSP cameras, a USB webcam, or upload clips to refresh the stream in real time.
      </p>
    </div>
  );
}
