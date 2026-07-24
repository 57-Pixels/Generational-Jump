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

/** Web Mercator max latitude used by MapLibre / EPSG:3857. */
const MERCATOR_MAX_LAT = 85.05112878;
const WORLD_IMAGE_BOUNDS = [
  [-180, MERCATOR_MAX_LAT],
  [180, MERCATOR_MAX_LAT],
  [180, -MERCATOR_MAX_LAT],
  [-180, -MERCATOR_MAX_LAT],
];

/**
 * Basemap as XYZ raster tiles (not an image source).
 * MapLibre globe extends tile meshes to the poles the same way it does for
 * Earth satellite rasters; ImageSource passes allowPoles=false.
 */
function worldStyle() {
  const tiles = [asset("world/tiles/color/{z}/{x}/{y}.png")];
  return {
    version: 8,
    name: "veldara-algorithmic",
    sources: {
      world: {
        type: "raster",
        tiles,
        tileSize: 256,
        minzoom: 0,
        maxzoom: 3,
        attribution: "Algorithmic world (deeptime v2)",
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
  coal_basin: "#1f1f24",
  petroleum_system: "#1f7338",
  helium_gas: "#74b8d9",
  bif_iron: "#b8472e",
  bauxite_laterite: "#c78c47",
  sedimentary_manganese: "#776b82",
  vanadium_titanomagnetite: "#446c87",
  layered_chromite_pgm: "#798a9b",
  porphyry_cu_mo: "#d97a1f",
  sediment_cu_co: "#b46d3a",
  vms_cu_zn: "#8b7658",
  sedex_zn_pb: "#a9aeb3",
  mvt_zn_pb: "#b8bec4",
  magmatic_ni_cu: "#598cb2",
  nickel_laterite: "#6b9e85",
  granite_sn_w: "#8c59bf",
  hydrothermal_gold: "#ebc72e",
  antimony_hydrothermal: "#81565f",
  uranium_system: "#73d940",
  carbonatite_ree_nb: "#d940a6",
  ionic_clay_hree: "#e271ba",
  mineral_sands: "#d1b772",
  lithium_brine: "#8cbfd1",
  lct_pegmatite: "#74a8db",
  metamorphic_graphite: "#4a4f55",
  phosphorite: "#66a659",
  potash_evaporite: "#a6668c",
  fluorspar_hydrothermal: "#68c6bb",
  high_purity_quartz: "#d9ebf2",
};

const riverToggle = document.getElementById("river-layers");
const settlementToggle = document.getElementById("settlement-layers");

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
  for (const id of ["resources-fill", "resources-outline", "resources-label"]) {
    if (map.getLayer(id)) {
      map.setLayoutProperty(id, "visibility", visibility);
    }
  }
}

function setRiverLayersVisible(visible) {
  if (map.getLayer("world-rivers")) {
    map.setLayoutProperty("world-rivers", "visibility", visible ? "visible" : "none");
  }
}

function setSettlementLayersVisible(visible) {
  const visibility = visible ? "visible" : "none";
  for (const id of ["settlement-raster", "settlement-sites", "settlement-sites-fill"]) {
    if (map.getLayer(id)) {
      map.setLayoutProperty(id, "visibility", visibility);
    }
  }
}

async function addSurfaceLayers() {
  const [rivers, settlements] = await Promise.all([
    fetch(asset("world/world-rivers.geojson")).then((response) => response.json()),
    fetch(asset("world/world-settlement.geojson")).then((response) => response.json()),
  ]);

  map.addSource("world-rivers", { type: "geojson", data: rivers });
  map.addLayer({
    id: "world-rivers",
    type: "line",
    source: "world-rivers",
    paint: {
      "line-color": "#48b8f0",
      "line-width": ["interpolate", ["linear"], ["zoom"], 0, 0.35, 6, 2.2],
      "line-opacity": 0.8,
    },
  });

  map.addSource("settlement-raster-source", {
    type: "image",
    url: asset("world/world-settlement.png"),
    coordinates: WORLD_IMAGE_BOUNDS,
  });
  map.addLayer({
    id: "settlement-raster",
    type: "raster",
    source: "settlement-raster-source",
    layout: { visibility: "none" },
    paint: { "raster-opacity": 0.68, "raster-fade-duration": 0 },
  });

  map.addSource("settlement-sites-source", {
    type: "geojson",
    data: settlements,
  });
  map.addLayer({
    id: "settlement-sites-fill",
    type: "fill",
    source: "settlement-sites-source",
    layout: { visibility: "none" },
    paint: {
      "fill-color": [
        "match",
        ["get", "mechanism"],
        "incentive_driven",
        "#ff7b47",
        "technology_enabled",
        "#4cd4ff",
        "combined",
        "#d45cff",
        "#fff2a8",
      ],
      "fill-opacity": 0.55,
    },
  });
  map.addLayer({
    id: "settlement-sites",
    type: "line",
    source: "settlement-sites-source",
    layout: { visibility: "none" },
    paint: {
      "line-color": "#101820",
      "line-width": 1,
    },
  });
  map.on("click", "settlement-sites-fill", (event) => {
    const feature = event.features?.[0];
    if (!feature) return;
    const properties = feature.properties ?? {};
    const lon = Number(properties.lon ?? event.lngLat.lng);
    const lat = Number(properties.lat ?? event.lngLat.lat);
    new maplibregl.Popup()
      .setLngLat([lon, lat])
      .setHTML(
        `<strong>Settlement candidate #${properties.rank}</strong><br/>` +
          `<span>${properties.mechanism}; ${properties.dominant_incentive}</span><br/>` +
          `<span>pre ${properties.h_pre} · industrial ${properties.h_ind} · A/C ${properties.h_ac}</span><br/>` +
          `<span>A/C ${properties.ac_kwh_pc_yr} kWh/person/year</span>`,
      )
      .addTo(map);
  });
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
    id: "resources-fill",
    type: "fill",
    source: "resources",
    paint: {
      "fill-color": matchColor,
      "fill-opacity": 0.72,
    },
  });

  map.addLayer({
    id: "resources-outline",
    type: "line",
    source: "resources",
    paint: {
      "line-color": "#111111",
      "line-width": 1,
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

  map.on("click", "resources-fill", (e) => {
    const f = e.features?.[0];
    if (!f) return;
    const {
      name,
      resource,
      grade,
      depth_m: depth,
      reserve_2025_t: reserve,
      processing_difficulty: difficulty,
      byproducts,
      lon,
      lat,
    } = f.properties ?? {};
    new maplibregl.Popup()
      .setLngLat([Number(lon ?? e.lngLat.lng), Number(lat ?? e.lngLat.lat)])
      .setHTML(
        `<strong>${name ?? resource}</strong><br/>` +
          `<span>grade ${grade ?? "—"}</span><br/>` +
          `<span>depth ${depth ?? "—"} m · reserve ${reserve ?? "—"} t</span><br/>` +
          `<span>processing ${difficulty ?? "—"} · byproducts ${byproducts || "none"}</span>`,
      )
      .addTo(map);
  });
  map.on("mouseenter", "resources-fill", () => {
    map.getCanvas().style.cursor = "pointer";
  });
  map.on("mouseleave", "resources-fill", () => {
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
  await addSurfaceLayers();
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
  if (riverToggle) {
    riverToggle.checked = true;
    setRiverLayersVisible(true);
    riverToggle.addEventListener("change", () => {
      setRiverLayersVisible(riverToggle.checked);
    });
  }
  if (settlementToggle) {
    settlementToggle.checked = false;
    setSettlementLayersVisible(false);
    settlementToggle.addEventListener("change", () => {
      setSettlementLayersVisible(settlementToggle.checked);
    });
  }
});

map.on("zoom", applyProjection);
map.on("zoomend", applyProjection);

warToggle?.addEventListener("change", () => {
  setWarLayersVisible(warToggle.checked);
});
