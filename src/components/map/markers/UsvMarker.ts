import L from 'leaflet';

export function createUsvIcon(id: string, yaw: number, color = '56,189,248'): L.DivIcon {
  return L.divIcon({
    className: '',
    html: `<div class="usv-icon-wrap" id="icon-${id}">
      <div class="usv-map-label">${id}</div>
      <svg class="usv-svg" id="svg-${id}" viewBox="0 0 28 28" style="transform:rotate(${yaw}deg)">
        <path d="M14 3 L21 22 L14 18 L7 22 Z" fill="rgba(${color},0.85)" stroke="rgba(${color},1)" stroke-width="0.5"/>
      </svg>
    </div>`,
    iconSize: [28, 28],
    iconAnchor: [14, 14],
  });
}
