#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
`causedecoder.py`
=================
Builds a Python dictionary holding the values used to decode the causes of
crashes. Import elsewhere with:
`import causedecoder'
And then access the dictionary with:
causedecoder.causedecodedict
'''

import csv

data = "/home/richard/Documents/Projects/national-crash-statistics/data/decoders/cause-decoder.csv"
with open(data, 'rb') as decodecsv:
    decodereader = csv.reader(decodecsv, delimiter=',')
    header = decodereader.next()
    retdict = {}
    for coderow in decodereader:
        code = coderow[3]
        decode = coderow[4]
        retdict[code] = decode


