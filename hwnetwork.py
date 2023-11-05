#!/opt/homebrew/bin/python3

import os
import json
from math import radians, cos, sin, asin, sqrt, inf

class highways():
    def __init__(self):
        self.ways = {}

        for fileName in os.listdir('json/'):
            with open(f'json/{fileName}', 'r') as file:
                temp = json.load(file)
                self.ways.update(temp)
    
    def getEndWays(self, slat, slon, elat, elon):
        route = {'start': {'lat': slat, 'lon': slon}, 'end': {'lat': elat, 'lon': elon}}
        route['startWay'] = self.findClosestWay(slat, slon, 'start')
        route['endWay'] = self.findClosestWay(elat, elon, 'end')
        return route
    
    def findClosestWay(self, lat, lon, dir = 'start'):
        minDist = inf
        w = None
        for way in self.ways.values():
            node = way['startNode']
            if dir == 'end':
                node = way['endNode']
            wlat = node['lat']
            wlon = node['long']
            dist = self.getDistance(lat, lon, wlat, wlon)
            if dist < minDist:
                minDist = dist
                w = way

        return w

    def getDistance(self, lat1, lon1, lat2, lon2):
        lon1 = radians(lon1)
        lon2 = radians(lon2)
        lat1 = radians(lat1)
        lat2 = radians(lat2)

        # Haversine formula 
        dlon = lon2 - lon1 
        dlat = lat2 - lat1
        a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2

        return 3956 * 2 * asin(sqrt(a))

def main():
    hw = highways()
    print(hw.findClosestWay(43.5, -112.5, 'start'))
    # print(hw.getDistance(43.5, -112.5, 48.9990055, -97.2392881))

if __name__ == '__main__':
    main()