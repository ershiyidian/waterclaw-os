import L from 'leaflet';

export function createStationIcon(id: string): L.DivIcon {
  return L.divIcon({
    className: '',
    html: `<div class="map-marker-stack">
      <div class="station-marker"></div>
      <div class="marker-tooltip">${id}</div>
    </div>`,
    iconSize: [6, 6],
    iconAnchor: [3, 3],
  });
}
