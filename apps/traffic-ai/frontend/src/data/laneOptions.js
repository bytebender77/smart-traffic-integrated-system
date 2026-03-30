export const laneOptions = [
  { id: 'lane_A', label: 'Northbound' },
  { id: 'lane_B', label: 'Southbound' },
  { id: 'lane_C', label: 'Eastbound' },
  { id: 'lane_D', label: 'Westbound' }
];

export const getLaneLabel = (laneId) =>
  laneOptions.find((lane) => lane.id === laneId)?.label || laneId;
