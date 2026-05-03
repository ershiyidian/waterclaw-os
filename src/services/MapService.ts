import L from 'leaflet';
import { DRAIN_POINTS, MAP_CENTER, RIVER_CORRIDOR_RADIUS_M, RIVER_PATH, STATIONS, TAOPU_RIVER_OSM_SOURCE } from '@/config/constants';
import { useRootStore } from '@/core/StateStore';
import type { LatLngTuple } from '@/core/types/common';
import { makeBezierPath, nearestPointOnPath } from '@/utils/geo';
import { createDrainIcon } from '@/components/map/markers/DrainMarker';
import { createStationIcon } from '@/components/map/markers/StationMarker';
import { createUsvIcon } from '@/components/map/markers/UsvMarker';
import { createSpreadCircle } from '@/components/map/overlays/SpreadCircle';

export class MapService {
  private map: L.Map | null = null;
  private usvMarkers = new Map<string, L.Marker>();
  private drainMarkers = new Map<string, L.Marker>();
  private stationMarkers = new Map<string, L.Marker>();
  private trails = new Map<string, L.Polyline>();
  private spreadCircle: L.Circle | null = null;
  private blockadeLine: L.Polyline | null = null;
  private clusterMarkers: L.CircleMarker[] = [];
  private plannedLines: L.Layer[] = [];
  private waterStatusPopup: L.Popup | null = null;

  init(container: HTMLElement): void {
    if (this.map) return;
    const store = useRootStore();
    this.map = L.map(container, {
      zoomControl: false,
      attributionControl: false,
      preferCanvas: true,
    }).setView(MAP_CENTER, 16);

    L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
      maxZoom: 19,
      subdomains: 'abcd',
    }).addTo(this.map);

    this.addRiverAwarenessLayers();

    L.polyline(RIVER_PATH, {
      color: 'rgba(125,211,252,0.78)',
      weight: 3,
      opacity: 0.9,
      lineCap: 'round',
    }).addTo(this.map);

    DRAIN_POINTS.forEach((point) => {
      const marker = L.marker(point.pos, { icon: createDrainIcon(point.id) }).addTo(this.map!);
      this.drainMarkers.set(point.id, marker);
    });

    STATIONS.forEach((point) => {
      const marker = L.marker(point.pos, { icon: createStationIcon(point.id) }).addTo(this.map!);
      this.stationMarkers.set(point.id, marker);
    });

    Object.values(store.fleet).forEach((usv) => {
      const marker = L.marker(usv.position, { icon: createUsvIcon(usv.id, usv.headingDeg) }).addTo(this.map!);
      this.usvMarkers.set(usv.id, marker);
      const trail = L.polyline(usv.trail, {
        color: usv.id === 'USV-01' ? 'rgba(56,189,248,0.35)' : 'rgba(52,211,153,0.3)',
        weight: 1.5,
        dashArray: '3,4',
      }).addTo(this.map!);
      this.trails.set(usv.id, trail);
    });

    this.map.on('click', this.handleMapClick);
    this.showWaterClassification(MAP_CENTER);
  }

  destroy(): void {
    if (!this.map) return;
    this.map.off('click', this.handleMapClick);
    this.map.remove();
    this.map = null;
    this.usvMarkers.clear();
    this.drainMarkers.clear();
    this.stationMarkers.clear();
    this.trails.clear();
  }

  sync(): void {
    if (!this.map) return;
    const store = useRootStore();

    Object.values(store.fleet).forEach((usv) => {
      const marker = this.usvMarkers.get(usv.id);
      if (marker) {
        marker.setLatLng(usv.position);
        marker.setIcon(createUsvIcon(usv.id, usv.headingDeg, usv.mode === 'SENTRY' ? '129,140,248' : usv.mode === 'INTERCEPT' ? '245,158,11' : '56,189,248'));
      }
      this.trails.get(usv.id)?.setLatLngs(usv.trail);
    });

    DRAIN_POINTS.forEach((point) => {
      const marker = this.drainMarkers.get(point.id);
      if (marker) marker.setIcon(createDrainIcon(point.id, store.map.emergencyDrainId === point.id));
    });

    if (store.map.focusTarget) {
      this.map.flyTo(store.map.focusTarget, store.system.alertLevel === 'critical' ? 17 : 16, { duration: 1.2 });
      store.map.focusTarget = null;
    }

    this.syncCluster(store.map.clusterVisible);
    this.syncSpread(store.map.spreadVisible);
    this.syncBlockade(store.map.blockadeVisible);
  }

  drawDubinsPreview(usvId: string, end: LatLngTuple, color = 'rgba(245,158,11,0.5)'): LatLngTuple[] {
    if (!this.map) return [];
    const store = useRootStore();
    const start = store.fleet[usvId].position;
    const ctrl = [(start[0] + end[0]) / 2 + 0.002, (start[1] + end[1]) / 2 - 0.003] as LatLngTuple;
    const path = makeBezierPath(start, ctrl, end, 50);
    const line = L.polyline(path, { color, weight: 1.5, dashArray: '4,6' }).addTo(this.map);
    this.plannedLines.push(line);
    return path;
  }

  clearPlannedLines(): void {
    if (!this.map) return;
    this.plannedLines.forEach((line) => this.map!.removeLayer(line));
    this.plannedLines = [];
  }

  private syncSpread(visible: boolean): void {
    if (!this.map) return;
    const dp3 = DRAIN_POINTS.find((point) => point.id === 'DP-03');
    if (!dp3) return;
    if (visible && !this.spreadCircle) {
      this.spreadCircle = createSpreadCircle(dp3.pos).addTo(this.map);
      let r = 40;
      const timer = window.setInterval(() => {
        r += 5;
        if (!this.spreadCircle || r > 190) {
          window.clearInterval(timer);
          return;
        }
        this.spreadCircle.setRadius(r);
      }, 130);
    }
    if (!visible && this.spreadCircle) {
      this.map.removeLayer(this.spreadCircle);
      this.spreadCircle = null;
    }
  }

  private syncBlockade(visible: boolean): void {
    if (!this.map) return;
    if (visible && !this.blockadeLine) {
      this.blockadeLine = L.polyline(
        [
          [31.2711829, 121.3897608],
          [31.2725034, 121.3890913],
        ],
        { color: 'rgba(129,140,248,0.68)', weight: 2, dashArray: '6,4' },
      ).addTo(this.map);
    }
    if (!visible && this.blockadeLine) {
      this.map.removeLayer(this.blockadeLine);
      this.blockadeLine = null;
    }
  }

  private syncCluster(visible: boolean): void {
    if (!this.map) return;
    if (visible && this.clusterMarkers.length === 0) {
      const clusterPts: LatLngTuple[] = [
        [31.2728189, 121.3889883],
        [31.273237, 121.3887823],
        [31.2738679, 121.3883618],
      ];
      this.clusterMarkers = clusterPts.map((pt, i) =>
        L.circleMarker(pt, {
          radius: 6 + i * 2,
          color: 'rgba(239,68,68,0.6)',
          fillColor: 'rgba(239,68,68,0.2)',
          fillOpacity: 0.5,
          weight: 1,
        }).addTo(this.map!),
      );
    }
    if (!visible && this.clusterMarkers.length > 0) {
      this.clusterMarkers.forEach((marker) => this.map!.removeLayer(marker));
      this.clusterMarkers = [];
    }
  }

  private addRiverAwarenessLayers(): void {
    if (!this.map) return;

    L.polyline(RIVER_PATH, {
      className: 'river-corridor',
      color: 'rgba(14,165,233,0.18)',
      weight: 34,
      opacity: 1,
      lineCap: 'round',
      lineJoin: 'round',
      interactive: false,
    }).addTo(this.map);

    L.polyline(RIVER_PATH, {
      className: 'river-bank-edge',
      color: 'rgba(14,165,233,0.22)',
      weight: 42,
      opacity: 1,
      lineCap: 'round',
      lineJoin: 'round',
      dashArray: '2, 10',
      interactive: false,
    }).addTo(this.map);

    L.marker(MAP_CENTER, {
      icon: L.divIcon({
        className: '',
        html: `<div class="river-anchor-marker" title="${TAOPU_RIVER_OSM_SOURCE.name}"></div>`,
        iconSize: [14, 14],
        iconAnchor: [7, 7],
      }),
      interactive: false,
    }).addTo(this.map);
  }

  private handleMapClick = (event: L.LeafletMouseEvent): void => {
    this.showWaterClassification([event.latlng.lat, event.latlng.lng]);
  };

  private showWaterClassification(point: LatLngTuple): void {
    if (!this.map) return;

    const nearest = nearestPointOnPath(point, RIVER_PATH);
    const isRiver = nearest.distanceM <= RIVER_CORRIDOR_RADIUS_M;
    const label = isRiver ? '河道' : '陆地';
    const statusClass = isRiver ? 'river' : 'land';
    const lat = point[0].toFixed(6);
    const lng = point[1].toFixed(6);
    const distance = Number.isFinite(nearest.distanceM) ? `${nearest.distanceM.toFixed(1)} m` : 'N/A';
    const html = `<div class="water-classification-popup">
      <div class="water-classification-title ${statusClass}">${label}</div>
      <div class="water-classification-row"><span>坐标</span><b>${lat}, ${lng}</b></div>
      <div class="water-classification-row"><span>最近河道</span><b>${TAOPU_RIVER_OSM_SOURCE.name}</b></div>
      <div class="water-classification-row"><span>中线距离</span><b>${distance}</b></div>
      <div class="water-classification-source">OSM ${TAOPU_RIVER_OSM_SOURCE.tag} / way ${TAOPU_RIVER_OSM_SOURCE.osmWayId}</div>
    </div>`;

    this.waterStatusPopup = (this.waterStatusPopup ?? L.popup({ className: 'water-classification-leaflet-popup', closeButton: false, autoPan: false }))
      .setLatLng(point)
      .setContent(html)
      .openOn(this.map);
  }
}

export const mapService = new MapService();
