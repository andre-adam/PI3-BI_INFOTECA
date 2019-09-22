# -*- coding: utf-8 -*-
import dash
import dash_core_components as dcc
import dash_html_components as html
import psycopg2
import http.server
import socketserver


external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

app.layout = html.Div(children=[
    html.H1(children='Hello Dash'),

    html.Div(children='''
        TEste
    '''),

    dcc.Graph(
        id='example-graph',
        figure={
            'data': [
                {'x': [3,2,3], 'y': [5,3,1], 'type': 'bar', 'name': 'Wenner'},
                {'x': [1, 2, 3], 'y': [2, 4, 5], 'type': 'bar', 'name': u'Montréal'},
            ],
            'layout': {
                'title': 'Wenner'
            }
        }
    )
])

if __name__ == '__main__':
    app.run_server(debug=True,host='0.0.0.0', port=8080)
