// ─── FETCH EXPERIENCE DATA FROM BACKEND ──────────────────────────────────────
let experiences = [];
let dataLoaded = false;

// Initialise MapLibre with bright style and 3D view
const map = new maplibregl.Map({
  style: "https://tiles.openfreemap.org/styles/bright",
  center: [121.0, 14.6], // Default to Philippines
  zoom: 15.5,
  pitch: 45,
  bearing: -17.6,
  container: "map",
  canvasContextAttributes: { antialias: true },
});

map.addControl(new maplibregl.NavigationControl(), "top-left");

map.on("load", () => {
  // Add 3D buildings layer
  const layers = map.getStyle().layers;
  let labelLayerId;
  for (let i = 0; i < layers.length; i++) {
    if (layers[i].type === "symbol" && layers[i].layout["text-field"]) {
      labelLayerId = layers[i].id;
      break;
    }
  }

  map.addSource("openfreemap", {
    url: "https://tiles.openfreemap.org/planet",
    type: "vector",
  });

  map.addLayer(
    {
      id: "3d-buildings",
      source: "openfreemap",
      "source-layer": "building",
      type: "fill-extrusion",
      minzoom: 15,
      filter: ["!=", ["get", "hide_3d"], true],
      paint: {
        "fill-extrusion-color": [
          "interpolate",
          ["linear"],
          ["get", "render_height"],
          0,
          "lightgray",
          200,
          "royalblue",
          400,
          "lightblue",
        ],
        "fill-extrusion-height": [
          "interpolate",
          ["linear"],
          ["zoom"],
          15,
          0,
          16,
          ["get", "render_height"],
        ],
        "fill-extrusion-base": [
          "case",
          [">=", ["get", "zoom"], 16],
          ["get", "render_min_height"],
          0,
        ],
      },
    },
    labelLayerId,
  );

  if (dataLoaded) {
    addMarkers();
    // Center on point with id = 1 at zoom level 15
    const firstExp = experiences.find((exp) => exp.id === 1);
    if (firstExp) {
      map.flyTo({ center: firstExp.coords, zoom: 17, duration: 1000 });
    }
  }
});

fetch("/data")
  .then((response) => response.json())
  .then((data) => {
    experiences = data.features.map((feature) => ({
      id: feature.properties.id,
      country: feature.properties.country,
      role: feature.properties.title,
      place: feature.properties.place,
      period: feature.properties.period,
      description: feature.properties.description,
      safety: feature.properties.safety,
      inclusiveness: feature.properties.inclusiveness,
      women_spaces: feature.properties.women_spaces,
      coords: feature.geometry.coordinates,
    }));

    // Sort experiences by id ascending
    experiences.sort((a, b) => a.id - b.id);

    dataLoaded = true;
    buildExperienceList();
    if (map.loaded()) {
      addMarkers();
    }
  })
  .catch((error) => console.error("Error fetching data:", error));
// Function to generate star rating
function getStars(rating) {
  const filled = "★".repeat(rating);
  const empty = "☆".repeat(5 - rating);
  return filled + empty;
}

// Build the experience list in the sidebar
function buildExperienceList() {
  const expList = document.getElementById("exp-list");
  experiences.forEach((exp) => {
    const item = document.createElement("div");
    item.className = "exp-item";
    item.dataset.id = exp.id;
    item.innerHTML = `
      <div class="exp-dot"></div>
      <div class="exp-info">
        <div class="exp-role">${exp.role}</div>
        <div class="exp-place">${exp.place}</div>
        <div class="exp-period">${exp.period}</div>
      </div>`;
    item.addEventListener("click", () => selectExp(exp.id));
    expList.appendChild(item);
  });
}

// Add markers to the map
function addMarkers() {
  experiences.forEach((exp) => {
    const el = document.createElement("div");
    el.className = "marker-pin";
    el.title = `${exp.role} · ${exp.country}`;

    const marker = new maplibregl.Marker({ element: el, anchor: "bottom" })
      .setLngLat(exp.coords)
      .addTo(map);

    markers[exp.id] = { marker, el };

    el.addEventListener("click", (e) => {
      e.stopPropagation();
      selectExp(exp.id);
    });
  });
}

const detail = document.getElementById("detail");
const hint = document.getElementById("sidebar-hint");
const expList = document.getElementById("exp-list");

let activeId = null;
const markers = {};
let activePopup = null;

function selectExp(id) {
  const exp = experiences.find((e) => e.id === id);
  if (!exp) return;

  // Update sidebar list highlight
  document.querySelectorAll(".exp-item").forEach((el) => {
    el.classList.toggle("active", el.dataset.id == id);
  });

  // Update marker highlight
  Object.entries(markers).forEach(([mid, { el }]) => {
    el.classList.toggle("active", mid == id);
  });

  // Fly map to pin
  map.flyTo({ center: exp.coords, zoom: 17, duration: 1200, essential: true });

  // Close previous popup
  if (activePopup) activePopup.remove();

  // Open new popup
  activePopup = new maplibregl.Popup({ closeButton: false, offset: [0, -20] })
    .setLngLat(exp.coords)
    .setHTML(
      `
      <div class="maplibregl-popup-content">
        <img src="img/${exp.id}.jpg" alt="${exp.place}" class="popup-image">
        <div class="popup-role">${exp.role}</div>
        <div class="popup-place">${exp.place}</div>
        <div class="popup-period">${exp.period}</div>
      </div>
    `,
    )
    .addTo(map);

  // Populate detail panel
  document.getElementById("detail-role").textContent = exp.role;
  document.getElementById("detail-place").textContent = exp.place;
  document.getElementById("detail-country").textContent = exp.country;
  document.getElementById("detail-period").textContent = exp.period;
  document.getElementById("detail-desc").textContent = exp.description;

  document.getElementById("detail-safety").innerHTML = getStars(exp.safety);
  document.getElementById("detail-inclusiveness").innerHTML = getStars(
    exp.inclusiveness,
  );
  document.getElementById("detail-women-spaces").innerHTML = getStars(
    exp.women_spaces,
  );

  detail.classList.add("visible");
  activeId = id;
}

// Click map background → reset to list view
map.on("click", () => {
  if (activePopup) {
    activePopup.remove();
    activePopup = null;
  }
  document
    .querySelectorAll(".exp-item")
    .forEach((el) => el.classList.remove("active"));
  Object.values(markers).forEach(({ el }) => el.classList.remove("active"));
  detail.classList.remove("visible");
  activeId = null;
});
