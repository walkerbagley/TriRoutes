import os
import json

seen = set()
numFiles = 20

for file in os.listdir('.'):
    if 'road_tiles' in file:
        with open(file, 'r') as f:

            ways = json.load(f)
            print(f'{file}: {len(ways)}')
            newWays = {k:v for k, v in ways.items() if k not in seen}
            print(f'Found {len(ways) - len(newWays)} duplicates\n')
            
            for i in ways:
                seen.add(i)
            
            with open(f'road_tiles_{numFiles}.json', 'w') as newFile:
                ways_json = json.dumps(newWays, indent=4)
                newFile.write(ways_json)

        numFiles += 1

print(f'{len(seen)} total road segments')