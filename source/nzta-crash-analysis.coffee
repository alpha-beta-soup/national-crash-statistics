crashes = './data/data.geojson'
injuryColours = {
  'f': '#ff1a1a',
  's': '#ff821a',
  'm': '#a7ee18',
  'n': '#15CC15'
}
boolean_properties = ['to', 'al', 'dr', 'cp', 'dr', 'cp', 'fg', 'sp', 'dd', 'ca', 'pd', 'cy', 'mc', 'tx', 'tr', 'ch']
holidays = {
  'Labour Weekend 2014': 'Labour2014'
  'Christmas/New Year 2014-15': 'XmasNY2015'
}

special = ['zeroth','first', 'second', 'third', 'fourth', 'fifth', 'sixth', 'seventh', 'eighth', 'ninth', 'tenth', 'eleventh', 'twelvth', 'thirteenth', 'fourteenth', 'fifteenth', 'sixteenth', 'seventeenth', 'eighteenth', 'nineteenth']
deca = ['twent', 'thirt', 'fort', 'fift', 'sixt', 'sevent', 'eight', 'ninet']
stringify_number = (n) ->
  if n < 20
    return special[n]
  if n % 10 == 0
    return deca[Math.floor(n/10)-2] + 'ieth'
  return deca[Math.floor(n/10)-2] + 'y-' + special[n%10]

getPointStyleOptions = (feature) ->
  options = {}
  options.radius = 5
  options.fillOpacity = 0.9
  options.stroke = false
  options.fillColor = injuryColours[feature.properties.ij]
  classes = [feature.properties.ij]
  for prop in boolean_properties
    if feature.properties[prop]? and feature.properties[prop]
      classes.push(prop)
  for holiday in holidays
    if feature.properties.h == holiday[0]
      classes.push(holiday[1])
  options.className = classes.join(' ')
  return options

makeElem = (elem, inner, _class, _id) ->
  e = document.createElement(elem)
  if _class?
    e.className = _class
  if _id?
    e.id = _id
  if inner?
    if typeof(inner) is 'string'
      e.innerHTML = inner
    else
      e.innerHTML = inner.outerHTML
  return e

get_causes_text = (causes, modes, vehicles) ->
  # TODO when there are more given parties than listed modes?
  # TODO make more elegant
  causes_text = []
  modes_n = {}
  if !cause_decoder or !mode_decoder
    return
  for party, explanations of causes
    mode = if modes.hasOwnProperty(party) then modes[party] else null
    if mode?
      if modes_n.hasOwnProperty(mode)
        modes_n[mode] += 1
      else
        modes_n[mode] = 1
    for expl in explanations
      if mode?
        # Explanation with an associated mode
        if modes_n[mode] > 1
          # "The second car" if this is at least the second car
          n = stringify_number(modes_n[mode])
        if modes_n[mode] == 1 and vehicles[mode] > 1
          # "The first car" if this is the first example of a car,
          # but there are more to come
          n = stringify_number(modes_n[mode])
        else
          # "The car": this is the first and only instance of a particular mode
          n = ''
        t = "The " + mode_decoder[mode]['display_text'] + ' ' + cause_decoder[expl]['Pretty'] + '.<br>'
        causes_text.push t.replace /<strong>/, "#{n} <strong>"
      else
        # Explanation with no party or mode
        causes_text.push cause_decoder[expl]['Pretty'] + '.<br>'
  return causes_text.join('')

getPopup = (feature) ->
  # Decode the values in feature.properties.causes_dict.A
  crash_location = makeElem('span', feature.properties.t, 'crash-location')
  crash_date = makeElem('span', [feature.properties.d, feature.properties.dt].join(', '), 'date')
  crash_time = makeElem('span', feature.properties.ti, 'time')
  environment_icons = makeElem('span', makeElem('div', feature.properties.e, undefined, 'environment-icons'))
  road = makeElem('span', feature.properties.r, 'road')
  streetview = makeElem('span', makeElem('div', feature.properties.s, undefined, 'streetview-container'))
  vehicles_and_injuries = makeElem('span', makeElem('div', makeElem('div', feature.properties.v, undefined, 'vehicle-icons').outerHTML + makeElem('div', feature.properties.i, undefined, 'injury-icons').outerHTML + makeElem('div', undefined, undefined, 'clear').outerHTML, undefined, 'vehicle-injury'))
  causes_text = makeElem('span', get_causes_text(feature.properties.causes, feature.properties.modes, feature.properties.vehicles), 'causes-text')
  return (e.outerHTML for e in [
    crash_location,
    crash_date,
    crash_time,
    environment_icons,
    road,
    streetview,
    vehicles_and_injuries,
    causes_text
  ]).join('')

get_map = (mapdiv, centre, zoom) ->
  mapdiv = if mapdiv? then mapdiv else 'map'
  centre = if centre? then centre else [-41.17, 174.46]
  zoom = if zoom? then zoom else 6
  map = L.map mapdiv,
    continuousWorld: true
    worldCopyJump: true
  .setView centre, zoom

get_attribution = (nzta, stamen, osm) ->
  attr = []
  if nzta or !nzta?
    attr.push 'Crash data from <a href="http://www.nzta.govt.nz/resources/crash-analysis-reports/">NZTA</a>, under <a href="https://creativecommons.org/licenses/by/3.0/nz/">CC BY 3.0 NZ</a>, presented with changes'
  if stamen or !stamen?
    attr.push 'Map tiles by <a href="http://stamen.com">Stamen Design</a>, under <a href="http://creativecommons.org/licenses/by/3.0">CC BY 3.0</a>'
  if osm or !osm?
    attr.push 'Data by <a href="http://openstreetmap.org">OpenStreetMap</a>, under <a href="http://creativecommons.org/licenses/by-sa/3.0">CC BY SA</a>'
  return attr.join(' | ')

get_tileLayer = (maxZoom, minZoom) ->
  L.tileLayer 'https://stamen-tiles-{s}.a.ssl.fastly.net/toner-lite/{z}/{x}/{y}.png',
    maxZoom: if maxZoom? then maxZoom else 18
    minZoom: if minZoom? then minZoom else 5
    attribution: get_attribution()

onEachFeature = (feature, layer) ->
  # bind click
  layer.on 'click', (e) ->
    layer.bindPopup getPopup(feature),
      # offset: L.point(0, -2)
      autoPanPadding: L.point(0, 10)
    layer.openPopup()
    return
  return

sidebar_hide = ->
  #crash selector functionality checks for changes. CSS hide and show. Data called once. If 'All crashes' clicked nothing else can be checked. If others clicked 'All crashes' can't be checked.
  $('#checkArray').click ->
    $ ->
      $('#allCheck').on 'click', ->
        $(this).closest('fieldset').find(':checkbox').prop 'checked', false
        return
      return
    crashClassSelected = 'path'
    $(crashClassSelected).css 'display', 'none'
    $('#checkArray input[type=checkbox]').each ->
      if $(this).is(':checked')
        crashClassSelected = crashClassSelected + $(this).val()
      return
    $(crashClassSelected).css 'display', 'block'
    if crashClassSelected == 'path'
      $('#allCheck').prop 'checked', true
    else
      $('#allCheck').prop 'checked', false
    return
  return

frontpage_control = () ->
  $('#toMap').click ->
    $('#frontpage').hide()
    return
  $('#toInfo').click ->
    $('#info-box-container').show()
    return
  $('#info-button-on-map').click ->
    $('#info-box-container').show()
    return
  $('#close-button').click ->
    $('#info-box-container').hide()
    return

chevron_control = () ->
  $('.filter-collapse').on 'click', ->
    $($(this).children()[0]).toggleClass('glyphicon-chevron-down')
    $($(this).children()[0]).toggleClass('glyphicon-chevron-up')

$(document).ready ->
  frontpage_control()
  sidebar_hide()
  chevron_control()
  return

# Load the JSON decoders
cause_decoder = undefined
mode_decoder = undefined
get_decoder = () ->
  $.getJSON './data/decoders/cause-decoder.json', (data) ->
    cause_decoder = data
  $.getJSON './data/decoders/mode-decoder.json', (data) ->
    mode_decoder = data

get_decoder()
map = get_map()
get_tileLayer().addTo map

new L.GeoJSON.AJAX crashes,
  pointToLayer: (feature, latlng) ->
    cm = new L.CircleMarker latlng, getPointStyleOptions(feature)
  filter: (feature, layer) ->
    return true
  onEachFeature: onEachFeature
.addTo map
