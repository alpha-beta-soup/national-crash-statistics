//where, initial zoom level and remove zoom buttons
var map = L.map('map', {
    zoomControl: false,
    continuousWorld: true,
    worldCopyJump: true
    }).setView([-41.17, 174.46], 6);


//base map tiles, zoom and attribution
L.tileLayer(
    //found other base maps here: http://wiki.openstreetmap.org/wiki/OpenLayers
    'https://stamen-tiles-{s}.a.ssl.fastly.net/toner-lite/{z}/{x}/{y}.png' //toner stamen 
    , {
    maxZoom: 18,
    minZoom: 5,
    attribution: 'Crash data from <a href="http://www.nzta.govt.nz/resources/crash-analysis-reports/">NZTA</a>, under <a href="https://creativecommons.org/licenses/by/3.0/nz/">CC BY 3.0 NZ</a>, presented with changes | Map tiles by <a href="http://stamen.com">Stamen Design</a>, under <a href="http://creativecommons.org/licenses/by/3.0">CC BY 3.0</a> | Data by <a href="http://openstreetmap.org">OpenStreetMap</a>, under <a href="http://creativecommons.org/licenses/by-sa/3.0">CC BY SA</a>'

}).addTo(map);

//styles for crash points
var fatalCrashStyle = {
    radius: 5,
    fillOpacity: 0.9,
    fillColor: "#ff1a1a",
    stroke: false
}
var severeCrashStyle = {
    radius: 5,
    fillOpacity: 0.9,
    fillColor: "#ff821a",
    stroke: false
}
var minorCrashStyle = {
    radius: 5,
    fillOpacity: 0.9,
    fillColor: "#a7ee18",
    stroke: false
}
var noInjuryCrashStyle = {
    radius: 5,
    fillOpacity: 0.9,
    fillColor: "#15CC15",
    stroke: false
} 

//conditional styling by injury type
function injury (feature) {
    
    if (feature.properties.fatal == true) {
        return fatalCrashStyle
    
    } else if (feature.properties.severe == true) {
        return severeCrashStyle
    
    } else if (feature.properties.minor == true) {
        return minorCrashStyle
    
    } else if (feature.properties.no_injuries == true) {
        return noInjuryCrashStyle
    
    };
}

//pop-up text function different if other parties involved. Bound to when events are retrieved from data
function popUpText (row, layer) {      
    return '<span class="crash-location">' + row.properties.tla_name + "</span>" +
           '<span class="date">' + row.properties.crash_dow + ", " + row.properties.crash_date + "</span>" +
           '<span class="time">' + row.properties.crash_time + '</span>' +
           '<span class="environment-icons">' + row.properties.environment_icons + '</span>' +
           '<span class="road">' + row.properties.crash_road + "</span>" +
           '<div class="streetview-container">' + row.properties.streetview + '</div><br>' +
           '<span class="injury-icons">Injuries: ' + row.properties.injury_icons + '</span><br>' +
           '<span class="vehicle-icons">Vehicles involved: ' + row.properties.vehicle_icons + '</span><br><br>' + 
           '<span class="causes-text">' + row.properties.causes + '</span>'
};

//create div that appears above the layer selector for explanation and clarity
var layerTitle = L.Control.extend({
    
    options:{
    
        position: 'topright'
    
    },
    
    onAdd: function (map) {

        var container = L.DomUtil.create('div', 'layerTitle');
        
        container.innerHTML = '<h3><span class="red">Crash</span> events</h3><h4>Filter by consequence</h4>';
        
        return container;
    
    }

});

//add layer title to the map
map.addControl(new layerTitle());            

//path to the crash geojson from nzta2geojson.py
var crashes = "./data/data.geojson"

//create layers, bind popups (auto pan padding around popup to allow for streetview image) and filter the data. Add to map when clicked in the selector. One for each selection. Probably a more efficient way to do this
var layers = {};
layers["<div class='legendEntry'><div class='legendText'>Fatal</div><div class='legendDot' id='redDot'></div></div><div id='clear'></div>"] = new L.GeoJSON.AJAX(crashes,{
    
    pointToLayer: function(feature, latlng) {
            
        return new L.CircleMarker(latlng, injury(feature))

    },
    
    onEachFeature: function(feature, layer) {
        
        layer.bindPopup(popUpText(feature), {offset: L.point(0, -2), autoPanPadding: L.point(0, 10)})
    
    },

    filter: function(feature, layer) {

        return feature.properties.fatal

    }

})//.addTo(map);

layers["<div class='legendEntry'><div class='legendText'>Severe injuries</div><div class='legendDot' id='orangeDot'></div></div><div id='clear'></div>"] = new L.GeoJSON.AJAX(crashes,{
    
    pointToLayer: function(feature, latlng) {
            
        return new L.CircleMarker(latlng, injury(feature))

    },
    
    onEachFeature: function(feature, layer) {
        
        layer.bindPopup(popUpText(feature), {offset: L.point(0, -2), autoPanPadding: L.point(0, 10)})
    
    },

    filter: function(feature, layer) {

        return feature.properties.severe

    }

})//.addTo(map);

layers["<div class='legendEntry'><div class='legendText'>Minor injuries</div><div class='legendDot' id='yellowDot'></div></div><div id='clear'></div>"] = new L.GeoJSON.AJAX(crashes,{
    
    pointToLayer: function(feature, latlng) {
            
        return new L.CircleMarker(latlng, injury(feature))

    },
    
    onEachFeature: function(feature, layer) {
        
        layer.bindPopup(popUpText(feature), {offset: L.point(0, -2), autoPanPadding: L.point(0, 10)})
    
    },

    filter: function(feature, layer) {

        return feature.properties.minor

    }

})//.addTo(map);

layers["<div class='legendEntry'><div class='legendText'>No injuries</div><div class='legendDot' id='greenDot'></div></div><div id='clear'></div><h4>Filter by factor</h4>"] = new L.GeoJSON.AJAX(crashes,{
    
    pointToLayer: function(feature, latlng) {
            
        return new L.CircleMarker(latlng, injury(feature))

    },
    
    onEachFeature: function(feature, layer) {
        
        layer.bindPopup(popUpText(feature), {offset: L.point(0, -2), autoPanPadding: L.point(0, 10)})
    
    },

    filter: function(feature, layer) {

        return feature.properties.no_injuries

    }

})//.addTo(map);

layers["Tourist / recent migrant"] = new L.GeoJSON.AJAX(crashes,{
    
    pointToLayer: function(feature, latlng) {
            
        return new L.CircleMarker(latlng, injury(feature))

    },
    
    onEachFeature: function(feature, layer) {
        
        layer.bindPopup(popUpText(feature), {offset: L.point(0, -2), autoPanPadding: L.point(0, 10)})
    
    },

    filter: function(feature, layer) {

        return feature.properties.tourist

    }

})//.addTo(map);  

layers["Alcohol"] = new L.GeoJSON.AJAX(crashes,{
    
    pointToLayer: function(feature, latlng) {
            
        return new L.CircleMarker(latlng, injury(feature))

    },
    
    onEachFeature: function(feature, layer) {
        
        layer.bindPopup(popUpText(feature), {offset: L.point(0, -2), autoPanPadding: L.point(0, 10)})
    
    },

    filter: function(feature, layer) {

        return feature.properties.alcohol

    }

})//.addTo(map);

layers["Drugs"] = new L.GeoJSON.AJAX(crashes,{
    
    pointToLayer: function(feature, latlng) {
            
        return new L.CircleMarker(latlng, injury(feature))

    },
    
    onEachFeature: function(feature, layer) {
        
        layer.bindPopup(popUpText(feature), {offset: L.point(0, -2), autoPanPadding: L.point(0, 10)})
    
    },

    filter: function(feature, layer) {

        return feature.properties.drugs

    }

})//.addTo(map);

layers["Cellphone"] = new L.GeoJSON.AJAX(crashes,{
    
    pointToLayer: function(feature, latlng) {
            
        return new L.CircleMarker(latlng, injury(feature))

    },
    
    onEachFeature: function(feature, layer) {
        
        layer.bindPopup(popUpText(feature), {offset: L.point(0, -2), autoPanPadding: L.point(0, 10)})
    
    },

    filter: function(feature, layer) {

        return feature.properties.cellphone

    }

})//.addTo(map);

layers["Fatigue"] = new L.GeoJSON.AJAX(crashes,{
    
    pointToLayer: function(feature, latlng) {
            
        return new L.CircleMarker(latlng, injury(feature))

    },
    
    onEachFeature: function(feature, layer) {
        
        layer.bindPopup(popUpText(feature), {offset: L.point(0, -2), autoPanPadding: L.point(0, 10)})
    
    },

    filter: function(feature, layer) {

        return feature.properties.fatigue

    }

})//.addTo(map);

layers["Speed"] = new L.GeoJSON.AJAX(crashes,{
    
    pointToLayer: function(feature, latlng) {
            
        return new L.CircleMarker(latlng, injury(feature))

    },
    
    onEachFeature: function(feature, layer) {
        
        layer.bindPopup(popUpText(feature), {offset: L.point(0, -2), autoPanPadding: L.point(0, 10)})
    
    },

    filter: function(feature, layer) {

        return feature.properties.speed

    }

})//.addTo(map);

layers["Dangerous driving<div id='clear'></div><h4>Filter by party</h4>"] = new L.GeoJSON.AJAX(crashes,{
    
    pointToLayer: function(feature, latlng) {
            
        return new L.CircleMarker(latlng, injury(feature))

    },
    
    onEachFeature: function(feature, layer) {
        
        layer.bindPopup(popUpText(feature), {offset: L.point(0, -2), autoPanPadding: L.point(0, 10)})
    
    },

    filter: function(feature, layer) {

        return feature.properties.dangerous_driving

    }

})//.addTo(map);

layers["Pedestrian"] = new L.GeoJSON.AJAX(crashes,{
    
    pointToLayer: function(feature, latlng) {
            
        return new L.CircleMarker(latlng, injury(feature))

    },
    
    onEachFeature: function(feature, layer) {
        
        layer.bindPopup(popUpText(feature), {offset: L.point(0, -2), autoPanPadding: L.point(0, 10)})
    
    },

    filter: function(feature, layer) {

        return feature.properties.pedestrian

    }

})//.addTo(map);                 

layers["Cyclist"] = new L.GeoJSON.AJAX(crashes,{
    
    pointToLayer: function(feature, latlng) {
            
        return new L.CircleMarker(latlng, injury(feature))

    },
    
    onEachFeature: function(feature, layer) {
        
        layer.bindPopup(popUpText(feature), {offset: L.point(0, -2), autoPanPadding: L.point(0, 10)})
    
    },

    filter: function(feature, layer) {

        return feature.properties.cyclist

    }

})//.addTo(map);

layers["Motorcyclist"] = new L.GeoJSON.AJAX(crashes,{
    
    pointToLayer: function(feature, latlng) {
            
        return new L.CircleMarker(latlng, injury(feature))

    },
    
    onEachFeature: function(feature, layer) {
        
        layer.bindPopup(popUpText(feature), {offset: L.point(0, -2), autoPanPadding: L.point(0, 10)})
    
    },

    filter: function(feature, layer) {

        return feature.properties.motorcyclist

    }

})//.addTo(map);

layers["Taxi"] = new L.GeoJSON.AJAX(crashes,{
    
    pointToLayer: function(feature, latlng) {
            
        return new L.CircleMarker(latlng, injury(feature))

    },
    
    onEachFeature: function(feature, layer) {
        
        layer.bindPopup(popUpText(feature), {offset: L.point(0, -2), autoPanPadding: L.point(0, 10)})
    
    },

    filter: function(feature, layer) {

        return feature.properties.taxi

    }

})//.addTo(map);

layers["Truck"] = new L.GeoJSON.AJAX(crashes,{
    
    pointToLayer: function(feature, latlng) {
            
        return new L.CircleMarker(latlng, injury(feature))

    },
    
    onEachFeature: function(feature, layer) {
        
        layer.bindPopup(popUpText(feature), {offset: L.point(0, -2), autoPanPadding: L.point(0, 10)})
    
    },

    filter: function(feature, layer) {

        return feature.properties.truck

    }

})//.addTo(map);



//add layer selector to the map
L.control.layers(layers,[], {"position":"topright", "collapsed":false}).addTo(map);

//hide function for the sidebar
$(document).ready(function(){
    
    var clicked=false;

    var moveLeft;

    moveLeft = -($("#desc").width());

    $("#circleButton").addClass('rotate');
    
    $("#hideDesc").on('click', function(){
    
    if(clicked){
    
        clicked=false;
    
        $("#sidebarContainer").css({"left": 0});

        $("#circleButton").addClass('rotate');
    
        } else {

        clicked=true;
    
        $("#sidebarContainer").css({"left": moveLeft});

        $("#circleButton").removeClass('rotate');

        }
    
    });

});
