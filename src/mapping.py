#!/opt/homebrew/bin/python3

import folium
import time
from src.hwnetwork import network
from src.highwayRouter import HighwayRouter

# this mapper class contains all necessary mapping functions in order to make visualizing this project very easy
class mapper():

    # create a highway network and a router
    def __init__(self, threshold=5000):
        self.hw = network()
        self.router = HighwayRouter(self.hw, self, threshold)

    # DEPRECATED
    # this maps all highways within a specific bounding box where s and e are pairs of coordinates
    def mapHighways(self, s, e):
        slat = s[0]
        slon = s[1]
        elat = e[0]
        elon = e[1]

        # get all ways in our network where the start is contained in our bounding box
        ways = []
        for way in self.hw.ways.values():
            start = way.start
            if (start['lat'] > slat and start['lat'] < elat) and (start['long'] > slon and start['long'] < elon):
                ways.append(way)
        
        # create the map
        m = folium.Map()
        pts = []

        # iterate over every road we'd like to map
        for way in ways:
            sNode = [way['startNode']['lat'], way['startNode']['long']]
            eNode = [way['endNode']['lat'], way['endNode']['long']]

            # append each set of coordinates to pts so we can appropriately size the map later
            pts.append(sNode)
            pts.append(eNode)

            # add a line for each way and appropriate identifying information to make it easier to debug
            folium.PolyLine([sNode, eNode], weight=5, opacity=1, popup=self.popupInfo(way)).add_to(m)

        # size the map appropriately
        lats = [i[0] for i in pts]
        lons = [i[1] for i in pts]
        m.fit_bounds([[min(lats), min(lons)], [max(lats), max(lons)]])
        return m

    
    # this maps the two end ways returned by the router for a specific route with starting coordinates s and ending coordinates e
    def mapEndWays(self, s, e):
        # use the same pts system as before
        pts = [s, e]

        # get the end ways
        endWays = self.hw.tree.getEndWays(s, e)
        startWay = endWays['start']
        ssNode = startWay.start
        seNode = startWay.end
        endWay = endWays['end']
        esNode = endWay.start
        eeNode = endWay.end

        # append coordinates
        for i in [ssNode, seNode, esNode, eeNode]:
            pts.append([i.lat, i.lon])
        
        # create map and add starting and ending ways to it
        m = folium.Map()
        folium.PolyLine([pts[2], pts[3]], weight=5, opacity=1, popup=self.popupInfo(startWay)).add_to(m)
        folium.PolyLine([pts[4], pts[5]], weight=5, opacity=1, popup=self.popupInfo(endWay)).add_to(m)

        # add pins for the start and end coordinates to visualize the distance to the start/end ways
        folium.Marker(location = s, popup = f'lat: {s[0]}\nlon: {s[1]}').add_to(m)
        folium.Marker(location = e, popup = f'lat: {e[0]}\nlon: {e[1]}').add_to(m)

        # resize map appropriately
        lats = [i[0] for i in pts]
        lons = [i[1] for i in pts]
        m.fit_bounds([[min(lats), min(lons)], [max(lats), max(lons)]])
        return m

    def mapEndWaySearch(self, s, e, f = 'start'):
        way, _, boxes, ways = self.hw.tree.getClosestWayMap(s, e, f)


        m = folium.Map()
        folium.PolyLine([[way.start.lat, way.start.lon], [way.end.lat, way.end.lon]], weight=5, opacity=1, popup=self.popupInfo(way)).add_to(m)

        mark = s if f == 'start' else e
        folium.Marker(location=mark).add_to(m)

        for i, box in enumerate(boxes):
            sw = [box.center[0] - box.height / 2, box.center[1] - box.width / 2]
            se = [box.center[0] - box.height / 2, box.center[1] + box.width / 2]
            ne = [box.center[0] + box.height / 2, box.center[1] + box.width / 2]
            nw = [box.center[0] + box.height / 2, box.center[1] - box.width / 2]
            folium.Polygon([sw, se, ne, nw], opacity=0.3, popup=f'{i}').add_to(m)
        
        for i, w in enumerate(ways):
            folium.PolyLine([[w.start.lat, w.start.lon], [w.end.lat, w.end.lon]], weight=5, opacity=1, popup=f'{i}, ' + self.popupInfo(w)).add_to(m)
        
        return m

    # this function returns a map of the route from a pair of starting coordinates s and ending coordinates e
    def mapRoute(self, s, e):
        slat = s[0]
        slon = s[1]
        elat = e[0]
        elon = e[1]

        # get the route from the router
        duration = time.time()
        route = self.router.route(slat, slon, elat, elon)
        duration = time.time() - duration

        # print out the distance of the route and time in hours and minutes
        print(f'Search Time: {duration:.5f} s\n')
        dist = route['length_m']
        print(f'Expected Distance {dist:.2f} miles')
        time_m = int(route['time_s'] / 60)
        hrs_str = f'{time_m // 60} hrs ' if time_m // 60 > 0 else ''
        print(f'Expected Time: {hrs_str}{time_m % 60} min')

        # create the map
        m = folium.Map()
        pts = []

        # iterate over each way in the map, this might require querying the specific ways in the future in order to get the remaining points for more accurate lines on the map
        for way in route['path']:
            sNode = [way.start.lat, way.start.lon]
            eNode = [way.end.lat, way.end.lon]
            pts.append(sNode)
            pts.append(eNode)

            # add a line for the way onto the map with identifying info
            folium.PolyLine([sNode, eNode], weight=5, opacity=1, popup=self.popupInfo(way)).add_to(m)

        # add start/end pins
        pts.append([slat, slon])
        pts.append([elat, elon])
        folium.Marker(location = [slat, slon], popup = f'Start, lat: {slat}\nlon: {slon}').add_to(m)
        folium.Marker(location = [elat, elon], popup = f'End, lat: {elat}\nlon: {elon}').add_to(m)

        # resize map
        lats = [i[0] for i in pts]
        lons = [i[1] for i in pts]
        m.fit_bounds([[min(lats), min(lons)], [max(lats), max(lons)]])
        return m
    

    # this function returns a map for a step of the A* algorithm
    def mapAstarStep(self, route, adjacent):

        # create map
        pts = []
        m = folium.Map()

        # iterate over all ways in the current path
        for way in route['path']:
            # set a different color for the last way since this is the one we are looking at
            color = 'blue'
            if way.id == route['path'][-1].id:
                color = 'pink'
            
            sNode = [way.start.lat, way.start.lon]
            eNode = [way.end.lat, way.end.lon]
            pts.append(sNode)
            pts.append(eNode)

            folium.PolyLine([sNode, eNode], weight=5, opacity=1, color=color, popup=self.popupInfo(way)).add_to(m)

        # iterate over all connecting ways and use a new color since they are being added to the priority queue
        for way in adjacent:
            sNode = [way.start.lat, way.start.lon]
            eNode = [way.end.lat, way.end.lon]
            pts.append(sNode)
            pts.append(eNode)

            folium.PolyLine([sNode, eNode], weight=5, opacity=1, color='red', popup=self.popupInfo(way)).add_to(m)

        # resize map
        lats = [i[0] for i in pts]
        lons = [i[1] for i in pts]
        m.fit_bounds([[min(lats), min(lons)], [max(lats), max(lons)]])
        return m


    # this function returns a string with the required identifying information
    def popupInfo(self, way):
        # grab the ref of the way
        name = way.tags['ref'] + ', ' if 'ref' in way.tags else ''

        # get the way's ID
        i = str(way.id)

        sNode = way.start
        eNode = way.end

        # get direction of the way so we can tell which way we are supposed to be driving
        dirNS = ', N' if sNode.lat < eNode.lat else ', S'
        dirEW = 'E' if sNode.lon < eNode.lon else 'W'

        # get length
        length = ', ' + str(way.length)
        return name + i + dirNS + dirEW + length