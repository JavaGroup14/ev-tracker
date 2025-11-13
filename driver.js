// MAP  
const map = L.map("map").setView([17.9837, 79.5300], 16);
L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", { maxZoom: 18 }).addTo(map);

// LIVE REQUESTS 
let driverMarkers = [];
const centerLat = 17.9837;
const centerLng = 79.5300;

function addLiveRequests() {
  if (driverMarkers.length > 35) {
    const old = driverMarkers.shift();
    map.removeLayer(old);
  }

  const randomLat = centerLat + (Math.random() - 0.5) * 0.008;
  const randomLng = centerLng + (Math.random() - 0.5) * 0.008;

  const marker = L.circleMarker([randomLat, randomLng], {
    radius: 6,
    fillColor: "#00ff6a",
    color: "#007a3d",
    weight: 1,
    fillOpacity: 0.9
  }).addTo(map);

  marker.bindPopup("🎓 New Student Request");
  driverMarkers.push(marker);

  setTimeout(() => {
    map.removeLayer(marker);
    driverMarkers = driverMarkers.filter(m => m !== marker);
  }, 25000);
}
setInterval(addLiveRequests, 1500);

// DRIVER DETAILS 
const toggleDetails = document.getElementById("toggleDetails");
const driverDetails = document.getElementById("DriverDetails");

toggleDetails.addEventListener("click", () => {
  const visible = driverDetails.style.display === "block";
  driverDetails.style.display = visible ? "none" : "block";
  toggleDetails.textContent = visible ? "Show Details" : "Hide Details";
});

// STATUS  
const statusBtn = document.getElementById("statusBtn");
const capacityBtn = document.getElementById("capacityBtn");
const scanBtn = document.getElementById("scanBtn");
const qrModal = document.getElementById("qrModal");
const closeQr = document.getElementById("closeQr");

statusBtn.addEventListener("click", () => {
  const online = statusBtn.textContent.includes("Online");
  statusBtn.textContent = online ? "🔴 Offline" : "🟢 Online";
  statusBtn.classList.toggle("offline", online);
});

capacityBtn.addEventListener("click", () => {
  const full = capacityBtn.textContent.includes("Available");
  capacityBtn.textContent = full ? "🔴 Full" : "🟡 Available";
  capacityBtn.classList.toggle("full", !full);
});

scanBtn.addEventListener("click", () => qrModal.style.display = "flex");
closeQr.addEventListener("click", () => qrModal.style.display = "none");

// LOGOUT 
const logoutBtn = document.getElementById("logoutBtn");
logoutBtn.addEventListener("click", () => {
  alert("You have been successfully logged out.");
  localStorage.removeItem("DriverName");
  window.location.href = "index.html";
});

//  PROFILE 
const name = localStorage.getItem("DriverName") || "Anil Kumar";
document.getElementById("DriverName").textContent = name;
document.getElementById("DriverInitials").textContent = name.split(" ").map(w => w[0]).join("").toUpperCase();
