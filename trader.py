from nameko.rpc import rpc, RpcProxy
from nameko.timer import timer
# import oandaapi
from keras.models import load_model
import numpy as np
from pymongo import MongoClient

pyclient = MongoClient()
db = pyclient['historical_data']


class Trader:
    """
    Gets data and predicts. 
    """
    name = "trader_service"
    y = RpcProxy("trainer_service")

    @timer(interval=10)
    def predict(self):
        """
        :return: Read Data from MongoDB. Apply ML Model on Data
        """
        decimal_num = 6

        # read data from MongoDB
        collection = db['historical_ohlc']
        newest_candle = collection.find() \
            .sort([('candles.0.time', -1)]) \
            .limit(1)

        for nc in newest_candle:
            newest_candle = nc['candles'][0]['mid']

        # get processed X
        X = np.ndarray(shape=(0, 4))

        # Process data in the same way we processed it in trainer. 
        newest_candle['o'] = float(newest_candle['o'])
        newest_candle['h'] = float(newest_candle['h'])
        newest_candle['l'] = float(newest_candle['l'])
        newest_candle['c'] = float(newest_candle['c'])
        
        X = np.append(X,
                      np.array([[
                          # H2L
                          round(newest_candle['h'] / newest_candle['o'] - 1, decimal_num),
                          # L2O
                          round(newest_candle['l'] / newest_candle['o'] - 1, decimal_num),
                          # C2O
                          round(newest_candle['c'] / newest_candle['o'] - 1, decimal_num),
                          # H2L
                          round(newest_candle['h'] / newest_candle['l'] - 1, decimal_num)]]),
                      axis=0)

        print(X)

        model = load_model('2019-05-04-19-51-08-AUS_USD_H1')
        Y = model.predict(X)
        print(Y)
