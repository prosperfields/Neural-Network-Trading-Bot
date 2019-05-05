from nameko.rpc import rpc, RpcProxy
from nameko.timer import timer
from keras.models import Sequential
from keras.layers import Dense
from keras import regularizers
from keras import optimizers
from keras.utils import to_categorical
import numpy as np
from sklearn.model_selection import train_test_split
import datetime


class Trainer: 
    name = 'trainer_service'
    
    y = RpcProxy('data_service')
    y_change_threshold = .001
    decimal_num = 10

    def get_model(self):
        """  
        Make up of the neural network. A LSTM may actually work better than a ReLu activation layer and two Softmax layers. Future work.
        """

        y = RpcProxy('data_service')   
        model = Sequential()

        model.add(Dense(units=16,activation='relu',input_shape=(4,)))

        model.add(Dense(units=16, activation='softmax', kernel_regularizer=regularizers.l2(0.001), activity_regularizer=regularizers.l1(0.001)))
        model.add(Dense(units=3, activation='softmax'))

        sgd = optimizers.SGD(lr=0.0001)

        model.compile(loss='categorical_crossentropy', optimizer=sgd, metrics=['accuracy'])

        return model
    
    week = 60*60*24*7

    @timer(interval=10)
    def retrain(self):
        """
        You can train this model for any instrument, number of variables (price ratios of the candles), and time period through the timer.
        """

        # get historical data from data service
        candles = self.y.get_historical_data()['candles']
        X, Y = self.process(candles, type='train')

        X_train, X_test, Y_train, Y_test = train_test_split(X, Y, test_size=0.20, random_state=2)

        model = self.get_model()
        fit = model.fit(X_train, Y_train, epochs=100, verbose=True)
        score = model.evaluate(X_test, Y_test, batch_size=128)
        print(score)
        print(model.summary())

        filename = datetime.datetime.now().strftime("""%Y-%m-%d-%H-%M-%S""")#Saves as current time and date
        model.save(filename + '-AUS_USD_H1')

    @rpc
    def process(self, candles, type='train'):
        """
        processing candles to a format/shape consumable for the model
        """

        if type=='train':
            X = np.ndarray(shape=(0, 4))
            Y = np.ndarray(shape=(0, 1))

            #Process Data (hence the name of the function) 
            previous_close = None
            for candle in candles:
                candle = candle['mid']

                candle['o'] = float(candle['o'])
                candle['h'] = float(candle['h'])
                candle['l'] = float(candle['l'])
                candle['c'] = float(candle['c'])

                X = np.append(X,
                              np.array([[
                                  # H2O
                                  round(candle['h'] / candle['o'] - 1, self.decimal_num),
                                  # L2O
                                  round(candle['l'] / candle['o'] - 1, self.decimal_num),
                                  # H2O
                                  round(candle['c'] / candle['o'] - 1, self.decimal_num),
                                  # H2O
                                  round(candle['h'] / candle['l'] - 1, self.decimal_num)]]),
                              axis=0)

                # Compute the Y / Target Variable -- VALUES ARE FROM 0-1 
                if previous_close is not None:
                    y = 0
                    precise_prediction = round(1 - previous_close / candle['c'], self.decimal_num)

                    # Determines if price will stay the grow
                    if precise_prediction > self.y_change_threshold:
                        y = 1
                    # Determines if price will stay the decrease
                    elif precise_prediction < 0 - self.y_change_threshold:
                        y = 2
                    # Determines if price will stay the same or grow
                    elif precise_prediction < self.y_change_threshold and precise_prediction > 0 - self.y_change_threshold:
                        y = 0

                    Y = np.append(Y, np.array([[y]]))
                else:
                    Y = np.append(Y, np.array([[0]]))

                previous_close = candle['c']

            Y = np.delete(Y, 0)
            Y = np.append(Y, np.array([0]))
            Y = to_categorical(Y, num_classes=3)

            return X, Y
        elif type == 'predict':
            print('prediction')
            print(candles)
            X = np.ndarray(shape=(0, 4))

            # clean and process data
            candles['o'] = float(candles['o'])
            candles['h'] = float(candles['h'])
            candles['l'] = float(candles['l'])
            candles['c'] = float(candles['c'])

            X = np.append(X,
                          np.array([[
                              # High 2 Open Price
                            # H2O
                            round(candle['h'] / candle['o'] - 1, self.decimal_num),
                            # L2O
                            round(candle['l'] / candle['o'] - 1, self.decimal_num),
                            # H2O
                            round(candle['c'] / candle['o'] - 1, self.decimal_num),
                            # H2O
                            round(candle['h'] / candle['l'] - 1, self.decimal_num)]]))
        return X

        
