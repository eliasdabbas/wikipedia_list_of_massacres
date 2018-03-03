import re
import datetime
import textwrap
from functools import reduce
from math import log
from operator import add

import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
from plotly.offline import iplot, plot
import plotly.graph_objs as go
import pandas as pd


massacres_df = pd.read_csv('massacres.csv')
massacres_df['date'] = [datetime.datetime.strptime(x, '%Y-%m-%d %H:%M:%S') for x in massacres_df['date']]
massacres_df = massacres_df[massacres_df['lat_clean'].notna()].reset_index(drop=True)
massacres_df['description'] = [re.sub('\[\d+\]', '', x) for x in massacres_df['description']]

all_locations = set(reduce(add, [x.split(', ') for x in massacres_df['location']]))
app = dash.Dash(__name__)

server = app.server

app.css.append_css({"external_url": "https://codepen.io/chriddyp/pen/bWLwgP.css"})

app.layout = html.Div([ 

        html.H4('Year from:'),
        dcc.Slider(id='from_year', 
                   marks={
                       num: {'label': num}
                       for num in list(range(50, 2020, 200))
                   },
                   min=50,
                   max=2020,
                   step=5,
                   value=1900,
                   dots=True,
                   included=False,
                   updatemode='mouseup'
                   ),
                
        html.H4('Year to:'),
        dcc.Slider(id='to_year', 
                   marks={
                       num: {'label': num}
                       for num in list(range(50, 2020, 200))
                   },
                   min=50,
                   max=2020,
                   step=5,
                   value=2016,
                   dots=True,
                   included=False,
                   updatemode='mouseup'
                   ), 
        html.Br(),

        dcc.Graph(id='bubble_chart',
                  config={'displayModeBar': False, 'frameMargins': '90%'},
                 ),

        html.Br(),
        html.Div([
            html.P('Change "from" and "to" years to see events within a certain range '),
            html.P('Pan, zoom, and scroll zoom'),
            html.P('Double-click to go back to full map view'),
            html.A('Wikipedia List of Events Named Massacres',
                   title='Wikipedia List of Events Named Massacres',
                   href='https://en.wikipedia.org/wiki/List_of_events_named_massacres'),
        ]),
        dcc.Dropdown(id='loc_select',
                     multi=True,
                     value=tuple(),
                     placeholder='Select countries or cities',

                     options=[{'label': loc, 'value': loc}
                              for loc in sorted(all_locations)]),

        dcc.Graph(id='incident_by_date',
                  config={'displayModeBar': False}),

    
], style={'background-color': '#eeeeee'})

    


@app.callback(Output('bubble_chart', 'figure'),
             [Input('from_year', 'value'),
              Input('to_year', 'value')])
def filter_date(fromyear, toyear):
    massacres_df = pd.read_csv('massacres.csv')
    massacres_df['date'] = [datetime.datetime.strptime(x, '%Y-%m-%d %H:%M:%S') for x in massacres_df['date']]
    massacres_df = massacres_df[massacres_df['lat_clean'].notna()].reset_index(drop=True)
    massacres_df['description'] = [re.sub('\[\d+\]', '', x) for x in massacres_df['description']]
    
    massacres_df = massacres_df[[fromyear <= x.year <= toyear for x in massacres_df['date']]]

    return  {'data':[go.Scattergeo(lon=massacres_df['lon_clean'],
                         lat=massacres_df['lat_clean'],
                         marker={'size': [log(x)*4 for x in massacres_df['deaths']],
                                 'color': [log(x)*10 for x in massacres_df['deaths']],
                                 'colorscale': 'Reds', 'showscale': True, 
                                 'colorbar': {'title': 'Deaths',
                                              'x': 0.03,
                                              'tickvals':[0, 10, 20, 40, 80, 130],
                                              'ticktext': [1,100, 200, 400, 2000, 900000],
                                              'separatethousands': True,
                                              'outlinecolor': '#eeeeee'}},

                         hoverinfo='text',
                         hoverlabel={'font': {'size': 15}, 'bgcolor': {'opacity': '0.5'}},
                         hovertext=massacres_df['name'] + '<br>' + 'Deaths: ' + 
                         [f'{x:,}' for x in massacres_df['deaths']] + '<br>' +
                         massacres_df['location'] + ' ' + 
                         [str(x.date()) for x in massacres_df['date']] + '<br><br>' +
                         ['<br>'.join(textwrap.wrap(x, 40)) for x in massacres_df['description']]      
                 )],

          'layout': go.Layout({
              'title': 'Massacres of the World ' + str(fromyear) + ' - ' + str(toyear) +  '   Wikipedia',
              'font': {'family': 'palatino'}, 'titlefont': {'size': 30},
              'width': 1400, 'height': 700,
              'paper_bgcolor': '#eeeeee',
              'geo': {'showland': True, 'landcolor': '#eeeeee',
                      'countrycolor': '#cccccc', 
                      'showcountries': True,
                      'oceancolor': '#eeeeee',
                      'showocean': True,
                      'showcoastlines': True, 'showframe': False,
                      'coastlinecolor': '#cccccc',
                      'projection': {'type': 'Mercator'}, # 'scale': 1.15},
                      }
          })}

@app.callback(Output('incident_by_date', 'figure'),
              [Input('loc_select', 'value')])
def plot_locations(locations):
   
    return {'data':
            [go.Scatter(x=massacres_df[massacres_df['location'].str.contains(loc)]['date'],
                        y=massacres_df[massacres_df['location'].str.contains(loc)]['deaths'],
                        mode='markers',
                        name=loc,
                        hoverinfo='text',
                         hovertext=massacres_df[massacres_df['location'].str.contains(loc)]['name'] + '<br>' + 'Deaths: ' + 
                         [f'{x:,}' for x in massacres_df[massacres_df['location'].str.contains(loc)]['deaths']] + '<br>' +
                         massacres_df[massacres_df['location'].str.contains(loc)]['location'] + ' ' + 
                         [str(x.date()) for x in massacres_df[massacres_df['location'].str.contains(loc)]['date']] + '<br><br>' +
                         ['<br>'.join(textwrap.wrap(x, 40)) for x in massacres_df[massacres_df['location'].str.contains(loc)]['description']],     

                        marker={'size': 15})
             for loc in locations],             
             
            'layout': go.Layout({'title': 'Number of Deaths per Massacre by Date & Location',
                                 'height': 500,
                                 'font': {'family': 'palatino'},
                                 'titlefont': {'size': 30},
                                 'hovermode': 'closest',
                                 'paper_bgcolor': '#eeeeee',
                                 'plot_bgcolor': '#eeeeee',
                                 'yaxis': {'type': 'log', 'autorange': True,
                                          'tickmode': 'linear'},
                                 'xaxis': {'zeroline': False, 'type': 'date',
                                          'rangeslider': {'autorange': True,
                                                          'bgcolor': '#dedede'}},
                                 
                                 }),
           'config': {'displayModeBar': False}}




if __name__ == '__main__':
    app.run_server(debug=True)