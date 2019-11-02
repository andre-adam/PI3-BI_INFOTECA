# -*- coding: utf-8 -*-
#TODO: Fazer os titulos dos grafícos sticky
import dash
import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objs as go
import psycopg2
import http.server
import socketserver
import time
from plotly.subplots import make_subplots
from dash.dependencies import Input, Output, State
from datetime import datetime as dt
FONT_AWESOME = "https://use.fontawesome.com/releases/v5.7.2/css/all.css"

def consulta(sql):
    try:
        connection = psycopg2.connect(user = "tad",
                                    password = "tad",
                                    host = "postgres",
                                    port = "5432",
                                    database = "bi_infoteca")
        cursor = connection.cursor()
        # Print PostgreSQL Connection properties
        # print ( connection.get_dsn_parameters(),"\n")
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
            #print("PostgreSQL connection is closed")
        return record

datainicial = consulta('''
    select to_char(min(c.data_dim), 'mm-dd-yyyy'), extract(year from min(c.data_dim)),extract(month from min(c.data_dim)),
    extract(day from min(c.data_dim)), to_char(min(c.data_dim), 'dd/mm/yyyy')
    from dw.dim_calendario c
''')
datainicialSa = datainicial[0][0]
datainicialFormat = datainicial[0][4]
dataIni = {"dia": int(datainicial[0][3]), "mes": int(datainicial[0][2]), "ano": int(datainicial[0][1])}
datainicial = "'"+datainicial[0][0]+"'"
datafinal = consulta('''
    select to_char(max(c.data_dim), 'mm-dd-yyyy'), extract(year from max(c.data_dim)),extract(month from max(c.data_dim)),
    extract(day from max(c.data_dim)), to_char(max(c.data_dim), 'dd/mm/yyyy')
    from dw.dim_calendario c
''')
datafinalSa = datafinal[0][0]
datafinalFormat = datafinal[0][4]
dataFim = {"dia": int(datafinal[0][3]), "mes": int(datafinal[0][2]), "ano": int(datafinal[0][1])}
datafinal = "'"+datafinal[0][0]+"'"

def getPeriodo(dataini, datafim):
    if dataini and datafim:
        return dataini + " a " + datafim
    elif dataini:
        return dataini + " a " + datafinalFormat
    else:
        return datainicialFormat+" a "+datafinalFormat
def consultarLivros(dataini, datafim, area, limit):
    resultadoLivroLabelsInside = []
    resultadoLivroValuesInside = []
    if(limit == None):
        limit = 10
    resultadoLivro = consulta('''
        select l.sk_dim_livro, l.nome_titulo, sum(qtd.total)
        from dw.ft_qtdlivrosemprestados qtd
        inner join dw.dim_calendario c on c.sk_dim_calendario = qtd.sk_dim_calendario
        inner join dw.dim_livro l on l.sk_dim_livro = qtd.sk_dim_livro
        inner join dw.dim_areaturma a on a.sk_dim_areaturma = qtd.sk_dim_areaturma
        where c.data_dim between %s and coalesce(%s, current_date)
        and (trim(a.siglaarea) = '%s' or '%s' = '')
        group by l.sk_dim_livro, l.nome_titulo
        order by 3 desc
        limit %d
    ''' % (dataini, datafim, area, area, limit))
    for i in resultadoLivro:
        resultadoLivroValuesInside.append(i[2])
        resultadoLivroLabelsInside.append((i[1][:78] + '...') if len(i[1]) > 75 else i[1])
    return [resultadoLivroLabelsInside, resultadoLivroValuesInside]
OptionsAreas=[]
resultadoAreasOptions = consulta('''
    select sk_dim_areaturma, nomearea, siglaarea
    from dw.dim_areaturma
''')
for oa in resultadoAreasOptions:
    OptionsAreas.append({'label': oa[1], 'value': oa[2]})

resultadoOptionsTurma = consulta(''' 
    select sigla, a.siglaarea
    from dw.dim_turma t
    inner join dw.dim_areaturma a on a.sk_dim_areaturma = t.sk_dim_areaturma
''')

def getOptionsTurma(area):
    options = []
    if area:
        for w in resultadoOptionsTurma:
            if w[1] == area:
                options.append({'label': w[0], 'value': w[0]})
    else:
        for i in resultadoOptionsTurma:
            options.append({'label': i[0], 'value': i[0]})
    return options

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP, FONT_AWESOME])

modalFiltro = html.Div(
    [   html.Span(
            [html.I(className="fa fa-filter")], 
            id="popover-target",
            style={
                'position': 'fixed',
                'marginLeft': '10px',
                'zIndex': '1',
                'fontSize': '30px',
                'cursor':'pointer',
                # 'marginTop': '60px',
                'transform': 'translateY(2em)'
            }
        ),
        dbc.Popover(
            [
                dbc.PopoverHeader("Filtros",
                    style={
                        "textAlign": "center",
                        'position': 'sticky',
                    }
                ),
                dbc.PopoverBody(
                    [dbc.FormGroup(
                    [dbc.Row([
                        dbc.Label("Curso", html_for="dropdown-area", width=3),
                        dbc.Col(
                            dcc.Dropdown(
                                id="dropdown-area",
                                options=OptionsAreas,
                                placeholder="Selecione um curso"
                            ),
                        id="col-dropdown-area",
                        width=9),
                    ], style={"width":"100%", "marginLeft": "0px"}),
                    dbc.Row([
                        dbc.Label("Turma", html_for="dropdown-turma", width=3),
                    dbc.Col(
                        dcc.Dropdown(
                            id="dropdown-turma",
                            options=getOptionsTurma(""),
                            placeholder="Selecione uma turma"
                        ),  
                    width=9),
                    ], style={"width":"100%", "marginLeft": "0px"}),
                    
                    dbc.Label("Data", html_for="my-date-picker", width=3),
                    dbc.Col(
                        dcc.DatePickerRange(
                            id='my-date-picker',
                            min_date_allowed=dt(dataIni["ano"], dataIni["mes"], dataIni["dia"]).strftime('%Y-%m-%d'),
                            max_date_allowed=dt(dataFim["ano"], dataFim["mes"], dataFim["dia"]).strftime('%Y-%m-%d'),
                            start_date=dt(dataIni["ano"], dataIni["mes"], dataIni["dia"]).strftime('%Y-%m-%d'),
                            # initial_visible_month=dt(dataIni["ano"], dataIni["mes"], dataIni["dia"]).strftime('%Y-%m-%d'),
                            display_format='DD/MM/YYYY',
                            start_date_placeholder_text='Data Inicial',
                            end_date_placeholder_text='Data Final'
                        ), width=9
                    ),
                    dbc.Col(
                        dbc.Button("Limpar",id="limparFiltro", color="info", className="mr-1"),
                        style={
                            'textAlign':'center',
                            'paddingTop': '10px',
                        }
                    )
                    ], row=True),
                ])],
                id="popover-filtro",
                is_open=False,
                target="popover-target",
                style={
                    "minWidth": "20em",
                }
        ),
        
    ]
)

PLOTLY_LOGO = "/assets/icone.png"

search_bar = dbc.Row(
    [
        # dbc.Col(dbc.Input(type="search", placeholder="Procurar")),
        # dbc.Col(
        #     dbc.Button("Procurar", color="primary", className="ml-2"),
        #     width="auto",
        # ),
    ],
    no_gutters=True,
    className="ml-auto flex-nowrap mt-3 mt-md-0",
    align="center",
)

navbar = dbc.Navbar(
    [
        html.A(
            # Use row and col to control vertical alignment of logo / brand
            dbc.Row(
                [
                    dbc.Col(html.Img(src=PLOTLY_LOGO, height="30px")),
                    dbc.Col(dbc.NavbarBrand("BI InfoTeca", className="ml-2")),
                ],
                align="center",
                no_gutters=True,
            ),
        ),
        dbc.NavbarToggler(id="navbar-toggler"),
        dbc.Collapse(search_bar, id="navbar-collapse", navbar=True),
    ],
    color="dark",
    dark=True,
)

def criarGrafico1(dataini, datafim):
    if dataini:
        dataini = "'"+dataini+"'"
    else:
        dataini = datainicial
    if datafim:
        datafim = "'"+datafim+"'"
    else:
        datafim = datafinal
    # Quantidade de livros emprestado por mês
    resultado = consulta('''
        select c.mes_nome, SUM(qtd.total) 
        from dw.ft_qtdlivrosemprestados qtd
        inner join dw.dim_calendario c on c.sk_dim_calendario = qtd.sk_dim_calendario
        where c.data_dim between %s and coalesce(%s, current_date)
        group by c.mes, c.mes_nome
        order by c.mes
    ''' % (dataini, datafim))

    resultadoX = [] 
    resultadoY = []

    for i in resultado:
        resultadoX.append(i[0])
        resultadoY.append(i[1])
    return [dcc.Graph(
            id='graph-qtd-mes',
            figure={
                'data': [
                    {'x': resultadoX, 'y': resultadoY, 'type': 'bar', 'name': 'Qtd'},
                ],
                'layout': {
                    'title': 'Quantidade de empréstimo por mês',
                }
            },
        )
    ]

def criarGrafico2(tipo, dataini, datafim):
    if dataini:
        dataini = "'"+dataini+"'"
    else:
        dataini = datainicial
    if datafim:
        datafim = "'"+str(datafim)+"'"
    else:
        datafim = datafinal
    resultadoAreaTurma  = consulta('''
        select t.nomearea, c.mes_nome, SUM(qtd.total), t.siglaarea
        from dw.ft_qtdlivrosemprestados qtd
        inner join dw.dim_calendario c on c.sk_dim_calendario = qtd.sk_dim_calendario
        inner join dw.dim_areaturma t on t.sk_dim_areaturma = qtd.sk_dim_areaturma
        where c.data_dim between %s and coalesce(%s, current_date)
        group by c.mes, c.mes_nome, t.nomearea, t.siglaarea
        order by c.mes
    ''' % (dataini, datafim))
    resultadoAreas = []
    resultadoATGrafico = {"labels": [], "values": [], "names": []}
    for w in resultadoAreaTurma:
        resultadoATGrafico["labels"].append(w[0])
        resultadoATGrafico["values"].append(int(w[2]))
        resultadoATGrafico["names"].append(w[3])
    resultadoAreas=[go.Pie(labels=resultadoATGrafico["labels"], values=resultadoATGrafico["values"], hovertext=resultadoATGrafico["names"])]
    return [
            dcc.Graph(
                id='graph-qtd-mes-por-area',
                figure={
                    'data': resultadoAreas,
                    'layout': {
                        'title': 'Quantidade de empréstimo por mês e curso',
                    }
                },
            ),
        ]

def criarGrafico3(dataini, datafim, area, titulo, limitRows):
    if dataini:
        dataini = "'"+dataini+"'"
    else:
        dataini = datainicial
    if datafim:
        datafim = "'"+str(datafim)+"'"
    else:
        datafim = datafinal
    if(limitRows == None):
        limitRows = 10
    resultadoConsultaLivro = consultarLivros(dataini, datafim, area, limitRows)
    resultadoLivroLabels = resultadoConsultaLivro[0]
    resultadoLivroValues = resultadoConsultaLivro[1]
    return [dcc.Graph(
            id='graph-qtd-livro',
            figure={
                'data': [go.Pie(labels=resultadoLivroLabels, values=resultadoLivroValues)],
                'layout':{
                    'title': 'Quantidade de empréstimo por livro '+ str(titulo),
                    'legend':{
                        # 'xanchor':"center",
                        # 'yanchor': "bottom",
                        # 'orientation': 'h',
                        # 'y': 1.8, # play with it
                        # 'x': -1.8,   # play with it
                        # 'margin':{'t':50,'l':150}
                    },
                }
            }
        )
    ]

def criarGrafico4(dataini, datafim, area, limit):
    if dataini:
        dataini = "'"+dataini+"'"
    else:
        dataini = datainicial
    if datafim:
        datafim = "'"+str(datafim)+"'"
    else:
        datafim = datafinal
    if not area:
        area = ''
    limit = int(limit)
    resultado = consulta('''
        select t.sigla, SUM(qtd.total)
        from dw.ft_qtdlivrosemprestados qtd
        inner join dw.dim_calendario c on c.sk_dim_calendario = qtd.sk_dim_calendario
        inner join dw.dim_turma t on t.sk_dim_turma = qtd.sk_dim_turma
        inner join dw.dim_areaturma a on a.sk_dim_areaturma = t.sk_dim_areaturma
        where c.data_dim between %s and coalesce(%s, current_date)
        and a.siglaarea = '%s'
        group by t.sigla
        order by 2, t.sigla
        limit %d
    ''' % (dataini, datafim, area, limit))
    resultadoTurmaLabels = []
    resultadoTurmaValues = []
    area = area.encode('utf-8', 'replace')
    for i in resultado:
        resultadoTurmaLabels.append(str(i[0]))
        resultadoTurmaValues.append(int(i[1]))
    if area != '':
        return [dcc.Graph(
                id='graph-qtd-turma',
                figure={
                    'data': [go.Pie(labels=resultadoTurmaLabels, values=resultadoTurmaValues)],
                    'layout':{
                        'title': 'Quantidade de empréstimo por turma do curso de ' + area,
                    },
                },
                style={
                    'display': 'block',
                }
            )
        ]
    else:
        return [
            dcc.Graph(
                id='graph-qtd-turma',
                style={"visibility":"hidden", "height": "0px"}
            )
        ]
    
def criarGrafico5(turma, dataini, datafim):
    if dataini:
        dataini = "'"+dataini+"'"
    else:
        dataini = datainicial
    if datafim:
        datafim = "'"+str(datafim)+"'"
    else:
        datafim = datafinal
    resultado = consulta('''
        select t.sigla, to_char(c.data_dim, 'dd/mm'), SUM(qtd.total)
        from dw.ft_qtdlivrosemprestados qtd
        inner join dw.dim_calendario c on c.sk_dim_calendario = qtd.sk_dim_calendario
        inner join dw.dim_turma t on t.sk_dim_turma = qtd.sk_dim_turma
        where c.data_dim between %s and coalesce(%s, current_date)
        and t.sigla = '%s'
        group by t.sigla, c.data_dim
        order by c.data_dim, t.sigla
    ''' % (dataini, datafim, turma))
    resultadoTurma = []
    resultadoTGrafico = []
    for w in resultado:
        resultadoTGrafico.append({'x':[w[1]], 'y': [int(w[2])], 'type':'scatter', 'name':str(w[0])})
        l = True
        for index, a in enumerate(resultadoTurma):
            if a['name'] == w[0]:
                l = False
                a['x'].append(w[1])
                a['y'].append(int(w[2]))
        if l:
            resultadoTurma.append({'x':[w[1]], 'y': [int(w[2])], 'type':'scatter', 'name':str(w[0]), 'sigla': str(w[0])})
    if len(resultado) > 0:
        return [dcc.Graph(
                id='graph-qtd-turma-dia',
                figure={
                    'data': resultadoTurma,
                    'layout': {
                        'title': 'Quantidade de empréstimo pela turma ' + str(turma) + ' por dia',
                        'xaxis':{
                            'title':'Data'
                        },
                        'yaxis': {
                            'title':'Qtd. Empréstimo'
                        }
                    },
                },style={
                    'width': '100%'
                }
            )
        ]
    else:
        return []

def criarGrafico6(curso, turma, dataini, datafim):
    if dataini:
        dataini = "'"+dataini+"'"
    else:
        dataini = datainicial
    if datafim:
        datafim = "'"+str(datafim)+"'"
    else:
        datafim = datafinal
    titulo = ""
    if curso:
        titulo += " curso de " + str(curso)
    if turma:
        titulo += " pela turma " + str(turma) 
    if not turma:
        turma = ''
    if not curso:
        curso = ''
    resultado = consulta('''
        select c.dia_semana, c.dia_semana_ini_nome, sum(qtd.total), c.dia_semana_nome
        from dw.ft_qtdlivrosemprestados qtd
        inner join dw.dim_calendario c on c.sk_dim_calendario = qtd.sk_dim_calendario
        inner join dw.dim_turma t on t.sk_dim_turma = qtd.sk_dim_turma
        inner join dw.dim_areaturma a on a.sk_dim_areaturma = qtd.sk_dim_areaturma
        where c.data_dim between {2} and coalesce({3}, current_date)
        and (t.sigla = '{1}' or '{1}' = '')
        and (a.siglaarea = '{0}' or '{0}' = '')
        group by c.dia_semana_ini_nome, c.dia_semana, c.dia_semana_nome
        order by c.dia_semana
    '''.format(curso, turma, dataini, datafim))
    resultadoFinal = []
    resultadoLGrafico = []
    resultadoDia = []    
    for w in resultado:
        resultadoLGrafico.append({'x':[w[1]], 'y': [int(w[2])], 'type':'bar', 'name':str(w[3])})
        l = True
        for index, a in enumerate(resultadoDia):
            if a['name'] == w[0]:
                l = False
                a['x'].append(w[1])
                a['y'].append(int(w[2]))
        if l:
            resultadoDia.append({'x':[w[1]], 'y': [int(w[2])], 'type':'bar', 'name':str(w[3])})
    resultadoFinal += resultadoDia
    return [dcc.Graph(
            id='graph-qtd-livro-dia',
            figure={
                'data': resultadoFinal,
                'layout': {
                    'title': 'Quantidade de empréstimo por dia da semana' + titulo,
                    'xaxis':{
                        'title':'Dia da semana'
                    },
                    'yaxis': {
                        'title':'Qtd. Empréstimo'
                    }
                },
            },style={
                'width': '100%'
            }
        )
    ]
    

app.title = "BI InfoTeca" 

app.layout = html.Div(children=[
    navbar,
    modalFiltro,
    html.Div(children=[
    dbc.Row([
        dbc.Col(
            [html.Span(getPeriodo("",""),id="top-bar", style={"width": "100%"})
            ], md=12
        )
    ],
    style={
        "position": "sticky",
        "textAlign": "center",
        "margin": "0",
        "width": "100%",
        "top": "0",
        "zIndex": "1",
        "backgroundColor":"#F8F8F8",
        "boxShadow": "0px 2px 5px lightgrey"
    }),
    dbc.Row([
        dbc.Col(criarGrafico1("",""), md=5, id="col1"),
        dbc.Col(criarGrafico2(0, "", ""), md=7,id='col-graph-qtd-mes-por-area')
    ], style={
        'width': '100%',
    }),
    dbc.Row([
        dbc.Col([dcc.Graph(
                    id='graph-qtd-turma',
                    style={"visibility":"hidden", "height": "0px"}
                )
            ], md=11, id="col-graph-qtd-turma"),
        dbc.Col([
            dbc.FormGroup([
                dbc.Label("Limite Resultado", html_for="limitGraph4", width=12),
                dbc.Col(
                    dbc.Input(id="limitGraph4", placeholder="Limite resultado", type="number", value="10"), width=10, 
                )
            ], row=True)
        ], id="col-limitGraph4",md=1, style={
            'paddingTop': '100px',
            'paddingLeft': '0',
            'paddingRight': '0',
            'display': 'none',
        })   
    ],style={"width":"100%"}),
    dbc.Row([
      dbc.Col(md=12, id="col-graph-qtd-turma-dia") ,
    ],style={"width":"100%"}),
    dbc.Row([
    dbc.Col(
        criarGrafico6("", "", "","")
    , md=11, id="col-graph-qtd-livro-dia")
    ], style={"width": "100%"}),
    dbc.Row([
        dbc.Col(
            criarGrafico3("", "", "", "",10)
        , md=11, id="col-graph-qtd-livro"),
        dbc.Col([
            dbc.FormGroup([
                dbc.Label("Limite Resultado", html_for="limitGraph3", width=12),
                dbc.Col(
                    dbc.Input(id="limitGraph3", placeholder="Limite resultado", type="number", value="10"), width=10, 
                )
            ], row=True)
        ],md=1, style={
            'paddingTop': '100px',
            'paddingLeft': '0',
            'paddingRight': '0',
        })
    ]
    , style={
        'width': "100%",
    }
    ),
    ])
])

@app.callback(
    Output("top-bar", "children"),[
    Input("my-date-picker", "start_date"),
    Input("my-date-picker", "end_date")
])
def attPeriodo(dataini, datafim):
    print(getPeriodo("", ""))
    # print(start)
    # if start:
    #     dataI = 
    if dataini:
        dataI = dt.strptime(dataini,'%Y-%m-%d')
        dataini = dataI.strftime('%d/%m/%Y')
    if datafim:
        dataF = dt.strptime(datafim,'%Y-%m-%d')
        datafim = dataF.strftime('%d/%m/%Y')
    return getPeriodo(dataini, datafim)

@app.callback(
    Output("col-graph-qtd-livro-dia", "children"),[
    Input("my-date-picker", "start_date"),
    Input("my-date-picker", "end_date"),
    Input("dropdown-area", "value"),
    # Input("dropdown-turma", "value")
])
def criarGraph6(dataini, datafim, curso):
    return criarGrafico6(curso, "", dataini, datafim)

@app.callback(
    Output("col-graph-qtd-turma-dia", "children"),[
    Input("graph-qtd-turma", "clickData"),
    Input("dropdown-turma", "value"),
    Input("my-date-picker", "start_date"),
    Input("my-date-picker", "end_date")
    ]
)
def criarGraph5(click, turma, start_date, end_date):
    clickL = click
    if clickL:
        turmaL = click["points"][0]["label"].encode("utf-8", "replace")
        return criarGrafico5(turmaL, start_date, end_date)
    elif turma:
        return criarGrafico5(turma, start_date, end_date)
    else:
        return criarGrafico5("", start_date, end_date)

@app.callback(Output("col1", "children"),[
    Input("my-date-picker", "start_date"),
    Input("my-date-picker", "end_date")
])
def filtroData(dataini, datafim):
    return criarGrafico1(dataini, datafim)

# add callback for toggling the collapse on small screens
@app.callback(
    Output("navbar-collapse", "is_open"),
    [Input("navbar-toggler", "n_clicks")],
    [State("navbar-collapse", "is_open")],
)
def toggle_navbar_collapse(n, is_open):
    if n:
        return not is_open
    return is_open

@app.callback(
    [Output("col-graph-qtd-turma", "children"),
    Output("col-limitGraph4", "style")],[
    Input("my-date-picker", "start_date"),
    Input("my-date-picker", "end_date"),
    Input("dropdown-area", "value"),
    Input("limitGraph4", "value"),
])
def criarGraphQtdTurma(start, end, area, limit):
    if start and area:
        style = {"display": "block"}
        return criarGrafico4(start, end, area, limit), style
    else:
        style={
            'paddingTop': '100px',
            'paddingLeft': '0',
            'paddingRight': '0',
            'display': 'none',
        }
        return criarGrafico4(start, end, area, limit), style

@app.callback(
    Output("popover-filtro", "is_open"),
    [Input("popover-target", "n_clicks")],
    [State("popover-filtro", "is_open")],
)
def toggle_popover(n1, is_open):
    if n1:
        return not is_open
    return is_open

# @app.callback([Output("dropdown-mes", "value"), Output("dropdown-mes-background", "children")],[
#     Input("graph-qtd-mes", "clickData"),
#     Input("graph-qtd-mes-por-area", "clickData"),
#     Input("dropdown-mes", "options"),
#     Input("limparFiltro", "n_clicks")],
#     [State("dropdown-mes-background", "children")]    
# )
# def alterarDropdownMes(clickMes, clickMesArea, mesOptions, limparFiltro, mesBG):
#     if limparFiltro != None:
#         return None,None
#     if clickMes != None:
#         clickX = clickMes["points"][0]["x"].encode('utf-8', 'replace')
#         return clickX, clickX
#     elif clickMesArea != None:
#         clickX = clickMesArea["points"][0]["x"].encode('utf-8', 'replace')
#         for mes in mesOptions:
#             if(mes["label"].encode("utf-8", "replace") == clickX):
#                 return clickX, clickX
#         return mesBG, mesBG
#     else:
#         return [None, None]

@app.callback(
    Output("col-graph-qtd-mes-por-area", "children"),
    [
    Input("my-date-picker", "start_date"),
    Input("my-date-picker", "end_date")]
)
def criarGraphQtdMesPorArea(start_date, end_date):
    return criarGrafico2(0, start_date, end_date)


@app.callback(Output("dropdown-turma", "value"),[
    Input("graph-qtd-turma", "clickData"),
])
def dropdownTurma(click):
    if click:
        turma = click["points"][0]["label"].encode("utf-8", "replace")
        return turma
    else:
        return ""

@app.callback(
    Output("dropdown-turma", "options"),[
    Input("dropdown-area", "value")]
)
def attDropdownTurma(curso):
    if curso:
        return getOptionsTurma(curso)
    else:
        return getOptionsTurma("")

@app.callback(
    Output("dropdown-area","value"),[
    Input("graph-qtd-mes-por-area", "clickData"),
    Input("limparFiltro", "n_clicks")
    ]
)
def alterarDropdownArea(click, limparFiltro):
    if(limparFiltro != None):
        return None
    if(click != None):
        clickX = click["points"][0]["text"].encode('utf-8', 'replace')
        return clickX
    else:
        return None

@app.callback(
    Output("col-graph-qtd-livro", "children"),[
    Input("my-date-picker", "start_date"),
    Input("my-date-picker", "end_date"),
    Input("dropdown-area", "value"),
    Input("dropdown-area", "options"),
    Input("limitGraph3", "value")
    ]
)
def criarGraphQtdMesPorLivro(dataini, datafim, area, areaOptions, limitRows):
    limitRows = int(limitRows)
    if(area != None):
        area = area.encode("utf-8", "replace")
        areaLabel = ""
        for a in areaOptions:
            if(a["value"] == area):
                areaLabel = a["label"]
        areaLabel = areaLabel.encode("utf-8", "replace")
        if(datafim == None):
            return criarGrafico3(dataini, datafim, area, "pelo curso de "+areaLabel, limitRows)   
        else:
            return criarGrafico3(dataini, datafim, area, " pelo curso "+ areaLabel, limitRows)            
    else:
        if(datafim != None):
            return criarGrafico3(dataini, datafim, "", "", limitRows)
        elif(limitRows != None):
            return criarGrafico3(dataini, datafim, "", "", limitRows)
        else:
            return criarGrafico3(dataini, datafim, "", "", limitRows)
            
if __name__ == '__main__':
    app.run_server(host='0.0.0.0', port=8080)
