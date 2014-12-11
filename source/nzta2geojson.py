#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
`nzta2geojson.py`
=================
A Python script to read the New Zealand Transport Agency crash data into a
GeoJSON, to be styled and filtered for presentation in a Leaflet map.

Depends
=======
pyproj
folium
geojson
'''

import pyproj
import folium
import geojson
import json
import csv
import string
import generalFunctions as genFunc
     
class nztacrash:
    '''A crash recorded by NZTA'''
    def __init__(self, row, causedecoder, streetdecoder):
        '''
        A row from one of the crash .csv files gives us all the attrbiutes we
        have to define it as a Python object. When initialising, we typecast
        appropriate values: dates are no longer strings, they are datetimes,
        empty values are no longer ' ' but actual Nonetypes. One day government
        agencies will give out SQLite files by default. Until then...
        
        Also requires the parameter `causedecoder`, which is the output of
        the function causeDecoderCSV(). This should be the output of this function,
        to avoid running it each tim an nztacrash object is instantiated.
        '''
        # Original data
        self.row = row
        self.tla_name = genFunc.formatString(row[0])
        self.crash_road = self.get_crash_road()
        self.crash_dist = genFunc.formatInteger(row[2])
        self.crash_dirn = genFunc.formatString(row[3])
        self.crash_intsn = genFunc.formatString(row[4])
        self.side_road = self.get_side_road()
        self.crash_id = genFunc.formatString(row[6])
        self.crash_date = genFunc.formatDate(row[7])
        self.crash_dow = self.get_crash_dow()
        self.crash_time = genFunc.formatCrashTime(row[9], self.crash_date) # Returns a datetime.datetime.time() object
        self.mvmt = genFunc.formatString(row[10])
        self.vehicles = genFunc.formatString(row[11])
        self.causes = genFunc.formatStringList(row[12],delim=' ') # Returns a list
        self.objects_struck = genFunc.formatStringList(row[13],delim=None)
        self.road_curve = genFunc.formatString(row[14])
        self.road_wet = genFunc.formatString(row[15])
        self.light = genFunc.formatStringList(row[16])
        self.wthr_a = genFunc.formatStringList(row[17])
        self.junc_type = genFunc.formatString(row[18])
        self.traf_ctrl = genFunc.formatString(row[19])
        self.road_mark = genFunc.formatString(row[20])
        self.spd_lim = self.get_spd_lim() # Can be integer or string
        self.crash_fatal_cnt = genFunc.formatInteger(row[22]) # Number of people who died as a result
        self.crash_sev_cnt = genFunc.formatInteger(row[23]) # Number of people with severe injuries
        self.crash_min_cnt = genFunc.formatInteger(row[24]) # Number of people with minor injuries
        self.pers_age1 = genFunc.formatInteger(row[25])
        self.pers_age2 = genFunc.formatInteger(row[26])
        
        # Spatial information
        self.easting = genFunc.formatInteger(row[27]) # NZTM
        self.northing = genFunc.formatInteger(row[28]) # NZTM
        self.proj = pyproj.Proj(init='epsg:2193') # NZTM projection
        self.hasLocation = self.get_hasLocation()
        if self.hasLocation == True:
            self.lat, self.lon = self.proj(self.easting, self.northing, inverse=True) # Lat/lon
        else:
            self.lat, self.lon = None, None
        
        # Output of causeDecoderCSV()
        self.causedecoder = causedecoder
        
        # Output of streetDecoderCSV()
        self.streetdecoder = streetdecoder
        
        # Derived and associated data
        self.keyvehicle = self.getKeyVehicle(decode=False)
        self.keyvehicle_decoded = self.getKeyVehicle(decode=True)
        self.keyvehiclemovement = self.getKeyVehicleMovement(decode=False)
        self.keyvehiclemovement_decoded = self.getKeyVehicleMovement(decode=True)
        self.secondaryvehicles = self.getSecondaryVehicles(decode=False)
        self.secondaryvehicles_decoded = self.getSecondaryVehicles(decode=True)
        self.causesdict = self.getCauses(decode=False)
        self.causesdict_decoded = self.getCauses(decode=True)
        self.objects_struck_decoded = self.getObjectsStruck()
        self.light_decoded = self.decodeLight()
        self.wthr_a_decoded = self.decodeWeather()
        self.junc_type_decoded = self.decodeJunction()
        
        # Some booleans (good for filters)
        if self.crash_fatal_cnt > 0:
            self.fatal = True
        elif self.crash_fatal_cnt == 0:
            self.fatal = False
        if self.crash_sev_cnt > 0 or self.crash_min_cnt > 0:
            self.injuries = True
        elif self.crash_sev_cnt == 0 and self.crash_min_cnt == 0:
            self.injuries = False
        if self.crash_sev_cnt > 0:
            self.injuries_severe = True
        elif self.crash_sev_cnt == 0:
            self.injuries_severe = False
        if self.crash_min_cnt > 0:
            self.injuries_minor = True
        elif self.crash_min_cnt == 0:
            self.injuries_minor = False
        if self.fatal == False and self.injuries_severe == False and self.injuries_minor == False:
            self.injuries_none = True
        else:
            self.injuries_none = False
        self.cyclist = self.get_cyclist()
        self.pedestrian = self.get_pedestrian()
        
        # HTML text descriptions, used in self.__str__()
        if self.road_wet == 'W':
            self.__roadwet = 'The road was wet.'
        elif self.road_wet == 'D':
            self.__roadwet = 'The road was dry.'
        elif self.road_wet == 'I':
            self.__roadwet = 'There was snow or ice on the road.'
        else:
            self.__roadwet = None
        if self.wthr_a != None:
            self.__wthr = 'Weather: %s' % self.wthr_a_decoded[0]
            if self.wthr_a_decoded[1] != None:
                self.__wthr += ' - %s' % self.wthr_a_decoded[1]
        if self.light != None:
            self.__light = 'Lighting: %s' % self.light_decoded[0]
            if self.light_decoded[1] != None:
                self.__light += ' - %s' % self.light_decoded[1]
        if self.decodeMovement() != None and self.decodeMovement()[0] != None:
            self.__movement = 'Movement: %s' % self.decodeMovement()[0]
            if self.decodeMovement()[1] != None:
                self.__movement += '- %s' % self.decodeMovement()[1]
        else:
            self.__movement = None
        self.__atype = '<b>Vehicle A was a %s</b> (it may or may not have been at fault).' % self.keyvehicle_decoded.lower()
        if self.keyvehiclemovement_decoded != None:
            self.__amovement = 'Vehicle A was moving %s.' % self.keyvehiclemovement_decoded.lower()
        else:
            self.__amovement = None
        if self.secondaryvehicles_decoded != None:
            party = genFunc.grammar('party', 'parties', len(self.secondaryvehicles))
            self.__secondary = 'Secondary %s: ' % party
            for v in self.secondaryvehicles_decoded:
                self.__secondary += '<b>%s</b>, ' % v
            self.__secondary = self.__secondary.strip(', ')
        else:
            self.__secondary = 'No other parties were involved.'
        if self.pers_age1 != None and self.secondaryvehicles != None:
            youngest = genFunc.grammar('', ' youngest', len(self.secondaryvehicles))
            self.__youngestped = '<b>The%s pedestrian was %d years old.</b>' % (youngest, self.pers_age1)
        else:
            self.__youngestped = None
        if self.pers_age2 != None and self.secondaryvehicles != None:
            youngest = genFunc.grammar('', ' youngest', len(self.secondaryvehicles))
            self.__youngestcyc = '<b>The%s cyclist was %d years old.</b>' % (youngest, self.pers_age2) 
        else:
            self.__youngestcyc = None
        self.__factors = "<u>Factors and roles</u>:<ol>\n"
        for vehicle in list(string.ascii_uppercase): # 'A', 'B', ..., 'Z'
            if self.causesdict_decoded != None and vehicle in self.causesdict_decoded.keys():
                for cause in self.causesdict_decoded[vehicle]:
                    self.__factors += "<li>Vehicle <b>%s</b>: %s.</li>" % (vehicle, cause)
        if self.causesdict_decoded != None and 'Environment' in self.causesdict_decoded.keys():
            for cause in self.causesdict_decoded['Environment']:
                self.__factors += '<li>Environmental factor: %s.</li>' % cause
        self.__factors += '</ol>'
        if len(self.objects_struck) > 0:
            self.__objects = '<u>Stationary objects hit</u>:<ul>'
            for o in self.objects_struck_decoded:
                self.__objects += '<li>%s</li>' % o.capitalize()
            self.__objects += '</ul>'
        else:
            self.__objects = 'No stationary objects were hit.'
        self.__consequences = '<center>'
        if self.crash_fatal_cnt > 0:
            person = genFunc.grammar('person', 'people', self.crash_fatal_cnt)
            self.__consequences += '\nUnfortunately, <b>%d %s died</b> as a result of this crash.'  % (self.crash_fatal_cnt, person)
        if self.crash_sev_cnt > 0:
            person = genFunc.grammar('person', 'people', self.crash_sev_cnt)
            self.__consequences += '\n<b>%d %s suffered serious injuries</b>.' % (self.crash_sev_cnt, person)
        if self.crash_min_cnt > 0:
            was = genFunc.grammar('was', 'were', self.crash_min_cnt)
            injury = genFunc.grammar('injury', 'injuries', self.crash_min_cnt)
            self.__consequences += '\nThere %s <b>%d minor %s</b>.' % (was, self.crash_min_cnt, injury)
        if self.fatal == False and self.injuries == False:
            self.__consequences = '\nFortunately, there were <b>no deaths or injuries</b>.'
        self.__consequences = self.__consequences.strip() + '</center>'
        
    def get_hasLocation(self):
        if self.easting == None or self.northing == None:
            return False
        else:
            return True
            
    def get_crash_road(self):
        crash_road = genFunc.formatString(self.row[1])
        if crash_road != None and crash_road[0:3] != 'SH ':
            crash_road = crash_road.title()
        return crash_road
        
    def get_crash_dow(self):
        '''Returns a full text representation of the English day of the week,
        e.g. "Monday"'''
        return self.crash_date.strftime("%A")
     
    def get_spd_lim(self):
        '''Speed limit can either be a number (integer is returned) or a character,
        as both 'U' and 'LSZ' are also valid speed limits.'''
        try:
            spd_lim = genFunc.formatInteger(self.row[21]) # Integer
        except:
            spd_lim = genFunc.formatString(self.row[21]) # String
        return spd_lim
        
    def get_side_road(self):
        side_road = genFunc.formatString(self.row[5])
        if side_road != None and side_road[0:3] != 'SH ':
            side_road = side_road.title()
        return side_road
        
    def get_cyclist(self):
        '''Returns a Boolean indicating whether or not a cyclist was an involved party'''
        cyclist = False # Until shown otherwise
        if self.secondaryvehicles != None:
            if ('S' in self.secondaryvehicles) or (self.keyvehicle =='S'):
                # A cyclist was involved
                cyclist = True
        elif self.keyvehicle == 'S':
            cyclist == True
        return cyclist
    
    def get_pedestrian(self):
        '''Returns a Boolean indicating whether or not a pedestrian was an involved party'''
        pedestrian = False # Until shown otherwise
        if self.secondaryvehicles != None:
            if ('E' or 'K' in self.secondaryvehicles) or (self.keyvehicle == 'E'):
                # A pedestrian/skater was involved
                pedestrian = True
        elif self.keyvehicle == 'E':
            pedestrian = True
        return pedestrian
        
    def __streetview__(self):
        '''Creates the Google Streetview API request'''
        if self.hasLocation == False:
            return None
        h = 300
        w = 300
        fov = 90
        heading = 235
        pitch = 10
        link = 'http://maps.google.com/?cbll=%s,%s&cbp=12,20.09,,0,5&layer=c' % (self.lon,self.lat)
        return '<a href="%s" target="_blank"><img src="https://maps.googleapis.com/maps/api/streetview?size=%sx%s&location=%s,%s&pitch=%s"></a>' % (link,h,w,self.lon,self.lat,pitch)
        
            
    def __str__(self):
        '''Creates an HTML-readable summary of the nztacrash object.'''
        text = ''
        for t in [self.tla_name, self.crash_dow, self.crash_road, self.side_road,
        self.__roadwet, self.__wthr, self.__light,
        self.__movement, self.__atype, self.__amovement, self.__secondary,
        self.__youngestped, self.__youngestcyc, self.__factors, self.__objects,
        self.__consequences]:
            if t != None:
                text += t + '\n'
        rettext = ''
        for l in text.split('\n'):
            if 'None' not in l:
                rettext += l + '\n'    
        return rettext
    
    def __geo_interface__(self):
        '''
        Returns a geojson object representing the point.
        '''
        #return {'type': 'Point', 'coordinates': (self.lat, self.lon), }
        if self.hasLocation is False:
            return None
        if self.crash_intsn == 'I':
            crashroad = self.crash_road + ' at ' + self.side_road
        else:
            crashroad = self.crash_road
        return {'type': 'Feature',
        'properties': {'crash_id': self.crash_id,
        'tla_name': self.tla_name,
        'crash_dow': self.crash_dow,
        'crash_date': genFunc.formatNiceDate(self.crash_date),
        'crash_time': genFunc.formatNiceTime(self.crash_time),
        'streetview': self.__streetview__(),
        'crash_road': genFunc.formatNiceRoad(crashroad,self.streetdecoder),
        'weather_icon': self.weatherIcon(),
        'road_conditions_txt': self.__roadwet,
        'light_txt': self.__light,
        'movement_txt': self.__movement,
        'vehicle_a_txt': self.__atype,
        'vehicle_a_movement_txt': self.__amovement,
        'secondary_vehicles_txt': self.__secondary,
        'youngest_pedestrian_txt': self.__youngestped,
        'youngest_cyclist_txt': self.__youngestcyc,
        'factors_txt': self.__factors,
        'objects_txt': self.__objects,
        'consequences_txt': self.__consequences,
        'cyclist': self.cyclist,
        'pedestrian': self.pedestrian,
        'fatal': self.fatal,
        'severe': self.injuries_severe,
        'minor': self.injuries_minor,
        'no_injuries': self.injuries_none},
        'geometry': {'type': 'Point', 'coordinates': (self.lat, self.lon)}}
        
    def decodeMovement(self):
        '''Decodes self.mvmt into a human-readable form.
        Movement applies to left and right hand bends, curves, or turns.'''
        decoder = {'A': ('Overtaking and lane change', {'A': 'Pulling out or changing lane to right', 'B': 'Head on', 'C': 'Cutting in or changing lane to left', 'D': 'Lost control (overtaking vehicle)', 'E': 'Side road', 'F': 'Lost control (overtaken vehicle)', 'G': 'Weaving in heavy traffic', 'O': 'Other'}),
                 'B': ('Head on',{'A': 'On straight', 'B': 'Cutting corner', 'C': 'Swinging wide', 'D': 'Both cutting corner and swining wide, or unknown', 'E': 'Lost control on straight', 'F': 'Lost control on curve', 'O': 'Other'}),
                 'C': ('Lost control or off road (straight roads)',{'A': 'Out of control on roadway', 'B': 'Off roadway to left', 'C': 'Off roadway to right', 'O': 'Other'}),
                 'D': ('Cornering',{'A': 'Lost control turning right', 'B': 'Lost control turning left', 'C':' Missed intersection or end of road', 'O': 'Other'}),
                 'E': ('Collision with obstruction',{'A': 'Parked vehicle', 'B': 'Crash or broken down', 'C': 'Non-vehicular obstructions (including animals)', 'D': 'Workman\'s vehicle', 'E': 'Opening door', 'O': 'Other'}),
                 'F': ('Rear end',{'A': 'Slower vehicle', 'B': 'Cross traffic', 'C': 'Pedestrian', 'D': 'Queue', 'E': 'Signals', 'F': 'Other', 'O': 'Other'}),
                 'G': ('Turning versus same direction',{'A': 'Rear of left turning vehicle', 'B': 'Left turn side swipe', 'C': 'Stopped or turning from left side', 'D': 'Near centre line', 'E': 'Overtaking vehicle', 'F': 'Two turning', 'O': 'Other'}),
                 'H': ('Crossing (no turns)',{'A': 'Right angle (70 to 110 degress)', 'O': 'Other'}),
                 'J': ('Crossing (vehicle turning)',{'A': 'Right turn right side', 'B': 'Opposing right turns', 'C': 'Two turning', 'O': 'Other'}),
                 'K': ('Merging',{'A': 'Left turn in', 'B': 'Opposing right turns', 'C': 'Two turning', 'O': 'Other'}),
                 'L': ('Right turn against',{'A': 'Stopped waiting to turn', 'B': 'Making turn', 'O': 'Other'}),
                 'M': ('Manoeuvring',{'A': 'Parking or leaving', 'B': 'U turn', 'C': 'U turn', 'D': 'Driveway manoeuvre', 'E': 'Entering or leaving from opposite side', 'F': 'Enetering or leaving from same side', 'G': 'Reversing along road', 'O': 'Other'}),
                 'N': ('Pedestrians crossing road',{'A': 'Left side', 'B': 'Right side', 'C': 'Left turn left side', 'D': 'Right turn right side', 'E': 'Left turn right side', 'F': 'Right turn left side', 'G': 'Manoeuvring vehicle', 'O': 'Other'}),
                 'P': ('Pedestrians other',{'A': 'Walking with traffic', 'B': 'Walking facing traffic', 'C': 'Walking on footpath', 'D': 'Child playing (including tricycle)', 'E': 'Attending to vehicle', 'F': 'Entering or leaving vehicle', 'O': 'Other'}),
                 'Q': ('Miscellaneous',{'A': 'Fell while boarding or alighting', 'B': 'Fell from moving vehicle', 'C': 'Train', 'D': 'Parked vehicle ran away', 'E': 'Equestrian', 'F': 'Fell inside vehicle', 'G': 'Trailer or load', 'O': 'Other'})}
        try:
            return (decoder[self.mvmt[0]][0], decoder[self.mvmt[0]][1][self.mvmt[1]])
        except KeyError:
            return None
        
    def getKeyVehicle(self, decode=False):
        '''Returns the key vehicle code (or the decoded value), which is one part
        of self.vehicles'''
        if self.vehicles != None:
            code = self.vehicles[0]
            if not decode:
                return code
            else:
                try:
                    decoder = {'C': 'car',
                               'V': 'van/ute',
                               'X': 'taxi/taxi van',
                               'B': 'bus',
                               'L': 'school bus',
                               '4': 'SUV/4X4',
                               'T': 'truck',
                               'M': 'motorcycle',
                               'P': 'moped',
                               'S': 'bicycle',
                               'O': 'other/unknown',
                               'E': 'pedestrian'}
                except KeyError:
                    return None
                return decoder[code]
        else:
            return None
    
    def getKeyVehicleMovement(self, decode=False):
        '''Returns the key vehicle movement (or the decoded value), which is the
        second part of self.vehicles'''
        if self.vehicles != None:
            code = self.vehicles[1:]
            if not decode:
                return code
            else:
                try:
                    decoder = {'N': 'North', 'S': 'South', 'E': 'East', 'W': 'West', '1': 'on the first street', '2': 'on the second street'}
                    try:
                        return '%s %s' % (decoder[code[0]], decoder[code[1]])
                    except IndexError:
                        return None
                except KeyError:
                    return None
                
    def getSecondaryVehicles(self, decode=False):
        '''Returns the secondary vehicle type codes (or the decoded values)
        as a list of strings'''
        if len(self.vehicles) > 3:
            # Other vehicles were involved
            # Get a list of the other vehicle codes
            vehicles = self.vehicles[3:]
            if not decode:
                return [v for v in vehicles]
            else:
                try:
                    decoder = {'C': 'car',
                           'V': 'van/ute',
                           'X': 'taxi/taxi van',
                           'B': 'bus',
                           'L': 'school bus',
                           '4': 'SUV/4X4',
                           'T': 'truck',
                           'M': 'motorcycle',
                           'P': 'moped',
                           'S': 'bicycle',
                           'E': 'pedestrian',
                           'K': 'skateboard/in-line skater/etc.',
                           'Q': 'equestrian',
                           'H': 'wheeled pedestrian (wheelchairs, etc.)',
                           'O': 'other/unknown'}
                    return [decoder[v] for v in vehicles]
                except KeyError:
                    return None
        else:
            # There were no other vehicles
            return None
            
    def getObjectsStruck(self, decode=False):
        '''Returns the objects struck as a list, or their decoded value, also
        as a list.
        
        During a crash the vehicle(s) involved may strike objects either in the
        roadway or on the roadside. Since the same vehicle might not have
        struck all the objects involved, each object is linked to the vehicle
        that hit it, but this is not shown on the listing.
        
        The coded crash listings show only the first three objects struck. The
        same object type may appear twice but only if it has been struck by
        different vehicles.
        
        Note:
        If one vehicle strikes the same object type more than once (i.e. 2
        parked cars) then only the first is coded.
        '''
        if self.objects_struck == None:
            return None
        decoder = {'A': 'driven or accompanied animals, i.e. under control',
                       'B': 'bridge abutment, handrail or approach, includes tunnels',
                       'C': 'upright cliff or bank, retaining walls',
                       'D': 'debris, boulder or object dropped from vehicle',
                       'E': 'over edge of bank',
                       'F': 'fence, letterbox, hoarding etc.',
                       'G': 'guard or guide rail (including median barriers)',
                       'H': 'house or building',
                       'I': 'traffic island or median strip',
                       'J': 'public furniture, eg phone boxes, bus shelters, signal controllers, etc.',
                       'K': 'kerb, when directly contributing to incident',
                       'L': 'landslide, washout or floodwater',
                       'M': 'parked motor vehicle',
                       'N': 'train',
                       'P': 'utility pole, includes lighting columns',
                       'Q': 'broken down vehicle, workmen\'s vehicle, taxis picking up, etc.',
                       'R': 'roadwork signs or drums, holes and excavations, etc',
                       'S': 'traffic signs or signal bollards',
                       'T': 'trees, shrubbery of a substantial nature',
                       'V': 'ditch',
                       'W': 'wild animal, strays, or out of control animals',
                       'X': 'other',
                       'Y': 'objects thrown at or dropped onto vehicles',
                       'Z': 'into water, river or sea'}
        try:
            return [decoder[o] for o in self.objects_struck]
        except KeyError:
            return None
        
    def decodeLight(self):
        '''Takes self.light (a list of strings) and applies a decoder to it,
        returning a list of strings that are human-readable.'''
        decoder1 = {'B': 'Bright sun',
                    'O': 'Overcast',
                    'T': 'Twilight',
                    'D': 'Dark',
                    ' ': None}
        decoder2 = {'O': 'street lights on',
                    'F': 'street lights off',
                    'N': 'No street lights present',
                    ' ': None}
        return [decoder1[self.light[0]], decoder2[self.light[1]]]
       
    def decodeWeather(self):
        '''Takes self.wthr_a (a list of strings) and applies a decoder to it,
        returning a list of strings that are human-readable.'''
        decoder1 = {'F': 'Fine',
                    'M': 'Mist/fog',
                    'L': 'Light rain',
                    'H': 'Heavy rain',
                    'S': 'Snow',
                    ' ': None}
        decoder2 = {'F': 'Frost',
                    'S': 'Strong wind',
                    ' ': None}
        try:
            return [decoder1[self.wthr_a[0]], decoder2[self.wthr_a[1]]]
        except KeyError:
            return None
    
    def weatherIcon(self):
        '''Takes self.wthr_a (a list of strings) and applies a decoder to it,
        return a list of strings that represent paths to PNG icons that represent
        the weather.'''
        if self.light[0] in ['T', 'D']: 
            # If not daytime
            light = 'Night'
        else:
            light = 'Day'
        decoder1 = {'F': {'Night': 'Weather-Moon-icon.png', 'Day': 'Weather-Sun-icon.png'},
                    'M': {'Night': 'Weather-Fog-Night-icon.png', 'Day': 'Weather-Fog-Day-icon.png'},
                    'L': 'Weather-Little-Rain-icon.png',
                    'H': 'Weather-Downpour-icon.png',
                    'S': 'Weather-Snow-icon.png',
                    ' ': None}
        decoder2 = {'F': 'Temperature-2-icon.png',
                    'S': '05-strong-wind-weather-icon.png',
                    ' ': None}
        w1 = self.wthr_a[0]
        if w1 != ' ':
            # Get the appropriate icon
            if w1 in ['F','M']:
                # Also need the light parameter
                icon1 = decoder1[w1][light]
            else:
                icon1 = decoder1[w1]
        else:
            icon1 = None
        w2 = self.wthr_a[1]
        if w2 != ' ':
            # Get the appropriate secondary icon
            icon2 = decoder2[w2]
        else:
            icon2 = None
        
        ret = ''
        h,w = 30,30
        base = './icons'
        if icon1 == None and icon2 == None:
            # No weather data at all
            return None
        if icon1 != None:
            ret += '<img src="%s/%s" height="%d" width="%d">' % (base,icon1,h,w)
        if icon2 != None:
            ret += '<img src="%s/%s" height="%d" width="%d">' % (base,icon2,h,w)
        return ret
        
    def decodeJunction(self):
        '''Takes self.junc_type (a single-character string) and applies a decoder to
        it, returning a human-readable string.
        
        Note:
        When one of the vehicles involved is attempting to enter or leave a
        driveway at an intersection location, the driveway code takes
        precedence.'''
        if self.junc_type == None:
            return None
        decoder = {'D': 'Driveway',
                   'R': 'Roundabout',
                   'X': 'Crossroads',
                   'T': 'T intersection',
                   'Y': 'Y intersection',
                   'M': 'Multi-leg intersection'}
        try:
            return decoder[self.junc_type]
        except KeyError:
            return None
        
    def projectedpt(self, target=pyproj.Proj(init='epsg:3728')):
        '''Takes the original NZTM point coordinates, and transforms them into
        a `target` pyproj.Proj() projected coordinate system, returning the
        crash location as a tuple (X,Y) (Easting,Northing)
        
        Example `target`: pyproj.Proj(init='epsg:3857') (Web Mercator) (Default)
        '''
        if self.easting != None and self.northing != None:
            xt, yt = pyproj.transform(self.proj, target, self.easting, self.northing)
            return (xt, yt)
            
    def getCauses(self, decode=False):
        '''Returns the causes of the crash, and the vehicle to which the (in)action
        is ascribed to as a dictionary in the following structure:
        {'A': ['Cause1', 'Cause2',],
         'B': ['Cause3'],
         'Environment': ['Cause4']}
         
        If decode == False: codes are used in the returned dictionary.
        Else if decode == True: the codes are converted to human-readable string
        values in the returned dictionary.
        In either case, the keys of the dictionary are 'A' for vehicle 1, 'B'
        for vehicle 2, etc., and 'Environment' for the factors not attributed
        to any particular vehicle. 'A', 'B' etc. only exist if appropriate,
        but 'Environment' always exists, but with None if there are no
        environmental factors. 
         
        The factor codes are a set of three digit numerical codes that identify
        reasons why the crash occurred.
        They are grouped into related categories, (see Appendix 2). These
        factors are coded after consideration of the written explanation of
        what happened in the drivers', the witnesses', and any other involved
        parties' statements, and in the Police descriptions and comments.

        A letter after the factor code indicates the vehicle or driver to which
        that factor applies. 'A' applies to V1; 'B' applies to V2, etc., e.g.
        '301B' indicates that the driver of vehicle 2 failed to give way at a
        stop sign.

        As well as describing driver and vehicle-related factors, there are
        also codes for other aspects of a crash such as the road conditions and
        the environmental conditions. These environmental factor codes are
        numbered from 800 onwards.

        Note:
        Driver and vehicle factor codes were not added to non-injury crashes in
        the areas north of a line approximately from East Cape, south of Taupo,
        to the mouth of the Mokau River prior to 2007.

        Note:
        All contributing factors may not be shown in the listing due to space
        limitations on the report.'''
        
        # Miscellaneous lookup information
        majorcauses_lookup = {(100, 210): 'Driver control',
        (300, 387): 'Vehicle conflicts',
        (400, 448): 'General driver',
        (500, 534): 'General person',
        (600, 696): 'Vehicles',
        (700, 732): 'Pedestrians',
        (800, 873): 'Road',
        (900, 998): 'Miscellaneous'}
        minorcauses_lookup = {100: 'Alcohol or drugs',
        110: 'Too fast for conditions',
        120: 'Failed to keep left',
        130: 'Lost control',
        140: 'Failed to signal in time',
        150: 'Overtaking',
        170: 'Wrong lane or turned from wrong positions',
        180: 'In line of traffic',
        190: 'Sudden action',
        200: 'Forbidden movements',
        300: 'Failed to give way',
        320: 'Did not stop',
        330: 'Inattentive: failed to notice',
        350: 'Attention diverted by:',
        370: 'Did not see or look for another party until too late',
        380: 'Misjudged speed, distance, size or position of:',
        400: 'Inexperience',
        410: 'Fatigue (drowsy, tired, fell asleep',
        420: 'Incorrect use of vehicle controls',
        430: 'Showing off',
        440: 'Parked or stopped',
        500: 'Illness and disability',
        510: 'Intentional or criminal',
        520: 'Driver or passenger, boarding, leaving, in vehicle',
        530: 'Miscellaneous person',
        600: 'Lights and reflectors at fault or dirty',
        610: 'Brakes',
        620: 'Steering',
        630: 'Types',
        640: 'Windscreen or mirror',
        650: 'Mechanical',
        660: 'Body or chassis',
        680: 'Load',
        690: 'Miscellaneous vehicle',
        700: 'Walking along road',
        710: 'Crossing road',
        720: 'Miscellaneous',
        800: 'Slippery',
        810: 'Surface',
        820: 'Obstructed',
        830: 'Visibility limited',
        840: 'Signs and signals',
        850: 'Markings',
        860: 'Street lighting',
        870: 'Raised islands and roundabouts',
        900: 'Weather',
        910: 'Animals',
        920: 'Entering or leaving land use',
        970: 'Unconverted old codes'}
        
        retdict = {}
        for cause in self.causes:
            if len(cause) == 4:
                vehicle = cause[-1] # A, B, etc.
                causecode = cause[:-1]
            elif len(cause) == 3:
                vehicle = 'Environment'
                causecode = cause
            else:
                #raise Exception # Invalid party
                return None
            if len(causecode) > 3:
                raise Exception # Cause codes must be 3 digits in length
            elif len(causecode) < 3:
                # Append a leading 0
                # TODO: is this correct?
                causecode = '0' + causecode
            if vehicle not in retdict.keys():
                retdict[vehicle] = [causecode]
            else:
                retdict[vehicle].append(causecode)
        if not decode:
            return retdict
        else:
            decodedretdict = {}
            for vehicle in retdict.keys():
                causecodes = retdict[vehicle]
                for causecode in causecodes:
                    major, minor, detail = None, None, None # Default
                    # Get the major category the cause falls into
                    while major == None:
                        for k in majorcauses_lookup.keys():
                            if int(causecode) >= k[0] and int(causecode) <= k[1]:
                                major = majorcauses_lookup[k]
                                
                    # Get the minor category the cause falls into
                    # Round the cause code down to the nearest 10
                    minorcode = genFunc.round_down(int(causecode),10)
                    while minor == None: # Until we find a matching entry...
                        if minorcode not in minorcauses_lookup.keys():
                            # If there's no matching entry, subtract 10 and look again
                            minorcode -= 10
                        else:
                            # If there's a match, decode the value
                            minor = minorcauses_lookup[minorcode]

                    # Get the lowest level of detail if applicable
                    if causecode[2] != '0': # If there's a trailing zero...
                        # ...then we have more detail available
                        detail = self.causedecoder[causecode]
                        
                    # Now piece together the decoded cause string
                    causedecoded = major + ": " + minor
                    if detail != None:
                        causedecoded += ' - ' + detail

                    if vehicle not in decodedretdict.keys():
                        decodedretdict[vehicle] = [causedecoded]
                    else:
                        decodedretdict[vehicle].append(causedecoded)
            return decodedretdict

def makeFolium(instances, peds=True, cyclists=True, others=True):
    '''
    Makes a Folium map with a list of crash instances to plot.
    
    Able to filter with peds, cyclists and others (Booleans)
    '''
    # instantiate map
    # add points iteratively
    # save map
    map_osm = folium.Map(location=[-41.17, 174.46], width='100%',height='100%',tiles='OpenStreetMap', zoom_start=6)
    for crash in instances:
        # Add a marker
        desc, lat, lon, fatal, injuries_severe, injuries_minor, ped, cyc = crash[0], crash[1][1], crash[1][0], crash[2], crash[3], crash[4], crash[5], crash[6]
        
        # Data filtering
        if peds == False and ped == True:
            continue
        if cyclists == False and cyc == True:
            continue
        if others == False and (cyc == False or ped == False):
            continue
        # Handle jQuery special characters in the pop-up
        for sc in [':',',','\n','-', '\t']:
            if sc == '\n':
                replace = '<br>'
            elif sc == '\t':
                # Just get rid of these
                replace = ''
            else:
                replace = '\\%s' % sc
            desc = desc.replace(sc,replace)
        #map_osm.simple_marker([lat, lon], popup=desc)
        if fatal:
            # Death
            color = 'red'
            radius = 90
            fill_opacity = 0.9
        elif injuries_severe:
            # Severe injuries
            color = 'orange'
            radius = 60
            fill_opacity = 0.8
        elif injuries_minor:
            # Minor injuries
            color = 'purple'
            radius = 30
            fill_opacity = 0.6
        else:
            # No injuries
            color = 'blue'
            radius = 15
            fill_opacity = 0.4
        #fill_opacity = 0.8 # Override
        try:
            map_osm.circle_marker([lat, lon], popup=desc, fill_color=color, radius=radius, fill_opacity=fill_opacity, line_color=color)
        except UnicodeDecodeError:
            print desc
    map_osm.create_map(path='../nzta-crash-analysis.html')
    
def causeDecoderCSV(data):
    '''
    Reads a CSV, dervied from a PDF (!) of crash cause codes and their text
    descriptions. Returns a dictionary of the codes (keys) and the values
    (values), both as strings. Hard coded.
    '''
    with open(data, 'rb') as decodecsv:
        decodereader = csv.reader(decodecsv, delimiter=',')
        header = decodereader.next()
        retdict = {}
        for coderow in decodereader:
            code = coderow[3]
            decode = coderow[4]
            retdict[code] = decode
    return retdict

def streetDecoderCSV(data):
    '''
    Reads a CSV, derived from a PDF of NZ street abbreviations. Returns a dictionary
    of the abbreviated form (key) and the full form (value).
    '''
    with open(data, 'rb') as decodecsv:
        decodereader = csv.reader(decodecsv, delimiter=',')
        header = decodereader.next()
        retdict = {}
        for coderow in decodereader:
            code = coderow[1]
            decode = coderow[0]
            retdict[code] = decode
    return retdict
    
def main(data,causes,streets):
    # Open and read the CSV of crash events
    with open(data, 'rb') as crashcsv:
        crashreader = csv.reader(crashcsv, delimiter=',')
        header = crashreader.next()
        causedecoder = causeDecoderCSV(causes) # Decode the coded values
        streetdecoder = streetDecoderCSV(streets)
        crashes = []
        # Empty feature collection, ready for geojson-ing
        feature_collection = {"type": "FeatureCollection",
                              "features": []}
        for crash in crashreader:
            Crash = nztacrash(crash, causedecoder, streetdecoder)
            # Collect crash descriptions and locations into a list of tuples
            if Crash.hasLocation:
                # Append it to our list to map
                crashes.append((Crash.__str__(), (Crash.lat, Crash.lon), Crash.fatal, Crash.injuries_severe, Crash.injuries_minor, Crash.pedestrian, Crash.cyclist))
                
                # Add to the GeoJSON feature collection
                feature_collection["features"].append(Crash.__geo_interface__())

        # Write the geojson output
        with open('../data/data.geojson', 'w') as outfile:
            outfile.write(json.dumps(feature_collection))

    # Make the map
    #makeFolium(crashes)

if __name__ == '__main__':
    data = '/home/richard/Documents/Projects/national-crash-statistics/data/crash-data-2014-partial.csv'
    causes = '/home/richard/Documents/Projects/national-crash-statistics/data/decoders/cause-decoder.csv'
    streets = '/home/richard/Documents/Projects/national-crash-statistics/data/decoders/NZ-post-street-types.csv'
    main(data,causes,streets)


