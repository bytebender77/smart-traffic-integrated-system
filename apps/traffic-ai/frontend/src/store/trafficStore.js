import { create } from 'zustand';
import {
  calculateDensity,
  checkEmergency,
  checkEmergencyUpload,
  deactivateEmergency,
  detectTraffic,
  detectTrafficUpload,
  detectForNode,
  detectForNodeUpload,
  emergencyForNodeUpload,
  getEmergencyRoute,
  getIntersectionData,
  getRoadNetwork,
  getSignalPlan,
  getSimulationState,
  getSystemStatus
} from '../services/api.js';
import { laneOptions } from '../data/laneOptions.js';

const lanes = laneOptions.map((lane) => lane.id);

const mapCongestion = (level) => {
  if (!level) return 'medium';
  const normalized = level.toLowerCase();
  if (normalized === 'low') return 'low';
  if (normalized === 'medium') return 'medium';
  return 'high';
};

const buildLaneDensity = (density) => {
  if (!density) return {};
  return lanes.reduce((acc, lane) => {
    acc[lane] = {
      density_percent: density.density_percent,
      congestion_level: density.congestion_level
    };
    return acc;
  }, {});
};

const normalizeVehicleCounts = (counts) => ({
  cars: counts?.cars ?? 0,
  buses: counts?.buses ?? 0,
  trucks: counts?.trucks ?? 0,
  motorcycles: counts?.motorcycles ?? 0,
  total_vehicles: counts?.total_vehicles ?? 0
});

const isFileSource = (source) => {
  if (!source) return false;
  const value = source.trim();
  if (!value) return false;
  if (value.startsWith('rtsp://')) return false;
  if (value.startsWith('http://') || value.startsWith('https://')) return false;
  if (value.startsWith('camera:')) return false;
  if (/^[0-9]+$/.test(value)) return false;
  return true;
};

const initialState = {
  loading: false,
  error: null,
  statusMessage: 'Awaiting live feed.',
  liveSource: '',
  frameCursor: {},
  requestInFlight: false,
  streamUrl: '',
  streamSource: '',
  selectedIntersection: '',
  selectedLane: lanes[0] || 'lane_A',
  vehicleCounts: normalizeVehicleCounts(null),
  trafficDensity: null,
  signalPlan: null,
  emergencyStatus: {
    active: false,
    route: [],
    message: 'No emergency vehicle detected.',
    etaSeconds: null,
    totalDistance: null,
    vehicleType: null
  },
  intersectionData: [],
  roadNetwork: [],
  systemStatus: null,
  lastUpdated: null,
  // Simulation state
  simulationData: null,
  simulationMode: true, // true when no video feed is active
};

const useTrafficStore = create((set, get) => ({
  ...initialState,
  setError: (error) => set({ error }),
  clearError: () => set({ error: null }),
  setStatusMessage: (statusMessage) => set({ statusMessage }),
  setLiveSource: (source) =>
    set((state) => ({
      liveSource: source,
      simulationMode: !source,
      frameCursor: source
        ? { ...state.frameCursor, [source]: 0 }
        : state.frameCursor,
      statusMessage: source ? null : 'Simulation mode — showing generated traffic data.'
    })),
  clearLiveSource: () =>
    set({
      liveSource: '',
      simulationMode: true,
      statusMessage: 'Simulation mode — showing generated traffic data.'
    }),
  setStreamInfo: ({ streamUrl, streamSource }) =>
    set({ streamUrl, streamSource }),
  clearStreamInfo: () => set({ streamUrl: '', streamSource: '' }),
  setSelectedIntersection: (intersectionId) =>
    set({ selectedIntersection: intersectionId }),
  setSelectedLane: (laneId) => set({ selectedLane: laneId }),
  fetchSystemStatus: async () => {
    try {
      const systemStatus = await getSystemStatus();
      set({ systemStatus });
    } catch (error) {
      set({ error: error?.response?.data?.detail || error.message });
    }
  },
  fetchIntersectionData: async () => {
    try {
      const data = await getIntersectionData();
      const roads = await getRoadNetwork();

      const intersections = (data?.intersections || [])
        .filter((intersection) => intersection.lat !== null && intersection.lon !== null)
        .map((intersection) => ({
          id: intersection.id,
          name: intersection.id,
          position: [intersection.lat, intersection.lon],
          congestion: 'medium'
        }));
      set((state) => ({
        intersectionData: intersections,
        roadNetwork: roads?.edges || [],
        selectedIntersection:
          state.selectedIntersection || intersections[0]?.id || ''
      }));
    } catch (error) {
      set({ error: error?.response?.data?.detail || error.message });
    }
  },

  // ── Simulation data fetcher ─────────────────────────────────────────
  fetchSimulationData: async () => {
    try {
      const simData = await getSimulationState();
      if (!simData || !simData.nodes) return;

      const nodes = simData.nodes;
      const nodeIds = Object.keys(nodes);
      if (nodeIds.length === 0) return;

      // Aggregate vehicle counts across all nodes for the stats panel
      const aggregatedCounts = { cars: 0, buses: 0, trucks: 0, motorcycles: 0, total_vehicles: 0 };
      for (const nodeId of nodeIds) {
        const vc = nodes[nodeId]?.vehicle_counts;
        if (vc) {
          aggregatedCounts.cars += vc.cars || 0;
          aggregatedCounts.buses += vc.buses || 0;
          aggregatedCounts.trucks += vc.trucks || 0;
          aggregatedCounts.motorcycles += vc.motorcycles || 0;
          aggregatedCounts.total_vehicles += vc.total_vehicles || 0;
        }
      }

      // Update intersection markers with per-node congestion
      const currentIntersections = get().intersectionData;
      const updatedIntersections = currentIntersections.map((intersection) => {
        const nodeData = nodes[intersection.id];
        if (nodeData) {
          return {
            ...intersection,
            congestion: mapCongestion(nodeData.congestion_level),
            vehicleCounts: nodeData.vehicle_counts,
            densityPercent: nodeData.density_percent,
            avgSpeedKmph: nodeData.avg_speed_kmph,
            speedLevel: nodeData.speed_level,
          };
        }
        return intersection;
      });

      // Build a density summary for the density panel
      const avgDensity = nodeIds.reduce((sum, id) => sum + (nodes[id]?.density_percent || 0), 0) / nodeIds.length;
      const overallCongestion = avgDensity > 70 ? 'HIGH' : avgDensity > 30 ? 'MEDIUM' : 'LOW';

      const isSimMode = get().simulationMode;

      set({
        simulationData: simData,
        ...(isSimMode ? {
          vehicleCounts: normalizeVehicleCounts(aggregatedCounts),
          trafficDensity: {
            density_percent: Math.round(avgDensity * 100) / 100,
            congestion_level: overallCongestion,
            total_vehicles: aggregatedCounts.total_vehicles,
            weighted_load: avgDensity,
          },
          signalPlan: simData.signal_plan || null,
          intersectionData: updatedIntersections,
          lastUpdated: new Date().toISOString(),
        } : {
          intersectionData: updatedIntersections,
        }),
      });
    } catch (error) {
      // Silently fail simulation fetches — not critical
      console.warn('Simulation fetch failed:', error?.message);
    }
  },

  fetchTrafficData: async ({
    videoPath,
    emergencyStart,
    emergencyDestination = 'Hospital'
  }) => {
    if (!videoPath) {
      // No video feed — rely on simulation data
      set({
        simulationMode: true,
        statusMessage: null,
        error: null
      });
      return;
    }

    if (get().requestInFlight) {
      return;
    }

    const isInitialLoad = !get().lastUpdated;
    set({
      requestInFlight: true,
      loading: isInitialLoad,
      error: null,
      statusMessage: null,
      simulationMode: false
    });

    try {
      const trafficWindow = 30;
      const emergencyWindow = 60;
      const useCursor = isFileSource(videoPath);
      const cursor = useCursor ? get().frameCursor?.[videoPath] || 0 : 0;
      const startIntersection =
        emergencyStart || get().selectedIntersection || 'A';

      // Detect vehicles for ONE node only (selectedIntersection/startIntersection),
      // and let the backend keep other nodes independent via simulation_state.
      const nodeDetection = await detectForNode(startIntersection, videoPath, {
        maxFrames: trafficWindow,
        startFrame: cursor
      });

      const normalizedCounts = nodeDetection?.vehicle_counts || normalizeVehicleCounts(null);
      const trafficDensity = nodeDetection?.density || null;
      const signalResponse = nodeDetection?.signal_plan || null;

      const emergencyCheck = await checkEmergency(videoPath, {
        maxFrames: emergencyWindow,
        startFrame: cursor
      });
      let emergencyStatus = {
        active: emergencyCheck.detected,
        vehicleType: emergencyCheck.vehicle_type,
        confidence: emergencyCheck.confidence,
        route: [],
        message: emergencyCheck.message,
        etaSeconds: null,
        totalDistance: null
      };

      if (emergencyCheck.detected) {
        const routeResponse = await getEmergencyRoute(
          startIntersection,
          emergencyDestination
        );
        emergencyStatus = {
          ...emergencyStatus,
          route: routeResponse.route || [],
          corridorSignals: routeResponse.signals,
          message: routeResponse.message,
          etaSeconds: routeResponse.estimated_travel_time,
          totalDistance: routeResponse.total_distance
        };
      }

      // Update intersections from backend-provided `all_nodes`.
      const allNodes = nodeDetection?.all_nodes || {};
      const intersectionData = get().intersectionData.map((intersection) => {
        const nodeData = allNodes?.[intersection.id];
        if (!nodeData) return intersection;
        return {
          ...intersection,
          congestion: mapCongestion(nodeData.congestion_level),
          vehicleCounts: nodeData.vehicle_counts,
          densityPercent: nodeData.density_percent,
          avgSpeedKmph: nodeData.avg_speed_kmph,
          speedLevel: nodeData.speed_level,
          source: intersection.id === startIntersection ? 'video_detection' : intersection.source
        };
      });

      set({
        vehicleCounts: normalizedCounts,
        trafficDensity,
        signalPlan: signalResponse || null,
        emergencyStatus,
        intersectionData,
        lastUpdated: new Date().toISOString(),
        frameCursor: useCursor
          ? {
              ...get().frameCursor,
              [videoPath]: cursor + trafficWindow
            }
          : get().frameCursor
      });
    } catch (error) {
      set({ error: error?.response?.data?.detail || error.message });
    } finally {
      set({ loading: false, requestInFlight: false });
    }
  },
  processVideoFile: async (file, emergencyStart = 'A', emergencyDestination = 'Hospital') => {
    if (!file) {
      set({ error: 'Please select a video file to process.' });
      return;
    }

    set({ loading: true, error: null, statusMessage: null, simulationMode: false });

    try {
      const vehicleCounts = await detectTrafficUpload(file);
      const normalizedCounts = normalizeVehicleCounts(vehicleCounts);

      const trafficDensity = await calculateDensity(normalizedCounts);
      const laneDensityData = buildLaneDensity(trafficDensity);
      const signalResponse = await getSignalPlan(laneDensityData);

      const emergencyCheck = await checkEmergencyUpload(file);
      let emergencyStatus = {
        active: emergencyCheck.detected,
        vehicleType: emergencyCheck.vehicle_type,
        confidence: emergencyCheck.confidence,
        route: [],
        message: emergencyCheck.message,
        etaSeconds: null,
        totalDistance: null
      };

      if (emergencyCheck.detected) {
        const routeResponse = await getEmergencyRoute(
          emergencyStart,
          emergencyDestination
        );
        emergencyStatus = {
          ...emergencyStatus,
          route: routeResponse.route || [],
          corridorSignals: routeResponse.signals,
          message: routeResponse.message,
          etaSeconds: routeResponse.estimated_travel_time,
          totalDistance: routeResponse.total_distance
        };
      }

      const congestion = mapCongestion(trafficDensity?.congestion_level);
      const intersectionData = get().intersectionData.map((intersection) => ({
        ...intersection,
        congestion
      }));

      set({
        vehicleCounts: normalizedCounts,
        trafficDensity,
        signalPlan: signalResponse?.signal_plan ?? null,
        emergencyStatus,
        intersectionData,
        lastUpdated: new Date().toISOString()
      });
    } catch (error) {
      set({ error: error?.response?.data?.detail || error.message });
    } finally {
      set({ loading: false });
    }
  },

  // ── Node-specific video detection ─────────────────────────────────
  processVideoForNode: async (file, nodeId = 'A') => {
    if (!file) {
      set({ error: 'Please select a video file to process.' });
      return;
    }

    set({ loading: true, error: null, statusMessage: `Detecting vehicles at node ${nodeId}...` });

    try {
      const result = await detectForNodeUpload(file, nodeId);

      // Update this node in intersection data
      const currentIntersections = get().intersectionData;
      const updatedIntersections = currentIntersections.map((intersection) => {
        if (intersection.id === nodeId) {
          const nodeData = result.all_nodes?.[nodeId];
          return {
            ...intersection,
            congestion: mapCongestion(result.density?.congestion_level),
            vehicleCounts: result.vehicle_counts,
            densityPercent: result.density?.density_percent,
            avgSpeedKmph: nodeData?.avg_speed_kmph,
            speedLevel: nodeData?.speed_level,
            source: 'video_detection',
          };
        }
        // Update other nodes from all_nodes response
        const nodeData = result.all_nodes?.[intersection.id];
        if (nodeData) {
          return {
            ...intersection,
            congestion: mapCongestion(nodeData.congestion_level),
            vehicleCounts: nodeData.vehicle_counts,
            densityPercent: nodeData.density_percent,
            avgSpeedKmph: nodeData.avg_speed_kmph,
            speedLevel: nodeData.speed_level,
          };
        }
        return intersection;
      });

      // Aggregate across all nodes for stats
      const allNodes = result.all_nodes || {};
      const nodeIds = Object.keys(allNodes);
      const aggregatedCounts = { cars: 0, buses: 0, trucks: 0, motorcycles: 0, total_vehicles: 0 };
      for (const nid of nodeIds) {
        const vc = allNodes[nid]?.vehicle_counts;
        if (vc) {
          aggregatedCounts.cars += vc.cars || 0;
          aggregatedCounts.buses += vc.buses || 0;
          aggregatedCounts.trucks += vc.trucks || 0;
          aggregatedCounts.motorcycles += vc.motorcycles || 0;
          aggregatedCounts.total_vehicles += vc.total_vehicles || 0;
        }
      }

      set({
        vehicleCounts: normalizeVehicleCounts(aggregatedCounts),
        signalPlan: result.signal_plan || null,
        intersectionData: updatedIntersections,
        lastUpdated: new Date().toISOString(),
        statusMessage: `✅ Node ${nodeId}: ${result.vehicle_counts.total_vehicles} vehicles detected (real data). Signals re-optimized.`,
      });
    } catch (error) {
      set({ error: error?.response?.data?.detail || error.message });
    } finally {
      set({ loading: false });
    }
  },

  // ── Node-specific emergency detection ─────────────────────────────
  processEmergencyForNode: async (file, nodeId = 'A', destination = 'Hospital') => {
    if (!file) {
      set({ error: 'Please select a video file to process.' });
      return;
    }

    set({ loading: true, error: null, statusMessage: `Checking for emergency vehicles at node ${nodeId}...` });

    try {
      const result = await emergencyForNodeUpload(file, nodeId, destination);

      if (result.detected) {
        set({
          emergencyStatus: {
            active: true,
            vehicleType: result.vehicle_type,
            confidence: result.confidence,
            route: result.route || [],
            corridorSignals: result.signals,
            message: result.message,
            etaSeconds: result.estimated_travel_time,
            totalDistance: result.total_distance
          },
          statusMessage: result.message,
          lastUpdated: new Date().toISOString(),
        });
      } else {
        set({
          emergencyStatus: {
            active: false,
            vehicleType: null,
            route: [],
            message: result.message || 'No emergency vehicles detected.',
            etaSeconds: null,
            totalDistance: null
          },
          statusMessage: result.message,
        });
      }
    } catch (error) {
      set({ error: error?.response?.data?.detail || error.message });
    } finally {
      set({ loading: false });
    }
  },

  // ── Manual emergency trigger (demo-safe) ───────────────────────────
  triggerEmergencyRoute: async (start, destination = 'Hospital', vehicleType = 'ambulance') => {
    const source = start || get().selectedIntersection || 'A';
    const typeLabel = vehicleType === 'fire' ? 'Fire service' : 'Ambulance';
    set({
      loading: true,
      error: null,
      statusMessage: `Activating ${typeLabel} corridor from ${source}…`
    });
    try {
      const routeResponse = await getEmergencyRoute(source, destination);
      const routeLabel = (routeResponse.route || []).join(' → ');
      const corridorMessage = vehicleType === 'fire'
        ? `🚒 Fire service corridor activated: ${routeLabel || 'route ready'}.`
        : (routeResponse.message || `${typeLabel} corridor activated.`);
      set({
        emergencyStatus: {
          active: true,
          vehicleType,
          confidence: null,
          route: routeResponse.route || [],
          corridorSignals: routeResponse.signals,
          message: corridorMessage,
          etaSeconds: routeResponse.estimated_travel_time,
          totalDistance: routeResponse.total_distance
        },
        statusMessage: corridorMessage,
        lastUpdated: new Date().toISOString(),
      });
    } catch (error) {
      set({ error: error?.response?.data?.detail || error.message });
    } finally {
      set({ loading: false });
    }
  },

  // ── Manual emergency clear ─────────────────────────────────────────
  clearEmergencyRoute: async () => {
    set({ loading: true, error: null, statusMessage: 'Clearing emergency mode…' });
    try {
      await deactivateEmergency();
      set({
        emergencyStatus: {
          active: false,
          route: [],
          message: 'Emergency mode cleared.',
          etaSeconds: null,
          totalDistance: null,
          vehicleType: null
        },
        statusMessage: 'Emergency mode cleared.',
        lastUpdated: new Date().toISOString(),
      });
    } catch (error) {
      set({ error: error?.response?.data?.detail || error.message });
    } finally {
      set({ loading: false });
    }
  },
}));

export default useTrafficStore;
