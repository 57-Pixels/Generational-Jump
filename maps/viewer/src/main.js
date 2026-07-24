import "./style.css";
import maplibregl from "maplibre-gl";

/** Zoom below this → globe; at/above → mercator (theater / war-map mode). */
const GLOBE_MAX_ZOOM = 4.25;

/**
 * Placeholder center for a future Eastmarch theater.
 * Coordinates are stand-ins on the real Earth sphere until custom world tiles
 * and a locked CRS exist — then re-point style + these numbers.
 */
const EASTMARCH = {
  center: [36.5, 48.5],
  zoom: 5.5,
  bearing: 0,
  pitch: 0,
};

const WAR_LAYER_IDS = [
  "control-fill",
  "control-outline",
  "front-line",
  "events-circle",
];

const map = new maplibregl.Map({
  container: "map",
  style: "https://demotiles.maplibre.org/style.json",
  center: EASTMARCH.center,
  zoom: EASTMARCH.zoom,
  attributionControl: true,
});

map.addControl(new maplibregl.NavigationControl({ visualizePitch: true }), "top-right");
map.addControl(new maplibregl.ScaleControl({ maxWidth: 120 }), "bottom-right");

const projLabel = document.getElementById("proj-label");
const zoomLabel = document.getElementById("zoom-label");
const warToggle = document.getElementById("war-layers");

function projectionForZoom(zoom) {
  return zoom < GLOBE_MAX_ZOOM ? "globe" : "mercator";
}

function applyProjection() {
  const zoom = map.getZoom();
  const next = projectionForZoom(zoom);
  const current = map.getProjection()?.type;
  if (current !== next) {
    map.setProjection({ type: next });
  }
  if (projLabel) projLabel.textContent = `projection: ${next}`;
  if (zoomLabel) zoomLabel.textContent = `zoom: ${zoom.toFixed(2)}`;
}

function setWarLayersVisible(visible) {
  const visibility = visible ? "visible" : "none";
  for (const id of WAR_LAYER_IDS) {
    if (map.getLayer(id)) {
      map.setLayoutProperty(id, "visibility", visibility);
    }
  }
}

async function addWarLayers() {
  const [control, front, events] = await Promise.all([
    fetch("/data/layers/control.geojson").then((r) => r.json()),
    fetch("/data/layers/front.geojson").then((r) => r.json()),
    fetch("/data/layers/events.geojson").then((r) => r.json()),
  ]);

  map.addSource("war-control", { type: "geojson", data: control });
  map.addSource("war-front", { type: "geojson", data: front });
  map.addSource("war-events", { type: "geojson", data: events });

  map.addLayer({
    id: "control-fill",
    type: "fill",
    source: "war-control",
    paint: {
      "fill-color": [
        "match",
        ["get", "controller"],
        "veldara",
        "#3d8bfd",
        "korvath",
        "#e35d6a",
        "#888888",
      ],
      "fill-opacity": 0.35,
    },
  });

  map.addLayer({
    id: "control-outline",
    type: "line",
    source: "war-control",
    paint: {
      "line-color": "#ffffff",
      "line-width": 1,
      "line-opacity": 0.35,
    },
  });

  map.addLayer({
    id: "front-line",
    type: "line",
    source: "war-front",
    paint: {
      "line-color": "#f5d76e",
      "line-width": 3,
      "line-opacity": 0.95,
    },
  });

  map.addLayer({
    id: "events-circle",
    type: "circle",
    source: "war-events",
    paint: {
      "circle-radius": 5,
      "circle-color": "#ffffff",
      "circle-stroke-width": 1.5,
      "circle-stroke-color": "#111111",
    },
  });

  map.on("click", "events-circle", (e) => {
    const f = e.features?.[0];
    if (!f) return;
    const { name, date, note } = f.properties ?? {};
    new maplibregl.Popup()
      .setLngLat(e.lngLat)
      .setHTML(
        `<strong>${name ?? "Event"}</strong><br/><span>${date ?? ""}</span><br/><span>${note ?? ""}</span>`,
      )
      .addTo(map);
  });

  map.on("mouseenter", "events-circle", () => {
    map.getCanvas().style.cursor = "pointer";
  });
  map.on("mouseleave", "events-circle", () => {
    map.getCanvas().style.cursor = "";
  });
}

map.on("load", async () => {
  applyProjection();
  await addWarLayers();
  setWarLayersVisible(warToggle?.checked ?? true);
});

map.on("zoom", applyProjection);
map.on("zoomend", applyProjection);

warToggle?.addEventListener("change", () => {
  setWarLayersVisible(warToggle.checked);
});
