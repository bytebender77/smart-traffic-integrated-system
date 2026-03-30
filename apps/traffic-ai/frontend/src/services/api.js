import axios from 'axios';

const baseURL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

// Central Axios client for FastAPI integration.
const apiClient = axios.create({
  baseURL: `${baseURL}/api/v1`,
  timeout: 10000
});

export const getHealthStatus = async () => {
  const { data } = await apiClient.get('/health');
  return data;
};

export const detectTraffic = async (videoPath, options = {}) => {
  const { maxFrames = 30, startFrame = 0 } = options;
  const { data } = await apiClient.post('/traffic/detect', {
    video_path: videoPath,
    max_frames: maxFrames,
    start_frame: startFrame
  });
  return data;
};

export const detectTrafficUpload = async (file) => {
  const formData = new FormData();
  formData.append('file', file);
  const { data } = await apiClient.post('/traffic/detect/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  });
  return data;
};

export const uploadTrafficVideo = async (file) => {
  const formData = new FormData();
  formData.append('file', file);
  const { data } = await apiClient.post('/traffic/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  });
  return data;
};

export const getTrafficStreamUrl = (source, params = {}) => {
  const base = apiClient.defaults.baseURL;
  const query = new URLSearchParams({
    source,
    ...params
  });
  return `${base}/traffic/stream?${query.toString()}`;
};

export const calculateDensity = async (vehicleCounts, laneCapacity) => {
  const { data } = await apiClient.post('/traffic/density', {
    vehicle_counts: vehicleCounts,
    lane_capacity: laneCapacity
  });
  return data;
};

export const getSignalPlan = async (densityData, cycleTime) => {
  const { data } = await apiClient.post('/traffic/signals', {
    lane_density_data: densityData,
    cycle_time: cycleTime
  });
  return data;
};

export const checkEmergency = async (videoPath, options = {}) => {
  const { maxFrames = 60, startFrame = 0 } = options;
  const { data } = await apiClient.post('/emergency/check', {
    video_path: videoPath,
    max_frames: maxFrames,
    start_frame: startFrame
  });
  return data;
};

export const checkEmergencyUpload = async (file) => {
  const formData = new FormData();
  formData.append('file', file);
  const { data } = await apiClient.post('/emergency/check/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  });
  return data;
};

export const getEmergencyRoute = async (start, destination) => {
  const { data } = await apiClient.post('/emergency/route', {
    start,
    destination
  });
  return data;
};

export const deactivateEmergency = async () => {
  const { data } = await apiClient.post('/emergency/deactivate');
  return data;
};

export const getSystemStatus = async () => {
  const { data } = await apiClient.get('/system/status');
  return data;
};

// Optional helper for mapping intersections.
export const getIntersectionData = async () => {
  const { data } = await apiClient.get('/system/intersections');
  return data;
};

export const getRoadNetwork = async () => {
  const { data } = await apiClient.get('/system/road-network');
  return data;
};

// ── Simulation endpoints ──────────────────────────────────────────────
export const getSimulationState = async () => {
  const { data } = await apiClient.get('/simulation/state');
  return data;
};

export const startSimulation = async () => {
  const { data } = await apiClient.get('/simulation/start');
  return data;
};

export const stopSimulation = async () => {
  const { data } = await apiClient.get('/simulation/stop');
  return data;
};

// ── Node-specific detection endpoints ─────────────────────────────────
export const detectForNodeUpload = async (file, nodeId = 'A') => {
  const formData = new FormData();
  formData.append('file', file);
  const { data } = await apiClient.post(`/node/detect/upload?node_id=${nodeId}`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: 60000,
  });
  return data;
};

// Node-specific detection for video sources (RTSP/HTTP URLs, camera:0, file paths).
export const detectForNode = async (nodeId = 'A', videoPath, options = {}) => {
  const { maxFrames = 30, startFrame = 0 } = options;
  const { data } = await apiClient.post('/node/detect', {
    node_id: nodeId,
    video_path: videoPath,
    max_frames: maxFrames,
    start_frame: startFrame,
  });
  return data;
};

export const emergencyForNodeUpload = async (file, nodeId = 'A', destination = 'Hospital') => {
  const formData = new FormData();
  formData.append('file', file);
  const { data } = await apiClient.post(
    `/node/emergency/upload?node_id=${nodeId}&destination=${destination}`,
    formData,
    {
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: 60000,
    }
  );
  return data;
};

export default apiClient;
