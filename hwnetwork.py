#!/opt/homebrew/bin/python3

import os
import json
from math import radians, cos, sin, asin, sqrt, inf

# this class contains the entire highway network and appropriate functions
class highways():

    # get all ways from the json folder of this project
    def __init__(self):
        self.ways = {}

        for fileName in os.listdir('json/'):
            with open(f'json/{fileName}', 'r') as file:
                temp = json.load(file)
                self.ways.update(temp)
    

    # get the end ways for a specified set of coordinates
    def getEndWays(self, slat, slon, elat, elon):
        route = {'start': {'lat': slat, 'lon': slon}, 'end': {'lat': elat, 'lon': elon}}

        # call the findClosestStart and findClosestEnd helper functions
        route['startWay'] = self.findClosestStart(slat, slon, elat, elon)
        route['endWay'] = self.findClosestEnd(slat, slon, elat, elon)
        return route
    
    
    # find the closest road to the start coordinates heading in the right direction
    def findClosestStart(self, lat, lon, elat, elon):
        # setup
        minDist = inf
        w = None

        # iterate over all ways in our dataset
        for way in self.ways.values():
            snode = way['startNode']
            snlat = snode['lat']
            snlon = snode['long']

            enode = way['endNode']
            enlat = enode['lat']
            enlon = enode['long']

            # distance from start coordinates to start node
            dist1 = self.getDistance(lat, lon, snlat, snlon)
            # distance from start coordinates to end node
            dist2 = self.getDistance(lat, lon, enlat, enlon)
            # distance from end coordinates to start node
            snDist = self.getDistance(elat, elon, snlat, snlon)
            # distance from end coordinates to end node
            enDist = self.getDistance(elat, elon, enlat, enlon)

            # if the distance to the start is better and the road gets us closer to our destination, use it
            if dist1 < minDist and enDist < snDist:
                minDist = dist1
                w = way

            # if the distance to the end is better, the road is not one way and it gets us close to the destination, swap the start/end nodes and use it
            if dist2 < minDist and snDist < enDist and not self.isOneWay(way):
                way['startNode'], way['endNode'] = way['endNode'], way['startNode']
                minDist = dist2
                w = way

        return w
    

    # find the closest road to the end coordinates heading in the right direction
    # this works the exact same as findClosestStart, with a couple modifications
    def findClosestEnd(self, lat, lon, elat, elon):
        minDist = inf
        w = None

        # iterate over all ways in the dataset
        for way in self.ways.values():
            snode = way['startNode']
            snlat = snode['lat']
            snlon = snode['long']

            enode = way['endNode']
            enlat = enode['lat']
            enlon = enode['long']

            # same distances as before
            dist1 = self.getDistance(lat, lon, snlat, snlon)
            dist2 = self.getDistance(lat, lon, enlat, enlon)
            snDist = self.getDistance(elat, elon, snlat, snlon)
            enDist = self.getDistance(elat, elon, enlat, enlon)

            # if the distance to the end is better and the road starts closer to the start than it ends, then use it
            if enDist < minDist and dist1 < dist2:
                minDist = enDist
                w = way
            
            # if the distance to the end from the start of this way is better, the road is not one way and it starts closer to the start than the end, then swap the start/end nodes and use it
            if snDist < minDist and dist2 < dist1 and not self.isOneWay(way):
                way['startNode'], way['endNode'] = way['endNode'], way['startNode']
                minDist = snDist
                w = way

        return w


    # returns the distance between two sets of coordinates
    def getDistance(self, lat1, lon1, lat2, lon2):
        # convert all degrees to radians for the trigonometric functions
        lon1 = radians(lon1)
        lon2 = radians(lon2)
        lat1 = radians(lat1)
        lat2 = radians(lat2)

        # calculate the Haversine formula 
        dlon = lon2 - lon1 
        dlat = lat2 - lat1
        a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2

        return 3956 * 2 * asin(sqrt(a))
    
    # returns whether or not a given way is one way
    def isOneWay(self, way):
        if 'oneway' in way['tags'] and way['tags']['oneway'] == 'yes':
            return True
        return False
    

    # DEPRECATED: use findClosestStart and findClosestEnd instead
    # this function fails to account for the direction and distance from the start/end, so returns roads that may be going in a suboptimal direction
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