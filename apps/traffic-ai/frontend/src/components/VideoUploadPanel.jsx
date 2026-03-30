import { useEffect, useMemo, useState } from 'react';
import useTrafficStore from '../store/trafficStore.js';
import { uploadTrafficVideo, getTrafficStreamUrl } from '../services/api.js';
import { laneOptions, getLaneLabel } from '../data/laneOptions.js';

export default function VideoUploadPanel() {
  const {
    processVideoFile,
    processVideoForNode,
    processEmergencyForNode,
    loading,
    setLiveSource,
    clearLiveSource,
    intersectionData,
    selectedIntersection,
    selectedLane,
    setSelectedIntersection,
    setSelectedLane,
    streamUrl,
    streamSource,
    setStreamInfo,
    clearStreamInfo
  } = useTrafficStore();
  const [file, setFile] = useState(null);
  const [localError, setLocalError] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [feedUrl, setFeedUrl] = useState('');

  const intersections = useMemo(
    () => intersectionData || [],
    [intersectionData]
  );

  useEffect(() => {
    if (!selectedIntersection && intersections.length) {
      setSelectedIntersection(intersections[0].id);
    }
  }, [intersections, selectedIntersection, setSelectedIntersection]);

  const handleFileChange = (event) => {
    const selected = event.target.files?.[0] || null;
    setFile(selected);
    setLocalError(null);
  };

  const handleDetectForNode = async () => {
    if (!file) {
      setLocalError('Please choose a video file first.');
      return;
    }
    if (!selectedIntersection) {
      setLocalError('Please select an intersection node first.');
      return;
    }
    setLocalError(null);
    await processVideoForNode(file, selectedIntersection);
  };

  const handleEmergencyCheck = async () => {
    if (!file) {
      setLocalError('Please choose a video file first.');
      return;
    }
    if (!selectedIntersection) {
      setLocalError('Please select an intersection node first.');
      return;
    }
    setLocalError(null);
    await processEmergencyForNode(file, selectedIntersection, 'Hospital');
  };

  const handleProcess = async () => {
    if (!file) {
      setLocalError('Please choose a video file first.');
      return;
    }
    setLocalError(null);
    await processVideoFile(file);
  };

  const handleStartStream = async () => {
    if (!file) {
      setLocalError('Please choose a video file first.');
      return;
    }
    setLocalError(null);
    setUploading(true);
    try {
      const { path } = await uploadTrafficVideo(file);
      const url = getTrafficStreamUrl(path, { frame_skip: 2 });
      setStreamInfo({ streamUrl: url, streamSource: path });
      setLiveSource(path);
    } catch (err) {
      setLocalError(err?.response?.data?.detail || err.message);
    } finally {
      setUploading(false);
    }
  };

  const handleStartLiveFeed = () => {
    const trimmed = feedUrl.trim();
    if (!trimmed) {
      setLocalError('Enter an RTSP/HTTP URL or camera:0 to start a live feed.');
      return;
    }
    setLocalError(null);
    const url = getTrafficStreamUrl(trimmed, { frame_skip: 2 });
    setStreamInfo({ streamUrl: url, streamSource: trimmed });
    setLiveSource(trimmed);
  };

  const handleStopStream = () => {
    clearLiveSource();
    clearStreamInfo();
  };

  return (
    <section className="glass rounded-2xl p-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <p className="card-title">Live Feed Control</p>
          <h2 className="text-xl font-semibold text-white">Connect a Camera or Clip</h2>
          <p className="mt-2 text-sm text-white/60">
            Upload a video for a specific node to detect vehicles. Other nodes use simulated data.
            Upload an ambulance video to trigger a green corridor. Fire service is simulated (manual trigger).
          </p>
          <div className="mt-4 flex flex-wrap gap-3 text-xs uppercase tracking-[0.2em] text-white/40">
            <span>Node: <strong className="text-neon-cyan">{selectedIntersection || 'Select below'}</strong></span>
            <span>Lane: {getLaneLabel(selectedLane)}</span>
          </div>
        </div>
        <div className="flex flex-wrap gap-3">
          {/* Primary: Detect vehicles at selected node */}
          <button
            type="button"
            onClick={handleDetectForNode}
            disabled={loading}
            className="rounded-full border border-neon-lime/50 bg-neon-lime/10 px-6 py-3 text-xs font-semibold uppercase tracking-[0.3em] text-neon-lime transition hover:bg-neon-lime/20 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {loading ? 'Detecting...' : '🚗 Detect at Node'}
          </button>
          {/* Emergency: Check for ambulance at selected node */}
          <button
            type="button"
            onClick={handleEmergencyCheck}
            disabled={loading}
            className="rounded-full border border-neon-red/50 bg-neon-red/10 px-6 py-3 text-xs font-semibold uppercase tracking-[0.3em] text-neon-red transition hover:bg-neon-red/20 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {loading ? 'Checking...' : '🚑 Ambulance Check'}
          </button>
          <button
            type="button"
            onClick={handleStartLiveFeed}
            disabled={loading}
            className="rounded-full border border-neon-cyan/50 bg-neon-cyan/10 px-6 py-3 text-xs font-semibold uppercase tracking-[0.3em] text-neon-cyan transition hover:bg-neon-cyan/20 disabled:cursor-not-allowed disabled:opacity-50"
          >
            Start Live Feed
          </button>
          <button
            type="button"
            onClick={handleStartStream}
            disabled={uploading || loading}
            className="rounded-full border border-neon-cyan/50 bg-neon-cyan/10 px-6 py-3 text-xs font-semibold uppercase tracking-[0.3em] text-neon-cyan transition hover:bg-neon-cyan/20 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {uploading ? 'Starting Stream...' : 'Start Video Stream'}
          </button>
          {streamUrl && (
            <button
              type="button"
              onClick={handleStopStream}
              className="rounded-full border border-neon-red/50 bg-neon-red/10 px-6 py-3 text-xs font-semibold uppercase tracking-[0.3em] text-neon-red transition hover:bg-neon-red/20"
            >
              Stop Stream
            </button>
          )}
        </div>
      </div>

      <div className="mt-6 grid gap-4 lg:grid-cols-[1.3fr_1fr]">
        <div className="rounded-xl border border-white/10 bg-abyss/70 px-4 py-4">
          <p className="text-xs uppercase tracking-[0.3em] text-white/50">Live Feed URL</p>
          <input
            type="text"
            value={feedUrl}
            onChange={(event) => setFeedUrl(event.target.value)}
            placeholder="rtsp://user:pass@ip/stream   or   camera:0"
            className="mt-3 w-full rounded-lg border border-white/10 bg-transparent px-3 py-2 text-sm text-white/80 outline-none placeholder:text-white/40"
          />
          <p className="mt-2 text-xs text-white/50">
            Use <span className="text-white/70">camera:0</span> for the default USB webcam.
          </p>
        </div>

        <div className="rounded-xl border border-white/10 bg-abyss/70 px-4 py-4">
          <p className="text-xs uppercase tracking-[0.3em] text-white/50">Upload Video</p>
          <input
            type="file"
            accept="video/*"
            onChange={handleFileChange}
            className="mt-3 w-full rounded-xl border border-white/10 bg-abyss/70 px-4 py-3 text-sm text-white/70 file:mr-4 file:rounded-full file:border-0 file:bg-neon-cyan/20 file:px-4 file:py-2 file:text-xs file:font-semibold file:uppercase file:tracking-[0.2em] file:text-neon-cyan"
          />
          {file && (
            <span className="mt-2 block text-sm text-white/60">Selected: {file.name}</span>
          )}
        </div>
      </div>

      <div className="mt-6 grid gap-4 md:grid-cols-2">
        <div className="rounded-xl border border-white/10 bg-abyss/70 px-4 py-4">
          <p className="text-xs uppercase tracking-[0.3em] text-white/50">Assign Intersection Node</p>
          <select
            value={selectedIntersection}
            onChange={(event) => setSelectedIntersection(event.target.value)}
            className="mt-3 w-full rounded-lg border border-white/10 bg-transparent px-3 py-2 text-sm text-white/80"
          >
            {intersections.length === 0 && (
              <option value="">No intersections loaded</option>
            )}
            {intersections.map((intersection) => (
              <option key={intersection.id} value={intersection.id}>
                Node {intersection.name}
                {intersection.source === 'video_detection' ? ' (📹 Real Data)' : ''}
              </option>
            ))}
          </select>
          <p className="mt-2 text-xs text-white/40">
            Select which intersection node this video belongs to.
          </p>
        </div>

        <div className="rounded-xl border border-white/10 bg-abyss/70 px-4 py-4">
          <p className="text-xs uppercase tracking-[0.3em] text-white/50">Assign Lane</p>
          <select
            value={selectedLane}
            onChange={(event) => setSelectedLane(event.target.value)}
            className="mt-3 w-full rounded-lg border border-white/10 bg-transparent px-3 py-2 text-sm text-white/80"
          >
            {laneOptions.map((lane) => (
              <option key={lane.id} value={lane.id}>
                {lane.label}
              </option>
            ))}
          </select>
        </div>
      </div>

      {localError && (
        <div className="mt-4 rounded-xl border border-neon-red/50 bg-neon-red/10 px-4 py-3 text-sm text-neon-red">
          {localError}
        </div>
      )}

      {streamSource && (
        <div className="mt-4 text-xs uppercase tracking-[0.3em] text-white/40">
          Streaming from: {streamSource}
        </div>
      )}
    </section>
  );
}
