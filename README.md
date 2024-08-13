# TriRoutes

## Overview
I wanted to implement a Google Maps style routing platform by breaking down long haul routes into 3 distinct parts: navigating surface streets in the origin and destination and the highway route. I was looking to write an A* algorithm that efficiently found a route to the destination by taking into consideration the speed and distance required to travel on various roads. Initially, I had a number of ideas for expanding on this project, like including live traffic data, accounting for weather conditions, timing for traffic trends, and adding in rest stop locations. I did know this would be a massive undertaking from the start and planned to see how the project went.

## Pivots
I made a number of pivots throughout the lifespan of this project due to a variety of unforeseen issues. First, actually obtaining highway data is rather difficult, so I ended up spending a great deal of time finding a good API and learning the query language to get the data I was actually looking for. It was only towards the end of the project that I realized this data was not everything I would need to actually create good routes, so I ended up implementing a dynamic query system that would get new roads to investigate if I did not already have connecting roads for a particular path in my database. I also spent a lot of time thoughtfully considering things like what happens when a road is one way versus bidirectional and how to find roads for the start and end of the highway route.

The biggest pivot was that I did not end up having time to implement the end portions of a path since the highway routing ate up all of my time. Along the way, I found it difficult to debug my code when dealing with such a great amount of data and a project with an imperative visual component (maps). As a result, I implemented a mapping library to generate Folium visualizations of many of the features in my routing system, like the final route, grabbing the end roads for a route, and mapping each step of my A* algorithm.

An example of the quadtree search for a starting road:

IMAGE

## Status
As it stands, there is still a lot I’d like to do with this project in the future, though it has a reasonable routing library and appropriate matching mapping functionality for easy testing and examples of what my project can do. I wrote a new quadtree structure for my highway network that increased search times significantly, however I should note that when testing, I would advise against trying really long routes as they will still take a while. I added a search threshold so that a user can specify how many nodes they’d like to search before my algorithm times out so to speak, which would make it easier to test and view on a smaller and more reasonable scale. When I realized I was lacking some necessary data, I rewrote my entire query script to be multithreaded which took significant time. The router seems to perform very well when there is a clear path to the destination or when the distance from start to end is not too great.

There are 3 main files that comprise the majority of this project: mapping.py, quadtree.py and highwayRouter.py. mapping.py contains almost all necessary mapping functions and is what should be used in testing and examples as it implements the other two beneath the surface. quadtree.py contains the necessary data structures for nodes, roads and the recursive quadtree that comprises my highway network. It has built in methods for querying different data from a tree such as the closest road to a given pair of coordinates and all roads that connect with a given road. highwayRouter.py contains the majority of my search algorithm, which includes methods for a simple route as well as maps at each step in addition to the heuristic, which was very important for this project. See the photos below for some examples of what my project is capable of.

Sample highway route:

IMAGE

Sample step of A* algorithm on long route:

IMAGE

Another example route, this time a little questionable:

IMAGE

## Reflection
Overall, I am proud of what I was able to accomplish in this project given the difficulty of such a task and the constraints of an undergraduate computer science student. I tackled a number of intensive problems surrounding APIs, mapping, search algorithms, data structures and data engineering. I learned a ton throughout this project and was constantly searching and considering ways I could improve upon it, even when I was not physically coding in my repository. I would say overall this project was a huge success even though I am far from a final state akin to what I set out to accomplish from the get go. I thoroughly enjoyed putting in an absurd amount of hours and hard work into this project and I genuinely hope to continue working on it after this course concludes because I have a lot of ideas I’d still like to get to and eventually make an interactive web application to go with it. That being said, I am a little sad I wasn’t able to get this to a super functional state, but I am also very grateful for the challenges it presented me along the way.

## Instructions
This is a very large and complex project, but I tried to make my libraries as easy to use as possible. I would suggest only using the mapper I created in mapping.py to see examples of this project at work. As far as setup is concerned, you must have the json, src and script folders from the repository in order to use this library. A sample project tree would look something like:

/json
	/road_tiles_1.json
	…
	/road_tiles_13.json

/src
	/highwayRouter.py
/mapping.py
/quadtree.py
/hwnetwork.py
/multiRouter.py

/scripts
	/overpy.py

notebook.ipynb

We will consider notebook.ipynb our workspace for testing this project. Begin by importing creating a new mapper object and specifying a search timeout (default 5000). This should take a little bit but no longer than 15-20 seconds, and I’d suggest setting the timeout in the 1000-5000 range as any longer and you might be waiting around a while for a route.

from src.mapping import mapper
mapper = mapper(1000)

From here you can call any of the appropriate mapping functions as specified below:

// maps a route from start (lat, lon) to end (lat, lon)
// returns a folium map
mapper.mapRoute(start, end)


// maps the end roads selected by the algorithm for a particular route from start (lat, lon) to end (lat, lon)
mapper.mapEndWays(start, end)

// maps the quadtree search for the starting/ending road (f='start' or f='end') on a route from start (lat, lon) to end (lat, lon)
// returns a folium map
mapper.mapEndWaySearch(start, end, f='start')


// maps each step of the A* algorithm separately, with blue roads denoting current path, red being the current search road, and pink being connected roads to consider
// returns a list of folium maps
mapper.router.routeMaps(start lat, start lon, end lat, end lon)

You will need to save the output of any of these functions in order to display it. An example notebook would look something like (though it’s worth noting the mapper should not be remade each time you’d like to generate a map):

from src.mapping import mapper
mapper = mapper(1000)

maps = mapper.router.routeMaps(42.293894, -84.275253, 42.271693, -84.847918)
for mp in maps[:-15]:
   display(mp)

m = mapper.router.mapRoutes([42.293894, -84.275253], [42.271693, -84.847918])
m

The two top level notebooks in my GitHub repository contain more examples of how I was using these functions if you’d like to see them.
