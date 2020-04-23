import base64
import os
import sys
sys.path.insert(0, os.path.realpath(os.path.dirname(__file__)))
os.chdir(os.path.realpath(os.path.dirname(__file__)))

import pandas as pd
from flask import Flask
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import dash_bootstrap_components as dbc

from datetime import datetime 
from datetime import timedelta
import urllib3, shutil
import model


UPLOAD_DIRECTORY = "../dash/data"

if not os.path.exists(UPLOAD_DIRECTORY):
    os.makedirs(UPLOAD_DIRECTORY)


external_stylesheets=[dbc.themes.BOOTSTRAP]

# Normally, Dash creates its own Flask server internally. By creating our own,
# we can create a route for downloading files directly:
server = Flask(__name__)
app = dash.Dash(server=server, external_stylesheets=external_stylesheets)

controls = dbc.Card(
    [
        dbc.FormGroup(
            [
                dbc.Label("Select Stock"),
                dcc.Dropdown(
                    id="my-dropdown",
                    options=[
                        {'label': 'Google', 'value': 'GOOGL'},
                        {'label': 'Coke', 'value': 'COKE'},
                        {'label': 'Tesla', 'value': 'TSLA'},
                        {'label': 'Apple', 'value': 'AAPL'},
            
                    ],
                    value='GOOGL',
                ),
                html.Br(),
                html.P(id="output"),
            ]
        ),
    ],
    body=True,
)

app.layout = dbc.Container(
    [
        html.H1("Stock Recomandation System", style={
            'textAlign': 'center'}),
        html.Hr(),
        dbc.Row(
            [
                dbc.Col(controls, md=4),
                
                dbc.Col(dcc.Graph(id="my-graph"), md=8),
            ],
            align="left",
        ),

        html.Div(id='my-div', style={
            'textAlign': 'center',
            'color':'red',
            'font':'16px',

        }),

    ],
    fluid=True,


)


@app.callback(Output('my-graph', 'figure'), [Input('my-dropdown', 'value')])
def get_data(selected_dropdown_value):


    date = datetime.today()
    ts = datetime.timestamp(date)
    start = int(ts)

    tss = datetime.today() - timedelta(days=3650)
    tss = datetime.timestamp(tss)
    end = int(tss)
    end

    url = 'https://query1.finance.yahoo.com/v7/finance/download/{}?period1={}&period2={}&interval=1d&events=history'.format(selected_dropdown_value,end,start)
    c = urllib3.PoolManager()
    filename = "../dash/data/{}.csv".format(selected_dropdown_value)


    with c.request('GET', url, preload_content=False) as res, open(filename, 'wb') as out_file:
        shutil.copyfileobj(res, out_file)

    data = pd.read_csv("../dash/data/{}.csv".format(selected_dropdown_value))



    #data = yf.download(selected_dropdown_value, start=datetime(2008, 5, 5), end=datetime.now())

    dff = pd.DataFrame(data)
    dfff = dff.set_index('Date')
    
    df = model.moving_avg(dfff)
    
    dff = model.make_predictions(dfff)
    
    
    

    return {
        'data': [{
            'x': df.index,
            'y': df['Close'],
            'name': 'Close'
        },
        {
            'x': df.index,
            'y': df['MA10'],
            'name': 'MA10'

        },
        {
            'x': df.index,
            'y': df['MA30'],
            'name': 'MA30'

        },
        {
            'x': df.index,
            'y': df['MA50'],
            'name': 'MA50'

        },
        {
            'x': df.index,
            'y': df['rets'],
            'name': 'Returns'

        },
        {
            'x': dff.index,
            'y': dff['Forecast_reg'],
            'name': 'Regression',
            
        },
        {
            'x': dff.index,
            'y': dff['Forecast_knn'],
            'name': 'KNN',
            

        },
        {
            'x': dff.index,
            'y': dff['forecast_by'],
            'name': 'Bayesian',
            

        }
        ],
        'layout': {'margin': {'l': 60, 'r': 60, 't': 30, 'b': 30},'title': 'Stock Data Visualization', 'align':'center'}
    }


@app.callback(
    Output(component_id='my-div', component_property='children'),
    [Input(component_id='my-dropdown', component_property='value')]
)
def sentiment(input_value):

    polarity = model.retrieving_tweets_polarity(input_value)

    if polarity > 0:
        return 'According to the predictions and twitter sentiment analysis -> Investing in "{}" is a GREAT idea!'.format(str(input_value))
    
    elif polarity < 0:
        return 'According to the predictions and twitter sentiment analysis -> Investing in "{}" is a BAD idea!'.format(str(input_value))
            
    return 'According to the predictions and twitter sentiment analysis -> Investing in "{}" is a BAD idea!'.format(str(input_value))






if __name__ == "__main__":
    app.run_server(debug=True, port=8888)