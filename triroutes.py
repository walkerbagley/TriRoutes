#!/opt/homebrew/python3

import overpy
import json
from tqdm import tqdm

# rel['route'='road']['network'='US:I'](if:(t['is_in:state'] != 'AK') && (t['is_in:state'] != 'HI'));
# rel['route'='road']['network'='US:US'](if:(t['is_in:state'] != 'AK') && (t['is_in:state'] != 'HI'));
# way(r);
# node(w);

# rel['route'='road']['network'='US:US'];

api = overpy.Overpass()
result = api.query("""
    [out:json][timeout:240][bbox:48.0,-118.0,49.0,-117.0];
    (
        rel['route'='road']['network'='US:I'](if:(t['is_in:state'] != 'AK') && (t['is_in:state'] != 'HI'));
        rel['route'='road']['network'='US:US'](if:(t['is_in:state'] != 'AK') && (t['is_in:state'] != 'HI'));
    );

    way(r)->.w;
    way(r);
    convert length 'length'=length(),::id=id(),'type'='length';
    out;
    .w out;
    node(w.w);
    out;
    convert road ::=::,::geom=geom(),'length'=length(),::id=id(),'type'=type();
    """)

print(result._lengths)

# ways = []
# for way in tqdm(result.ways):
#     wayData = {'id': way.id}
#     ways.append(wayData)

# print(ways[:5])

# overpassURL = "https://overpass-api.de/api/interpreter"

# query = {'method': 'POST', ''}

# response = requests.post(overpassURL, query)
# print(response)