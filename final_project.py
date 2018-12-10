import json
import requests
import csv
import sqlite3 as sqlite
from bs4 import BeautifulSoup

import plotly
import plotly.plotly as py
import plotly.graph_objs as go

import secrets


# -----------------------------------------------------------#
plotly.tools.set_credentials_file(username=secrets.PLOTLY_USERNAME, api_key=secrets.PLOTLY_API_KEY)
# -----------------------------------------------------------#

DBNAME='tacos.sqlite'

# Create DB for tacos restuarants
def create_tacos_db():
    try:
        conn = sqlite.connect('tacos.sqlite')
    except:
        print("Error: Can't connect to tacos.sqlite")
        return
    cur = conn.cursor()

    statement = '''
        DROP TABLE IF EXISTS 'Restaurants';
    '''
    cur.execute(statement)

    statement = '''
        DROP TABLE IF EXISTS 'Cities';
    '''
    cur.execute(statement)
    conn.commit()

def populate_tacos_db():
    conn = sqlite.connect('tacos.sqlite')
    cur = conn.cursor()
    with open('tacos.csv','r',encoding='utf-8') as f:
        reader = csv.reader(f)
        tacos = list(reader)
        f.close()


    # Create table Cities
    statement = '''
    CREATE TABLE `Cities` (
        `ID`	INTEGER PRIMARY KEY AUTOINCREMENT,
        `city`	TEXT UNIQUE
    );
    '''
    cur.execute(statement)
    counter=0
    for r in tacos:
        if counter==0:
            counter=1
            continue
        insertion=(None,r[1])
        statement = 'INSERT or IGNORE INTO "Cities"'
        statement += 'VALUES (?,?)'
        cur.execute(statement,insertion)
    conn.commit()

    # Create table Restaurants
    statement = '''
        CREATE TABLE `Restaurants` (
            `ID`	INTEGER PRIMARY KEY AUTOINCREMENT,
            `Address`	TEXT UNIQUE,
            `City`	INTEGER NOT NULL,
            `Latitude`	REAL NOT NULL,
            `Longitude`	REAL NOT NULL,
            `Name`	TEXT,
            `Url`	TEXT
        );
    '''
    cur.execute(statement)
    counter=0
    for r in tacos:
        if counter==0:
            counter=1
            continue
        city_id_state='SELECT Id From Cities WHERE city="{}"'.format(r[1])
        cur.execute(city_id_state)
        city_id=cur.fetchone()[0]
        insertion=(None, r[0],city_id,r[2],r[3],r[4],r[6])
        statement = 'INSERT or IGNORE INTO "Restaurants"'
        statement += 'VALUES (?,?,?,?,?,?,?)'
        cur.execute(statement,insertion)
    
    # Delete Empty Data
    statement="DELETE FROM Restaurants WHERE Latitude IS NULL OR trim(Latitude) = '';"
    conn.execute(statement)
    conn.commit()
    conn.close()

# Yelp API
BASE_URL = 'https://api.yelp.com/v3/businesses/search'

# CACHE file
CACHE_FNAME = 'cache.json'
try:
    cache_file = open(CACHE_FNAME, 'r')
    cache_contents = cache_file.read()
    CACHE_DICTION = json.loads(cache_contents)
    cache_file.close()
except:
    CACHE_DICTION = {}


def make_request_using_cache(url_params,key):
    unique_ident = key
    headers = {'Authorization': 'Bearer %s' % secrets.API_KEY,}
    if unique_ident in CACHE_DICTION:
        # print("Getting cached data...")
        return CACHE_DICTION[unique_ident]
    else:
        # print("Making a request for new data...")
        resp = requests.request('GET', BASE_URL, headers=headers, params=url_params)
        CACHE_DICTION[unique_ident] = resp.json()
        dumped_json_cache = json.dumps(CACHE_DICTION)
        fw = open(CACHE_FNAME,"w")
        fw.write(dumped_json_cache)
        fw.close()
        return CACHE_DICTION[unique_ident]

def yelp_search(term, location):
    url_params = {
        'term': term.replace(' ', '+'),
        'location': location.replace(' ', '+'),
        'limit': 20
    }
    key = '{}+{}'.format(term,location)
    return make_request_using_cache(url_params,key)


# scrape Yelp page
# CACHE file
CACHE_FNAME2 = 'reviews_cache.json'
try:
    cache_file = open(CACHE_FNAME2, 'r')
    cache_contents = cache_file.read()
    CACHE_DICTION2 = json.loads(cache_contents)
    cache_file.close()
except:
    CACHE_DICTION2 = {}

def scrape_review(url):
    try:
        if url in CACHE_DICTION2:
            return CACHE_DICTION2[url]

        html = requests.get(url).text
        soup = BeautifulSoup(html, 'html.parser')
        data = soup.find_all(class_='quote')
        reviews = []
        for r in data:
            reviews.append(r.text)
        CACHE_DICTION2[url] = reviews
        dumped_json_cache = json.dumps(CACHE_DICTION2)
        fw = open(CACHE_FNAME2,"w")
        fw.write(dumped_json_cache)
        fw.close()
        return  CACHE_DICTION2[url]
    except:
        return "No reviews."


# plot results to plotly map
class Place():
    def __init__(self, name, lat, lon, url):
        self.name=name
        self.lat=lat
        self.lon=lon
        self.url=url

    def __str__(self):
        return self.name

def plot_results(place_list):
    lat_vals=[]
    lon_vals=[]
    info_vals=[]

    for p in place_list:
        lat_vals.append(p.lat)
        lon_vals.append(p.lon)
        info_vals.append(p.name+'\n'+p.url)

    
    data = [ dict(
            type = 'scattermapbox',
            lon = lon_vals,
            lat = lat_vals,
            text = info_vals,
            mode = 'markers',
            marker = dict(
                size = 8,
                symbol = 'circle',
                color = 'blue'
            ))]

    min_lat = 10000
    max_lat = -10000
    min_lon = 10000
    max_lon = -10000

    for lat in lat_vals:
        if lat < min_lat:
            min_lat=lat
        if lat > max_lat:
            max_lat=lat
    
    for lon in lon_vals:
        if lon < min_lon:
            min_lon=lon
        if lon > max_lon:
            max_lon=lon

    center_lat = (max_lat+min_lat) / 2
    center_lon = (max_lon+min_lon) / 2

    layout = dict(
        title = 'Results',
        autosize=True,
        showlegend = False,
        mapbox=dict(
            accesstoken=secrets.MAPBOX_TOKEN,
            bearing=0,
            center= {'lat': center_lat, 'lon': center_lon},
            pitch=0,
            zoom=11,
          ),
    )


    fig = dict( data=data, layout=layout )
    py.plot( fig, validate=False, filename='Search Results',auto_open = True )

# Plot Top 10 Cities that have taco restaurants
def plot_top10():
    conn = sqlite.connect('tacos.sqlite')
    cur = conn.cursor()
    statement='''
    SELECT Cities.city, count(*)
    From Cities 
    JOIN Restaurants ON Cities.ID=Restaurants.City
    GROUP BY (Restaurants.City)
    ORDER BY COUNT(*) DESC
    LIMIT 10
    '''
    cur.execute(statement)
    results=cur.fetchall()
    cities=[]
    amount=[]
    for r in results:
        cities.append(r[0])
        amount.append(r[1])
    
    data = [go.Bar(
            x=cities,
            y=amount
    )]

    py.plot(data, filename='Top 10 Cities With The Most Taco Restaurants (USA)')

# Search Taco Restaurants By DB
def db_search(city):
    conn = sqlite.connect('tacos.sqlite')
    cur = conn.cursor()
    statement='''
    SELECT R.Name,R.Latitude,R.Longitude,R.Url,R.Address
    From Restaurants as R 
    JOIN Cities ON Cities.ID=R.City
    WHERE Cities.city='{}'
    LIMIT 20
    '''.format(city)
    cur.execute(statement)
    results=cur.fetchall()
    db_results={}
    for r in results:
        db_results[r[0]]={
            'lat':r[1],
            'lon':r[2],
            'url':r[3],
            'address':r[4]
        }
    
    return db_results

# Compare Results on Ploty
def plot_compare(yelp_places,db_places):
    yelp_lat_vals=[]
    yelp_lon_vals=[]
    yelp_info_vals=[]
    db_lat_vals=[]
    db_lon_vals=[]
    db_info_vals=[]

    for p in yelp_places:
        yelp_lat_vals.append(p.lat)
        yelp_lon_vals.append(p.lon)
        yelp_info_vals.append(p.name+'\n'+p.url)
    
    for key, p in db_places.items():
        db_lat_vals.append(p['lat'])
        db_lon_vals.append(p['lon'])
        db_info_vals.append(key+"\n"+p['url'])
    
    trace1 = dict(
            type = 'scattermapbox',
            lon = yelp_lon_vals,
            lat = yelp_lat_vals,
            text = yelp_info_vals,
            mode = 'markers',
            marker = dict(
                size = 8,
                symbol = 'circle',
                color = 'blue'
            ))
    
    trace2 = dict(
            type = 'scattermapbox',
            lon = db_lon_vals,
            lat = db_lat_vals,
            text = db_info_vals,
            mode = 'markers',
            marker = dict(
                size = 8,
                symbol = 'circle',
                color = 'red'
            ))

    data=[trace1,trace2]

    min_lat = 10000
    max_lat = -10000
    min_lon = 10000
    max_lon = -10000
    for v in yelp_lat_vals:
        if v < min_lat:
            min_lat = v
        if v > max_lat:
            max_lat = v
    
    for v in db_lat_vals:
        if v < min_lat:
            min_lat = v
        if v > max_lat:
            max_lat = v
    
    for v in yelp_lon_vals:
        if v < min_lon:
            min_lon = v
        if v > max_lon:
            max_lon = v
    
    for v in db_lon_vals:
        if v < min_lon:
            min_lon = v
        if v > max_lon:
            max_lon = v

    center_lat = (max_lat+min_lat) / 2
    center_lon = (max_lon+min_lon) / 2
    


    layout = dict(
        title = 'Results',
        autosize=True,
        showlegend = False,
        mapbox=dict(
            accesstoken=secrets.MAPBOX_TOKEN,
            bearing=0,
            center= {'lat': center_lat, 'lon': center_lon},
            pitch=0,
            zoom=11,
          ),
    )

    fig = dict( data=data, layout=layout )
    py.plot( fig, validate=False, filename='Compare Results',auto_open = True )

# output to csv file
def output_csv(results,flag):
    with open('results.csv','w',encoding='utf-8') as csv_file:
        writer=csv.writer(csv_file)
        writer.writerow(['Name','Address','Url'])
        if flag:
            for value in results:
                writer.writerow([value['name'],value['location']['address1'],value['url']])
        else:
            for key, value in results.items():
                writer.writerow([key,value['address'],value['url']])
    
        csv_file.close()



# -----------------------------------------------#

if __name__=='__main__':
    # Create DB #
    print('Creating DB...')
    create_tacos_db()
    populate_tacos_db()
    while True:
        line1 = input("\n1. Search \n2. Exit \nPlease input your command (1 or 2): ")
        if line1 == '1':
            while True:
                line2=input("\n1. Yelp Fushion API\n2. Tacos Restaurants in the U.S.\nChoose Your Data Source (1 or 2): ")
                if line2 == '1':
                    # yelp search
                    term=input("Please input your interest (e.g. pizza ): ")
                    location=input("Please input the location (e.g. Ann Arbor ): ")
                    results=yelp_search(term, location)['businesses']
                    yelp_places=[]
                    for data in results:
                        name=data['name']
                        lat=data['coordinates']['latitude']
                        lon=data['coordinates']['longitude']
                        url=data['url']
                        yelp_places.append(Place(name,lat,lon,url))
                    # choose output
                    while True:
                        print("\n1. Output to csv file\n2. Plotly Map\n3. Read Comments\n4. Back")
                        line3=input("\nChoose output (1, 2, 3 or 4) : ")
                        if line3=='1':
                            output_csv(results,True)
                        elif line3=='2':
                            plot_results(yelp_places)
                        elif line3=='3':
                            counter=1
                            for p in yelp_places:
                                print("{}. {}".format(counter,p))
                                counter += 1
                            if len(yelp_places)==0:
                                print("No result is found.")
                                break
                            n=input("Read comments for (index of the results): ")
                            try:
                                reviews=scrape_review(yelp_places[int(n)-1].url)
                                for r in reviews:
                                    print(r)
                            except:
                                print("Invalid Input")
                        elif line3=='4':
                            break
                        else:
                            print("Invalid Input!1")
                    break
                elif line2 == '2':
                    # db search
                    while True:
                        print("\n1. Top 10 Cities With The Most Tacos Restaurants in The U.S.\n2. Search Tacos Restaurants By Cities")
                        line3=input("Choose your option (1 or 2): ")
                        if line3 == '1':
                            plot_top10()
                            break
                        elif line3 == '2':
                            city=input("Input the city (e.g Ann Arbor): ")
                            while True:
                                print("\n1. Output to csv file\n2. Plotly Map\n3. Compare with Yelp on Plotly Map\n4. Back")
                                line4=input("\nChoose output (1, 2, 3 or 4) : ")
                                db_places_dict=db_search(city)
                                if line4 == '1':
                                    output_csv(db_places_dict,False)
                                elif line4 == '2':
                                    db_places=[]
                                    for key, value in db_places_dict.items():
                                        db_places.append(Place(key,value['lat'],value['lon'],value['url']))
                                    plot_results(db_places)
                                elif line4 == '3':
                                    results=yelp_search("tacos", city)['businesses']
                                    yelp_places=[]
                                    for data in results:
                                        name=data['name']
                                        lat=data['coordinates']['latitude']
                                        lon=data['coordinates']['longitude']
                                        url=data['url']
                                        yelp_places.append(Place(name,lat,lon,url))
                                    
                                    plot_compare(yelp_places,db_places_dict)
                                elif line4 == '4':
                                    break
                                else:
                                    print("\nInvalid Input!")
                                
                            break
                        else:
                            print("\nInvalid Input!")
                    break
                else:
                    # Invalid Input
                    print("\nInvalid Input!")
        elif line1 == '2':
            print('\nBYE!')
            break
        else:
            print("\nInvalid Input!")