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
geojson
'''

import pyproj
import geojson
import json
import csv
import string
import generalFunctions as genFunc
import re
import logging
     
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
        # Output of causeDecoderCSV()
        self.causedecoder = causedecoder
        
        # Output of streetDecoderCSV()
        self.streetdecoder = streetdecoder
        
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
        self.hasLocation = self.get_hasLocation()
        
        # Approximate correction for Chatham Islands, which NZTA has offset
        if self.tla_name == 'Chatham Islands County' and self.hasLocation:
             # In units of the projection system (NZTM)
            lat_correction = -96135
            lon_correction = 355966
            self.easting += lon_correction
            self.northing += lat_correction
        
        self.proj = pyproj.Proj(init='epsg:2193') # NZTM projection
        
        if self.hasLocation == True:
            self.lat, self.lon = self.proj(self.easting, self.northing, inverse=True) # Lat/lon
        else:
            logging.warning('Crash does not have XY location, so is not added to GeoJSON')
            self.lat, self.lon = None, None

        # Google Streetview API key
        self.api = open('google-streetview-api-key','r').read()
        
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
            
        # Now assign booleans to identify the worst (and only the worst) injury
        self.worst_fatal = False # Default
        self.worst_severe = False # Default
        self.worst_minor = False # Default
        self.worst_none = False # Default
        if self.fatal:
            self.worst_fatal = True
        elif not self.fatal:
            if self.injuries:
                if self.injuries_severe:
                    self.worst_severe = True
                elif self.injuries_minor:
                    self.worst_minor = True
        if self.injuries_none:
            self.worst_none = True
        
        # Party involvement
        self.pedestrian = self.get_mode_involvement(['E','K','H']) # Pedestrian, skater, wheeled pedestrian
        self.cyclist = self.get_mode_involvement(['S']) # Cyclist
        self.motorcyclist = self.get_mode_involvement(['M','P']) # Motorcyclist, moped
        self.taxi = self.get_mode_involvement(['X']) # Taxi/taxi van
        self.truck = self.get_mode_involvement(['T']) # Truck
        
        # Roles and factors
        self.tourist = self.get_factor_involvement(['404','731'])
        self.alcohol = self.get_factor_involvement(['101','102','103','104','105'])
        self.drugs = self.get_factor_involvement(['107','108','109'])
        self.cellphone = self.get_factor_involvement(['359'])
        self.fatigue = self.get_factor_involvement(['410','411','412','413','414','415'])
        self.dickhead = self.get_factor_involvement(['430','431','432','433','434'])
        self.speeding = self.get_factor_involvement(['110','111','112','113','114','115','116','117'])
        
    def get_hasLocation(self):
        if self.easting in [0,None] or self.northing in [0,None]:
            # If either coordinate is invalid, accident does not have location
            # 0 considered erroneous because of NZTA data entry error
            return False
        else:
            return True
       
    def get_crash_road(self):
        crash_road = genFunc.formatString(self.row[1])
        if crash_road != None and crash_road[0:3] != 'SH ':
            if len(crash_road) == 2 and crash_road != 'TE':
                crash_road = crash_road # Acronym, don't apply title()
            else:
                crash_road = crash_road.title()
        crash_road = genFunc.check_offroad(crash_road)
        crash_road = genFunc.streetExpander(crash_road,self.streetdecoder)
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
            if len(side_road) == 2 and side_road != 'TE':
                side_road = side_road # Acronym, don't apply title()
            else:
                side_road = side_road.title()
        side_road = genFunc.check_offroad(side_road)
        side_road = genFunc.streetExpander(side_road,self.streetdecoder)
        return side_road
        
    def get_mode_involvement(self, mode_list):
        '''Returns a boolean indicating whether the key vehicle or any of the
        secondary vehicles were of the same type of vehicle/person as any of the
        modes supplies in mode_list (a list of modes). Used to determine if a 
        pedestrian was involved in an accident, for example.'''
        if self.keyvehicle in mode_list:
            return True
        if self.secondaryvehicles != None:
            for m in self.secondaryvehicles:
                if m in mode_list:
                    return True
        else:
            return False
            
    def get_factor_involvement(self, factor_list):
        '''Returns a boolean indicating whether any of the 3-digit factor codes
        listed in the factor_list parameter (list of strings) have been cited to
        explain the accident'''
        for c in self.causes:
            if len(c) == 4:
                c = c[0:3]
            if c in factor_list:
                return True
            else:
                pass
        return False
        
    def get_number_of_vehicles(self):
        '''Returns integers representing the numbers of the different types of vehicles
        involved in the accident. Returns None if this information cannot be obtained'''
        retdict = {self.keyvehicle: 1} # Initialise
        if self.secondaryvehicles == None:
            # No more vehicles to add
            return retdict
        for v in self.secondaryvehicles:
            if v not in retdict.keys():
                retdict[v] = 1
            else:
                retdict[v] = retdict[v] + 1
        return retdict
    
    def __vehicle_icons__(self):
        '''Returns a series of <img> tags and paths representing icons of the 
        vehicles and people involved in the accident.'''
        vehicles = self.get_number_of_vehicles()
        if vehicles in [None,'',' ']:
            return None
        base = './icons/transport'
        h,w = 30,30
        hspace = 10
        default = 'Car-2-icon.svg'
        other = 'skateboard-icon.svg'
        decoder = {'C': [default, 'Car'],
                   'V': ['Transport-Bus-2-icon.svg', 'Van or Ute'],
                   'X': ['Taxi-2-icon.svg', 'Taxi or Taxi Van'],
                   'B': ['Transport-Bus-3-icon.svg', 'Bus'],
                   'L': ['Transport-Bus-4-icon.svg', 'School Bus'],
                   '4': ['SUV.svg', '4X4 or SUV'],
                   'T': ['Transport-Truck-icon.svg', 'Truck'],
                   'M': ['motorcycle-icon.svg', 'Motorcycle'],
                   'P': ['moped-icon.svg', 'Moped'],
                   'S': ['bicycle-icon.svg', 'Bicycle'],
                   'O': [other, 'Miscellaneous Vehicle'],
                   'E': ['pedestrian-icon.svg', 'Pedestrian'],
                   'K': [other, 'Skateboard, inline skater, etc.'],
                   'Q': ['equestrian-icon.svg', 'equestrian'],
                   'H': ['wheelchair-icon.svg', 'Wheeled Pedestrian']}
        ret = ''
        for v in vehicles.keys():
            icon = decoder[v][0]
            alt = decoder[v][1]
            multiplier = vehicles[v]
            ret += '<img src="%s/%s" alt="%s" title="%s" height="%d" width="%d" hspace="%d"> ' % (base,icon,alt,alt,h,w,hspace) * multiplier
        return ret
        
    def get_injury_icons(self):
        base = './icons/injuries'
        h,w = 30,30
        hspace = 10
        icons = {'fatal': 'RedMan.svg',
                 'severe': 'OrangeMan.svg',
                 'minor': 'YellowMan.svg'}
        ret = ''
        def add_img(alt,title,icon,multiplier):
            return '<img src="%s/%s" alt="%s" title="%s" height="%d" width="%d" hspace="%d"> ' % (base,icon,alt,alt,h,w,hspace) * multiplier
        ret += add_img('Fatality','Fatality',icons['fatal'],self.crash_fatal_cnt)
        ret += add_img('Severe injury','Severe injury',icons['severe'],self.crash_sev_cnt)
        ret += add_img('Minor injury','Minor injury',icons['minor'],self.crash_min_cnt)
        return ret

        
    def __streetview__(self):
        '''Creates the Google Streetview API request'''
        if self.hasLocation == False:
            return None
        h = 200
        w = 300
        fov = 90
        heading = 235
        pitch = 5
        link = 'http://maps.google.com/?cbll=%s,%s&cbp=12,20.09,,0,5&layer=c' % (self.lon,self.lat)
        alt = 'Click to go to Google Streetview'
        return '<a href="%s" alt="%s" title="%s" target="_blank"><img src="https://maps.googleapis.com/maps/api/streetview?size=%sx%s&location=%s,%s&pitch=%s&key=%s"></a>' % (link,alt,alt,w,h,self.lon,self.lat,pitch,self.api)
    
    def make_causes(self):
        '''
        Returns a nice, readable string of the "factors and roles" of the accident
        '''
        # Map letters to index positions
        vehicles_dict = {}
        for i,v in enumerate(string.ascii_uppercase):
            vehicles_dict[v] = i # {'A': 0, 'B': 1, 'C': 2}
            
        # Map the modes to a text about tbe kind of controller
        decoder = {'C': 'driver of the <strong>car</strong>',
           'V': 'driver of the <strong>van/ute</strong>',
           'X': '<strong>taxi/taxi van driver</strong>',
           'B': '<strong>bus driver</strong>',
           'L': '<strong>school bus driver</strong>',
           '4': 'driver of the <strong>SUV/4X4</strong>',
           'T': '<strong>truck driver</strong>',
           'M': '<strong>motorcyclist</strong>',
           'P': '<strong>moped rider</strong>',
           'S': '<strong>cyclist</strong>',
           'O': 'driver of the <strong>vehicle</strong> of unknown type',
           'E': '<strong>pedestrian</strong>', 
           'K': '<strong>skater</strong>',
           'Q': '<strong>equestrian</strong>',
           'H': '<strong>wheeled pedestrian</strong>'}
        
        # Keep track of the numbers of each mode we see, so the text can be formed
        # using ordinal text ('the first car', etc.)
        modes, mode_counter = ['C','V','X','B','L','4','T','M','P','S','E','K','Q','H','O'], {}
        for m in modes:
            mode_counter[m] = 0 # Initially 0, gets incremented
        
        def find_mode(v,vehicle_counts,mode_counter):
            '''Takes the vehicle code 'A', 'B', etc. and returns the mode of that
            party (e.g. 'car', 'truck')'''
            
            if v == 'Environment' or v == '+':
                # The environment is not a mode
                return None
            
            # Expand the list of modes involved, in order 'A' ... 'Z'
            if self.secondaryvehicles_decoded == None:
                vehicle_map = [self.keyvehicle_decoded]
                vehicle_map_coded = [self.keyvehicle]
            else:
                index = vehicles_dict[v] # Gets the index position to insert the vehicle
                vehicle_map = [self.keyvehicle_decoded] + self.secondaryvehicles_decoded[:]
                vehicle_map_coded = [self.keyvehicle] + self.secondaryvehicles[:]
                
            # Make a version of the mode to included in the causes
            # This ensures that multiple versions of the same mode get labelled
            # appropriately
            if vehicles_dict[v] > len(vehicle_map)-1:
                # There are more parties involved than vehicles listed
                logging.warning('There are more given parties than listed vehicles, so cause attribution has not been conducted: Crash ID %s' % self.crash_id) 
                return None
                
            mode_v = vehicle_map_coded[vehicles_dict[v]]
            mode = vehicle_map[vehicles_dict[v]]
            # Increase the mode counter appropriately
            mode_counter[mode_v] = mode_counter[mode_v] + 1
            
            if vehicle_counts[mode_v] == 1:
                # Then there is only one type of this vehicle involved
                the_mode = 'The %s' % decoder[mode_v]
            elif vehicle_counts[mode_v] > 1:
                # Then there is multiple instances of this type of vehicle involved
                the_mode = 'The %s' % decoder[mode_v].replace('<strong>', '<strong>%s ' % genFunc.ordinal(mode_counter[mode_v]))
  
            # Finally, replace '1st' with 'first', etc.
            ordinal_text = {'1st':'first','2nd':'second','3rd':'third',
                '4th':'fourth','5th':'fifth','6th':'sixth',
                '7th':'seventh','8th':'eighth','9th':'ninth'}
            for s in ordinal_text.keys(): # More?
                if s in the_mode:
                    the_mode = the_mode.replace(s,ordinal_text[s])
            return (the_mode, mode_counter)
            
        vehicle_counts = self.get_number_of_vehicles() # {'C': 1, 'V': 1}
        
        the_text = ''
        causesdict_decoded_sorted = self.causesdict_decoded.keys()
        causesdict_decoded_sorted.sort()
        for v in causesdict_decoded_sorted:
            fmode = find_mode(v,vehicle_counts,mode_counter)
            if fmode != None:
                # A vehicle
                mode, mode_counter = fmode[0], fmode[1]
            else:
                mode = fmode # None; the Environment
            for r in self.causesdict_decoded[v]:
                if r[1] == 'FALSE':
                    # The cause is NULL
                    continue
                subject = r[0]
                if subject is False:
                    # Explanation does not require a subject
                    the_text += '%s.<br>' % (r[1])
                else:
                    # Explanation requires a subject
                    the_text += '%s %s.<br>' % (mode,r[1])
        #raw_input("pause")
        return the_text
    
    def __geo_interface__(self):
        '''
        Returns a geojson object representing the point.
        '''
        if self.hasLocation is False:
            # Can't add it to the map if it does not have a location
            return None
        return {'type': 'Feature',
        'properties': {'crash_id': self.crash_id,
        'tla_name': self.tla_name,
        'crash_dow': self.crash_dow,
        'crash_date': genFunc.formatNiceDate(self.crash_date),
        'crash_time': genFunc.formatNiceTime(self.crash_time),
        'streetview': self.__streetview__(),
        'crash_road': genFunc.formatNiceRoad(self.get_crashroad()),
        'weather_icon': self.weatherIcon(),
        'vehicle_icons': self.__vehicle_icons__(),
        'injury_icons': self.get_injury_icons(),
        'causes': self.make_causes(),
        'cyclist': self.cyclist,
        'pedestrian': self.pedestrian,
        'motorcyclist': self.motorcyclist,
        'taxi': self.taxi,
        'truck': self.truck,
        'tourist': self.tourist,
        'alcohol': self.alcohol,
        'drugs': self.drugs,
        'cellphone': self.cellphone,
        'fatigue': self.fatigue,
        'dangerous_driving': self.dickhead,
        'speed': self.speeding,
        'fatal': self.worst_fatal,
        'severe': self.worst_severe,
        'minor': self.worst_minor,
        'no_injuries': self.worst_none},
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
            
    def get_crashroad(self):
        if self.crash_intsn == 'I':
            # The crash happened at an intersection
            crashroad = self.crash_road + ' at ' + self.side_road
        else:
            if self.side_road != None:
                # Not stated as occuring at a side road, but one still provided
                crashroad = self.crash_road + ' near ' + self.side_road
            else:
                # Only one road provided
                crashroad = self.crash_road
        return crashroad
        
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
        decoder1 = {'F': {'Night': ['weather-moon-icon.svg','Clear Night'], 'Day': ['weather-sun-icon.svg','Clear Day']},
                    'M': {'Night': ['Fog-Night-icon.svg','Night Fog'], 'Day': ['Fog-Day-icon.svg','Day Fog']},
                    'L': ['weather-little-rain-icon.svg','Light Rain'],
                    'H': ['weather-downpour-icon.svg','Heavy Rain'],
                    'S': ['weather-snow-icon.svg','Snow'],
                    ' ': None}
        decoder2 = {'F': ['weather-frost-icon.svg','Frost'],
                    'S': ['weather-wind-icon.svg','Strong Winds'],
                    ' ': None}
        if len(self.wthr_a) > 2:
            raise Exception # More than 2 weather indicators are not permitted
        w1 = self.wthr_a[0]
        if w1 != ' ':
            # Get the appropriate icon
            if w1 in ['F','M']:
                # Also need the light parameter
                icon = decoder1[w1][light]
            else:
                icon = decoder1[w1]
            icon1 = icon[0]
            alt1 = icon[1]
        else:
            icon1 = None
            alt1 = None
        w2 = self.wthr_a[1]
        if w2 != ' ':
            # Get the appropriate secondary icon
            icon = decoder2[w2]
            icon2 = icon[0]
            alt2 = icon[1]
        else:
            icon2 = None
            alt2 = None
        ret = ''
        h,w = 30,30
        base = './icons'
        if icon1 == None and icon2 == None:
            # No weather data at all
            return ''
        if icon1 != None:
            ret += '<img src="%s/%s" alt="%s" title="%s" height="%d" width="%d">' % (base,icon1,alt1,alt1,h,w)
        if icon2 != None:
            ret += '<img src="%s/%s" alt="%s" title="%s" height="%d" width="%d">' % (base,icon2,alt2,alt2,h,w)
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
        {'A': [(Subject, 'Cause1'), (Subject, 'Cause2')],
         'B': [(Subject, 'Cause3'],
         'Environment': [(Subject, 'Cause4')]}
         
        <Subject> in the above indicates if the cause (which is written in a nice,
        grammatical structure, requires a subject to be used at the beginning of
        the string in order to be grammatical. If False, the string must be used
        as a standalone piece of text, as it is a generality: it does not refer
        to the actions of a particular person, or it is better presented as a
        generality. This is an interpretation of the original data. Previous versions
        of this function retained the exact text used in the reports. These have
        not been opted for because they were difficult for users to read and 
        understand.
         
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
        retdict = {}
        for cause in self.causes:
            if len(cause) == 4:
                vehicle = cause[-1] # A, B, etc.
                causecode = cause[:-1]
            elif len(cause) == 3:
                vehicle = 'Environment'
                causecode = cause
            else:
                # Invalid party
                # Log error, but ignore
                logging.warning('Invalid cause/party for an accident (should be of form 000X or 000 for environmental variables): "%s"' % cause)
            if len(causecode) > 3:
                raise Exception # Cause codes must be 3 digits in length
            elif len(causecode) < 3:
                # Append a leading 0, because the listed cause is only two
                # digits long when it must be threee
                causecode = '0' + causecode
            if vehicle not in retdict.keys():
                retdict[vehicle] = [causecode]
            else:
                retdict[vehicle].append(causecode)
        if decode:
            decodedretdict = {}
            for vehicle in retdict.keys():
                causecodes = retdict[vehicle]
                for causecode in causecodes:
                    # Get the pretty explanations
                    explanation = self.causedecoder[causecode][1] # String
                    if explanation[0] == "'":
                        # It begins with a possessive apostrophe, so add a space
                        explanation = ' %s' % explanation
                    subject = self.causedecoder[causecode][0] # Boolean
                    if vehicle not in decodedretdict.keys():
                        decodedretdict[vehicle] = [(subject, explanation)]
                    else:
                        decodedretdict[vehicle].append((subject, explanation))
            retdict = decodedretdict
        return retdict
    
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
            subject = coderow[6]
            pretty_explanation = coderow[7]
            if subject == 'TRUE':
                subject = True
            elif subject == 'FALSE':
                subject = False
            else:
                raise ValueError
            if pretty_explanation in ['FALSE','',' ']:
                pretty_explanation = None
            retdict[code] = (subject, pretty_explanation)
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
            # Collect crash descriptions and locations into the feature collection
            if Crash.hasLocation:
                feature_collection["features"].append(Crash.__geo_interface__())

        # Write the geojson output
        with open('../data/data.geojson', 'w') as outfile:
            outfile.write(json.dumps(feature_collection))

if __name__ == '__main__':
    # Set paths
    data = '../data/crash-data-2014-partial.csv'
    causes = '../data/decoders/cause-decoder.csv'
    streets = '../data/decoders/NZ-post-street-types.csv'
    
    # Set up error logging
    logger = 'crash_error.log'
    with open(logger,'w'):
        pass # Clear the log from previous runs
    logging.basicConfig(filename=logger,level=logging.DEBUG)
    
    # Run main function
    main(data,causes,streets)


