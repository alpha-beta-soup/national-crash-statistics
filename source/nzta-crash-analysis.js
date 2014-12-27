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
    
    if (feature.properties.ij == 'f') {
        return fatalCrashStyle
    
    } else if (feature.properties.ij == 's') {
        return severeCrashStyle
    
    } else if (feature.properties.ij == 'm') {
        return minorCrashStyle
    
    } else if (feature.properties.ij == 'n') {
        return noInjuryCrashStyle
    
    };
}

//pop-up text function different if other parties involved. Bound to when events are retrieved from data
function popUpText (row, layer) {      
    return '<span class="crash-location">' + row.properties.t + "</span>" +
           '<span class="date">' + row.properties.d + ", " + row.properties.dt + "</span>" +
           '<span class="time">' + row.properties.ti + '</span>' +
           '<span><div id="environment-icons">' + row.properties.e + '</div></span>' +
           '<span class="road">' + row.properties.r + "</span>" +
           '<span><div id="streetview-container">' + row.properties.s+ '</div></span>' +
           '<span><div id="vehicle-injury"><div id="vehicle-icons">' + row.properties.v + '</div><div id="injury-icons">' + row.properties.i + '</div><div id="clear"></div></div></span>' +
           '<span class="causes-text">' + row.properties.c + '</span>'
};

//create div that appears above the layer selector for explanation and clarity
var layerTitle = L.Control.extend({
    
    options:{
    
        position: 'topright'
    
    },
    
    onAdd: function (map) {

        var container = L.DomUtil.create('div', 'layerTitle');
        
        
        
        container.innerHTML = '<h3><span class="red">Crash</span> events</h3>';
        
        return container;
    
    }

});

//add layer title to the map
map.addControl(new layerTitle());            

//path to the crash geojson from nzta2geojson.py
var crashes = "./data/data.geojson"

//create layers, bind popups (auto pan padding around popup to allow for streetview image) and filter the data. Add to map when clicked in the selector. One for each selection. Probably a more efficient way to do this
var layers = {};
layers["All crashes<div id='clear'></div><h4>Filter by consequence</h4>"] = new L.GeoJSON.AJAX(crashes,{
    
    pointToLayer: function(feature, latlng) {
            
        return new L.CircleMarker(latlng, injury(feature))

    },
    
    onEachFeature: function(feature, layer) {
        
        layer.bindPopup(popUpText(feature), {offset: L.point(0, -2), autoPanPadding: L.point(0, 10)})
    
    },

    filter: function(feature, layer) {

        return true

    }

})//.addTo(map);

layers["<div class='legendEntry'><div class='legendText'>Fatal</div><div class='legendDot' id='redDot'></div></div><div id='clear'></div>"] = new L.GeoJSON.AJAX(crashes,{
    
    pointToLayer: function(feature, latlng) {
            
        return new L.CircleMarker(latlng, injury(feature))

    },
    
    onEachFeature: function(feature, layer) {
        
        layer.bindPopup(popUpText(feature), {offset: L.point(0, -2), autoPanPadding: L.point(0, 10)})
    
    },

    filter: function(feature, layer) {

        return feature.properties.ij == 'f'

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

        return feature.properties.ij == 's'

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

        return feature.properties.ij == 'm'

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

        return feature.properties.ij == 'n'

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

        return feature.properties.to

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

        return feature.properties.al

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

        return feature.properties.dr

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

        return feature.properties.cp

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

        return feature.properties.fg

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

        return feature.properties.sp

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

        return feature.properties.dd

    }

})//.addTo(map);

layers["Car / van / ute / SUV"] = new L.GeoJSON.AJAX(crashes,{
    
    pointToLayer: function(feature, latlng) {
            
        return new L.CircleMarker(latlng, injury(feature))

    },
    
    onEachFeature: function(feature, layer) {
        
        layer.bindPopup(popUpText(feature), {offset: L.point(0, -2), autoPanPadding: L.point(0, 10)})
    
    },

    filter: function(feature, layer) {

        return feature.properties.ca

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

        return feature.properties.pd

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

        return feature.properties.cy

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

        return feature.properties.mc

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

        return feature.properties.tx

    }

})//.addTo(map);

layers["Truck<div id='clear'></div><h4>Official Holiday Periods</h4>"] = new L.GeoJSON.AJAX(crashes,{
    
    pointToLayer: function(feature, latlng) {
            
        return new L.CircleMarker(latlng, injury(feature))

    },
    
    onEachFeature: function(feature, layer) {
        
        layer.bindPopup(popUpText(feature), {offset: L.point(0, -2), autoPanPadding: L.point(0, 10)})
    
    },

    filter: function(feature, layer) {

        return feature.properties.tr

    }

})//.addTo(map);

layers["Easter 2014"] = new L.GeoJSON.AJAX(crashes,{
    
    pointToLayer: function(feature, latlng) {
            
        return new L.CircleMarker(latlng, injury(feature))

    },
    
    onEachFeature: function(feature, layer) {
        
        layer.bindPopup(popUpText(feature), {offset: L.point(0, -2), autoPanPadding: L.point(0, 10)})
    
    },

    filter: function(feature, layer) {

        return feature.properties.h == 'Easter Holiday 2014'

    }

})//.addTo(map);

layers["Queen's Birthday 2014"] = new L.GeoJSON.AJAX(crashes,{
    
    pointToLayer: function(feature, latlng) {
            
        return new L.CircleMarker(latlng, injury(feature))

    },
    
    onEachFeature: function(feature, layer) {
        
        layer.bindPopup(popUpText(feature), {offset: L.point(0, -2), autoPanPadding: L.point(0, 10)})
    
    },

    filter: function(feature, layer) {

        return feature.properties.h == "Queen's Birthday 2014"

    }

})//.addTo(map);

layers["Christmas & New Year 2013–14"] = new L.GeoJSON.AJAX(crashes,{
    
    pointToLayer: function(feature, latlng) {
            
        return new L.CircleMarker(latlng, injury(feature))

    },
    
    onEachFeature: function(feature, layer) {
        
        layer.bindPopup(popUpText(feature), {offset: L.point(0, -2), autoPanPadding: L.point(0, 10)})
    
    },

    filter: function(feature, layer) {

        return feature.properties.h == 'Christmas/New Year 2013-14'

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
