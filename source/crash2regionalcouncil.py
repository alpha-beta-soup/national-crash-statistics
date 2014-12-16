import fiona
from shapely.geometry import shape, Point

# TODO: get this to accept a CSV input, and add a column to the CSV with the RC
# Then it only needs to be run once when the CSV is read

# Or test it in the main code. If it has no serious overhead, just run it each time.

fc = fiona.open("nz-regional-councils-2012-yearly-pattern.shp")
for f in fc:
    print f['type'],
    print f['id'],
    print f['properties']
    
    # Make a shapely object from the dict
    geom = shape(f['geometry'])
    point = Point(171.8,-34.2) # longitude, latitude
    if geom.contains(point):
        print "Found it!"
    print geom.bounds
