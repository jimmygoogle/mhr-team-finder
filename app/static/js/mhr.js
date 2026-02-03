
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

            loadMHRData();
        },
        (err) => {
            console.warn("Geolocation failed, using default center", err);
            loadMHRData();
        }
    );
    } else {
        console.warn("Geolocation not supported, using default center");
        loadMHRData();
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
    // clear search boxes
    document.getElementById("association-search").value = '';
    document.getElementById("team-search").value = '';

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
    loadMHRData();
});

// we are restoring the default reference point (geolocation or user set)
document.addEventListener('click', (e) => {
  const link = e.target.closest('#default-association-reference');
  if (!link) return;

  e.preventDefault();

  const lat = parseFloat(link.dataset.lat);
  const lon = parseFloat(link.dataset.lon);

    referencePoint = { lat, lon };
    loadMHRData();
});

async function loadMHRData() {
    const { lat, lon } = referencePoint || getMapCenter();
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
        const response = await fetch(`/hockey?${params}`);
        const data = await response.json();

        updateMap(data);
    } catch (err) {
        console.error("Error loading data:", err);
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

    if (el.tagName === "INPUT" && el.type === "text") {
        return;
    }

    loadMHRData();
});

const loader = document.getElementById('loader');

function showLoader() {
    loader.classList.remove('hidden');
}

function hideLoader() {
    loader.classList.add('hidden');
}

document.addEventListener('DOMContentLoaded', () => {
    if (window.innerWidth <= 768) {
        document.querySelectorAll('.filter-group').forEach(group => {
            group.classList.add('collapsed');

            const toggle = group.querySelector('.filter-toggle');
            if (toggle) {
                toggle.classList.add('collapsed-rounded');
            }
        });
    }
});

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

function debounce(fn, delay = 300) {
    let timeout;
    return (...args) => {
        clearTimeout(timeout);
        timeout = setTimeout(() => fn(...args), delay);
    };
}

const associationInput = document.getElementById("association-search");
const associationFilterOptions = associationInput.closest(".filter-options");
const associationResults = document.getElementById("association-results");

associationInput.addEventListener("input", () => {
    associationFilterOptions.classList.add("active");
});

const teamInput = document.getElementById("team-search");
const teamFilterOptions = teamInput.closest(".filter-options");
const teamResults = document.getElementById("team-results");

teamInput.addEventListener("input", () => {
    teamFilterOptions.classList.add("active");
});

async function searchMHRData(query, type) {
    let results = teamResults;
    let input = teamInput;

    if (type == 'associations') {
        results = associationResults;
        input = associationInput;
    }

    if (!query || query.length < 2) {
        results.innerHTML = "";
        results.classList.add("hidden");
        return;
    }

    // show .search-results css
    results.classList.add("open");

    const resp = await fetch(`/${type}?q=${encodeURIComponent(query)}`);
    const data = await resp.json();

    results.innerHTML = "";

    if (!data.length) {
        results.classList.add("hidden");
        return;
    }

    data.forEach(d => {
        const li = document.createElement("li");
        li.textContent = d.name;

        li.addEventListener("click", () => {
            input.value = d.name;
            results.innerHTML = "";
            results.classList.add("hidden");

            referencePoint = {lat: d.lat, lon: d.lon };
            loadMHRData();
        });

        results.appendChild(li);
    });

    results.classList.remove("hidden");
}

associationInput.addEventListener("input", debounce(e => searchMHRData(e.target.value, 'associations')));
teamInput.addEventListener("input", debounce(e => searchMHRData(e.target.value, 'teams')));

associationInput.addEventListener("click", e => {
    if (!e.target.closest(".typeahead")) {
        associationResults.classList.add("hidden");
    }
});

teamInput.addEventListener("click", e => {
    if (!e.target.closest(".typeahead")) {
        teamResults.classList.add("hidden");
    }
});
