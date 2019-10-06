# -*- coding: utf-8 -*-
import dash
import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objs as go
import psycopg2
import http.server
import socketserver
from plotly.subplots import make_subplots
from dash.dependencies import Input, Output
def consulta(sql):
    try:
        connection = psycopg2.connect(user = "tad",
                                    password = "tad",
                                    host = "postgres",
                                    port = "5432",
                                    database = "bi_infoteca")
        cursor = connection.cursor()
        # Print PostgreSQL Connection properties
        print ( connection.get_dsn_parameters(),"\n")
        # Print PostgreSQL version
        cursor.execute(sql)
        record = cursor.fetchall()
    except (Exception, psycopg2.Error) as error :
        print ("Error while connecting to PostgreSQL", error)
    finally:
        #closing database connection.
        if(connection):
            cursor.close()
            connection.close()
            print("PostgreSQL connection is closed")
        return record

# Quantidade de livros emprestado por mês
resultado = consulta('''
    select c.mes_nome, SUM(qtd.total) 
    from dw.ft_qtdlivrosemprestados qtd
    inner join dw.dim_calendario c on c.sk_dim_calendario = qtd.sk_dim_calendario
    where c.mes <> 9
    group by c.mes, c.mes_nome
    order by c.mes
''')

resultadoX = [] 
resultadoY = []

for i in resultado:
    resultadoX.append(i[0])
    resultadoY.append(i[1])

def consultarLivros(mes, area):
    resultadoLivroLabelsInside = []
    resultadoLivroValuesInside = []
    resultadoLivro = consulta('''
        select l.sk_dim_livro, l.nome_titulo, sum(qtd.total)
        from dw.ft_qtdlivrosemprestados qtd
        inner join dw.dim_calendario c on c.sk_dim_calendario = qtd.sk_dim_calendario
        inner join dw.dim_livro l on l.sk_dim_livro = qtd.sk_dim_livro
        inner join dw.dim_areaturma a on a.sk_dim_areaturma = qtd.sk_dim_areaturma
        where c.mes <> 9
        and (c.mes_nome = '%s' or '%s' = '')
        and (trim(a.siglaarea) = '%s' or '%s' = '')
        group by l.sk_dim_livro, l.nome_titulo
        order by 3 desc
        limit 10
    ''' % (mes, mes, area, area))
    for i in resultadoLivro:
        resultadoLivroValuesInside.append(i[2])
        resultadoLivroLabelsInside.append((i[1][:78] + '...') if len(i[1]) > 75 else i[1])
    return [resultadoLivroLabelsInside, resultadoLivroValuesInside]

resultadoConsultaLivro = consultarLivros("","")
resultadoLivroLabels = resultadoConsultaLivro[0]
resultadoLivroValues = resultadoConsultaLivro[1]


resultadoAreaTurma  = consulta('''
    select t.nomearea, c.mes_nome, SUM(qtd.total), t.siglaarea
    from dw.ft_qtdlivrosemprestados qtd
    inner join dw.dim_calendario c on c.sk_dim_calendario = qtd.sk_dim_calendario
    inner join dw.dim_areaturma t on t.sk_dim_areaturma = qtd.sk_dim_areaturma
    where c.mes <> 9
    group by c.mes, c.mes_nome, t.nomearea, t.siglaarea
    order by c.mes
''')

resultadoAreas = []
resultadoATGrafico = []
for w in resultadoAreaTurma:
    resultadoATGrafico.append({'x':[w[1]], 'y': [int(w[2])], 'type':'bar', 'name':str(w[0])})
    l = True
    for index, a in enumerate(resultadoAreas):
        if a['name'] == w[0]:
            l = False
            a['x'].append(w[1])
            a['y'].append(int(w[2]))
    if l:
        resultadoAreas.append({'x':[w[1]], 'y': [int(w[2])], 'type':'bar', 'name':str(w[0]), 'sigla': str(w[3])})

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

app.layout = html.Div(children=[
    html.H1(style={'text-align':'center'},children='BI InfoTeca'),
    html.Div([
        dcc.Dropdown(
            id="dropdown-ano",
            options=[
                {'label': '2019', 'value': '2019'}
            ],
            value='2019',
            style={
                'display': 'none'
            }
        ),
        dcc.Dropdown(
            id="dropdown-mes",
            options=[
                {'label': 'Janeiro', 'value': 'Janeiro'},
                {'label': 'Fevereiro', 'value': 'Fevereiro'},
                {'label': 'Março', 'value':'Março'},
                {'label': 'Abril', 'value': 'Abril'},
                {'label': 'Maio', 'value': 'Maio'},
                {'label': 'Junho', 'value':'Junho'},
                {'label': 'Julho', 'value': 'Julho'},
                {'label': 'Agosto', 'value': 'Agosto'},
                {'label': 'Setembro', 'value':'Setembro'},
                {'label': 'Outubro', 'value': 'Outubro'},
                {'label': 'Novembro', 'value': 'Novembro'},
                {'label': 'Dezembro', 'value':'Dezembro'},
            ],
            value='Janeiro',
            style={
                'display': 'none'
            }
        ),
    ]),
    dbc.Row([
        dbc.Col([
            dcc.Graph(
                id='graph-qtd-mes',
                figure={
                    'data': [
                        {'x': resultadoX, 'y': resultadoY, 'type': 'bar', 'name': 'Qtd'},
                    ],
                    'layout': {
                        'title': 'Quantidade de empréstimo por mês em 2019',
                    }
                }
            )
        ], md=5),
        dbc.Col([
            dcc.Graph(
                id='graph-qtd-mes-por-area',
                figure={
                    'data': resultadoAreas,
                    'layout': {
                        'title': 'Quantidade de empréstimo por mês e área',
                    }
                },
            ),
        ], md=7,id='col-graph-qtd-mes-por-area')
    ]),
    dbc.Row([
        dbc.Col([
            dcc.Graph(
                id='graph-qtd-livro',
                figure={
                    'data': [go.Pie(labels=resultadoLivroLabels, values=resultadoLivroValues)],
                    'layout':{
                        'title': 'Quantidade de empréstimo por livro no ano de 2019'
                    }
                }
            )
        ], md=12, id="col-graph-qtd-livro")
    ])
    ,
])
          
@app.callback(
    [Output("col-graph-qtd-mes-por-area", "children"),
     Output("dropdown-mes", "value")
    ],
    [Input("graph-qtd-mes", "clickData")]
)
def criarGraphQtdMesPorArea(click):
    grafico = []
    if click != None:
        clickX = click["points"][0]["x"].encode('utf-8', 'replace')
        for i in resultadoAreas:
            ind = 0
            for val in i["x"]:
                if(val[0:3] == clickX[0:3]):
                    grafico.append({'x':[i["sigla"]], 'y': [i["y"][ind]], 'type':'bar', 'name':str(i["name"]), 'label': str(val)})
                ind+=1
        for t in range(0,len(grafico)):
            for w in range(0, len(grafico)):
                if(grafico[t]["name"][0:3] < grafico[w-1]["name"][0:3]):
                    grafico[t],grafico[w-1] = grafico[w-1],grafico[t]
        return [
            dcc.Graph(
                id='graph-qtd-mes-por-area',
                figure={
                    'data': grafico,
                    'layout': {
                        'title': 'Quantidade de empréstimo por área no mês de ' + clickX
                    }
                }
            ),
        ], clickX
    else:
        return [
            dcc.Graph(
                id='graph-qtd-mes-por-area',
                figure={
                    'data': resultadoAreas,
                    'layout': {
                        'title': 'Quantidade de empréstimo por mês e área',
                    }
                },
            ),
        ], "Janeiro"

@app.callback(
    Output("col-graph-qtd-livro", "children"),[
    Input("graph-qtd-mes-por-area", "clickData"),
    Input("dropdown-mes", "value")
    ]
)
def criarGraphQtdMesPorLivro(click, mes):
    mes = mes.encode("utf-8", "replace")
    if(click != None):
        if(len(click["points"]) > 1):
            clickX = click["points"][0]["x"].encode("utf-8", "replace")
            mes = clickX
            resultadoConsultaLivro = consultarLivros(clickX,"")
            resultadoLivroLabels = resultadoConsultaLivro[0]
            resultadoLivroValues = resultadoConsultaLivro[1]
            return [dcc.Graph(
                    id='graph-qtd-livro',
                    figure={
                        'data': [go.Pie(labels=resultadoLivroLabels, values=resultadoLivroValues)],
                        'layout':{
                            'title': 'Quantidade de empréstimo por livro no ano de 2019 no mês de '+ mes 
                        }
                    }
                )
            ]
        else:
            clickX = click["points"][0]["x"].encode("utf-8", "replace")
            resultadoConsultaLivro = consultarLivros(mes,clickX)
            resultadoLivroLabels = resultadoConsultaLivro[0]
            resultadoLivroValues = resultadoConsultaLivro[1]
            return [dcc.Graph(
                    id='graph-qtd-livro',
                    figure={
                        'data': [go.Pie(labels=resultadoLivroLabels, values=resultadoLivroValues)],
                        'layout':{
                            'title': 'Quantidade de empréstimo por livro no ano de 2019 no mês de '+ mes +' pela área '+ clickX
                        }
                    }
                )
            ]
    else:
        resultadoConsultaLivro = consultarLivros(mes,"")
        resultadoLivroLabels = resultadoConsultaLivro[0]
        resultadoLivroValues = resultadoConsultaLivro[1]
        return [dcc.Graph(
                id='graph-qtd-livro',
                figure={
                    'data': [go.Pie(labels=resultadoLivroLabels, values=resultadoLivroValues)],
                    'layout':{
                        'title': 'Quantidade de empréstimo por livro no ano de 2019 no mês de '+ mes
                    }
                }
            )
        ]
if __name__ == '__main__':
    app.run_server(host='0.0.0.0', port=8080)
