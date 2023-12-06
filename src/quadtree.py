#!/opt/homebrew/bin/python3

from math import radians, sin, cos, asin, sqrt, inf
from copy import deepcopy
import time
import os, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from scripts import overpy


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

    def __str__(self) -> str:
        i = f'\n\tRoad {self.id}\n'
        r = f'\t{self.tags["ref"] if "ref" in self.tags else ""}'
        return i + r


class BoundingBox:
    def __init__(self, sw: list, ne: list) -> None:
        self.width = abs(ne[1] - sw[1])
        self.height = abs(ne[0] - sw[0])
        self.center = [sw[0] + self.height / 2, sw[1] + self.width / 2]
    
    def containsNode(self, node: Node) -> bool:
        minLat = self.center[0] - self.height / 2
        maxLat = self.center[0] + self.height / 2
        minLon = self.center[1] - self.width / 2
        maxLon = self.center[1] + self.width / 2
        if minLat <= node.lat <= maxLat and minLon <= node.lon <= maxLon:
            return True
        return False


class QuadTree:
    MAX_WAYS = 10

    def __init__(self, bounds: BoundingBox) -> None:
        self.bounds = bounds
        self.ways = []
        self.ul = None
        self.ur = None
        self.ll = None
        self.lr = None
        self.size = 0
    
    def __str__(self) -> str:
        s = f'Size: {self.size}'
        w = ''
        for way in self.ways:
            w += str(way)
        d = '\n'
        if self.ul:
            d += 'UR\n'
            d += '\n'.join(['  ' + i for i in str(self.ur).strip().split('\n')])
            d += '\nUL\n'
            d += '\n'.join(['  ' + i for i in str(self.ul).strip().split('\n')])
            d += '\nLL\n'
            d += '\n'.join(['  ' + i for i in str(self.ll).strip().split('\n')])
            d += '\nLR\n'
            d += '\n'.join(['  ' + i for i in str(self.lr).strip().split('\n')])
        return s + w + d  

    def add(self, way: Way) -> None:
        self._add(way, way.start)
        self._add(way, way.end)

    def _add(self, way: Way, node: Node) -> None:
        if not self.bounds.containsNode(node):
            return

        if not self.ul and len(self.ways) < self.MAX_WAYS:
            if way in self.ways:
                return
            self.size += 1
            self.ways.append(way)  
        
        else:
            if not self.ul:
                self.__divide()
            
            if self.ul.bounds.containsNode(node):
                self.ul._add(way, node)
            elif self.ur.bounds.containsNode(node):
                self.ur._add(way, node)
            elif self.ll.bounds.containsNode(node):
                self.ll._add(way, node)
            elif self.lr.bounds.containsNode(node):
                self.lr._add(way, node)
            
            self.size += 1
    
    def __divide(self) -> None:
        c = self.bounds.center
        h = self.bounds.height
        w = self.bounds.width

        sw = [[c[0] - h / 2, c[1] - w / 2], [c[0], c[1] - w / 2], [c[0], c[1]], [c[0] - h / 2, c[1]]]
        
        ne = [[c[0], c[1]], [c[0] + h / 2, c[1]], [c[0] + h / 2, c[1] + w / 2], [c[0], c[1] + w / 2]]

        bbs = []
        for a, b in zip(sw, ne):
            bbs.append(BoundingBox(a, b))
        
        self.ll = QuadTree(bbs[0])
        self.ul = QuadTree(bbs[1])
        self.ur = QuadTree(bbs[2])
        self.lr = QuadTree(bbs[3])

        for w in self.ways:
            nodes = []
            if self.bounds.containsNode(w.start):
                nodes.append(w.start)
            if self.bounds.containsNode(w.end):
                nodes.append(w.end)
            
            for node in nodes:
                if self.ul.bounds.containsNode(node) and w not in self.ul.ways:
                    self.ul._add(w, node)
                elif self.ur.bounds.containsNode(node) and w not in self.ur.ways:
                    self.ur._add(w, node)
                elif self.ll.bounds.containsNode(node) and w not in self.ll.ways:
                    self.ll._add(w, node)
                elif self.lr.bounds.containsNode(node) and w not in self.lr.ways:
                    self.lr._add(w, node)

        self.ways = []

    def getConnected(self, way: Way) -> list:
        connected = []
        node = way.end
        if not self.ul:
            for w in self.ways:
                if w.id == way.id:
                    continue
                if w.start.id == node.id:
                    connected.append(w)
                elif w.end.id == node.id and not w.oneway:
                    reverse = deepcopy(w)
                    reverse.start, reverse.end = reverse.end, reverse.start
                    connected.append(reverse)
            if not connected:
                return []
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
        return {'start': self.getClosestWay(start, end)[0], 'end': self.getClosestWay(start, end, f='end')[0]}

    def getClosestWay(self, start: list, end: list, visited = set(), f = 'start') -> Way:
        # check if quadtree has been visited already
        minDist = inf
        w = None
        # if self in visited:
        #     return w, minDist
        
        # if not, check current quadtree
        visited.add(self)

        if not self.ul:
            for way in self.ways:
                snode = way.start
                snlat = snode.lat
                snlon = snode.lon

                enode = way.end
                enlat = enode.lat
                enlon = enode.lon

                # distance from start coordinates to start node
                dist1 = getDistance(start, [snlat, snlon])
                # distance from start coordinates to end node
                dist2 = getDistance(start, [enlat, enlon])
                # distance from end coordinates to start node
                snDist = getDistance(end, [snlat, snlon])
                # distance from end coordinates to end node
                enDist = getDistance(end, [enlat, enlon])

                # if the distance to the start is better and the road gets us closer to our destination, use it
                if f == 'start':
                    if dist1 < minDist and enDist < snDist:
                        minDist = dist1
                        w = way
                else:
                    if enDist < minDist and dist1 < dist2:
                        minDist = enDist
                        w = way
            
            return w, minDist
        
        # search the child quadtree containing the start coordinates
        else:
            node = Node({'id': -1, 'lat': start[0], 'long': start[1]}) if f == 'start' else Node({'id': -1, 'lat': end[0], 'long': end[1]})
            newMin = inf

            nearestChild = self.closestChild(node)
            newW, newMin = nearestChild.getClosestWay(start, end, visited, f)

            # if self.ul.bounds.containsNode(node):
            #     newW, newMin = self.ul.getClosestWay(start, end, visited, f)
            # elif self.ur.bounds.containsNode(node):
            #     newW, newMin = self.ur.getClosestWay(start, end, visited, f)
            # elif self.ll.bounds.containsNode(node):
            #     newW, newMin = self.ll.getClosestWay(start, end, visited, f)
            # elif self.lr.bounds.containsNode(node):
            #     newW, newMin = self.lr.getClosestWay(start, end, visited, f)

            if newMin < minDist:
                minDist, w = newMin, newW
        
            # search neighboring quadtrees if their bounds are closer than the distance to the current best way

            # dlat and dlon give distance directly to the latitudinal and longitudinal axes of the current quadtree
            dlat = getDistance([self.bounds.center[0], start[1]], start) if f == 'start' else getDistance([self.bounds.center[0], end[1]], end)
            dlon = getDistance([start[0], self.bounds.center[1]], start) if f == 'start' else getDistance([end[0], self.bounds.center[1]], end)

            # latdir and londir specify which quadrant we just searched
            #     londir
            #  1, -1 |  1, 1
            # -------------- latdir
            # -1, -1 | -1, 1
            if f == 'start':
                latdir = 1 if start[0] >= self.bounds.center[0] else -1
                londir = 1 if start[1] >= self.bounds.center[1] else -1
            else:
                latdir = 1 if end[0] >= self.bounds.center[0] else -1
                londir = 1 if end[1] >= self.bounds.center[1] else -1

            # ABOVE/BELOW
            # if the distance to latitudinal axis < distance to best way, check quadrant above/below the one just searched and compare to current best way
            if abs(dlat) < minDist:
                if latdir == 1:
                    if londir == 1:
                        newW, newMin = self.lr.getClosestWay(start, end, visited, f=f)
                        if newMin < minDist:
                            minDist, w = newMin, newW
                    else:
                        newW, newMin = self.ll.getClosestWay(start, end, visited, f=f)
                        if newMin < minDist:
                            minDist, w = newMin, newW
                else:
                    if londir == 1:
                        newW, newMin = self.ur.getClosestWay(start, end, visited, f=f)
                        if newMin < minDist:
                            minDist, w = newMin, newW
                    else:
                        newW, newMin = self.ul.getClosestWay(start, end, visited, f=f)
                        if newMin < minDist:
                            minDist, w = newMin, newW
            
            # LEFT/RIGHT
            # if the distance to longitudinal axis < distance to best way, check quadrant left/right the one just searched and compare to current best way
            if abs(dlon) < minDist:
                if londir == 1:
                    if latdir == 1:
                        newW, newMin = self.ul.getClosestWay(start, end, visited, f=f)
                        if newMin < minDist:
                            minDist, w = newMin, newW
                    else:
                        newW, newMin = self.ll.getClosestWay(start, end, visited, f=f)
                        if newMin < minDist:
                            minDist, w = newMin, newW
                else:
                    if latdir == 1:
                        newW, newMin = self.ur.getClosestWay(start, end, visited, f=f)
                        if newMin < minDist:
                            minDist, w = newMin, newW
                    else:
                        newW, newMin = self.lr.getClosestWay(start, end, visited, f=f)
                        if newMin < minDist:
                            minDist, w = newMin, newW
            
            # DIAGONAL
            # if the distance to center < distance to best way, check quadrant diagonal the one just searched and compare to current best way
            if sqrt(abs(dlat)**2 + abs(dlon)**2) < minDist:
                if londir == 1:
                    if latdir == 1:
                        newW, newMin = self.ll.getClosestWay(start, end, visited, f=f)
                        if newMin < minDist:
                            minDist, w = newMin, newW
                    else:
                        newW, newMin = self.ul.getClosestWay(start, end, visited, f=f)
                        if newMin < minDist:
                            minDist, w = newMin, newW
                else:
                    if latdir == 1:
                        newW, newMin = self.lr.getClosestWay(start, end, visited, f=f)
                        if newMin < minDist:
                            minDist, w = newMin, newW
                    else:
                        newW, newMin = self.ur.getClosestWay(start, end, visited, f=f)
                        if newMin < minDist:
                            minDist, w = newMin, newW
        
        return w, minDist


    def closestChild(self, node: Node):
        if not self.ul:
            return None
        elif self.ul.bounds.containsNode(node):
            return self.ul
        elif self.ur.bounds.containsNode(node):
            return self.ur
        elif self.ll.bounds.containsNode(node):
            return self.ll
        elif self.lr.bounds.containsNode(node):
            return self.lr
        else:
            dUL = getDistance([node.lat, node.lon], self.ul.bounds.center)
            dUR = getDistance([node.lat, node.lon], self.ur.bounds.center)
            dLL = getDistance([node.lat, node.lon], self.ll.bounds.center)
            dLR = getDistance([node.lat, node.lon], self.ul.bounds.center)
            best = min(dUL, dUR, dLL, dLR)
            if best == dUL:
                return self.ul
            elif best == dUR:
                return self.ur
            elif best == dLL:
                return self.ll
            else:
                return self.lr
    
    def getClosestWayMap(self, start: list, end: list, f = 'start', boxes = [], ways = []) -> Way:
        # check if quadtree has been visited already
        minDist = inf
        w = None
        boxes.append(self.bounds)

        if not self.ul:
            for way in self.ways:
                snode = way.start
                snlat = snode.lat
                snlon = snode.lon

                enode = way.end
                enlat = enode.lat
                enlon = enode.lon

                # distance from start coordinates to start node
                dist1 = getDistance(start, [snlat, snlon])
                # distance from start coordinates to end node
                dist2 = getDistance(start, [enlat, enlon])
                # distance from end coordinates to start node
                snDist = getDistance(end, [snlat, snlon])
                # distance from end coordinates to end node
                enDist = getDistance(end, [enlat, enlon])

                # if the distance to the start is better and the road gets us closer to our destination, use it
                if f == 'start':
                    if dist1 < minDist and enDist < snDist:
                        minDist = dist1
                        w = way
                else:
                    if enDist < minDist and enDist < snDist:
                        minDist = enDist
                        w = way
            
            if w:
                ways.append(w)
            return w, minDist, boxes, ways
        
        # search the child quadtree containing the start coordinates
        else:
            node = Node({'id': -1, 'lat': start[0], 'long': start[1]}) if f == 'start' else Node({'id': -1, 'lat': end[0], 'long': end[1]})
            newMin = inf

            nearestChild = self.closestChild(node)
            newW, newMin, boxes, ways = nearestChild.getClosestWayMap(start, end, f, boxes)

            # if self.ul.bounds.containsNode(node):
            #     newW, newMin = self.ul.getClosestWay(start, end, visited, f)
            # elif self.ur.bounds.containsNode(node):
            #     newW, newMin = self.ur.getClosestWay(start, end, visited, f)
            # elif self.ll.bounds.containsNode(node):
            #     newW, newMin = self.ll.getClosestWay(start, end, visited, f)
            # elif self.lr.bounds.containsNode(node):
            #     newW, newMin = self.lr.getClosestWay(start, end, visited, f)

            if newMin < minDist:
                minDist, w = newMin, newW
        
            # search neighboring quadtrees if their bounds are closer than the distance to the current best way

            # dlat and dlon give distance directly to the latitudinal and longitudinal axes of the current quadtree
            dlat = getDistance([self.bounds.center[0], start[1]], start) if f == 'start' else getDistance([self.bounds.center[0], end[1]], end)
            dlon = getDistance([start[0], self.bounds.center[1]], start) if f == 'start' else getDistance([end[0], self.bounds.center[1]], end)

            # latdir and londir specify which quadrant we just searched
            #     londir
            #  1, -1 |  1, 1
            # -------------- latdir
            # -1, -1 | -1, 1
            if f == 'start':
                latdir = 1 if start[0] >= self.bounds.center[0] else -1
                londir = 1 if start[1] >= self.bounds.center[1] else -1
            else:
                latdir = 1 if end[0] >= self.bounds.center[0] else -1
                londir = 1 if end[1] >= self.bounds.center[1] else -1

            # ABOVE/BELOW
            # if the distance to latitudinal axis < distance to best way, check quadrant above/below the one just searched and compare to current best way
            if abs(dlat) < minDist:
                if latdir == 1:
                    if londir == 1:
                        newW, newMin, boxes, ways = self.lr.getClosestWayMap(start, end, f, boxes, ways)
                        if newMin < minDist:
                            minDist, w = newMin, newW
                    else:
                        newW, newMin, boxes, ways = self.ll.getClosestWayMap(start, end, f, boxes, ways)
                        if newMin < minDist:
                            minDist, w = newMin, newW
                else:
                    if londir == 1:
                        newW, newMin, boxes, ways = self.ur.getClosestWayMap(start, end, f, boxes, ways)
                        if newMin < minDist:
                            minDist, w = newMin, newW
                    else:
                        newW, newMin, boxes, ways = self.ul.getClosestWayMap(start, end, f, boxes, ways)
                        if newMin < minDist:
                            minDist, w = newMin, newW
            
            # LEFT/RIGHT
            # if the distance to longitudinal axis < distance to best way, check quadrant left/right the one just searched and compare to current best way
            if abs(dlon) < minDist:
                if londir == 1:
                    if latdir == 1:
                        newW, newMin, boxes, ways = self.ul.getClosestWayMap(start, end, f, boxes, ways)
                        if newMin < minDist:
                            minDist, w = newMin, newW
                    else:
                        newW, newMin, boxes, ways = self.ll.getClosestWayMap(start, end, f, boxes, ways)
                        if newMin < minDist:
                            minDist, w = newMin, newW
                else:
                    if latdir == 1:
                        newW, newMin, boxes, ways = self.ur.getClosestWayMap(start, end, f, boxes, ways)
                        if newMin < minDist:
                            minDist, w = newMin, newW
                    else:
                        newW, newMin, boxes, ways = self.lr.getClosestWayMap(start, end, f, boxes, ways)
                        if newMin < minDist:
                            minDist, w = newMin, newW
            
            # DIAGONAL
            # if the distance to center < distance to best way, check quadrant diagonal the one just searched and compare to current best way
            if sqrt(abs(dlat)**2 + abs(dlon)**2) < minDist:
                if londir == 1:
                    if latdir == 1:
                        newW, newMin, boxes, ways = self.ll.getClosestWayMap(start, end, f, boxes, ways)
                        if newMin < minDist:
                            minDist, w = newMin, newW
                    else:
                        newW, newMin, boxes, ways = self.ul.getClosestWayMap(start, end, f, boxes, ways)
                        if newMin < minDist:
                            minDist, w = newMin, newW
                else:
                    if latdir == 1:
                        newW, newMin, boxes, ways = self.lr.getClosestWayMap(start, end, f, boxes, ways)
                        if newMin < minDist:
                            minDist, w = newMin, newW
                    else:
                        newW, newMin, boxes, ways = self.ur.getClosestWayMap(start, end, f, boxes, ways)
                        if newMin < minDist:
                            minDist, w = newMin, newW
        
        return w, minDist, boxes, ways
    
    def queryNeighborRoads(self, node) -> None:
        keepTags = ['highway', 'lanes', 'maxspeed', 'name', 'oneway', 'ref', 'surface']
        api = overpy.Overpass()
        querybox = f"""
            [out:json][timeout:600];
            node(id:{node.id});
            way(bn)->.w;
            way(bn);
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
                result = api.query(querybox)
            except:
                time.sleep(0.5)
        
        # print(f'Query on node {node.id}: {len(result._lengths.values())} roads found')

        for length in result._lengths.values():

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
            self.add(Way(wayData))