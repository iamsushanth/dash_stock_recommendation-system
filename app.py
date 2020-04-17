import dash
import yfinance as yf
import pandas as pd
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output
import dash_core_components as dcc
import dash_html_components as html
from datetime import datetime 
from datetime import timedelta

import model



external_stylesheets=[dbc.themes.BOOTSTRAP]

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)


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
                        {'label': 'Amazon', 'value': 'AMZN'},
                    ],
                    value='GOOGL',
                ),
            ]
        ),
    ],
    body=True,
)

app.layout = dbc.Container(
    [
        html.H1("Stock Recomandation System"),
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
    data = yf.download(selected_dropdown_value, start=datetime(2008, 5, 5), end=datetime.now())
    dff = pd.DataFrame(data)
    
    df = model.moving_avg(dff)
    
    dt, dd, reg, knn, by, a, b, c = model.make_predictions(dff)
    

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
            'y': reg,
            'name': 'Regression',
            
        },
        {
            'x': dff.index,
            'y': knn,
            'name': 'KNN',
            

        },
        {
            'x': dff.index,
            'y': by,
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




if __name__ == '__main__':
    app.run_server()
