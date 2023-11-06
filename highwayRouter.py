#!/opt/homebrew/bin/python3

from hwnetwork import highways
import heapq

class HighwayRouter():
    def __init__(self, hw):
        self.hw = hw
    
    def route(self, slat, slon, elat, elon):
        init = self.hw.getEndWays(slat, slon, elat, elon)
        route = self.routeAstar(init['startWay'], init['endWay'], elat, elon)
        if not route:
            return None
        
        route['start'] = init['start']
        route['end'] = init['end']
        return route
    
    def routeAstar(self, start, end, elat, elon):
        visited = set()
        route = {'length_m': 0, 'time_s': 0, 'path': [start]}
        pq = [(0, route)]
        while (pq):
            # print(pq[0][1])
            heuristic, route = heapq.heappop(pq)
            lastWayID = route['path'][-1]['id']
            if lastWayID in visited:
                continue
            if lastWayID == end['id']:
                return route

            visited.add(lastWayID)

            for adjacent in self.getAdjacentHighways(route['path'][-1]):
                newRoute = route.copy()
                h = self.heuristic(newRoute, adjacent, elat, elon)
                newRoute['path'].append(adjacent)
                newRoute['length_m'] += adjacent['length_mi']
                newRoute['time_s'] += adjacent['time_s']
                heapq.heappush(pq, (h, newRoute))
            
            if not pq:
                return route
        
        return None

    
    def heuristic(self, route, way, elat, elon):
        lastNode = way['endNode']
        dist = self.hw.getDistance(elat, elon, lastNode['lat'], lastNode['long'])
        return dist + route['length_m']

    
    def getAdjacentHighways(self, current):
        adjacent = []
        for way in self.hw.ways.values():
            if way['startNode']['id'] == current['endNode']['id']:
                adjacent.append(way)
        return adjacent

def main():
    data = highways()
    router = HighwayRouter(data)
    route = router.route(35.128556, -111.200147, 35.054526, -110.802710)
    print(route)

if __name__ == '__main__':
    main()
