#!/opt/homebrew/python3

import overpy
import json
# from tqdm import tqdm

# query Overpass API for all national highways and interstates excluding Alaska and Hawaii
api = overpy.Overpass()
ways = {}
seen = set()
keepTags = ['highway', 'lanes', 'maxspeed', 'name', 'oneway', 'ref', 'surface']

startlat = 24.164785
startlong = -127.826991
endlat = 49.726580
endlong = -65.641307
# endlat = 37.726580
# endlong = -115.641307

tilesize = 5.0

lastlat = startlat
lastlong = startlong
currlat = startlat
currlong = startlong
numTiles = 0

while currlat < endlat:
    currlat = currlat + tilesize if currlat + tilesize < endlat else endlat
    currlong = startlong
    lastlong = currlong
    while currlong < endlong:
        currlong = currlong + tilesize if currlong + tilesize < endlong else endlong
        print(f'\nStarting tile {numTiles}:')
        print(f'slat ({lastlat}) elat ({currlat})')
        print(f'slon ({lastlong}) elon ({currlong})')
        boundbox = f'[bbox:{lastlat},{lastlong},{currlat},{currlong}]'
        querybox = """
            [out:json][timeout:600];
            (
                rel['route'='road']['network'='US:I'](if:(t['is_in:state'] != 'AK') && (t['is_in:state'] != 'HI'));
                rel['route'='road']['network'='US:US'](if:(t['is_in:state'] != 'AK') && (t['is_in:state'] != 'HI'));
            );

            way(r)->.w;
            way(r);
            convert length 'length'=length(),::id=id(),'type'='length';
            out;
            .w out;
            node(w.w);
            out;
            convert road ::=::,::geom=geom(),'length'=length(),::id=id(),'type'=type();
            """
        result = api.query(boundbox + querybox)

        # iterate through each length to generate a road dictionary
        for length in result._lengths.values():

            if length.id in seen:
                continue

            seen.add(length.id)

            # get the corresponding way for a particular id and eliminate unnecessary tag elements
            way = result.get_way(length.id)
            tags = {tag: val for tag, val in way.tags.items() if tag in keepTags}

            # do mileage and time calculations based on the road length and max speed
            length_miles = float(length.length) * 0.000621371
            speed = 45
            if 'maxspeed' in tags:
                try:
                    speed = int(tags['maxspeed'].split(' ')[0])
                except:
                    speed = 45
            time_seconds = (length_miles / speed) * 3600

            # get start and end node for each road and create new dictionaries for the endpoints
            start = way.nodes[0]
            end = way.nodes[-1]
            startNode = {'id': start.id, 'lat': float(start.lat), 'long': float(start.lon)}
            endNode = {'id': end.id, 'lat': float(end.lat), 'long': float(end.lon)}

            # create road dictionary and add to ways list
            wayData = {'id': length.id, 'length_mi': length_miles, 'time_s': time_seconds, 'tags': tags, 'startNode': startNode, 'endNode': endNode}
            ways[length.id] = wayData

        # remove duplicate ways
        # print('\nRemoving duplicate ways\n')
        # newWays = set()
        # for w in ways:
        #     if w in newWays:
        #         continue
        #     newWays.add(w)
        # ways = {i: ways[i] for i in newWays}

        lastlong = currlong
        numTiles += 1

    lastlat = currlat

# dump all transformed road structures into massive json file for future use
# no excessive querying here
ways_json = json.dumps(ways, indent=4)
with open("highway_network.json", "w") as file:
    file.write(ways_json)