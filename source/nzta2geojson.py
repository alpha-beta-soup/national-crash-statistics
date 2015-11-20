#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
`nzta2geojson.py`
=================
A Python script to read the New Zealand Transport Agency crash data into a
GeoJSON, to be styled and filtered for presentation in a Leaflet map.
'''

import json
import csv
import string
import generalFunctions as genFunc
import re
import logging
import datetime

import pytz
import pyproj
import geojson
import ephem
import mx.DateTime

import moon


class nztacrash:
    '''A crash recorded by NZTA'''
    def __init__(self, row, causedecoder, streetdecoder, holidays):
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

        # Official Holiday Periods
        self.holidays = holidays

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
        self.crash_datetime = self.get_crash_datetime()
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
            self.chathams = True
        else:
            self.chathams = False

        self.proj = pyproj.Proj(init='epsg:2193') # NZTM projection

        if self.hasLocation == True:
            self.lon, self.lat = self.proj(self.easting, self.northing, inverse=True) # Lon/lat
            if self.chathams == True:
                self.lon * -1
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
        self.daytime = self.get_daylight()

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

        # Official holiday period information
        self.holiday = self.get_holiday()
        self.holiday_name = self.get_holiday_period()

        # Party involvement
        self.pedestrian = self.get_mode_involvement(['E','K','H']) # Pedestrian, skater, wheeled pedestrian
        self.cyclist = self.get_mode_involvement(['S']) # Cyclist
        self.motorcyclist = self.get_mode_involvement(['M','P']) # Motorcyclist, moped
        self.taxi = self.get_mode_involvement(['X']) # Taxi/taxi van
        self.truck = self.get_mode_involvement(['T']) # Truck
        self.car = self.get_mode_involvement(['C','V','4']) # Car, van/ute, SUV

        # Roles and factors
        self.tourist = self.get_factor_involvement(['404','731'])
        self.alcohol = self.get_factor_involvement(['101','102','103','104','105'])
        self.drugs = self.get_factor_involvement(['107','108','109'])
        self.cellphone = self.get_factor_involvement(['359'])
        self.fatigue = self.get_factor_involvement(['410','411','412','413','414','415'])
        self.dickhead = self.get_factor_involvement(['430','431','432','433','434','510','511','512','513','514','515','516','517'])
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
        if self.crash_date != None:
            return self.crash_date.strftime("%A")
        else:
            return None

    def get_crash_datetime(self, as_utc=False):
        '''Returns a datetime.datetime object expressing the date and time of the
        crash, if the crash has both of those attributes. If it does not, this
        returns None.

        Note, the original data has time in Pacific/Auckland timezone, which
        means at daylight savings transition periods, the UTC time is
        ambiguous for one hour. UTC time can be returned with the as_utc flag.
        '''
        if self.crash_date != None and self.crash_time != None:
            local_dt = datetime.datetime.combine(self.crash_date, self.crash_time)
        else:
            return None
        if not as_utc:
            return local_dt
        else:
            return pytz.timezone('Pacific/Auckland').localize(local_dt, is_dst=True).astimezone(pytz.utc)

    def get_daylight(self, twilight='civil', elev=0, temp=15.0, pressure=1010):
        '''Returns boolean indicating whether the accident occurred at a time
        when there was sunlight.'''
        assert twilight in ['civil', 'nautical', 'astronomical']
        if self.hasLocation is False or self.crash_datetime is None:
            return
        twilights = {
            'civil': -6,
            'nautical': -12,
            'astronomical': -18
        }
        observer = ephem.Observer()
        observer.date = self.get_crash_datetime(as_utc=True).strftime(
            '%Y-%m-%d %H:%M:%S'
        )
        observer.lon = str(self.lon)
        observer.lat = str(self.lat)
        observer.elev = elev
        observer.pressure = pressure
        observer.temp = temp
        observer.horizon = str(twilights[twilight])

        next_sunrise = datetime.datetime.strptime(str(
            observer.next_rising(ephem.Sun(), use_center=True)
        ), '%Y/%m/%d %H:%M:%S').replace(tzinfo=pytz.UTC)
        next_sunset = datetime.datetime.strptime(str(
            observer.next_setting(ephem.Sun(), use_center=True)
        ), '%Y/%m/%d %H:%M:%S').replace(tzinfo=pytz.UTC)

        return next_sunset < next_sunrise

    def get_moon(self):
        '''Returns a Moon when the accident occurred (see moon.py for
        properties and methods)'''
        if self.crash_datetime is None:
            return
        return moon.MoonPhase(mx.DateTime.DateTimeFrom(self.crash_datetime))

    def get_holiday(self):
        '''Returns a Boolean indicating whether the accident involved a severe
        injury AND occured during an official holiday period.'''
        if self.crash_datetime == None:
            return False
        if self.worst_severe == False and self.worst_fatal == False:
            return False
        for hp in self.holidays.keys():
            start, end = self.holidays[hp][0], self.holidays[hp][1]
            if start <= self.crash_datetime <= end:
                return True
        return False

    def get_holiday_period(self):
        '''If self.get_holiday is True, then this function returns the name of
        the holiday period in which it occurred, otherwise it returns an empty
        string'''
        if self.holiday == False or self.crash_datetime == None:
            return ''
        for hp in self.holidays.keys():
            start, end = self.holidays[hp][0], self.holidays[hp][1]
            if start <= self.crash_datetime <= end:
                return hp

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
            return 1
        if self.secondaryvehicles != None:
            for m in self.secondaryvehicles:
                if m in mode_list:
                    return 1
        return 0

    def get_factor_involvement(self, factor_list):
        '''Returns a boolean indicating whether any of the 3-digit factor codes
        listed in the factor_list parameter (list of strings) have been cited to
        explain the accident'''
        for c in self.causes:
            if len(c) == 4:
                c = c[0:3]
            if c in factor_list:
                return 1
            else:
                pass
        return 0

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

    def get_injured_child(self,childAge=15):
        '''
        The CAS record has a "PEDage" property, defined as:
            Age of any pedestrian injured. If more than one pedestrian is
            injured, the age of the youngest pedestrian below 20 years old is
            shown; otherwise this shows the age of the oldest pedestrian.
        This is kinda tricky to deal with, because it is not either the "youngest"
        or the "oldest" that is recorded, and it is only recorded for pedestrians
        (and cyclists in another property, "CYCage").

        Thus, this method returns a Boolean indicating whether a child* has
        been injured, on foot or on a bike. Where the maximum age of a "child"
        is given by the `childAge` parameter.
        '''
        if self.pers_age1 != None and self.pers_age1 <= childAge:
            # A child pedestrian was injred
            return True
        elif self.pers_age2 != None and self.pers_age2 <= childAge:
            # A child cyclist was injured
            return True
        else:
            return False

    def get_injured_child_age(self):
        '''
        See method self.get_injured_child().
        This method returns the age(s) of the injured child(ren).
        '''
        if self.get_injured_child() == True:
            # Either (or both) a child walking or (and) a child on a bike were
            # injured.
            if self.pers_age1 != None and self.pers_age2 != None:
                # BOTH
                youngest = min(self.pers_age1,self.pers_age2)
            elif self.pers_age1 != None:
                youngest = self.pers_age1
            elif self.pers_age2 != None:
                youngest = self.pers_age2
            else:
                raise Exception
            return int(youngest)
        else:
            return None

    def get_injured_child_icon(self):
        '''
        See method self.get_injured_child().
        This method returns the path to an icon indicating that the crash
        involved a child, with the hover text including their age.
        '''
        if self.get_injured_child() == True:
            base = './icons/other'
            icon = 'children.png'
            age = self.get_injured_child_age()
            if age == 1:
                title = 'A one year old infant was harmed'
            elif age < 13:
                title = 'A %s year old child was harmed' % age
            elif age >= 13 and age < 20:
                title = 'A %s year old teenager was harmed' % age
            else:
                # Nothing else prepared
                raise Exception
            return '<img src="%s/%s" title="%s"> ' % (base,icon,title)
        else:
            # Return an empty string
            return ''

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
                   '4': ['SUV-icon.svg', '4X4 or SUV'],
                   'T': ['Transport-Truck-2-icon.svg', 'Truck'],
                   'M': ['motorcycle-icon.svg', 'Motorcycle'],
                   'P': ['moped-icon.svg', 'Moped'],
                   'S': ['bicycle-icon.svg', 'Bicycle'],
                   'O': [other, 'Miscellaneous Vehicle'],
                   'U': [other, 'Miscellaneous Vehicle'],
                   'E': ['pedestrian-icon.svg', 'Pedestrian'],
                   'K': [other, 'Skateboard, inline skater, etc.'],
                   'Q': ['equestrian-icon.svg', 'equestrian'],
                   'H': ['wheelchair-icon.svg', 'Wheeled Pedestrian']}
        ret = ''
        for v in vehicles.keys():
            icon = decoder[v][0]
            alt = decoder[v][1]
            title = alt
            multiplier = vehicles[v]
            ret += '<img src="%s/%s" title="%s"> ' % (base,icon,title) * multiplier
        return ret

    def get_worst_injury_text(self):
        if self.worst_fatal:
            return 'f' # Fatal
        elif self.worst_severe:
            return 's' # Severe
        elif self.worst_minor:
            return 'm' # minor
        elif self.worst_none:
            return 'n' # no injury
        else:
            return '' # no data

    def get_injury_icons(self):
        if self.injuries_none:
            return ''
        base = './icons/injuries'
        icons = {'fatal': 'RedMan2.svg',
                 'severe': 'OrangeMan2.svg',
                 'minor': 'YellowMan2.svg'}
        ret = ''
        def add_img(alt,title,icon,multiplier):
            return '<img src="%s/%s" title="%s"> ' % (base,icon,title) * multiplier
        ret += add_img('Fatality','Fatality',icons['fatal'],self.crash_fatal_cnt)
        ret += add_img('Severe injury','Severe injury',icons['severe'],self.crash_sev_cnt)
        ret += add_img('Minor injury','Minor injury',icons['minor'],self.crash_min_cnt)
        return ret

    def speedingIcon(self):
        '''If speeding was a factor, returns the HTML <img> tag for the speeding icon,
        else returns an empty string.'''
        if self.speeding:
            base = './icons/actions'
            icon = 'speeding.svg'
            alt = 'Speeding'
            title = alt
            return '<img src="%s/%s" title="%s">' % (base,icon,title)
        else:
            return ''

    def trafficControlIcon(self):
        if self.traf_ctrl not in ['T','S','G','P']:
            if self.traf_ctrl != None:
                if len(self.traf_ctrl) > 1:
                    # Only one type of control is anticipated
                    raise Exception
            return '' # Empty string
        decoder = {'T': ['Traffic signals', 'traffic-light.png'],
            'S': ['Stop sign', 'stop-sign.png'],
            'G': ['Give way sign', 'give-way.png'],
            'P': ['School patrol', 'school-patrol.png']}
        if self.traf_ctrl not in decoder.keys():
            raise Exception
        base = './icons/controls'
        title = decoder[self.traf_ctrl][0]
        icon = '%s/%s' % (base,decoder[self.traf_ctrl][1])
        return '<img src="%s" title="%s">' % (icon,title)

    def speedLimitIcon(self):
        if self.spd_lim in ['','U']:
            # No information, or unknown
            # Do not return an icon
            return ''
        elif self.spd_lim == 'LSZ':
            # Limited speed zone
            # Could not be set since 2003, and was progressively replaced until 2009
            # It is now illegal
            alt = 'Limited speed zone'
        else:
            alt = '%skm/h speed limit' % self.spd_lim
        base = './icons/speed-limits'
        title = alt
        icon = '%s/limit_%s.svg' % (base,self.spd_lim)
        return '<img src="%s" title="%s">' % (icon,title)

    def curveIcon(self):
        if self.road_curve in [None,'R']:
            return '' # Empty string for NULL or straight
        decoder = {'E': ['Road with a slight curve', 'easy-curve-icon_v2.png'],
            'M': ['Road with a moderate curve', 'moderate-curve-icon_v2.png'],
            'S': ['Road with a severe bend', 'severe-curve-icon_v2.png']}
        if self.road_curve not in decoder.keys():
            raise Exception
        base = './icons/curves'
        title = decoder[self.road_curve][0]
        icon = '%s/%s' % (base,decoder[self.road_curve][1])
        return '<img src="%s" title="%s">' % (icon,title)

    def intersectionIcon(self):
        if self.junc_type == None:
            return ''
        decoder = {'D': ['driveway-icon_v2.png', 'Driveway'],
                   'R': ['roundabout-icon_v2.png', 'Roundabout'],
                   'X': ['crossroads-icon_v2.png', 'Crossroads'],
                   'T': ['t-intersection-icon_v2.png', 'T-intersection'],
                   'Y': ['y-intersection_v2.png', 'Y-intersection'],
                   'M': ['multi-leg-icon_v2.png', 'Multi-leg instersection']}
        try:
            icon = decoder[self.junc_type][0]
            title = decoder[self.junc_type][1]
        except KeyError:
            return ''
        base = './icons/junctions'
        icon = '%s/%s' % (base, icon)
        return '<img src="%s" title="%s">' % (icon,title)

    def __streetview__(self, w=300, h=200, fov=120, pitch=-15, alt='Click to go to Google Streetview', title=None):
        '''Creates the Google Streetview API request
        fov : Field of view, max 120
        pitch : Up or down angle relative to the Streetview vehicle'''
        if self.hasLocation == False:
            return None
        # Params for the Streetview API (not styling)
        h = 200
        w = 300
        fov = 120 # Field of view, max 120
        pitch = -15 # Up or down angle relative to the Streetview vehicle
        link = 'http://maps.google.com/?cbll=%s,%s&cbp=12,20.09,,0,5&layer=c' % (self.lon,self.lat)
        alt = 'Click to go to Google Streetview'
        if title is None:
            title = alt
        return '<a href="{link}" title="{title}" target="_blank"><img src="https://maps.googleapis.com/maps/api/streetview?size={w}x{h}&location={lat},{lon}&pitch={pitch}&key={key}"></a>'.format(
            link=link,
            title=title,
            w=w,
            h=h,
            lat=self.lat,
            lon=self.lon,
            pitch=pitch,
            key=self.api
        )

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
           'U': 'driver of the <strong>vehicle</strong> of unknown type',
           'E': '<strong>pedestrian</strong>',
           'K': '<strong>skater</strong>',
           'Q': '<strong>equestrian</strong>',
           'H': '<strong>wheeled pedestrian</strong>'}

        # Keep track of the numbers of each mode we see, so the text can be formed
        # using ordinal text ('the first car', etc.)
        modes, mode_counter = decoder.keys(), {}
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
        '''geojson
        Returns a geojson object representing the point.
        '''
        if self.hasLocation is False:
            # Can't add it to the map if it does not have a location
            return None

        return {
            'type': 'Feature',
            'properties': {
                't': self.tla_name, # Name of Territorial Local Authority
                'd': self.crash_dow, # Crash daw of the week
                'dt': genFunc.formatNiceDate(self.crash_date), # The date, nicely formatted
                'ti': genFunc.formatNiceTime(self.crash_time), # The time HH:MM
                's': self.__streetview__(), # The Streetview img container and call
                'r': genFunc.formatNiceRoad(self.get_crashroad()), # The road, nicely formatted
                'e': self.weatherIcon() + self.speedLimitIcon() + self.intersectionIcon() + self.trafficControlIcon() + self.curveIcon() + self.get_injured_child_icon() + self.moonIcon(), # The environment icon imgs
                'v': self.__vehicle_icons__(), # Vehicle icon imgs
                'i': self.get_injury_icons(), # Injury icon imgs
                'c': self.make_causes(), # Causes (formatted string)
                'h': self.holiday_name, # Name of holiday period, if the crash was injurious and occured during one
                'cy': self.cyclist, # Cyclist Boolean
                'pd': self.pedestrian, # Pedestrian Boolean
                'mc': self.motorcyclist, # Motorcyclist Boolean
                'tx': self.taxi, # Taxi Boolean
                'tr': self.truck, # Truck Boolean
                'ca': self.car, # Car, van, ute, SUV
                'to': self.tourist, # Tousit Boolean
                'al': self.alcohol, # Alcohol Boolean
                'dr': self.drugs, # Drugs Boolean
                'cp': self.cellphone, # Cellphone Boolean
                'fg': self.fatigue, # Faitgue Boolean
                'dd': self.dickhead, # Dangerous driving Boolean
                'sp': self.speeding, # Speeding Boolean
                'ch': self.get_injured_child(), # Child pedestrian/cyclist Boolean
                'ij': self.get_worst_injury_text(), # f,s,m,n >> worst injury as text
                'dy': self.daytime # Daytime
            },
            'geometry': {
                'type': 'Point',
                'coordinates': (self.lon, self.lat)
            }
        }

    def decodeMovement(self):
        '''Decodes self.mvmt into a human-readable form.
        Movement applies to left and right hand bends, curves, or turns.'''
        decoder = {'A': ('Overtaking and lane change', {'A': 'Pulling out or changing lane to right', 'B': 'Head on', 'C': 'Cutting in or changing lane to left', 'D': 'Lost control (overtaking vehicle)', 'E': 'Side road', 'F': 'Lost control (overtaken vehicle)', 'G': 'Weaving in heavy traffic', 'O': 'Other'}),
                 'B': ('Head on',{'A': 'On straight', 'B': 'Cutting corner', 'C': 'Swinging wide', 'D': 'Both cutting corner and swining wide, or unknown', 'E': 'Lost control on straight', 'F': 'Lost control on curve', 'O': 'Other'}),
                 'C': ('Lost control or off road (straight roads)',{'A': 'Out of control on roadway', 'B': 'Off roadway to left', 'C': 'Off roadway to right', 'O': 'Other'}),
                 'D': ('Cornering',{'A': 'Lost control turning right', 'B': 'Lost control turning left', 'C':'Missed intersection or end of road', 'O': 'Other'}),
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
                               'K': 'skateboard/in-line skater/etc.',
                               'O': 'other/unknown',
                               'U': 'other/unknown',
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

    def moonIcon(self, night_only=True):
        '''Returns an SVG icon representing the phase of the moon when the
        accident occurred. By default returns empty string if accident occured
        during daylight.'''
        if (night_only and not self.daytime) and self.crash_datetime is not None:
            moon = self.get_moon()
            base = './icons/moon'
            return '<img src="{base}/m{phase}.svg" title="{title}">'.format(
                base=base,
                phase=int(moon.phase * 26 + 0.5),
                title=moon.phase_text + ' moon'
            )
        else:
            return ''

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
                    'S': ['05-strong-wind-weaher-icon.png','Strong Winds'],
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
        hspace = 5
        base = './icons'
        title1 = alt1
        title2 = alt2
        if icon1 == None and icon2 == None:
            # No weather data at all
            return ''
        if icon1 != None:
            ret += '<img src="%s/%s" title="%s">' % (base,icon1,title1)
        if icon2 != None:
            ret += '<img src="%s/%s" title="%s">' % (base,icon2,title2)
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
                    if causecode == '999':
                        # This is not even recorded in the NZTA's documentation...
                        continue
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

def get_official_holiday_periods():
    '''
    See: http://www.transport.govt.nz/research/roadtoll/#holiday
    (#Holiday road toll information)

    Non-injury chrases are not considered when reporting the road toll, so the
    filter on this should pre-exclude non-injury crashes.
    '''
    hols = {'Christmas/New Year 2014-15': (datetime.datetime(2014,12,24,16), datetime.datetime(2015,1,5,6)),
        'Labour Weekend 2014': (datetime.datetime(2014,10,24,16), datetime.datetime(2014,10,28,6))}
    return hols


def get_crashes(file, causes, streets, holidays, global_start, global_end):
    '''
    Generates 'valid' crash records from a crash CSV
    '''
    causedecoder = causeDecoderCSV(causes) # Decode the coded values
    streetdecoder = streetDecoderCSV(streets)
    with open(file, 'rb') as crashcsv:
        crashreader = csv.reader(crashcsv, delimiter=',')
        header = crashreader.next()
        for crash in crashreader:
            Crash = nztacrash(crash, causedecoder, streetdecoder, holidays)
            # Only add features with a location
            # And that are within the acceptable date range
            if Crash.crash_date == None or Crash.hasLocation == False:
                continue
            if not (global_start <= Crash.crash_date <= global_end):
                continue
            yield Crash

def main(data, causes, streets, holidays, global_start, global_end):
    feature_collection = {"type": "FeatureCollection","features": []}
    with open('../data/data.geojson', 'w') as outfile:
        for d in data: # For each CSV of source data
            for crash in get_crashes(d, causes, streets, holidays, global_start, global_end):
                feature_collection["features"].append(crash.__geo_interface__())
        # Write the geojson output
        outfile.write(json.dumps(feature_collection, separators=(',',':')))
        outfile.close()

if __name__ == '__main__':
    # TODO specify paths with os.path
    global_start = datetime.date(2015,1,1)
    global_end = datetime.date(2015,3,31)
    # Set paths
    data = ['../data/crash-data-{i}.csv'.format(i=i) if i < 2015 else '../data/crash-data-{i}-partial.csv'.format(i=i) for i in xrange(global_start.year, global_end.year + 1)]
    causes = '../data/decoders/cause-decoder.csv'
    streets = '../data/decoders/NZ-post-street-types.csv'
    holidays = get_official_holiday_periods()

    # Set up error logging
    logger = 'crash_error.log'
    with open(logger, 'w'):
        pass # Clear the log from previous runs

    logging.basicConfig(filename=logger, level=logging.DEBUG)

    # Run main function
    main(data, causes, streets, holidays, global_start, global_end)
