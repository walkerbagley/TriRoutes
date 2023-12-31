#!/opt/homebrew/bin/python3

from src.hwnetwork import network
from src.quadtree import getDistance
import heapq
import copy

# this class serves as the main form of routing over the highway network we create in hwnetwork.py
class HighwayRouter():

    # setup the router with a highway network and a mapper
    def __init__(self, hw, mapper, threshold):
        self.threshold = threshold
        self.hw = hw
        self.mapper = mapper
    
    # main call to get a route between a pair of start and end coordinates
    def route(self, slat, slon, elat, elon):

        # get the start and end ways for this particular routing
        init = self.hw.tree.getEndWays([slat, slon], [elat, elon])

        # get the route from the actual A* algorithm
        route = self.routeAstar(init['start'], init['end'])
        if not route:
            return None
        
        # add start and end way information to the returned route
        route['start'] = {'lat': slat, 'lon': slon}
        route['end'] = {'lat': elat, 'lon': elon}
        return route
    

    # takes a pair of start and end ways, and the desired destination coordinates
    def routeAstar(self, start, end):

        count = 0

        # visited dictionary keeps track of the best heuristic it takes to reach each way that has been visited
        visited = {}

        # start off with a route only containing the starting way and add it to our priority queue
        route = {'length_m': 0, 'time_s': 0, 'path': [start]}
        pq = [(getDistance([start.start.lat, start.start.lon], [end.end.lat, end.end.lon]), 1, route)]

        # main loop of A*, keep popping from the priority queue until we reach the destination way or run out of paths
        while pq and count < self.threshold:

            # pop the best route available from the priority queue
            heuristic, _, route = heapq.heappop(pq)
            lastWayID = route['path'][-1].id
            count += 1

            # check if the end of the path is our destination
            if lastWayID == end.id:
                print(f'Roads searched: {count}')
                return route
            
            # check if we have been to this way in a more optimal fashion before
            if lastWayID in visited and visited[lastWayID] <= heuristic:
                continue

            # otherwise update the visited dictionary
            visited[lastWayID] = heuristic

            # iterate over all connecting highways to our current end way
            adjacents = self.hw.tree.getConnected(route['path'][-1])

            # for some reason adjacents can end up being none?
            validTypes = ['motorway', 'primary', 'motorway_link']
            if not adjacents and 'highway' in route['path'][-1].tags and route['path'][-1].tags['highway'] in validTypes:
            # if not adjacents:
                # print(route['path'][-1].tags['highway'])
                self.hw.tree.queryNeighborRoads(route['path'][-1].end)
                adjacents = self.hw.tree.getConnected(route['path'][-1])
            
            if not adjacents:
                adjacents = []

            for adjacent in adjacents:
                newRoute = route.copy()

                # calculate heuristic for the new path
                h = self.heuristic(newRoute, adjacent, end)

                # if we have visited this way more optimally, skip it
                if adjacent.id in visited and visited[adjacent.id] <= h:
                    continue

                # update the route to include the new road and length/time measures
                newRoute['path'].append(adjacent)
                newRoute['length_m'] += adjacent.length
                newRoute['time_s'] += adjacent.time
                # print((h, len(newRoute['path']), newRoute))
                heapq.heappush(pq, (h, len(newRoute['path']), copy.deepcopy(newRoute)))
        
        print(f'Roads searched: {count}')
        return route
    

    # returns a series of maps for a given A* search to make it easier to visualize the algorithm
    def routeMaps(self, slat, slon, elat, elon):
        init = self.hw.tree.getEndWays([slat, slon], [elat, elon])
        maps = self.AstarMaps(init['start'], init['end'])
        return maps


    # this works the exact same as the normal algorithm, just saving a map for each step of the algorithm
    def AstarMaps(self, start, end):
        count = 0
        maps = []
        visited = {}
        route = {'length_m': 0, 'time_s': 0, 'path': [start]}
        pq = [(getDistance([start.start.lat, start.start.lon], [end.end.lat, end.end.lon]), 1, route)]
        while pq and count < self.threshold:
            heuristic, _, route = heapq.heappop(pq)
            lastWayID = route['path'][-1].id
            count += 1
            if lastWayID == end.id:
                return maps
            if lastWayID in visited and visited[lastWayID] <= heuristic:
                continue

            visited[lastWayID] = heuristic

            # add map for current step to maps array
            adjacents = self.hw.tree.getConnected(route['path'][-1])
            maps.append(self.mapper.mapAstarStep(route, adjacents))

            for adjacent in adjacents:
                newRoute = route.copy()
                h = self.heuristic(newRoute, adjacent, end)
                if adjacent.id in visited and visited[adjacent.id] <= h:
                    continue
                newRoute['path'].append(adjacent)
                newRoute['length_m'] += adjacent.length
                newRoute['time_s'] += adjacent.time
                heapq.heappush(pq, (h, len(newRoute['path']), copy.deepcopy(newRoute)))
            
        return maps

    
    # this returns the distance traveled so far plus the Haversine distance remaining to the destination
    def heuristic(self, route, way, end):
        # distance traveled so far
        lastNode = way.end
        h = getDistance([end.start.lat, end.start.lon], [lastNode.lat, lastNode.lon])

        # Haversine distance remaining, which is an underestimation
        g = route['length_m'] + way.length
        return g + h


    # DEPRECATED
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


def main():
    hw = network()
    router = HighwayRouter(hw, None)
    print(router.route(42.293894, -84.275253, 42.271693, -84.847918))

if __name__ == '__main__':
    main()