$(document).ready(function(){    

    $("#toMap").click(function(){

        $("#frontpage").hide(200);

    });

    $("#toInfo").click(function(){

        $("#info-box-container").show();

    })

    $("#info-button-on-map").click(function(){

        $("#info-box-container").show();

    })
    
    $("#close-button").click(function(){

        $("#info-box-container").hide();

    })

});



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
var crashStyle = {
    radius: 5,
    fillOpacity: 0.9,
    stroke: false
}

//string for classes
var crashClass = ''

//conditional styling by injury type
function injury (feature, crashStyle, crashClass) {
    
    if (feature.properties.ij == 'f') {
        crashStyle.fillColor = "#ff1a1a";
        crashClass = crashClass + "f";
    
    } else if (feature.properties.ij == 's') {
        crashStyle.fillColor = "#ff821a";
        crashClass = crashClass + "s";
    
    } else if (feature.properties.ij == 'm') {
        crashStyle.fillColor = "#a7ee18";
        crashClass = crashClass + "m";
    
    } else if (feature.properties.ij == 'n') {
        crashStyle.fillColor = "#15CC15";
        crashClass = crashClass + "n";
    
    };

    if (feature.properties.to) {
        crashClass = crashClass + " to";
    };

    if (feature.properties.al) {
        crashClass = crashClass + " al";
    };

    if (feature.properties.dr) {
        crashClass = crashClass + " dr";
    };

    if (feature.properties.cp) {
        crashClass = crashClass + " cp";
    };   
    
    if (feature.properties.fg) {
        crashClass = crashClass + " fg";
    };

    if (feature.properties.sp) {
        crashClass = crashClass + " sp";
    };
    
    if (feature.properties.dd) {
        crashClass = crashClass + " dd";
    };

    if (feature.properties.ca) {
        crashClass = crashClass + " ca";
    };

    if (feature.properties.pd) {
        crashClass = crashClass + " pd";
    };

    if (feature.properties.cy) {
        crashClass = crashClass + " cy";
    };

    if (feature.properties.mc) {
        crashClass = crashClass + " mc";
    };

    if (feature.properties.tx) {
        crashClass = crashClass + " tx";
    };

    if (feature.properties.tr) {
        crashClass = crashClass + " tr";
    };

    if (feature.properties.h == "Easter Holiday 2014") {
        crashClass = crashClass + " Easter2014";
    };

    if (feature.properties.h == "Queen's Birthday 2014") {
        crashClass = crashClass + " QB2014";
    };

    if (feature.properties.h == "Christmas/New Year 2013-14") {
        crashClass = crashClass + " XmasNY2014";
    };

    crashStyle.className = crashClass;

    return crashStyle;
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

//path to the crash geojson from nzta2geojson.py
var crashes = "./data/data.geojson"

//create layers, bind popups (auto pan padding around popup to allow for streetview image) and filter the data. Add to map when clicked in the selector. One for each selection. Probably a more efficient way to do this
var layers = {};

//layers["All crashes<div id='clear'></div><h4>Filter by consequence</h4>"] = 

new L.GeoJSON.AJAX(crashes,{
    
    pointToLayer: function(feature, latlng) {
            
        return new L.CircleMarker(latlng, injury(feature, crashStyle, crashClass))

    },
    
    onEachFeature: function(feature, layer) {
        
        layer.bindPopup(popUpText(feature), {offset: L.point(0, -2), autoPanPadding: L.point(0, 10)})
    
    },

    filter: function(feature, layer) {

        return true

    }

}).addTo(map);

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

    //crash selector functionality checks for changes. CSS hide and show. Data called once. If 'All crashes' clicked nothing else can be checked. If others clicked 'All crashes' can't be checked.

    $("#checkArray").click(function(){

        $(function () {

            $('#allCheck').on('click', function () {
        
                $(this).closest('fieldset').find(':checkbox').prop('checked', false);
            
            });
        
        });

        var crashClassSelected = 'path';

        $(crashClassSelected).css('display', 'none');

        $("#checkArray input[type=checkbox]").each(
            
            function() {
            
                if($(this).is(':checked')) {

                    crashClassSelected = crashClassSelected + $(this).val();

                }
            }
        )

        $(crashClassSelected).css('display', 'block');

        if(crashClassSelected == 'path') {

            $('#allCheck').prop('checked', true);

        } else {

            $('#allCheck').prop('checked', false);

        };

    })

});

//crash selector functionality checks for changes. CSS hide and show. Data called once. If 'All crashes' clicked nothing else can be checked. If others clicked 'All crashes' can't be checked.
$(document).ready(function(){


});