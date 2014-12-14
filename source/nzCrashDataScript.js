var map = L.map('map').setview([51.505, -0.09], 13);

L.tileLayer("http://{s}.tiles.mapbox.com/v3/MapID/{z}/{x}/{y}.png", {
	attribution: "Map data &copy; [...]",
	maxZoom: 18
}).addTo(map);