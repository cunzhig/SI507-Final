# SI507-Final

## Data Source
  * Yelp Fushion API (business search): https://www.yelp.com/developers/documentation/v3/business_search
  
  * tacos.csv (Restaurant that sell burritos and tacos in the U.S.): https://data.world/datafiniti/restaurants-burritos-and-tacos


## Code Structure
### Create tacos restaurants database
     
    create_tacos_db() - Create tacos.sqlite
    populate_tacos_db() - Create Table Restaurants and Cities from tacos.csv
  
### Seacrh by Yelp API either by requests or CACHE (cache.json)
 
    yelp_search(term, location) - Pass queries to make_request_using_cache()
    make_request_using_cache() - Return requests results or cache
     
### Search by database tacos.sqlite according to the city input 
     
     db_search(city) - Pass city input to sqlite to search results from db
 
 
## User guide
run py file: final_project.py

>Search  
>>1.Yelp API  
>>>a. Output to csv file  
>>>b. Output to plotly map  
>>>c. Read Top Reviews from Yelp web page  

>>2.Tacos DB
>>>i. Plot Top 10 cities with the most tacos restaurants (U.S.) in plotly bar charts  
>>>ii.Choose city in the U.S.  
>>>>a. Output to csv file  
>>>>b. Output to plotly map  
>>>>c. Compare with Yelp results on plotly map  

>Exit
