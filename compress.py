import json

waysPerFile = 50000

for i in range(5):
    with open(f'road_tiles_{i}.json', 'r') as file:
        ways = [(k, v) for k, v in json.load(file).items()]
        if len(ways) > waysPerFile:
            numFiles = 0
            numWays = 0
            while numWays < len(ways):
                with open(f'road_tiles_{i}_{numFiles}.json', 'w') as f:
                    bound = numWays + waysPerFile if numWays + waysPerFile < len(ways) else len(ways)
                    ways_json = {i[0]: i[1] for i in ways[numWays:bound]}
                    ways_json = json.dumps(ways_json, indent=4)
                    f.write(ways_json)
                numWays += waysPerFile
                numFiles += 1