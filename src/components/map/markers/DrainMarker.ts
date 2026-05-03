import L from 'leaflet';

export function createDrainIcon(id: string, alert = false): L.DivIcon {
  return L.divIcon({
    className: '',
    html: `<div class="map-marker-stack">
      <div class="drain-marker ${alert ? 'alert-drain' : ''}" id="dm-${id}"></div>
      <div class="marker-tooltip">${id}</div>
    </div>`,
    iconSize: alert ? [16, 16] : [8, 8],
    iconAnchor: alert ? [8, 8] : [4, 4],
  });
}
