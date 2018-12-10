from final_project import *
import unittest


class TestDatabase(unittest.TestCase):
    # test create Table Cities
    def test_cities_table(self):
        conn = sqlite.connect(DBNAME)
        cur = conn.cursor()

        sql = 'SELECT city FROM Cities'
        results = cur.execute(sql)
        result_list = results.fetchall()
        self.assertIn(('Ann Arbor',), result_list)
        self.assertIn(('Cleveland',), result_list)
        self.assertIn(('New York',), result_list)
    
    # test create Table Restaurants
    def test_restaurants_table(self):
        conn = sqlite.connect(DBNAME)
        cur = conn.cursor()

        sql = 'SELECT Name FROM Restaurants'
        results = cur.execute(sql)
        result_list = results.fetchall()
        self.assertIn(('Subway',), result_list)
        self.assertIn(('METRO',), result_list)
        self.assertIn(('Taco Bell',), result_list)
        self.assertGreater(len(result_list),10000)

    def test_db_search(self):
        results=db_search("Ann Arbor")
        self.assertTrue('Lena' in results.keys())
        self.assertTrue('Umi Sushi' in results.keys())

        results=db_search('New York')
        self.assertTrue('Taco Mix' in results.keys())
        self.assertTrue('Sachi' in results.keys())

    

    # test plot functions
    class TestMapping(unittest.TestCase):
        data1 = yelp_search('pizza','Ann Arbor')['businesses']
        places=[]
        for data in data1:
            name=data['name']
            lat=data['coordinates']['latitude']
            lon=data['coordinates']['longitude']
            url=data['url']
            places.append(Place(name,lat,lon,url))
        
        db_places_dict=db_search('Ann Arbor')
        db_places=[]
        for key, value in db_places_dict.items():
            db_places.append(Place(key,value['lat'],value['lon'],value['url']))


        def test_plot_top10(self):
            try:
                plot_top10()
            except:
                self.fail()
        
        def test_plot_results(self):
            try:
                plot_results(db_places)
            except:
                self.fail()
        
        def test_plot_compare(self):
            try:
                plot_compare(yelp_places,db_places_dict)
            except:
                self.fail()

class TestYelpSearch(unittest.TestCase):
    def test_scrape_reviews(self):
        results=scrape_review('https://www.yelp.com/biz/neopapalis-ann-arbor?adjust_creative=ziguwByJV8X440VdHu1QZw&utm_campaign=yelp_api_v3&utm_medium=api_v3_business_search&utm_source=ziguwByJV8X440VdHu1QZw')
        correct="\n            “The north beach bianca pizza is to die for, and the sweet potato fries are unlike any you've ever had before!” in 33 reviews\n"
        self.assertIn(correct,results)
        results=scrape_review('https://www.yelp.com/biz/anthonys-gourmet-pizza-ann-arbor-3?adjust_creative=ziguwByJV8X440VdHu1QZw&utm_campaign=yelp_api_v3&utm_medium=api_v3_business_search&utm_source=ziguwByJV8X440VdHu1QZw')
        correct='\n            “Chicago style stuffed is definitely the way to go in terms of pie, but they do have other things like sandwiches and gyros and such.” in 6 reviews\n'
        self.assertIn(correct,results)

    def test_yelp_search(self):
        results=yelp_search('pizza','New York')['businesses']
        self.assertEqual("Lombardi's Pizza",results[2]['name'])
        self.assertEqual("Juliana's Pizza",results[0]['name'])
        self.assertEqual("Mama Rosa's Brick Oven Pizzaria Restaurant",results[16]['name'])
    


class TestCSVOutput(unittest.TestCase):
    def test_csv_list(self):
        output_csv(yelp_search('pizza','Ann Arbor')['businesses'],True)
        with open('results.csv','r') as csv_file:
            reader=csv.reader(csv_file)
            r= list(reader)
            self.assertGreater(len(r),20)
            csv_file.close()

    

    def test_csv_dict(self):
        output_csv(db_search("Ann Arbor"),False)
        with open('results.csv','r') as csv_file:
            reader=csv.reader(csv_file)
            r= list(reader)
            self.assertGreater(len(r),14)
            csv_file.close()




if __name__=='__main__':
    unittest.main()