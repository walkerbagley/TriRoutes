#!/opt/homebrew/bin/python3

import os, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import json
from src import quadtree

# this class contains the entire highway network and appropriate functions
class network():

    # get all ways from the json folder of this project
    def __init__(self):
        # sys.setrecursionlimit(1000000)
        bounds = quadtree.BoundingBox([24.164785, -127.826991], [49.726580, -65.641307])
        self.tree = quadtree.QuadTree(bounds)

        # for fileName in os.listdir('../json/'):
        #     with open(f'../json/{fileName}', 'r') as file:
        #         temp = json.load(file)
        #         for way in temp:
        #             print(way)

        for fileName in os.listdir('json/'):
            with open(f'json/{fileName}', 'r') as file:
                temp = json.load(file)
                for val in temp.values():
                    for i, way in enumerate(val.values()):
                        # if i > 5:
                        #     break
                        self.tree.add(quadtree.Way(way))


def main():
    hw = network()
    print(str(hw.tree))

if __name__ == '__main__':
    main()