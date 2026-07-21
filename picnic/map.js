// picnic table GeoJSON data
const PICNIC = {
  type: "FeatureCollection",
  features: [],
};
// static FlatGeobuf file, queried directly via HTTP range requests using
// its built-in packed Hilbert R-tree index
const PICNIC_DATA_URL = "picnic.fgb";
// show picnic tables at zoom 11 and above
const minZoom = 11;
const initialZoom = 12;
let prevZoom = initialZoom;
// bounding boxes that have been queried
const boxes = new Set();
const urlParams = new URLSearchParams(window.location.search);

/*
  map events
*/

maptilersdk.config.apiKey = MAP_TILER_API_KEY;
const map = new maptilersdk.Map({
  container: "map",
  style: maptilersdk.MapStyle.OUTDOOR,
  center: [
    parseFloat(urlParams.get("lng")) || -121.9,
    parseFloat(urlParams.get("lat")) || 37.35,
  ],
  zoom: initialZoom,
});

map.on("load", async function () {
  prevZoom = initialZoom;
  // add layer for picnic tables (initially empty)
  map.addSource("picnicSource", { type: "geojson", data: PICNIC });
  map.loadImage("picnic/picnic-120.png", function (error, image) {
    if (error) throw error;
    map.addImage("picnic", image);
  });
  map.addLayer({
    id: "picnic",
    type: "symbol",
    source: "picnicSource",
    layout: {
      "icon-image": "picnic",
      "icon-size": 0.2,
    },
    paint: {},
  });
  setLatLngParams();
  loadPicnicTables(map.getBounds().toArray());
});

map.on("zoomend", function () {
  setLatLngParams();
  const was = prevZoom;
  prevZoom = map.getZoom();
  setPicnicControlVisibility();
  if (map.getZoom() > was) {
    console.log("zoom in, skipping query");
    return;
  }
  loadPicnicTables(map.getBounds().toArray());
});

map.on("dragend", function () {
  setLatLngParams();
  loadPicnicTables(map.getBounds().toArray());
});

/* 
  map controls
*/

function setPicnicControlVisibility() {
  // show message on picnic table display, depending on zoom level
  const control = document.getElementById("picnic-control");
  if (map.getZoom() < minZoom) {
    control.innerHTML =
      '<i class="bi bi-exclamation-circle-fill text-warning"></i> Zoom in to see picnic tables';
  } else {
    control.innerHTML =
      '<i class="bi bi-check-circle-fill  text-success"></i> Showing picnic tables';
  }
}

// message about picnic table display
class picnicControl {
  onAdd(map) {
    this._container = document.getElementById("picnic-control");
    setPicnicControlVisibility();
    return this._container;
  }

  onRemove() {}
}

// style switcher control from https://docs.maptiler.com/sdk-js/examples/control-style-switcher/
class layerSwitcherControl {
  constructor(options) {
    this._container = document.getElementById("style-switcher-control");
  }

  _copyPicnicData(previousStyle, nextStyle) {
    // copy picnic table data when switching map styles
    const picnicLayer = previousStyle.layers.find(
      (layer) => layer.id === "picnic",
    );
    return {
      ...nextStyle,
      sources: {
        ...nextStyle.sources,
        picnicSource: previousStyle.sources.picnicSource,
      },
      layers: nextStyle.layers.concat(picnicLayer),
    };
  }

  onAdd(map) {
    // show outdoor and satellite basemaps
    ["OUTDOOR", "SATELLITE"].forEach((layerId) => {
      const basemapContainer = document.getElementById(layerId);
      basemapContainer.addEventListener("click", () => {
        const activeElement = this._container.querySelector(".active");
        activeElement.classList.remove("active");
        basemapContainer.classList.add("active");
        map.setStyle(maptilersdk.MapStyle[layerId], {
          transformStyle: this._copyPicnicData,
        });
      });
    });
    return this._container;
  }

  onRemove() {}
}

map.addControl(new layerSwitcherControl(), "bottom-left");
map.addControl(new picnicControl(), "bottom-right");

/*
  load picnic table data from FlatGeobuf
*/

function setLatLngParams() {
  // set lat and lng url params to map center
  const center = map.getCenter();
  const lat = center.lat.toFixed(3);
  const lng = center.lng.toFixed(3);
  const url = `${window.location.origin}${window.location.pathname}?lat=${lat}&lng=${lng}`;
  console.log(`center: ${lat}, ${lng}`);
  history.pushState({}, null, url);
}

function addFeatures(newFeatures) {
  // add new features to picic GeoJSON if not already present
  const ids = new Set(
    PICNIC.features.map((feature) => {
      return feature.properties.id;
    }),
  );
  console.log(
    `${ids.size} current features; ${newFeatures.length} new features`,
  );
  const seenIds = new Set(ids);
  newFeatures.forEach((feature) => {
    if (!seenIds.has(feature.properties.id)) {
      seenIds.add(feature.properties.id);
      PICNIC.features.push(feature);
    }
  });
  if (PICNIC.features.length > ids.size) {
    console.log(`${PICNIC.features.length - ids.size} new features`);
    map.getSource("picnicSource").setData(PICNIC);
  }
}

async function loadPicnicTables(bbox) {
  // load picnic tables within a bounding box from PICNIC_DATA_URL, using
  // FlatGeobuf's packed Hilbert R-tree index + HTTP range requests to
  // fetch only the bytes covering the requested area
  // Map Tiler returns LngLatBounds southwest and northeast coordinates
  // as an array: [[(-121.94,37.37,-121.70,37.48)]]
  if (map.getZoom() < minZoom) {
    console.log("zoomed out too far: ", map.getZoom());
    return;
  }
  const sw = bbox[0];
  const ne = bbox[1];
  // round to 3 decimal places (~110m) to dedupe near-identical queries
  const bboxStr = `${sw[1].toFixed(3)},${sw[0].toFixed(3)},${ne[1].toFixed(3)},${ne[0].toFixed(3)}`;
  if (boxes.has(bboxStr)) {
    console.log("already queried bbox ", bboxStr);
    return;
  }
  boxes.add(bboxStr);
  const rect = { minX: sw[0], minY: sw[1], maxX: ne[0], maxY: ne[1] };
  const features = [];
  for await (const feature of flatgeobuf.deserialize(PICNIC_DATA_URL, rect)) {
    features.push(feature);
  }
  console.log(`loaded ${features.length} picnic table features`);
  addFeatures(features);
}
