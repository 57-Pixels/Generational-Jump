import "./style.css";
import maplibregl from "maplibre-gl";

/** Zoom below this → globe; at/above → mercator (theater / war-map mode). */
const GLOBE_MAX_ZOOM = 4.25;

/**
 * Eastmarch theater on the *algorithmic* world sphere (see maps/generator).
 * Lon/lat are equirectangular coords from generate_world.py, not Earth.
 */
const EASTMARCH = {
  center: [-12, 34],
  zoom: 3.2,
  bearing: 0,
  pitch: 0,
};

const WAR_LAYER_IDS = [
  "control-fill",
  "control-outline",
  "front-line",
  "events-circle",
];

const asset = (path) =>
  `${import.meta.env.BASE_URL}${path.replace(/^\//, "")}`;

/** Algorithmic basemap from maps/generator → public/world/world-color.png */
function worldStyle() {
  const worldUrl = asset("world/world-color.png");
  return {
    version: 8,
    name: "veldara-algorithmic",
    sources: {
      world: {
        type: "image",
        url: worldUrl,
        coordinates: [
          [-180, 85],
          [180, 85],
          [180, -85],
          [-180, -85],
        ],
      },
    },
    layers: [
      {
        id: "background",
        type: "background",
        paint: { "background-color": "#0a1e33" },
      },
      {
        id: "world-raster",
        type: "raster",
        source: "world",
        paint: { "raster-opacity": 1, "raster-fade-duration": 0 },
      },
    ],
  };
}

const map = new maplibregl.Map({
  container: "map",
  style: worldStyle(),
  center: EASTMARCH.center,
  zoom: EASTMARCH.zoom,
  attributionControl: true,
  maxPitch: 60,
});

map.addControl(new maplibregl.NavigationControl({ visualizePitch: true }), "top-right");
map.addControl(new maplibregl.ScaleControl({ maxWidth: 120 }), "bottom-right");

const projLabel = document.getElementById("proj-label");
const zoomLabel = document.getElementById("zoom-label");
const warToggle = document.getElementById("war-layers");
const resourceToggle = document.getElementById("resource-layers");

const RESOURCE_COLORS = {
  coal: "#1f1f24",
  oil_gas: "#1f7338",
  iron: "#b8472e",
  copper: "#d97a1f",
  tin_tungsten: "#8c59bf",
  gold: "#ebc72e",
  silver_base: "#bfc7d1",
  rare_earths: "#d940a6",
  uranium: "#73d940",
  silica_hp: "#d9ebf2",
  bauxite: "#c78c47",
  nickel_pgm: "#598cb2",
  lithium: "#8cbfd1",
  phosphates: "#66a659",
  potash: "#a6668c",
};

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

function setResourceLayersVisible(visible) {
  const visibility = visible ? "visible" : "none";
  for (const id of ["resources-circle", "resources-label"]) {
    if (map.getLayer(id)) {
      map.setLayoutProperty(id, "visibility", visibility);
    }
  }
}

async function addResourceLayers() {
  const url = asset("world/world-resources.geojson");
  let data;
  try {
    const res = await fetch(url);
    if (!res.ok) throw new Error(String(res.status));
    data = await res.json();
  } catch {
    console.warn("Resource GeoJSON missing — run deeptime generator");
    return;
  }

  map.addSource("resources", { type: "geojson", data });

  const matchColor = ["match", ["get", "resource"]];
  for (const [id, color] of Object.entries(RESOURCE_COLORS)) {
    matchColor.push(id, color);
  }
  matchColor.push("#ffffff");

  map.addLayer({
    id: "resources-circle",
    type: "circle",
    source: "resources",
    paint: {
      "circle-radius": [
        "match",
        ["get", "grade"],
        "major",
        6,
        "significant",
        4.5,
        3.5,
      ],
      "circle-color": matchColor,
      "circle-stroke-width": 1,
      "circle-stroke-color": "#111111",
      "circle-opacity": 0.95,
    },
  });

  map.addLayer({
    id: "resources-label",
    type: "symbol",
    source: "resources",
    layout: {
      "text-field": ["get", "name"],
      "text-size": 10,
      "text-offset": [0, 1.1],
      "text-optional": true,
      "text-max-width": 8,
    },
    paint: {
      "text-color": "#f2f5f8",
      "text-halo-color": "#0a1218",
      "text-halo-width": 1.2,
    },
    minzoom: 3.2,
  });

  map.on("click", "resources-circle", (e) => {
    const f = e.features?.[0];
    if (!f) return;
    const { name, grade, resource, intensity } = f.properties ?? {};
    new maplibregl.Popup()
      .setLngLat(e.lngLat)
      .setHTML(
        `<strong>${name ?? resource}</strong><br/>` +
          `<span>${grade ?? ""} · intensity ${intensity ?? ""}</span>`,
      )
      .addTo(map);
  });
  map.on("mouseenter", "resources-circle", () => {
    map.getCanvas().style.cursor = "pointer";
  });
  map.on("mouseleave", "resources-circle", () => {
    map.getCanvas().style.cursor = "";
  });
}

async function addWarLayers() {
  const [control, front, events] = await Promise.all([
    fetch(asset("data/layers/control.geojson")).then((r) => r.json()),
    fetch(asset("data/layers/front.geojson")).then((r) => r.json()),
    fetch(asset("data/layers/events.geojson")).then((r) => r.json()),
  ]);

  // Demo war geometry was authored on Earth lon/lat — hide by default until
  // reauthored on the algorithmic sphere. Still load for schema wiring.
  map.addSource("war-control", { type: "geojson", data: control });
  map.addSource("war-front", { type: "geojson", data: front });
  map.addSource("war-events", { type: "geojson", data: events });

  map.addLayer({
    id: "control-fill",
    type: "fill",
    source: "war-control",
    layout: { visibility: "none" },
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
    layout: { visibility: "none" },
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
    layout: { visibility: "none" },
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
    layout: { visibility: "none" },
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
  await addResourceLayers();
  await addWarLayers();
  if (warToggle) warToggle.checked = false;
  setWarLayersVisible(false);
  if (resourceToggle) {
    resourceToggle.checked = true;
    setResourceLayersVisible(true);
    resourceToggle.addEventListener("change", () => {
      setResourceLayersVisible(resourceToggle.checked);
    });
  }
});

map.on("zoom", applyProjection);
map.on("zoomend", applyProjection);

warToggle?.addEventListener("change", () => {
  setWarLayersVisible(warToggle.checked);
});
