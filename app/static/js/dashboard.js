const hindi = document.documentElement.lang === "hi";

async function loadDashboard(lat, lon) {
  const response = await fetch(`/api/dashboard-data?lat=${encodeURIComponent(lat)}&lon=${encodeURIComponent(lon)}`);
  const data = await response.json();

  if (!response.ok) {
    document.getElementById("locationAlert").innerHTML =
      `<div class="alert alert-danger">${data.error || (hindi ? "डैशबोर्ड लोड नहीं हो सका।" : "Unable to load dashboard.")}</div>`;
    return;
  }

  if (!data.weather || !data.weather.available) {
    document.getElementById("locationAlert").innerHTML =
      `<div class="alert alert-warning">${data.weather?.message || (hindi ? "मौसम की जानकारी उपलब्ध नहीं है।" : "Weather unavailable.")}</div>`;
  } else {
    const w = data.weather;
    document.getElementById("weatherLocation").textContent =
      `${w.city || "Your location"} ${w.country ? "• " + w.country : ""}`;
    document.getElementById("weatherTemp").textContent = `${w.temperature}°C`;
    document.getElementById("humidity").textContent = `${w.humidity}%`;
    document.getElementById("feels").textContent = `${w.feels_like}°C`;
    document.getElementById("wind").textContent = w.wind_speed;
    document.getElementById("rain").textContent = w.rain_1h;
    document.getElementById("weatherDescription").textContent = w.description;

    document.getElementById("forecast").innerHTML = w.forecast.map(d => `
      <div class="col">
        <div class="forecast-card">
          <strong>${d.date.slice(5)}</strong>
          <div class="fs-5 mt-2">${d.max}° / ${d.min}°</div>
          <small>${d.description}</small>
          <div class="text-primary mt-1">🌧 ${d.rain_mm} mm</div>
        </div>
      </div>`).join("");
  }

  document.getElementById("savedCrops").innerHTML = data.saved_crops.length
    ? data.saved_crops.map(c => `<div class="border rounded p-2 mb-2">
        ${c.emoji} <strong>${c.crop}</strong><br><small>${c.stage}</small>
      </div>`).join("")
    : `<p class="text-muted">${hindi ? "अभी तक कोई फसल सहेजी नहीं गई है।" : "No saved crops yet."}</p>`;

  document.getElementById("advice").innerHTML = data.advice.length
    ? data.advice.map(a => `<div class="advice-item ${a.severity}">
        <strong>${a.crop}: ${a.title}</strong><br><span>${a.text}</span>
      </div>`).join("")
    : `<p class="text-muted">${hindi ? "अभी मौसम के आधार पर कोई विशेष सलाह नहीं है।" : "No weather-triggered advice right now."}</p>`;
}

function requestLocation() {
  if (!navigator.geolocation) {
    document.getElementById("locationAlert").innerHTML =
      `<div class="alert alert-warning">${hindi ? "यह ब्राउज़र स्थान पता करने की सुविधा नहीं देता।" : "Geolocation is not supported. Set location manually in your profile in a future version."}</div>`;
    return;
  }
  navigator.geolocation.getCurrentPosition(
    position => loadDashboard(position.coords.latitude, position.coords.longitude),
    () => {
      document.getElementById("locationAlert").innerHTML =
        `<div class="alert alert-warning">${hindi ? "स्थान की अनुमति नहीं मिली। निर्देशांक के बिना मौसम की जानकारी नहीं मिल सकती।" : "Location permission was denied. Weather cannot be loaded without coordinates."}</div>`;
    },
    { enableHighAccuracy: false, timeout: 10000, maximumAge: 300000 }
  );
}

document.getElementById("locateBtn")?.addEventListener("click", requestLocation);
window.addEventListener("load", requestLocation);
