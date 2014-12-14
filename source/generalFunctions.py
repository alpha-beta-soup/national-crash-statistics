#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
`generalFunctions.py`
=================
Containing general purpose Python functions for small bits of manipulation.
Import it: import generalFunctions

Depends
=======
datetime
'''

import datetime

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

def ordinal(n):
    return str(n)+("th" if 4<=n%100<=20 else {1:"st",2:"nd",3:"rd"}.get(n%10, "th"))

def formatNiceDate(datetime):
    '''Takes a datetime.datetime (e.g. datetime(2014,1,1)) and returns a nice
    string representation (e.g. "1st of January 2014"'''
    return ordinal(datetime.day) + " %s %d" % (datetime.strftime("%B"), datetime.year)

def formatNiceTime(time):
    '''Takes a datetime.time (e.g. time(12,0,0)) and returns a nice string representation
    (e.g. 12:00). Seconds are ignored, and not even considered for rounding.'''
    if time == None:
        return ''
    t = str(time).split(":")
    return "%s:%s" % (t[0],t[1])
    
def formatCrashTime(crashtime, dateobj):
    '''Returns a datetime.time object when given a time as a string from the
    `row`. These are purportedly recorded "in 24-hour time", but are lacking
    leading zeros in the dataset, which is addressed here.'''
    if empty(crashtime):
        return None
    return datetime.datetime.strptime(str(dateobj)+" "+'0'*(4-len(crashtime))+crashtime,'%Y-%m-%d %H%M').time()

def check_offroad(crash_road):
    '''Applies a check for 'Z': the flat for offroad indicator, and corrects
    strings representing these places so that they're a bit nicer to read.'''
    if 'Z' in crash_road.split(' '):
        # The crash was off-road
        # Apply some special formatting to make this read nicely
        # 1. Remove the now-superfluous 'Z'
        crash_road = crash_road.split(' ')
        crash_road.remove('Z')
        # 2. Special exception for the use of 'Beach' at the beginning of some locations
        if crash_road[0] == 'Beach' and len(crash_road) > 1:
            crash_road = crash_road[1:] + [crash_road[0]]
        #. 3. Expand the off-road abbreviations
        patterns = {'CPK': 'Carpark',
                    'BCH': 'Beach',
                    'DWY': 'Driveway',
                    'DWAY': 'Driveway',
                    'FCT': 'Forecourt'}
        for i, r in enumerate(crash_road):
            if r.upper() in patterns.keys():
                crash_road = crash_road[:i] + crash_road[i+1:] + [patterns[r.upper()], '(Off-roadway)']
                break
        # Join it back up to a proper description
        crash_road = ' '.join(crash_road)
    return crash_road

def formatNiceRoad(road, decoder):
    '''Takes a location expressed as a road, or a street or a highway... and
    makes some cosmetic changes. Minor ones are "St" >> "Street" and "Rd" >>> "Road"
    More major ones are taking State Highway linear references and returning something
    understandavble to people.
    CPK = car park
    BCH = beach
    DWY = driveway
    DWAY = driveway'''
    def striplinearref(linref):
        '''Fixes references to State Highways, by removing the linear referencing information'''
        if '/' not in linref:
            # Not a SH
            return linref
        elif '/' in linref:
            try:
                int(linref[0])
            except:
                # Not a SH, just has a slash
                return linref
        # Remaining are State Highways
        if len(linref.split(' ')) > 1 and ' at ' not in linref:
            # There is other location information included
            linref = linref.split(' ')[0] + ' (%s)' % ' '.join(linref.split(' ')[1:]).replace(' SH ',' State Highway ')
        if ' at ' not in linref:
            # SH without an intersection
            SH = linref.split(' ')
            SH = "State Highway %s " % SH[0].split('/')[0] + ' '.join(SH[1:])
        else:
            # SH with an intersection
            linref = linref.split(' at ')
            linref = [linref[0],'at',linref[1]]
            for i, r in enumerate(linref):
                if '/' in r:
                    linref[i] = "State Highway %s" % r.split('/')[0]
            SH = ' '.join(linref)
        return SH

    road = striplinearref(road).split(" ")
    knownAcronyms = ['BP', 'VTNZ'] # Ensure acronyms stay acronyms
    knownErrors = {'Coun': 'Countdown',
                   'C/Down': 'Countdown',
                   'Reserv': 'Reserve',
                   'Stn': 'Station',
                   'Roa': 'Road',
                   'S': 'South',
                   'E': 'East',
                   'W': 'West',
                   'N': 'North'}
    for i, r in enumerate(road):
        if r.upper() in knownAcronyms:
            road[i] = r.upper()
        if r.title() in knownErrors.keys():
            road[i] = knownErrors[r.title()]
        if '/' in r:
            # Split the linear ref: the SH is the side road
            r = striplinearref(r)
            check = r.split('/')
            for j, c in enumerate(check):
                if c in knownErrors:
                    check[j] = knownErrors[c]
                if c in knownAcronyms:
                    check[j] = knownAcronyms[c]
            check = '/'.join(check)
            road[i] = check

    for i, elem in enumerate(road):
        if elem in decoder.keys():
            road[i] = decoder[elem]
    return ' '.join(road)
 
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
