#!/opt/homebrew/python3

import overpy
import json
import threading
import time
# from tqdm import tqdm

def query(start, end, ways, seen, tile):
    tile = int(tile)
    duration = time.time()
    api = overpy.Overpass()
    print(f'\nStarting tile {tile}:')
    print(f'slat ({start[0]:4.2f}) elat ({end[0]:4.2f})')
    print(f'slon ({start[1]:4.2f}) elon ({end[1]:4.2f})')
    boundbox = f'[bbox:{start[0]},{start[1]},{end[0]},{end[1]}]'
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
    
    result = None
    while result == None:
        try:
            result = api.query(boundbox + querybox)
        except:
            time.sleep(5)
    
    ways[tile] = {}

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
        ways[tile][length.id] = wayData
    
    print(f'\nTile {tile} finished in {time.time() - duration:.2f} s')


# query Overpass API for all national highways and interstates excluding Alaska and Hawaii
ways = {}
seen = set()
keepTags = ['highway', 'lanes', 'maxspeed', 'name', 'oneway', 'ref', 'surface']

tilesize = 5.15

startlat = 24.164785
startlong = -127.826991
endlat = 49.726580
endlong = -65.641307

lastlat = startlat
lastlong = startlong
currlat = lastlat
currlong = lastlong
numTiles = 61

threads = []

while currlat < endlat:
    currlat = currlat + tilesize if currlat + tilesize < endlat else endlat
    currlong = startlong
    lastlong = currlong
    while currlong < endlong:
        currlong = currlong + tilesize if currlong + tilesize < endlong else endlong
        
        thread = threading.Thread(target=query, args=([lastlat, lastlong], [currlat, currlong], ways, seen, numTiles))
        thread.start()
        threads.append((numTiles, thread))

        time.sleep(0.5)

        numTiles += 1
        lastlong = currlong
    
    lastlat = currlat
    

fileNum = 13
tiles = []
for t, thread in enumerate(threads):
    thread[1].join()
    tiles.append(thread[0])

    # dump all transformed road structures into massive json file for future use
    # no excessive querying here
    if t > 0 and t % 5 == 0:
        print(f'\nWriting file: road_tiles_{fileNum}.json')
        temp = {k: v for k, v in ways.items() if k in tiles}
        ways_json = json.dumps(temp, indent=4)
        with open(f'road_tiles_{fileNum}.json', 'w') as file:
            file.write(ways_json)
        for tile in tiles:
            del ways[tile]
        tiles = []
        fileNum += 1

print(f'\nWriting file: road_tiles_{fileNum}.json')
temp = {k: v for k, v in ways.items() if k in tiles}
ways_json = json.dumps(temp, indent=4)
with open(f'road_tiles_{fileNum}.json', 'w') as file:
    file.write(ways_json)