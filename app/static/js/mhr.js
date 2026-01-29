
mapboxgl.accessToken = 'pk.eyJ1IjoiamltbXlnb29nbGUiLCJhIjoiY21rYmQ0dnVyMDJvdDNkcTNudWRsM3J2ZSJ9.3ctw2m9IKWZqevqHcAxuew';

const map = new mapboxgl.Map({
    container: 'map',
    style: 'mapbox://styles/mapbox/streets-v12',
    zoom: 5,
    projection: 'mercator',
    pitch: 0,
    bearing: 0
});

const nav = new mapboxgl.NavigationControl();
map.addControl(nav, 'top-left');

// our reference point for distance queries
let referencePoint = null; 
let markers = [];
let referenceMarker;
let selectedMarker = null;

// geographic center of the US
const DEFAULT_CENTER = {
  lat: 39.8283,
  lon: -98.5795   
};

// default max miles when there is no geolocation set
const DEFAULT_MILES = 250;

// attempt to get user location
if (navigator.geolocation) {
    navigator.geolocation.getCurrentPosition(
        (position) => {
            referencePoint = {
                lat: position.coords.latitude,
                lon: position.coords.longitude
            };

            // center map on user
            //map.setCenter([referencePoint.lon, referencePoint.lat]);
            map.setZoom(7);

            const marker = new mapboxgl.Marker({ color: "var(--primary-color)" })
                .setLngLat([referencePoint.lon, referencePoint.lat])
                .addTo(map);

            markers.push(marker);

            // set default reset (this can be changed)
            const link = document.getElementById('default-association-reference');
            link.dataset.lat = referencePoint.lat;
            link.dataset.lon = referencePoint.lon;

            loadAssociations();
        },
        (err) => {
            console.warn("Geolocation failed, using default center", err);
            loadAssociations();
        }
    );
    } else {
        console.warn("Geolocation not supported, using default center");
        loadAssociations();
}

function getMapCenter() {
    // there is no geolocation enabled so setup the lat/lon and make some UI tweaks
    referencePoint = {lat: DEFAULT_CENTER.lat, lon: DEFAULT_CENTER.lon };
    document.getElementById("maxMiles").value = DEFAULT_MILES;
    document.getElementById("milesValue").textContent = DEFAULT_MILES;
    document.getElementById("geolocation-disabled").style.display = "block";
    document.getElementById("default-association-reference").style.display = "none";

    return {
        lat: DEFAULT_CENTER.lat,
        lon: DEFAULT_CENTER.lon
    };
}

function updateMap(geojson) {
    // remove old markers
    markers.forEach(m => m.remove());
    markers = [];

    // center map on user
    map.setCenter([referencePoint.lon, referencePoint.lat]);

    const marker = new mapboxgl.Marker({ color:"var(--accent-color)" })
        .setLngLat([referencePoint.lon, referencePoint.lat])
        .addTo(map);

    markers.push(marker);

    geojson.features.forEach(f => {
        const [lon, lat] = f.geometry.coordinates;
        const { name, mhr_association_url, association_url, teams } = f.properties;

        let color = "var(--primary-color)";

        if (lon == referencePoint.lon && lat == referencePoint.lat) {
            color = "var(--accent-color)";
        }

        // create marker
        const marker = new mapboxgl.Marker({ color: color })
        .setLngLat([lon, lat])
        .setPopup(new mapboxgl.Popup({ offset: 25, maxWidth: '300px' }).setHTML(
            `<center><strong><a href="${mhr_association_url}" target="_blank">${name}</a></strong><br/>` +
            `(<a href="#" class="association-reference" data-lat="${lat}" data-lon="${lon}">Set as default organization</a>)</center><br/>` +
            `<strong>Website:</strong><br/><a href="${association_url}" target="_blank">${association_url}</a></br><br/>` + 
            `<strong>Teams:</strong></br>` +
            (teams ? teams.map(t => `<a href="${t.team_url}" target="_blank">${t.team_name}</a>: ${t.rating}`).join("</br>") : "")
        ))
        .addTo(map);

        const el = marker.getElement();
        markers.push(marker);
    });
}

// we are setting an association as a new reference point
document.addEventListener('click', (e) => {
  const link = e.target.closest('.association-reference');
  if (!link) return;

  e.preventDefault();

  const lat = parseFloat(link.dataset.lat);
  const lon = parseFloat(link.dataset.lon);

    referencePoint = { lat, lon };
    loadAssociations();
});

// we are restoring the default reference point (geolocation or user set)
document.addEventListener('click', (e) => {
  const link = e.target.closest('#default-association-reference');
  if (!link) return;

  e.preventDefault();

  const lat = parseFloat(link.dataset.lat);
  const lon = parseFloat(link.dataset.lon);

    referencePoint = { lat, lon };
    loadAssociations();
});

async function loadAssociations() {
    console.log(referencePoint);
    const { lat, lon } = referencePoint || getMapCenter();

    console.log("lat " + lat);
    console.log("lon " + lon);

    const minRating = document.getElementById("minRating").value;
    const maxRating = document.getElementById("maxRating").value;
    const maxMiles = document.getElementById("maxMiles").value;
    const tier = Array.from(document.querySelectorAll('input[name="tier"]:checked')).map(cb => cb.value);
    const age = Array.from(document.querySelectorAll('input[name="age"]:checked')).map(cb => cb.value);
    const region = Array.from(document.querySelectorAll('input[name="region"]:checked')).map(cb => cb.value);

    const params = new URLSearchParams({
        lat,
        lon,
        region,
        age,
        tier,
        min_rating: minRating,
        max_rating: maxRating,
        max_miles: maxMiles
    });

    showLoader();

    try {
        const response = await fetch(`/associations?${params}`);
        const data = await response.json();

        console.log(data);
        updateMap(data);
    } catch (err) {
        console.error("Error loading associations:", err);
    }
    finally {
        hideLoader();
    }
}

const slider = document.getElementById("maxMiles");
const output = document.getElementById("milesValue");

slider.addEventListener("input", () => {
    output.textContent = slider.value;
});

const form = document.getElementById('mhr_filters');

// change the map when the filters change
form.addEventListener('change', (e) => {
  const el = e.target;
  loadAssociations();
});

const loader = document.getElementById('loader');

function showLoader() {
  loader.classList.remove('hidden');
}

function hideLoader() {
  loader.classList.add('hidden');
}

document.addEventListener('click', (e) => {
  const filterToggle = e.target.closest('.filter-toggle');
  if (!filterToggle) return;

  const group = filterToggle.closest('.filter-group');
  group.classList.toggle('collapsed');
  filterToggle.classList.toggle('collapsed-rounded');

  filterToggle.setAttribute(
    'aria-expanded',
    !group.classList.contains('collapsed')
  );
});
