#!/opt/homebrew/bin/python3

from threading import Thread
from threading import Lock
from threading import Semaphore
import heapq
import copy

# this class serves as the main form of routing over the highway network we create in hwnetwork.py
class MultiRouter():
    # setup the router with a highway network and a mapper
    def __init__(self, hw, mapper):
        self.hw = hw
        self.mapper = mapper
        self.start = None
        self.end = None
        self.visited = {}
        self.pq = []
        self.vLock = Lock()
        self.pqLock = Lock()
        self.threads = Semaphore(5)
        self.activeThreads = []
    
    # main call to get a route between a pair of start and end coordinates
    def route(self, slat, slon, elat, elon):

        # get the start and end ways for this particular routing
        init = self.hw.getEndWays(slat, slon, elat, elon)
        self.start = init['startWay']
        self.end = init['endWay']

        # get the route from the actual A* algorithm
        route = self.routeAstar(elat, elon)
        if not route:
            return None
        
        # add start and end way information to the returned route
        route['start'] = init['start']
        route['end'] = init['end']
        return route
    

    # takes a pair of start and end ways, and the desired destination coordinates
    def routeAstar(self, elat, elon):

        # start off with a route only containing the starting way and add it to our priority queue
        route = {'length_m': 0, 'time_s': 0, 'path': [self.start]}
        tempNode = self.start['startNode']
        self.pq.append((self.hw.getDistance(tempNode['lat'], tempNode['long'], elat, elon), route))

        # main loop of A*, keep popping from the priority queue until we reach the destination way or run out of paths
        while (self.pq):
            # pop the best route available from the priority queue
            # self.pqLock.acquire()
            heuristic, route = heapq.heappop(self.pq)
            # self.pqLock.release()

            lastWayID = route['path'][-1]['id']
            # check if the end of the path is our destination
            if lastWayID == self.end['id']:
                self.pq = []
                self.visited = {}
                return route

            # check if we have been to this way in a more optimal fashion before
            if lastWayID in self.visited and self.visited[lastWayID] <= heuristic:
                continue

            while (self.threads._value < 1):
                thread = self.activeThreads.pop(0)
                thread.join()
                self.threads.release()

            self.threads.acquire()
            thread = Thread(target=self.AstarStep, args=[heuristic, route])
            thread.start()
            self.activeThreads.append(thread)

            while not self.pq and len(self.activeThreads) > 0:
                thread = self.activeThreads.pop(0)
                thread.join()
                self.threads.release()

            
        self.visited = {}
        return route
    

    def AstarStep(self, heuristic, route):
        lastWayID = route['path'][-1]['id']

        # otherwise update the visited dictionary
        # self.vLock.acquire()
        self.visited[lastWayID] = heuristic
        # self.vLock.release()

        # iterate over all connecting highways to our current end way
        for adjacent in self.getAdjacentHighways(route['path'][-1]):
            newRoute = route.copy()

            # calculate heuristic for the new path
            elat = self.end['endNode']['lat']
            elon = self.end['endNode']['long']
            h = self.heuristic(newRoute, adjacent, elat, elon)

            # if we have visited this way more optimally, skip it
            if adjacent['id'] in self.visited and self.visited[adjacent['id']] <= h:
                continue

            # update the route to include the new road and length/time measures
            newRoute['path'].append(adjacent)
            newRoute['length_m'] += adjacent['length_mi']
            newRoute['time_s'] += adjacent['time_s']

            # self.pqLock.acquire()
            heapq.heappush(self.pq, (h, copy.deepcopy(newRoute)))
            # self.pqLock.release()
        
        return

    
    # this returns the distance traveled so far plus the Haversine distance remaining to the destination
    def heuristic(self, route, way, elat, elon):
        # distance traveled so far
        lastNode = way['endNode']
        h = self.hw.getDistance(elat, elon, lastNode['lat'], lastNode['long'])

        # Haversine distance remaining, which is an underestimation
        g = route['length_m'] + way['length_mi']
        return g + h

    
    # returns all highways connecting to the end of the current highway
    def getAdjacentHighways(self, current):
        adjacent = []

        # iterate through all highways
        for way in self.hw.ways.values():

            # ignore the current highway
            if way['id'] == current['id']:
                continue

            # if the end of the way passed in is the same as the start of the current way, we have a match
            if way['startNode']['id'] == current['endNode']['id']:
                adjacent.append(way)

            # otherwise if the ends line up and the current way is not one way, we also have a match
            # this ensures we check bidirectional roads, so we switch the start and end nodes to make this the direction we want
            elif way['endNode']['id'] == current['endNode']['id'] and not self.hw.isOneWay(way):
                way['startNode'], way['endNode'] = way['endNode'], way['startNode']
                adjacent.append(way)

        return adjacent