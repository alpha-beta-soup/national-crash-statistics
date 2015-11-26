import os
import csv
import json

HERE = os.path.dirname(os.path.realpath(__file__))

def csv2json(csv_file, key, properties=None, outfile=os.path.join(HERE, 'cause-decoder.json')):
    '''
    csv_file : path to a csv file
    key : column name of the key for the output json
    properties : list of names for the properties, if None, everything is a property
    '''
    jsondata = {}
    with open(csv_file, 'rb') as csvfile:
        reader = csv.DictReader(open(csv_file))
        for row in reader:
            if properties is None:
                properties = row.keys().pop(key)
            jsonkey = row[key]
            jsonproperties = {i: row[i] for i in properties}
            jsondata[jsonkey] = jsonproperties
    with open(outfile, 'w') as outjson:
        json.dump(jsondata, outjson, ensure_ascii=False)

if __name__ == '__main__':
    csv2json(os.path.join(HERE, 'cause-decoder.csv'), 'code', ['Category', 'Requires Subject', 'Pretty'])
