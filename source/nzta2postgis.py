#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
`nzta2postgis.py`
=================
A Python script to read the New Zealand Transport Agency crash data into a
Postgres database (extended with PostGIS) database.

Depends
=======
pyproj
folium
'''

# TODO Update docstring to reflect that this is not longer postgis

import pyproj
import folium
import csv
import datetime
import string

def causeDecoderCSV():
    '''
    Reads a CSV, dervied from a PDF (!) of crash cause codes and their text
    descriptions. Returns a dictionary of the codes (keys) and he values
    (values), both as strings. Hard coded.
    '''
    data = "/home/richard/Documents/Projects/national-crash-statistics/data/decoders/cause-decoder.csv"
    with open(data, 'rb') as decodecsv:
        decodereader = csv.reader(decodecsv, delimiter=',')
        header = decodereader.next()
        retdict = {}
        for coderow in decodereader:
            code = coderow[3]
            decode = coderow[4]
            retdict[code] = decode
    return retdict

def empty(string):
    if string in ['', ' ']:
        return True
    return False

def formatInteger(integerstring):
    if empty(integerstring):
        return None
    return int(integerstring)
            
def formatString(string):
    # NOTE: be careful stripping encoded strings, which may have empty values
    # representing unknown values for particular values
    if empty(string):
        return None
    return string

def formatDate(datestring):
    '''Returns a datetime.date object when given a date as a string of the form
    DD/MM/YYYY (e.g. 30/01/2014)'''
    if empty(datestring):
        return None
    return datetime.datetime.strptime(datestring, "%d/%m/%Y").date()
        
def formatCrashTime(crashtime, dateobj):
    '''Returns a datetime.time object when given a time as a string from the
    `row`. These are purportedly recorded "in 24-hour time", but are lacking
    leading zeros in the dataset, which is addressed here.'''
    if empty(crashtime):
        return None
    return datetime.datetime.strptime(str(dateobj)+" "+'0'*(4-len(crashtime))+crashtime,'%Y-%m-%d %H%M').time()
    
def formatStringList(listofstrings, delim=None):
    '''Returns a list of strings given a string representation of a list data
    structure, separated by `delim`.
    Example:
    input: '308A 371A 727B 929'
    output: ['308A', '371A', '727B', '929']
    If delim is None, each character of the string is assumed to be an
    independent value'''
    if listofstrings == None or listofstrings == []:
        return None
    if delim != None:
        return [str(s) for s in listofstrings.split(delim) if not empty(s)]
    elif delim == None:
        return list(listofstrings)
        
def round_down(integer, base):
    '''Rounds an `integer` down to the nearest `base`
    E.g. round_down(19,10) >>> 10
         round_down(19,5)  >>> 15
         round_down(10,10) >>> 10'''
    return integer - (integer % base)
    
def grammar(singular, plural, integer):
    '''Returns the string `singular` if integer == 1; else it returns `plural`
    if integer > 1.
    Example:
    grammar('person', 'people', 1) >>> 'person'
    grammar('person', 'people', 3) >>> 'people'
    '''
    if integer == 1:
        return singular
    elif integer > 1:
        return plural

class nztacrash:
    '''A crash recorded by NZTA'''
    def __init__(self, row, causedecoder):
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
        self.tla_name = formatString(row[0])
        self.crash_road = formatString(row[1])
        if self.crash_road != None and self.crash_road[0:3] != 'SH ':
            self.crash_road = self.crash_road.title()
        self.crash_dist = formatInteger(row[2])
        self.crash_dirn = formatString(row[3])
        self.crash_intsn = formatString(row[4])
        self.side_road = formatString(row[5])
        if self.side_road != None and self.side_road[0:3] != 'SH ':
            self.side_road = self.side_road.title()
        self.crash_id = formatString(row[6])
        self.crash_date = formatDate(row[7])
        self.crash_dow = formatString(row[8])
        self.crash_time = formatCrashTime(row[9], self.crash_date) # Returns a datetime.datetime.time() object
        self.mvmt = formatString(row[10])
        self.vehicles = formatString(row[11])
        self.causes = formatStringList(row[12],delim=' ') # Returns a list
        self.objects_struck = formatStringList(row[13],delim=None)
        self.road_curve = formatString(row[14])
        self.road_wet = formatString(row[15])
        self.light = formatStringList(row[16])
        self.wthr_a = formatStringList(row[17])
        self.junc_type = formatString(row[18])
        self.traf_ctrl = formatString(row[19])
        self.road_mark = formatString(row[20])
        try:
            self.spd_lim = formatInteger(row[21]) # Integer
        except:
            self.spd_lim = formatString(row[21]) # String
            # Becuase 'U' and 'LSZ' are also valid
        self.crash_fatal_cnt = formatInteger(row[22]) # Number of people who died as a result
        self.crash_sev_cnt = formatInteger(row[23]) # Number of people with severe injuries
        self.crash_min_cnt = formatInteger(row[24]) # Number of people with minor injuries
        self.pers_age1 = formatInteger(row[25])
        self.pers_age2 = formatInteger(row[26])
        
        # Spatial information
        self.easting = formatInteger(row[27]) # NZTM
        self.northing = formatInteger(row[28]) # NZTM
        self.proj = pyproj.Proj(init='epsg:2193') # NZTM projection
        if self.easting == None or self.northing == None:
            self.hasLocation = False
        else:
            self.hasLocation = True
        if self.hasLocation == True:
            self.lat, self.lon = self.proj(self.easting, self.northing, inverse=True) # Lat/lon
        else:
            self.lat, self.lon = None, None
        #self.pt_projected = self.projectedpt() # Accept default target projection
        
        # Output of causeDecoderCSV()
        self.causedecoder = causedecoder
        
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

    def __str__(self):
        '''Creates an HTML-readable summary of the nztacrash object.'''
        text = 'The crash occured in %s on <b>%s %s at %s</b>.\n' % (str(self.tla_name), self.crash_dow, self.crash_date.strftime('%d %B, %Y'), str(self.crash_time)[:-3])
        text += 'Crash ID: %s.\n' % self.crash_id
        text += 'Location: %s.\n' % self.crash_road
        text += 'Side road: %s.\n' % self.side_road
        text += '%sm to the %s.\n' % (str(self.crash_dist), self.crash_dirn)
        if self.crash_intsn == 'I':
            text += 'It occurred at an intersection.'
        else:
            text += 'It did not occur at an intersection.'
        if self.junc_type != None:
            text =  text.strip('.') + ': %s' % self.junc_type_decoded
        text += '\n'
        if self.road_wet == 'W':
            text += 'The road was wet.\n'
        if self.road_wet == 'D':
            text += 'The road was dry.\n'
        if self.road_wet == 'I':
            text += 'There was snow or ice on the road.\n'
        if self.wthr_a != None:
            text += 'Weather: %s' % self.wthr_a_decoded[0]
            if self.wthr_a_decoded[1] != None:
                text += ' - %s' % self.wthr_a_decoded[1]
            text += '.\n'
        if self.light != None:
            text += 'Lighting: %s' % self.light_decoded[0]
            if self.light_decoded[1] != None:
                text += ' - %s' % self.light_decoded[1]
            text += '.\n'
        
        if self.decodeMovement() != None and self.decodeMovement()[0] != None:
            text += 'Movement: %s' % self.decodeMovement()[0]
            if self.decodeMovement()[1] != None:
                text += '- %s' % self.decodeMovement()[1]
        text += '.\n'
        text += '<b>Vehicle A was a %s</b> (it may or may not have been at fault).\n' % self.keyvehicle_decoded.lower()
        if self.keyvehiclemovement_decoded != None:
            text += 'Vehicle A was moving %s.\n' % self.keyvehiclemovement_decoded.lower()
        if self.secondaryvehicles_decoded != None:
            party = grammar('party', 'parties', len(self.secondaryvehicles))
            text += 'Secondary %s: ' % party
            for v in self.secondaryvehicles_decoded:
                text += '<b>%s</b>, ' % v
            text = text.strip(', ')+'.\n'
        else:
            text += 'No other parties were involved.\n'
        if self.pers_age1 != None and self.secondaryvehicles != None:
            youngest = grammar('', ' youngest', len(self.secondaryvehicles))
            text += '<b>The%s pedestrian was %d years old.</b>\n' % (youngest, self.pers_age1)
        if self.pers_age2 != None and self.secondaryvehicles != None:
            youngest = grammar('', ' youngest', len(self.secondaryvehicles))
            text += '<b>The%s cyclist was %d years old.</b>\n' % (youngest, self.pers_age2)
        text += "\n<u>Causes</u>:\n<ol>"
        for vehicle in list(string.ascii_uppercase): # 'A', 'B', ..., 'Z'
            if self.causesdict_decoded != None and vehicle in self.causesdict_decoded.keys():
                for cause in self.causesdict_decoded[vehicle]:
                    text += "\t<li>Vehicle <b>%s</b>: %s.</li>" % (vehicle, cause)
        if self.causesdict_decoded != None and 'Environment' in self.causesdict_decoded.keys():
            for cause in self.causesdict_decoded['Environment']:
                text += '\t<li>Environmental factor: %s.</li>' % cause
        text += '</ol>'
        
        if len(self.objects_struck) > 0:
            text += '<u>Stationary objects hit</u>:<ul>'
            for o in self.objects_struck_decoded:
                text += '\t<li>%s</li>' % o.capitalize()
            text += '</ul>'
        else:
            text += 'No stationary objects were hit.'
        text += '\n'
        
        text += '<center>'
        if self.crash_fatal_cnt > 0:
            person = grammar('person', 'people', self.crash_fatal_cnt)
            text += '\nUnfortunately, <b>%d %s died</b> as a result of this crash.\n'  % (self.crash_fatal_cnt, person)
        if self.crash_sev_cnt > 0:
            person = grammar('person', 'people', self.crash_sev_cnt)
            text += '\n<b>%d %s suffered serious injuries</b>.\n' % (self.crash_sev_cnt, person)
        if self.crash_min_cnt > 0:
            was = grammar('was', 'were', self.crash_min_cnt)
            injury = grammar('injury', 'injuries', self.crash_min_cnt)
            text += '\nThere %s <b>%d minor %s</b>.\n' % (was, self.crash_min_cnt, injury)
        if self.fatal == False and self.injuries == False:
            text += '\nFortunately, there were <b>no deaths or injuries</b>.\n'
        text = text.strip() + '</center>'
        
        rettext = ''
        for l in text.split('\n'):
            if 'None' not in l:
                rettext += l + '\n'
        return rettext
        
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
                    minorcode = round_down(int(causecode),10)
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

def makeFolium(instances):
    '''
    Makes a Folium map with a list of crash instances to plot
    '''
    # instantiate map
    # add points iteratively
    # save map
    map_osm = folium.Map(location=[-41.17, 174.46], width='100%',height='100%',tiles='OpenStreetMap', zoom_start=6)
    for crash in instances:
        # Add a marker
        desc, lat, lon, fatal, injuries_severe, injuries_minor = crash[0], crash[1][1], crash[1][0], crash[2], crash[3], crash[4]
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
    map_osm.create_map(path='nzta-crash-analysis.html')

# Open and read the CSV
#data = "/home/richard/Documents/Projects/national-crash-statistics/data/subsets/data-2014-hutt-city.csv"
data = "/home/richard/Documents/Projects/national-crash-statistics/data/crash-data-2014-partial.csv"
with open(data, 'rb') as crashcsv:
    crashreader = csv.reader(crashcsv, delimiter=',')
    header = crashreader.next()
    causedecoder = causeDecoderCSV()
    crashes = []
    for crash in crashreader:
        Crash = nztacrash(crash, causedecoder)
        # Collect crash descriptions and locations into a list of tuples
        if Crash.hasLocation:
            crashes.append((Crash.__str__(), (Crash.lat, Crash.lon), Crash.fatal, Crash.injuries_severe, Crash.injuries_minor))

# Make the map
makeFolium(crashes)

