var boolean_properties, cause_decoder, chevron_control, crashes, deca, frontpage_control, getPointStyleOptions, getPopup, get_attribution, get_causes_text, get_decoder, get_map, get_tileLayer, holidays, injuryColours, makeElem, map, mode_decoder, onEachFeature, sidebar_hide, special, stringify_number;

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
  var classes, holiday, i, j, len, len1, options, prop;
  options = {};
  options.radius = 5;
  options.fillOpacity = 0.9;
  options.stroke = false;
  options.fillColor = injuryColours[feature.properties.ij];
  classes = [feature.properties.ij];
  for (i = 0, len = boolean_properties.length; i < len; i++) {
    prop = boolean_properties[i];
    if ((feature.properties[prop] != null) && feature.properties[prop]) {
      classes.push(prop);
    }
  }
  for (j = 0, len1 = holidays.length; j < len1; j++) {
    holiday = holidays[j];
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

get_causes_text = function(causes, modes, vehicles) {
  var causes_text, expl, explanations, i, len, mode, modes_n, n, party, t;
  causes_text = [];
  modes_n = {};
  if (!cause_decoder || !mode_decoder) {
    return;
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
    for (i = 0, len = explanations.length; i < len; i++) {
      expl = explanations[i];
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

getPopup = function(feature) {
  var causes_text, crash_date, crash_location, crash_time, dt, e, environment_icons, road, streetview, utcoff, vehicles_and_injuries;
  utcoff = !feature.properties.chathams ? '+12:00' : '+12:45';
  dt = moment(feature.properties.unixt).utcOffset(utcoff);
  crash_location = makeElem('span', feature.properties.t, 'crash-location');
  crash_date = makeElem('span', dt.format('dddd, Do MMMM YYYY'), 'date');
  crash_time = makeElem('span', dt.format('H:mm'), 'time');
  environment_icons = makeElem('span', makeElem('div', feature.properties.e, void 0, 'environment-icons'));
  road = makeElem('span', feature.properties.r, 'road');
  streetview = makeElem('span', makeElem('div', feature.properties.s, void 0, 'streetview-container'));
  vehicles_and_injuries = makeElem('span', makeElem('div', makeElem('div', feature.properties.v, void 0, 'vehicle-icons').outerHTML + makeElem('div', feature.properties.i, void 0, 'injury-icons').outerHTML + makeElem('div', void 0, void 0, 'clear').outerHTML, void 0, 'vehicle-injury'));
  causes_text = makeElem('span', get_causes_text(feature.properties.causes, feature.properties.modes, feature.properties.vehicles), 'causes-text');
  return ((function() {
    var i, len, ref, results;
    ref = [crash_location, crash_date, crash_time, environment_icons, road, streetview, vehicles_and_injuries, causes_text];
    results = [];
    for (i = 0, len = ref.length; i < len; i++) {
      e = ref[i];
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

get_decoder = function() {
  $.getJSON('./data/decoders/cause-decoder.json', function(data) {
    return cause_decoder = data;
  });
  return $.getJSON('./data/decoders/mode-decoder.json', function(data) {
    return mode_decoder = data;
  });
};

get_decoder();

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
