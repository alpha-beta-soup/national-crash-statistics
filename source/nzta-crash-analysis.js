var boolean_properties, cause_decoder, chevron_control, crashes, curve_decoder, deca, frontpage_control, getPointStyleOptions, getPopup, get_attribution, get_causes_text, get_child_injured_icon, get_decoders, get_map, get_moon_icon, get_speed_limit_icon, get_straightforward_icon, get_streetview, get_tileLayer, get_vehicle_icons, get_weather_icons, holidays, injuryColours, intersection_decoder, light_decoder, makeElem, make_img, map, mode_decoder, onEachFeature, readStringFromFileAtPath, sidebar_hide, special, streetview_key, stringify_number, traffic_control_decoder, weather_decoder_1, weather_decoder_2;

crashes = './data/data.geojson';

injuryColours = {
  'f': '#ff1a1a',
  's': '#ff821a',
  'm': '#a7ee18',
  'n': '#15CC15'
};

boolean_properties = ['to', 'al', 'dr', 'cp', 'dr', 'cp', 'fg', 'sp', 'dd', 'ca', 'pd', 'cy', 'mc', 'tx', 'tr', 'ch'];

holidays = {
  'Labour Weekend 2014': 'Labour2014',
  'Christmas/New Year 2014-15': 'XmasNY2015'
};

readStringFromFileAtPath = function(pathOfFileToReadFrom) {
  var request;
  request = new XMLHttpRequest();
  request.open("GET", pathOfFileToReadFrom, false);
  request.send(null);
  return request.responseText;
};

special = ['zeroth', 'first', 'second', 'third', 'fourth', 'fifth', 'sixth', 'seventh', 'eighth', 'ninth', 'tenth', 'eleventh', 'twelvth', 'thirteenth', 'fourteenth', 'fifteenth', 'sixteenth', 'seventeenth', 'eighteenth', 'nineteenth'];

deca = ['twent', 'thirt', 'fort', 'fift', 'sixt', 'sevent', 'eight', 'ninet'];

stringify_number = function(n) {
  if (n < 20) {
    return special[n];
  }
  if (n % 10 === 0) {
    return deca[Math.floor(n / 10) - 2] + 'ieth';
  }
  return deca[Math.floor(n / 10) - 2] + 'y-' + special[n % 10];
};

getPointStyleOptions = function(feature) {
  var classes, holiday, j, k, len, len1, options, prop;
  options = {};
  options.radius = 5;
  options.fillOpacity = 0.9;
  options.stroke = false;
  options.fillColor = injuryColours[feature.properties.ij];
  classes = [feature.properties.ij];
  for (j = 0, len = boolean_properties.length; j < len; j++) {
    prop = boolean_properties[j];
    if ((feature.properties[prop] != null) && feature.properties[prop]) {
      classes.push(prop);
    }
  }
  for (k = 0, len1 = holidays.length; k < len1; k++) {
    holiday = holidays[k];
    if (feature.properties.h === holiday[0]) {
      classes.push(holiday[1]);
    }
  }
  options.className = classes.join(' ');
  return options;
};

makeElem = function(elem, inner, _class, _id) {
  var e;
  e = document.createElement(elem);
  if (_class != null) {
    e.className = _class;
  }
  if (_id != null) {
    e.id = _id;
  }
  if (inner != null) {
    if (typeof inner === 'string') {
      e.innerHTML = inner;
    } else {
      e.innerHTML = inner.outerHTML;
    }
  }
  return e;
};

make_img = function(src, title, alt) {
  var img;
  img = document.createElement('img');
  img.src = src;
  img.title = title;
  img.alt = alt != null ? alt : title;
  return img;
};

get_causes_text = function(causes, modes, vehicles) {
  var causes_text, expl, explanations, j, len, mode, modes_n, n, party, t;
  causes_text = [];
  modes_n = {};
  if ((typeof cause_decoder === "undefined" || cause_decoder === null) || (typeof mode_decoder === "undefined" || mode_decoder === null)) {
    return '';
  }
  for (party in causes) {
    explanations = causes[party];
    mode = modes.hasOwnProperty(party) ? modes[party] : null;
    if (mode != null) {
      if (modes_n.hasOwnProperty(mode)) {
        modes_n[mode] += 1;
      } else {
        modes_n[mode] = 1;
      }
    }
    for (j = 0, len = explanations.length; j < len; j++) {
      expl = explanations[j];
      if (mode != null) {
        if (modes_n[mode] > 1) {
          n = stringify_number(modes_n[mode]);
        } else if (modes_n[mode] === 1 && vehicles[mode] > 1) {
          n = stringify_number(modes_n[mode]);
        } else {
          n = '';
        }
        t = "The " + mode_decoder[mode]['display_text'] + ' ' + cause_decoder[expl]['Pretty'] + '.<br>';
        causes_text.push(t.replace(/<strong>/, n + " <strong>"));
      } else {
        causes_text.push(cause_decoder[expl]['Pretty'] + '.<br>');
      }
    }
  }
  return causes_text.join('');
};

get_weather_icons = function(weather, light, dy) {
  var day, img, title, weather_icons;
  if ((typeof weather_decoder_1 === "undefined" || weather_decoder_1 === null) || (typeof weather_decoder_2 === "undefined" || weather_decoder_2 === null)) {
    return '';
  }
  weather_icons = [];
  day = dy ? 'day' : 'night';
  if (weather_decoder_1[weather[0]].hasOwnProperty('icon')) {
    title = weather_decoder_1[weather[0]]['title'];
    img = weather_decoder_1[weather[0]]['icon'];
  } else if (weather_decoder_1[weather[0]].hasOwnProperty('icons')) {
    title = weather_decoder_1[weather[0]]['icons'][day]['title'];
    img = weather_decoder_1[weather[0]]['icons'][day]['icon'];
  }
  if ((title != null) && (img != null)) {
    weather_icons.push(make_img('./icons/' + img, title).outerHTML);
  }
  if (weather.length > 1) {
    title = weather_decoder_2[weather[1]]['title'];
    img = weather_decoder_2[weather[1]]['icon'];
    weather_icons.push(make_img("./icons/" + img, title).outerHTML);
  }
  return weather_icons.join("");
};

get_speed_limit_icon = function(speedlim) {
  var icon, title;
  if (speedlim === '' || speedlim === 'U') {
    return '';
  } else if (speedlim === 'LSZ') {
    title = 'Limited speed zone';
  } else {
    title = speedlim + "km/h speed limit";
  }
  if (speedlim != null) {
    icon = "./icons/speed-limits/limit_" + speedlim + ".svg";
    return make_img(icon, title).outerHTML;
  }
};

get_straightforward_icon = function(decoder, value, icon_path) {
  var icon, title;
  if ((decoder == null) || !value) {
    return '';
  }
  if ((!decoder.hasOwnProperty(value)) || (decoder[value]['icon'] == null)) {
    return '';
  }
  icon = decoder[value]['icon'];
  title = decoder[value]['title'];
  return make_img(icon_path + "/" + icon, title).outerHTML;
};

get_child_injured_icon = function(childage) {
  var article, child, icon, title;
  if (!childage) {
    return '';
  }
  icon = "./icons/otherchildren.png";
  article = childage === 8 || childage === 11 ? 'an' : 'a';
  if (childage === 1) {
    child = 'infant';
  } else if (childage < 13) {
    child = 'child';
  } else if (childage >= 13 && childage < 20) {
    child = 'teenager';
  }
  title = article + " " + childage + " year old " + child + " was harmed";
  return make_img("./icons/curves/" + icon, title).outerHTML;
};

get_moon_icon = function(moon) {
  var i, icon, title;
  if (!moon) {
    return '';
  }
  i = moon['moonphase'];
  icon = "./icons/moon/m" + i + ".svg";
  title = moon['moontext'] + ' moon';
  return make_img(icon, title).outerHTML;
};

get_streetview = function(lon, lat, fov, pitch) {
  var a, h, img, link, title, w;
  h = 200;
  w = 300;
  fov = fov != null ? Math.max(fov, 120) : 120;
  pitch = pitch != null ? pitch : -15;
  link = "http://maps.google.com/?cbll=" + lat + "," + lon + "&cbp=12,20.09,,0,5&layer=c";
  title = "Cick to go to Google Streetview";
  a = document.createElement('a');
  a.title = title;
  a.alt = title;
  a.target = "_blank";
  a.href = link;
  img = document.createElement('img');
  img.src = "https://maps.googleapis.com/maps/api/streetview?size=" + w + "x" + h + "&location=" + lat + "," + lon + "&pitch=" + pitch + "&key=" + streetview_key;
  a.innerHTML = img.outerHTML;
  return a.outerHTML;
};

get_vehicle_icons = function(vehicles) {
  var i, icon, icons, j, mode, n, ref, title;
  if (vehicles == null) {
    return '';
  }
  icons = [];
  for (mode in vehicles) {
    n = vehicles[mode];
    icon = mode_decoder[mode]['icon'];
    title = mode_decoder[mode]['title'];
    for (i = j = 1, ref = n; 1 <= ref ? j <= ref : j >= ref; i = 1 <= ref ? ++j : --j) {
      icons.push(make_img("./icons/transport/" + icon, title).outerHTML);
    }
  }
  return icons.join('');
};

getPopup = function(feature) {
  var causes_text, crash_date, crash_location, crash_time, dt, e, environment_icons, road, streetview, utcoff, vehicles_and_injuries;
  utcoff = !feature.properties.chathams ? '+12:00' : '+12:45';
  dt = moment(feature.properties.unixt).utcOffset(utcoff);
  crash_location = makeElem('span', feature.properties.t, 'crash-location');
  crash_date = makeElem('span', dt.format('dddd, Do MMMM YYYY'), 'date');
  crash_time = makeElem('span', dt.format('H:mm'), 'time');
  environment_icons = makeElem('span', makeElem('div', get_weather_icons(feature.properties.weather, feature.properties.light, feature.properties.dy) + get_speed_limit_icon(feature.properties.speedlim) + get_straightforward_icon(traffic_control_decoder, feature.properties.traffic_control, './icons/controls') + get_straightforward_icon(intersection_decoder, feature.properties.intersection, './icons/junctions') + get_straightforward_icon(curve_decoder, feature.properties.curve, './icons/curves') + get_child_injured_icon(feature.properties.childage) + (!feature.properties.dy ? get_moon_icon(feature.properties.moon) : ''), void 0, 'environment-icons'));
  road = makeElem('span', feature.properties.r, 'road');
  streetview = makeElem('span', makeElem('div', get_streetview(feature.geometry.coordinates[0], feature.geometry.coordinates[1]), void 0, 'streetview-container'));
  vehicles_and_injuries = makeElem('span', makeElem('div', makeElem('div', get_vehicle_icons(feature.properties.vehicles), void 0, 'vehicle-icons').outerHTML + makeElem('div', feature.properties.i, void 0, 'injury-icons').outerHTML + makeElem('div', void 0, void 0, 'clear').outerHTML, void 0, 'vehicle-injury'));
  causes_text = makeElem('span', get_causes_text(feature.properties.causes, feature.properties.modes, feature.properties.vehicles), 'causes-text');
  return ((function() {
    var j, len, ref, results;
    ref = [crash_location, crash_date, crash_time, environment_icons, road, streetview, vehicles_and_injuries, causes_text];
    results = [];
    for (j = 0, len = ref.length; j < len; j++) {
      e = ref[j];
      results.push(e.outerHTML);
    }
    return results;
  })()).join('');
};

get_map = function(mapdiv, centre, zoom) {
  var map;
  mapdiv = mapdiv != null ? mapdiv : 'map';
  centre = centre != null ? centre : [-41.17, 174.46];
  zoom = zoom != null ? zoom : 6;
  return map = L.map(mapdiv, {
    continuousWorld: true,
    worldCopyJump: true
  }).setView(centre, zoom);
};

get_attribution = function(nzta, stamen, osm) {
  var attr;
  attr = [];
  if (nzta || (nzta == null)) {
    attr.push('Crash data from <a href="http://www.nzta.govt.nz/resources/crash-analysis-reports/">NZTA</a>, under <a href="https://creativecommons.org/licenses/by/3.0/nz/">CC BY 3.0 NZ</a>, presented with changes');
  }
  if (stamen || (stamen == null)) {
    attr.push('Map tiles by <a href="http://stamen.com">Stamen Design</a>, under <a href="http://creativecommons.org/licenses/by/3.0">CC BY 3.0</a>');
  }
  if (osm || (osm == null)) {
    attr.push('Data by <a href="http://openstreetmap.org">OpenStreetMap</a>, under <a href="http://creativecommons.org/licenses/by-sa/3.0">CC BY SA</a>');
  }
  return attr.join(' | ');
};

get_tileLayer = function(maxZoom, minZoom) {
  return L.tileLayer('https://stamen-tiles-{s}.a.ssl.fastly.net/toner-lite/{z}/{x}/{y}.png', {
    maxZoom: maxZoom != null ? maxZoom : 18,
    minZoom: minZoom != null ? minZoom : 5,
    attribution: get_attribution()
  });
};

onEachFeature = function(feature, layer) {
  layer.on('click', function(e) {
    layer.bindPopup(getPopup(feature), {
      autoPanPadding: L.point(0, 10)
    });
    layer.openPopup();
  });
};

sidebar_hide = function() {
  $('#checkArray').click(function() {
    var crashClassSelected;
    $(function() {
      $('#allCheck').on('click', function() {
        $(this).closest('fieldset').find(':checkbox').prop('checked', false);
      });
    });
    crashClassSelected = 'path';
    $(crashClassSelected).css('display', 'none');
    $('#checkArray input[type=checkbox]').each(function() {
      if ($(this).is(':checked')) {
        crashClassSelected = crashClassSelected + $(this).val();
      }
    });
    $(crashClassSelected).css('display', 'block');
    if (crashClassSelected === 'path') {
      $('#allCheck').prop('checked', true);
    } else {
      $('#allCheck').prop('checked', false);
    }
  });
};

frontpage_control = function() {
  $('#toMap').click(function() {
    $('#frontpage').hide();
  });
  $('#toInfo').click(function() {
    $('#info-box-container').show();
  });
  $('#info-button-on-map').click(function() {
    $('#info-box-container').show();
  });
  return $('#close-button').click(function() {
    $('#info-box-container').hide();
  });
};

chevron_control = function() {
  return $('.filter-collapse').on('click', function() {
    $($(this).children()[0]).toggleClass('glyphicon-chevron-down');
    return $($(this).children()[0]).toggleClass('glyphicon-chevron-up');
  });
};

$(document).ready(function() {
  frontpage_control();
  sidebar_hide();
  chevron_control();
});

cause_decoder = void 0;

mode_decoder = void 0;

weather_decoder_1 = void 0;

weather_decoder_2 = void 0;

light_decoder = void 0;

intersection_decoder = void 0;

traffic_control_decoder = void 0;

curve_decoder = void 0;

streetview_key = void 0;

get_decoders = function() {
  YAML.load('./data/decoders/cause-decoder.yaml', function(data) {
    return cause_decoder = data;
  });
  YAML.load('./data/decoders/mode-decoder.yaml', function(data) {
    return mode_decoder = data;
  });
  YAML.load('./data/decoders/weather-decoder-1.yaml', function(data) {
    return weather_decoder_1 = data;
  });
  YAML.load('./data/decoders/weather-decoder-2.yaml', function(data) {
    return weather_decoder_2 = data;
  });
  YAML.load('./data/decoders/light-decoder.yaml', function(data) {
    return light_decoder = data;
  });
  YAML.load('./data/decoders/intersection-decoder.yaml', function(data) {
    return intersection_decoder = data;
  });
  YAML.load('./data/decoders/traffic-control-decoder.yaml', function(data) {
    return traffic_control_decoder = data;
  });
  YAML.load('./data/decoders/curve-decoder.yaml', function(data) {
    return curve_decoder = data;
  });
  streetview_key = readStringFromFileAtPath('./source/google-streetview-api-key');
};

get_decoders();

map = get_map();

get_tileLayer().addTo(map);

new L.GeoJSON.AJAX(crashes, {
  pointToLayer: function(feature, latlng) {
    var cm;
    return cm = new L.CircleMarker(latlng, getPointStyleOptions(feature));
  },
  filter: function(feature, layer) {
    return true;
  },
  onEachFeature: onEachFeature
}).addTo(map);
