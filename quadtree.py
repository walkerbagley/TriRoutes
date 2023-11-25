#!/opt/homebrew/bin/python3

from copy import deepcopy


# returns the distance between two sets of coordinates
def getDistance(p1: list, p2: list) -> float:
    # convert all degrees to radians for the trigonometric functions
    lon1 = radians(p1[1])
    lon2 = radians(p2[1])
    lat1 = radians(p1[0])
    lat2 = radians(p2[0])

    # calculate the Haversine formula 
    dlon = lon2 - lon1 
    dlat = lat2 - lat1
    a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2

    return 3956 * 2 * asin(sqrt(a))


class Node:
    def __init__(self, data: dict) -> None:
        self.id = data['id']
        self.lat = data['lat']
        self.lon = data['long']


class Way:
    def __init__(self, data: dict) -> None:
        self.id = data['id']
        self.length = data['length_mi']
        self.time = data['time_s']
        self.tags = data['tags']
        self.start = Node(data['startNode'])
        self.end = Node(data['endNode'])
        self.oneway = True if 'oneway' in self.tags and self.tags['oneway'] == 'yes' else False


class BoundingBox:
    def __init__(self, sw: list, ne: list) -> None:
        self.width = getDistance([sw[0], sw[1]], [sw[0], ne[1]])
        self.height = getDistance([sw[0], sw[1]], [ne[0], sw[1]])
        self.center = [sw[0] + self.height / 2, sw[1] + self.width / 2]
    
    def containsNode(self, node: Node) -> bool:
        minLat = self.center[0] - self.height / 2
        maxLat = self.center[0] + self.height / 2
        minLon = self.center[0] - self.width / 2
        maxLon = self.center[0] + self.width / 2
        if minLat <= node.lat <= maxLat and minLon <= node.lon <= maxLon:
            return True
        return False


class QuadTree:
    MAX_WAYS = 6

    def __init__(self, bounds: BoundingBox) -> None:
        self.bounds = bounds
        self.ways = []
        self.ul = None
        self.ur = None
        self.ll = None
        self.lr = None
    
    def add(self, way: Way) -> None:
        self.__add(way)
        if not way.oneway:
            reverse = deepcopy(way)
            reverse.start, reverse.end = reverse.end, reverse.start
            self.__add(reverse)
        

    def __add(self, way: Way) -> None:
        if not self.bound.containsNode(way.start):
            return

        if not self.ul and len(self.ways) < MAX_WAYS:
            self.ways.append(way)  
        
        else:
            if not self.ul:
                self.__divide()
            
            if self.ul.bounds.containsNode(way.start):
                self.ul.add(way)
            elif self.ur.bounds.containsNode(way.start):
                self.ur.add(way)
            elif self.ll.bounds.containsNode(way.start):
                self.ll.add(way)
            elif self.lr.bounds.containsNode(way.start):
                self.lr.add(way)
    
    def __divide(self) -> None:
        sw = [self.bounds.center[0] - self.bounds.height / 2, self.bounds.center[1] - self.bounds.width / 2]
        ne = self.bounds.center
        self.ll = QuadTree(BoundingBox(sw, ne))
        sw[0] = self.bounds.center[0]
        ne[0] += self.bounds.height / 2
        self.ul = QuadTree(BoundingBox(sw, ne))
        sw = self.bounds.center
        ne[1] += self.bounds.width / 2
        self.ur = QuadTree(BoundingBox(sw, ne))
        sw[0] -= self.bounds.height / 2
        ne[0] = self.bounds.center[0]
        self.lr = QuadTree(BoundingBox(sw, ne))

        for w in self.ways:
            if self.ul.bounds.containsNode(w.start):
                self.ul.add(w)
            elif self.ur.bounds.containsNode(w.start):
                self.ur.add(w)
            elif self.ll.bounds.containsNode(w.start):
                self.ll.add(w)
            elif self.lr.bounds.containsNode(w.start):
                self.lr.add(w)
        self.ways = []

    def getConnected(self, way: Way) -> list:
        connected = []
        node = way.end
        if not self.ul:
            for w in self.ways:
                if w.start.id == node.id:
                    connected.append(w)
            return connected
        else:
            if self.ul.bounds.containsNode(node):
                return self.ul.getConnected(way)
            elif self.ur.bounds.containsNode(node):
                return self.ur.getConnected(way)
            elif self.ll.bounds.containsNode(node):
                return self.ll.getConnected(way)
            elif self.lr.bounds.containsNode(node):
                return self.lr.getConnected(way)
    

    def getEndWays(self, start: list, end: list) -> dict:
        return {'start': self.getStartWay(start, end), 'end': self.getEndWay(start, end)}

    def getStartWay(self, start: list, end: list) -> Way:
        node = {'id': -1, 'lat': start[0], 'long': start[1]}
        node = Node(node)
        if not self.ul:
            lat, lon = start
            elat, elon = end
            minDist = inf
            w = None
            for way in self.ways:
                snode = way.start
                snlat = snode.lat
                snlon = snode.lon

                enode = way.end
                enlat = enode.lat
                enlon = enode.lon

                # distance from start coordinates to start node
                dist1 = getDistance(lat, lon, snlat, snlon)
                # distance from start coordinates to end node
                dist2 = getDistance(lat, lon, enlat, enlon)
                # distance from end coordinates to start node
                snDist = getDistance(elat, elon, snlat, snlon)
                # distance from end coordinates to end node
                enDist = getDistance(elat, elon, enlat, enlon)

                # if the distance to the start is better and the road gets us closer to our destination, use it
                if dist1 < minDist and enDist < snDist:
                    minDist = dist1
                    w = way
            
            return w
        
        else:
            if self.ul.bounds.containsNode(node):
                return self.ul.getStartWay(start, end)
            elif self.ur.bounds.containsNode(node):
                return self.ur.getStartWay(start, end)
            elif self.ll.bounds.containsNode(node):
                return self.ll.getStartWay(start, end)
            elif self.lr.bounds.containsNode(node):
                return self.lr.getStartWay(start, end)


    def getEndWay(self, start: list, end: list) -> Way:
        node = {'id': -1, 'lat': end[0], 'long': end[1]}
        node = Node(node)
        if not self.ul:
            lat, lon = start
            elat, elon = end
            minDist = inf
            w = None
            for way in self.ways:
                snode = way.start
                snlat = snode.lat
                snlon = snode.lon

                enode = way.end
                enlat = enode.lat
                enlon = enode.lon

                # distance from start coordinates to start node
                dist1 = getDistance(lat, lon, snlat, snlon)
                # distance from start coordinates to end node
                dist2 = getDistance(lat, lon, enlat, enlon)
                # distance from end coordinates to start node
                snDist = getDistance(elat, elon, snlat, snlon)
                # distance from end coordinates to end node
                enDist = getDistance(elat, elon, enlat, enlon)

                # if the distance to the end is better and the road starts closer to the start than it ends, then use it
                if enDist < minDist and dist1 < dist2:
                    minDist = enDist
                    w = way
            
            return w
        
        else:
            if self.ul.bounds.containsNode(node):
                return self.ul.getEndWay(start, end)
            elif self.ur.bounds.containsNode(node):
                return self.ur.getEndWay(start, end)
            elif self.ll.bounds.containsNode(node):
                return self.ll.getEndWay(start, end)
            elif self.lr.bounds.containsNode(node):
                return self.lr.getEndWay(start, end)