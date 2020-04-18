import tweepy
import math
import nltk
import numpy as np
from pandas import Series, DataFrame
from pandas.plotting import scatter_matrix
from sklearn import preprocessing
from sklearn.linear_model import LinearRegression, BayesianRidge
from sklearn.neighbors import KNeighborsRegressor
from sklearn.preprocessing import PolynomialFeatures
from sklearn.pipeline import make_pipeline
from sklearn.model_selection import train_test_split

from datetime import datetime 
from datetime import timedelta
from textblob import TextBlob



def moving_avg(df):
    df = df[['Open', 'High', 'Low', 'Close', 'Volume']]
    df['HighLoad'] = (df['High'] - df['Close']) / df['Close'] * 100.0
    df['Change'] = (df['Close'] - df['Open']) / df['Open'] * 100.0

    df = df[['Close', 'HighLoad', 'Change', 'Volume']]

    df['MA10'] = df['Close'].rolling(10).mean()
    df['MA30'] = df['Close'].rolling(30).mean()
    df['MA50'] = df['Close'].rolling(50).mean()

    df['rets'] = df['Close'] / df['Close'].shift(1) - 1

    return df



def make_predictions(df):

    df['HL_PCT'] = (df['High'] - df['Low']) / df['Close'] * 100.0
    df['PCT_change'] = (df['Close'] - df['Open']) / df['Open'] * 100.0

    # Drop missing value
    df.fillna(value=-99999, inplace=True)
    # We want to separate 1 percent of the data to forecast
    forecast_out = int(math.ceil(0.01 * len(df)))
    # Separating the label here, we want to predict the AdjClose
    forecast_col = 'Adj Close'
    df['label'] = df[forecast_col].shift(-forecast_out)
    X = np.array(df.drop(['label'], 1))
    # Scale the X so that everyone can have the same distribution for linear regression
    X = preprocessing.scale(X)
    # Finally We want to find Data Series of late X and early X (train) for model generation and evaluation
    X_forecast = X[-forecast_out:]
    X = X[:-forecast_out]
    # Separate label and identify it as y
    y = np.array(df['label'])
    y = y[:-forecast_out]
    
    #Split data
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=0)

    
    # Linear regression
    model = LinearRegression(n_jobs=-1)
    model.fit(X_train, y_train)


    # KNN Regression
    model_knn = KNeighborsRegressor(n_neighbors=2)
    model_knn.fit(X_train, y_train)


    # Bayesian Ridge Regression
    model_by = BayesianRidge()
    model_by.fit(X_train, y_train)
    


    #Create confindence scores
    confidencereg = model.score(X_test, y_test)
    confidence_model_knn = model_knn.score(X_test,y_test)
    confidence_model_by = model_by.score(X_test,y_test)
    

    # # results
    # print('The linear regression confidence is:',confidencereg*100)
    # print('The quadratic regression 2 confidence is:',confidence_model_knn*100)
    # print('The quadratic regression 3 confidence is:',confidence_model_by*100)
    

    #Create new columns
    forecast_reg = model.predict(X_forecast)
    forecast_knn = model_knn.predict(X_forecast)
    forecast_by = model_by.predict(X_forecast)
    

    #Process all new columns data
    df['Forecast_reg'] = np.nan

    last_date = df.iloc[-1].name
    last_unix = last_date
    next_unix = last_unix + timedelta(days=1)

    for i in forecast_reg:
        next_date = next_unix
        next_unix += timedelta(days=1)
        df.loc[next_date] = [np.nan for _ in range(len(df.columns))]
        df['Forecast_reg'].loc[next_date] = i
        
    df['Forecast_knn'] = np.nan

    last_date = df.iloc[-26].name
    last_unix = last_date
    next_unix = last_unix + timedelta(days=1)
        
    for i in forecast_knn:
        next_date = next_unix
        next_unix += timedelta(days=1)
        df['Forecast_knn'].loc[next_date] = i

    df['forecast_by'] = np.nan

    last_date = df.iloc[-26].name
    last_unix = last_date
    next_unix = last_unix + timedelta(days=1)
        
    for i in forecast_by:
        next_date = next_unix
        next_unix += timedelta(days=1)
        df['forecast_by'].loc[next_date] = i
        
    

    return df.index.format(formatter=lambda x: x.strftime('%Y-%m-%d')), df['Adj Close'].to_list(), df['Forecast_reg'].to_list(), df['Forecast_knn'].to_list(), df['forecast_by'].to_list(),confidencereg,confidence_model_knn,confidence_model_by


def retrieving_tweets_polarity(symbol):

    consumer_key= '9N4LhWmdtUZT0sbVpgbMyqEY5'
    consumer_secret= '89HtqbHBzmaD9YQSPO6hdU7PQHoMHRSF6NvwxlTCfsY0HZZtZ6'
    access_token='863387980492414976-6ljbFkaBtFMQv3RO8pwAcZGlkI3HXzP'
    access_token_secret='mkxCMzl3p9Eydhenw0iTyN0kKmgnXI8WyI813khmwDSfq'

    auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_token, access_token_secret)
    user = tweepy.API(auth)

    tweets = tweepy.Cursor(user.search, q=str(symbol), tweet_mode='extended', lang='en').items(100)

    tweet_list = []
    global_polarity = 0
    for tweet in tweets:
        tw = tweet.full_text
        blob = TextBlob(tw)
        polarity = 0
        for sentence in blob.sentences:
            polarity += sentence.sentiment.polarity
            global_polarity += sentence.sentiment.polarity
        tweet_list.append(tw)

    global_polarity = global_polarity / len(tweet_list)
    return global_polarity


