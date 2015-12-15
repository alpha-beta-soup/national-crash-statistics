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

readStringFromFileAtPath = (pathOfFileToReadFrom) ->
  request = new XMLHttpRequest()
  request.open("GET", pathOfFileToReadFrom, false)
  request.send(null)
  return request.responseText

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

make_img = (src, title, alt) ->
  img =  document.createElement('img')
  img.src = src
  img.title = title
  img.alt = if alt? then alt else title
  return img

get_causes_text = (causes, modes, vehicles) ->
  # TODO when there are more given parties than listed modes?
  # TODO make more elegant
  causes_text = []
  modes_n = {}
  if !cause_decoder? or !mode_decoder?
    return ''
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
        else if modes_n[mode] == 1 and vehicles[mode] > 1
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

get_straightforward_icon = (decoder, value, icon_path) ->
  if !decoder? or !value
    return ''
  if (!decoder.hasOwnProperty value) or (!decoder[value]['icon']?)
    return ''
  icon = decoder[value]['icon']
  title = decoder[value]['title']
  return make_img("#{icon_path}/#{icon}", title).outerHTML

get_straightforwad_multiple_icons = (values, decoder, icon_path) ->
  if !values? or !values or !decoder?
    return ''
  icons = []
  for v, n of values
    icon = decoder[v]['icon']
    title = decoder[v]['title']
    for i in [1..n]
      icons.push make_img("#{icon_path}#{icon}", title).outerHTML
  return icons.join('')

get_weather_icons = (weather, light, dy) ->
  # TODO light? (bright sun, dark, overcast, twilight)
  if !weather_decoder_1? or !weather_decoder_2? or weather.length == 0
    return ''
  weather_icons = []
  # First weather icon
  day = if dy then 'day' else 'night'
  if weather_decoder_1[weather[0]].hasOwnProperty('icon')
    title = weather_decoder_1[weather[0]]['title']
    img = weather_decoder_1[weather[0]]['icon']
  else if weather_decoder_1[weather[0]].hasOwnProperty('icons')
    title = weather_decoder_1[weather[0]]['icons'][day]['title']
    img = weather_decoder_1[weather[0]]['icons'][day]['icon']
  if title? and img?
    weather_icons.push make_img('./icons/' + img, title).outerHTML
  # Optional second weather icon
  if weather.length > 1
    title = weather_decoder_2[weather[1]]['title']
    img = weather_decoder_2[weather[1]]['icon']
    weather_icons.push make_img("./icons/" + img, title).outerHTML
  return weather_icons.join("")

get_speed_limit_icon = (speedlim) ->
  if speedlim in ['', 'U']
    return ''
  else if speedlim is 'LSZ'
    # Limited speed zone
    # Could not be set since 2003, and was progressively replaced until 2009
    # It is now illegal
    title = 'Limited speed zone'
  else
    title = "#{speedlim}km/h speed limit"
  if speedlim?
    icon = "./icons/speed-limits/limit_#{speedlim}.svg"
    return make_img(icon, title).outerHTML

get_child_injured_icon = (childage) ->
  if !childage
    return ''
  icon = "./icons/other/children.png"
  article = if childage in [8, 11] then 'an' else 'a'
  if childage == 1
    child = 'infant'
  else if childage < 13
    child = 'child'
  else if childage >=13 and childage < 20
    child = 'teenager'
  title = "#{article} #{childage} year old #{child} was harmed"
  return make_img("#{icon}", title).outerHTML + makeElem('span', childage.toString(), undefined, 'childage').outerHTML

get_moon_icon = (moon) ->
  if !moon
    return ''
  i = moon['moonphase']
  icon = "./icons/moon/m#{i}.svg"
  title = moon['moontext'] + ' moon'
  return make_img(icon, title).outerHTML

get_streetview = (lon, lat, fov, pitch) ->
  h = 200
  w = 300
  fov = if fov? then Math.max(fov, 120) else 120 # Field of view, max 120
  pitch = if pitch? then pitch else -15 # Up or down angle relate to Streetview vehicle
  link = "http://maps.google.com/?cbll=#{lat},#{lon}&cbp=12,20.09,,0,5&layer=c"
  title = "Cick to go to Google Streetview"
  a = document.createElement('a')
  a.title = title
  a.alt = title
  a.target = "_blank"
  a.href = link
  img = document.createElement('img')
  img.src = "https://maps.googleapis.com/maps/api/streetview?size=#{w}x#{h}&location=#{lat},#{lon}&pitch=#{pitch}&key=#{streetview_key}"
  a.innerHTML = img.outerHTML
  return a.outerHTML

utc_offset = (feature) ->
  if !feature.properties.chathams then '+12:00' else '+12:45'

getPopup = (feature) ->
  dt = moment(feature.properties.unixt).utcOffset(utc_offset(feature))
  crash_location = makeElem('span', feature.properties.t, 'crash-location')
  crash_date = makeElem('span', dt.format('dddd, Do MMMM YYYY'), 'date')
  crash_time = makeElem('span', dt.format('H:mm'), 'time')
  environment_icons = makeElem('span',
    makeElem(
      'div',
      get_weather_icons(feature.properties.weather, feature.properties.light, feature.properties.dy) +
      get_speed_limit_icon(feature.properties.speedlim) +
      get_straightforward_icon(traffic_control_decoder, feature.properties.traffic_control, './icons/controls') +
      get_straightforward_icon(intersection_decoder, feature.properties.intersection, './icons/junctions') +
      get_straightforward_icon(curve_decoder, feature.properties.curve, './icons/curves') +
      get_child_injured_icon(feature.properties.childage) +
      (if !feature.properties.dy then get_moon_icon(feature.properties.moon) else '')
      , undefined,
      'environment-icons'
    )
  )
  road = makeElem('span', feature.properties.r, 'road')
  streetview = makeElem('span', makeElem('div', get_streetview(feature.geometry.coordinates[0], feature.geometry.coordinates[1]), undefined, 'streetview-container'))
  vehicles_and_injuries = makeElem(
    'span',
    makeElem('div',
      makeElem('div',
        get_straightforwad_multiple_icons(feature.properties.vehicles, mode_decoder, './icons/transport/'),
        undefined, 'vehicle-icons'
      ).outerHTML +
      makeElem('div',
        get_straightforwad_multiple_icons(feature.properties.injuries, injuries_decoder, './icons/injuries/'),
        undefined, 'injury-icons'
      ).outerHTML +
      makeElem('div', undefined, undefined, 'clear').outerHTML,
      undefined, 'vehicle-injury'
    )
  )
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

get_map = (fg, bg, mapdiv, centre, zoom) ->
  mapdiv = if mapdiv? then mapdiv else 'map'
  centre = if centre? then centre else [-41.17, 174.46]
  zoom = if zoom? then zoom else 6
  map = L.map mapdiv,
    continuousWorld: true
    worldCopyJump: true
    layers: if bg? then [fg, bg] else [fg]
  .setView centre, zoom
  .on 'zoomend', ->
    z = map.getZoom()
    if z < 12
      bg.setOpacity 0
    else if z >= 12 and z < 16
      bg.setOpacity 0.4
    else if z == 16
      bg.setOpacity 0.5
    else if z == 17
      bg.setOpacity 0.6
    else if (z >= 18 and z < 20)
      bg.setOpacity 0.7
    else if z >= 20
      bg.setOpacity 0.8

  return map

get_attribution = (nzta, stamen, osm, linz) ->
  attr = []
  if nzta or !nzta?
    attr.push 'Crash data from <a href="http://www.nzta.govt.nz/resources/crash-analysis-reports/">NZTA</a>, under <a href="https://creativecommons.org/licenses/by/3.0/nz/">CC BY 3.0 NZ</a>, presented with changes'
  if stamen or !stamen?
    attr.push 'Map tiles by <a href="http://stamen.com">Stamen Design</a>, under <a href="http://creativecommons.org/licenses/by/3.0">CC BY 3.0</a>'
  if osm or !osm?
    attr.push 'Data by <a href="http://openstreetmap.org">OpenStreetMap</a>, under <a href="http://creativecommons.org/licenses/by-sa/3.0">CC BY SA</a>'
  if linz or !linz?
    attr.push 'Imagery <a href="http://www.linz.govt.nz/data/licensing-and-using-data/attributing-aerial-imagery-data">sourced from LINZ CC-BY 3.0</a>'
  return attr.join(' | ')

get_tileLayer = (maxZoom, minZoom) ->
  L.tileLayer 'https://stamen-tiles-{s}.a.ssl.fastly.net/toner-lite/{z}/{x}/{y}.png',
    maxZoom: if maxZoom? then maxZoom else 21
    minZoom: if minZoom? then minZoom else 5
    attribution: get_attribution()
    detectRetina: true
    reuseTiles: true

get_foreground_layer = (maxZoom, minZoom) ->
  key = "20865bd31bcc4e4dbea2181b9a23d825"
  epsg = "3857"
  v = 4
  set = 2
  url = "http://tiles-{s}.data-cdn.linz.govt.nz/services;key=#{key}/tiles/v#{v}/set=#{set}/EPSG:#{epsg}/{z}/{x}/{y}.png"
  mask = L.tileLayer url,
    maxZoom: if maxZoom? then maxZoom else 21
    minZoom: if minZoom? then minZoom else 12
    opacity: 0.7
    subdomains: ['a', 'b', 'c', 'd']
    detectRetina: true
    reuseTiles: true
  return mask

onEachFeature = (feature, layer) ->
  # bind click
  layer.on 'click', (e) ->
    layer.bindPopup getPopup(feature),
      # offset: L.point(0, -2)
      autoPanPadding: L.point(0, 10)
    layer.openPopup()
    return
  return

do_feature_count = (bool_filters) ->
  # TODO total recorded accidents (including non-injury)
  if !bool_filters? or !bool_filters
    return
  bool_filters = (b.replace('.', '') for b in bool_filters)
  counts = {'f': 0, 's': 0, 'm': 0}
  for crash, i in crashgeojson.toGeoJSON()['features']
    for bf in bool_filters
      valid = yes
      if counts.hasOwnProperty bf
        # It's an injury filter
        # Ignore these when counting up all injuries
      else
        # It's a standard boolean filter
        if !crash.properties[bf]
          # If a crash does not meet any of the criteria, it is not counted
          valid = no
          break
    if valid
      # If the crash meets all the boolean criteria
      # candidates.push i
      if crash.properties.injuries?
        for ij in ['f', 's', 'm']
          if crash.properties.injuries[ij]?
            counts[ij] += crash.properties.injuries[ij]
  alert JSON.stringify counts, null, 4


sidebar_hide = ->
  # crash selector functionality checks for changes.
  # CSS hide and show. Data called once.
  $('#checkArray').click ->
    $ ->
      $('#allCheck').on 'click', ->
        $(this).closest('fieldset').find(':checkbox').prop 'checked', false
        return
      return
    crashClassSelected = 'path'
    $(crashClassSelected).css 'display', 'none'
    bool_filters = []
    $('#checkArray input[type=checkbox]').each ->
      if $(this).is ':checked'
        val = $(this).val()
        bool_filters.push val
        crashClassSelected = crashClassSelected + val
      return
    $(crashClassSelected).css 'display', 'block'
    if crashClassSelected == 'path'
      $('#allCheck').prop 'checked', true
    else
      $('#allCheck').prop 'checked', false

    # Count features
    do_feature_count(bool_filters)
    return
  return

      # bool_filters = []
      #
      # crashes_meeting_criteria = []
      #
      #   bool_filters.push val.replace('.', '')
      #
      # if crashgeojson?
      #
      #   candidates = crashgeojson.toGeoJSON()['features']
      #
      #   for bool in bool_filters
      #
      #     for candidate, i in candidates
      #
      #       if candidate[bool]
      #
      #         crashes_meeting_criteria.push candidate
      #
      #         candidates.splice(i, 1)
      #
      # console.log crashes_meeting_criteria.length
      #
      #   # crashes_meeting_criteria.push c for c in crashgeojson.toGeoJSON()['features'] when c
      #
      #   # console.log crashgeojson.toGeoJSON()['features']
      #
      #   # for crash of crashgeojson.toGeoJSON()['features']
      #
      #   #   # console.log crash


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

# Load the YAML/JSON decoders
cause_decoder = undefined
mode_decoder = undefined
weather_decoder_1 = undefined
weather_decoder_2 = undefined
light_decoder = undefined
intersection_decoder = undefined
traffic_control_decoder = undefined
curve_decoder = undefined
injuries_decoder = undefined
streetview_key = undefined
get_decoders = () ->
  YAML.load './data/decoders/cause-decoder.yaml', (data) ->
    cause_decoder = data
  YAML.load './data/decoders/mode-decoder.yaml', (data) ->
    mode_decoder = data
  YAML.load './data/decoders/weather-decoder-1.yaml', (data) ->
    weather_decoder_1 = data
  YAML.load './data/decoders/weather-decoder-2.yaml', (data) ->
    weather_decoder_2 = data
  YAML.load './data/decoders/light-decoder.yaml', (data) ->
    light_decoder = data
  YAML.load './data/decoders/intersection-decoder.yaml', (data) ->
    intersection_decoder = data
  YAML.load './data/decoders/traffic-control-decoder.yaml', (data) ->
    traffic_control_decoder = data
  YAML.load './data/decoders/curve-decoder.yaml', (data) ->
    curve_decoder = data
  YAML.load './data/decoders/injuries-decoder.yaml', (data) ->
    injuries_decoder = data
  streetview_key = readStringFromFileAtPath './source/google-streetview-api-key'
  return

get_decoders()
map = get_map(get_tileLayer(), get_foreground_layer())

crashgeojson = new L.GeoJSON.AJAX crashes,
  pointToLayer: (feature, latlng) ->
    cm = new L.CircleMarker latlng, getPointStyleOptions(feature)
  filter: (feature, layer) ->
    return true
  onEachFeature: onEachFeature
.addTo map
