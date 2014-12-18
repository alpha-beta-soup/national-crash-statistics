import fiona
from shapely.geometry import shape, Point

# TODO change this function so it reads in a CSV and determines the region
# ONCE and for all, rather than on the fly. This takes ages.

def get_region(nztacrash,shapefile="../data/shapefiles/nz-rc-2012.shp"):
    '''
    Returns a string representation of the region the nztacrash object occurred in,
    according to the definition of the shapefile parameter (requires a field 'NAME')
    '''
    replace = ['Region','Country']
    fc = fiona.open(shapefile)
    pt = Point(nztacrash.lat,nztacrash.lon)
    for f in fc:
        geom = shape(f['geometry'])
        if geom.contains(pt):
            # Then we have found the region the crash occurred in
            fc.close()
            rc = f['properties']['NAME']
            for rep in replace:
                rc = rc.replace(rep,'')
            return rc.strip()
    # If no match, no region
    fc.close()
    return None

if __name__ == '__main__':
    fc = fiona.open("../data/shapefiles/nz-rc-2012.shp")

    # Perform testing
    wellington = {'loc':Point(174.774590,-41.286165),'expect':'Wellington Region'}
    auckland = {'loc':Point(174.763603,-36.853361),'expect':'Auckland Region'}
    christchurch = {'loc':Point(172.636547,-43.530868),'expect':'Canterbury Region'}
    whiteisland = {'loc':Point(177.183514,-37.520880),'expect':'Bay of Plenty Region'}
    chatham = {'loc':Point(-176.560373,-43.951542),'expect':'Chatham Islands County'}
    nowhere = {'loc':Point(-179.724436,-31.041451),'expect':None}
    tests = [wellington,auckland,christchurch,whiteisland,chatham,nowhere]
    
    def run(fc,place):
        for f in fc:
            geom = shape(f['geometry'])
            if geom.contains(place['loc']):
                if f['properties']['NAME'] != place['expect']:
                    print f['properties']['NAME'], place['expect']
                    raise Exception
                return None
        return None
    
    for place in tests:
        run(fc,place)
    print("Test passed successfully")
