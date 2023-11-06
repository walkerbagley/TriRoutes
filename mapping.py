#!/opt/homebrew/bin/python3

import folium
from hwnetwork import highways
from highwayRouter import HighwayRouter

class mapper():
    def __init__(self):
        self.hw = highways()
        self.router = HighwayRouter(self.hw)
    
    def mapHighways(self, s, e):
        slat = s[0]
        slon = s[1]
        elat = e[0]
        elon = e[1]

        ways = []
        for way in self.hw.ways.values():
            start = way['startNode']
            if (start['lat'] > slat and start['lat'] < elat) and (start['long'] > slon and start['long'] < elon):
                ways.append(way)
        
        m = folium.Map()
        pts = []
        for way in ways:
            sNode = [way['startNode']['lat'], way['startNode']['long']]
            eNode = [way['endNode']['lat'], way['endNode']['long']]
            pts.append(sNode)
            pts.append(eNode)

            name = way['tags']['ref'] + ', ' if 'ref' in way['tags'] else ''
            length = str(way['length_mi']) + ', '
            dirNS = 'N' if sNode[0] < eNode[0] else 'S'
            dirEW = 'E' if sNode[1] < eNode[1] else 'W'
            folium.PolyLine([sNode, eNode], weight=5, opacity=1, popup=name+length+dirNS+dirEW).add_to(m)

        lats = [i[0] for i in pts]
        lons = [i[1] for i in pts]
        m.fit_bounds([[min(lats), min(lons)], [max(lats), max(lons)]])
        return m

    
    def mapEndWays(self, s, e):
        pts = [s, e]
        endWays = self.hw.getEndWays(s[0], s[1], e[0], e[1])
        startWay = endWays['startWay']
        ssNode = startWay['startNode']
        seNode = startWay['endNode']
        endWay = endWays['endWay']
        esNode = endWay['startNode']
        eeNode = endWay['endNode']
        for i in [ssNode, seNode, esNode, eeNode]:
            pts.append([i['lat'], i['long']])
        
        m = folium.Map()
        name = startWay['tags']['ref'] if 'ref' in startWay['tags'] else ''
        folium.PolyLine([pts[2], pts[3]], weight=5, opacity=1, popup=name).add_to(m)

        name = endWay['tags']['ref'] if 'ref' in endWay['tags'] else ''
        folium.PolyLine([pts[4], pts[5]], weight=5, opacity=1, popup=name).add_to(m)

        folium.Marker(location = s, popup = f'lat: {s[0]}\nlon: {s[1]}').add_to(m)
        folium.Marker(location = e, popup = f'lat: {e[0]}\nlon: {e[1]}').add_to(m)

        lats = [i[0] for i in pts]
        lons = [i[1] for i in pts]
        m.fit_bounds([[min(lats), min(lons)], [max(lats), max(lons)]])
        
        return m

    def mapRoute(self, s, e):
        slat = s[0]
        slon = s[1]
        elat = e[0]
        elon = e[1]

        route = self.router.route(slat, slon, elat, elon)
        dist = route['length_m']
        print(f'Expected Distance {dist:.2f} miles')
        time_m = int(route['time_s'] / 60)
        hrs_str = f'{time_m // 60} hrs ' if time_m // 60 > 0 else ''
        print(f'Expected Time: {hrs_str}{time_m % 60} min')

        m = folium.Map()
        pts = []
        for way in route['path']:
            sNode = [way['startNode']['lat'], way['startNode']['long']]
            eNode = [way['endNode']['lat'], way['endNode']['long']]
            pts.append(sNode)
            pts.append(eNode)

            name = way['tags']['ref'] + ', ' if 'ref' in way['tags'] else ''
            dirNS = 'N' if sNode[0] < eNode[0] else 'S'
            dirEW = 'E' if sNode[1] < eNode[1] else 'W'
            folium.PolyLine([sNode, eNode], weight=5, opacity=1, popup=name+dirNS+dirEW).add_to(m)

        folium.Marker(location = [slat, slon], popup = f'Start, lat: {slat}\nlon: {slon}').add_to(m)
        folium.Marker(location = [elat, elon], popup = f'End, lat: {elat}\nlon: {elon}').add_to(m)

        lats = [i[0] for i in pts]
        lons = [i[1] for i in pts]
        m.fit_bounds([[min(lats), min(lons)], [max(lats), max(lons)]])
        return m