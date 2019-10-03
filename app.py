# -*- coding: utf-8 -*-
import dash
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objs as go
import psycopg2
import http.server
import socketserver
from plotly.subplots import make_subplots
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
    select c.mes, SUM(qtd.total) 
    from dw.ft_qtdlivrosemprestados qtd
    inner join dw.dim_calendario c on c.sk_dim_calendario = qtd.sk_dim_calendario
    where c.mes <> 9
    group by c.mes
    order by 1
''')

resultadoX = [] 
resultadoY = []

for i in resultado:
    resultadoX.append(i[0])
    resultadoY.append(i[1])

resultadoLivro = consulta('''
    select l.sk_dim_livro, l.nome_titulo, sum(qtd.total)
    from dw.ft_qtdlivrosemprestados qtd
    inner join dw.dim_calendario c on c.sk_dim_calendario = qtd.sk_dim_calendario
    inner join dw.dim_livro l on l.sk_dim_livro = qtd.sk_dim_livro
    where c.mes <> 9	
    group by l.sk_dim_livro, l.nome_titulo
    order by 3 desc
    limit 10
''')

resultadoLivroLabels = []
resultadoLivroValues = []
for i in resultadoLivro:
    resultadoLivroValues.append(i[2])
    resultadoLivroLabels.append(i[1])

resultadoAreaTurma  = consulta('''
    select t.nomearea, c.mes, SUM(qtd.total) 
    from dw.ft_qtdlivrosemprestados qtd
    inner join dw.dim_calendario c on c.sk_dim_calendario = qtd.sk_dim_calendario
    inner join dw.dim_areaturma t on t.sk_dim_areaturma = qtd.sk_dim_areaturma
    where c.mes <> 9
    group by c.mes, t.nomearea
    order by 2
''')

resultadoAreas = []
resultadoATGrafico = []
for w in resultadoAreaTurma:
    resultadoATGrafico.append({'x':[int(w[1])], 'y': [int(w[2])], 'type':'bar', 'name':str(w[0])})
    l = True
    for index, a in enumerate(resultadoAreas):
        print(index)
        print(a['name'])
        if a['name'] == w[0]:
            l = False
            a['x'].append(int(w[1]))
            a['y'].append(int(w[2]))
    if l:
        resultadoAreas.append({'x':[int(w[1])], 'y': [int(w[2])], 'type':'bar', 'name':str(w[0])})

graficos = []
for i in resultadoLivro:
    graficos.append({'x': [int(i[2])], 'y': [int(i[2])], 'type': 'domain', 'name': i[1]})

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

app.layout = html.Div(children=[
    html.H1(style={'text-align':'center'},children='BI InfoTeca'),

    html.Div(children='''

    '''),

    dcc.Graph(
        id='graph-qtd-mes',
        figure={
            'data': [
                {'x': resultadoX, 'y': resultadoY, 'type': 'bar', 'name': 'Qtd'},
            ],
            'layout': {
                'title': 'Quantidade de empréstimo por mês',
            }
        },
        style={
            'width': '35%',
            'display': 'inline-block'
        }
    ),
    dcc.Graph(
        id='graph-qtd-mes-por-area',
        figure={
            'data': resultadoAreas,
            'layout': {
                'title': 'Quantidade de empréstimo por mês e turma',
            }
        },
        style={
            'width': '60%',
            'display': 'inline-block'
        }
    ),
    dcc.Graph(
        id='graph-qtd-livro',
        figure={
            'data': [go.Pie(labels=resultadoLivroLabels, values=resultadoLivroValues)],
            'layout':{
                'title': 'Quantidade de livros emprestados no ano'
            }
        }
    ),
])
          
if __name__ == '__main__':
    app.run_server(host='0.0.0.0', port=8080)
