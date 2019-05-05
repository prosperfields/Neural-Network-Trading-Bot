from nameko.rpc import rpc
from nameko.timer import timer

from oandapyV20 import API    # the client
import oandapyV20.endpoints.pricing as pricing
import oandapyV20.endpoints.instruments as instruments

from pymongo import MongoClient

mongoclient = MongoClient('127.0.0.1')
db = mongoclient['historical_data']


#Access granted
access_token = "70b8616dce917e9b71174eba5461bc67-defd77f09ef6c6c72520b3d3b6bd23ca"
accountID = "101-001-11053079-001"
client = API(access_token=access_token, environment="practice")
#Access granted

GRANULARITY = 'H1'#Type of Candle
INSTRUMENT = 'AUD_USD' #Type of Instrument


class Data:
    name = "data_service"

    hour= 60*60
    @timer(interval=10)
    def get_ohlc(self):
        #Get Data
        
        params ={'granularity': GRANULARITY,'count': 2 #Use 2 count to get the earlier candle (because candle[1] is currently still incomplete)
        }
        
        newest_candle = instruments.InstrumentsCandles(INSTRUMENT, params=params)
        newest_candle = client.request(newest_candle)
        current_timestamp= newest_candle['candles'][0]['time']
        collection = db['streaming_data'] #database for new candles

        
        double_finder = collection.find_one({'candles.0.time': current_timestamp}) 


        if double_finder != None:#Don't save duplicates
            return False
        #Save to MongoDB

        collection.insert_one(newest_candle)#since not double, insert

      

    @rpc
    def get_historical_data(self, instrument=INSTRUMENT, granularity=GRANULARITY, count=5000):#Api call limit is 5000
        
        ##Getting the data from Oanda. USE "conda activate myenv" because of python 3.7 compatability issue
        
        
        params ={'granularity': GRANULARITY,'count': count
        }
          
        hist_data = instruments.InstrumentsCandles(instrument, params)
        hist_data = client.request(hist_data)
          
        #Save to MongoDB
        collection = db['historical_ohlc']
        collection.insert_one(hist_data)
        del hist_data['_id']

        return hist_data

