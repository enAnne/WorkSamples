import os
import dash
import visdcc
import pandas as pd
import numpy as np
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import dash_bootstrap_components as dbc
import networkx as nx

folder = r'C:\Users\eeann\OneDrive\KOL List/'
os.chdir(folder)

all_nodes_dupe = pd.read_csv('Nodes.csv')
all_nodes_dupe['NrSynonym'] = 1
all_nodes = all_nodes_dupe.groupby('id',as_index=False).agg({'fullname':'first','country':'first','eigenvector':'mean','synonym':'; '.join,'NrSynonym':'sum'})
all_edges = pd.read_csv('Edges.csv')
# all_edges['Shared_clinical_trials_link'] = pd.to_numeric(all_edges['Shared_clinical_trials_link'],errors='coerce')
# all_edges['Shared_organization_link'] = pd.to_numeric(all_edges['Shared_organization_link'],errors='coerce')
# all_edges['Shared_articles_Link'] = pd.to_numeric(all_edges['Shared_articles_Link'],errors='coerce')
all_edges['Shared_clinical_trials_link'] = np.random.randint(0, 10, all_edges.shape[0])
all_edges['Shared_organization_link'] = np.random.randint(0, 10, all_edges.shape[0])
all_edges['Shared_articles_Link'] = np.random.randint(0, 10, all_edges.shape[0])
all_edges['weight'] = 1
all_edges['totalLinkages'] = all_edges.Shared_clinical_trials_link + all_edges.Shared_articles_Link + all_edges.Shared_organization_link 

# Create graph
G = nx.from_pandas_edgelist(all_edges,'Source','Target',['weight','totalLinkages','Shared_clinical_trials_link','Shared_articles_Link','Shared_organization_link'])
G.add_nodes_from(list(zip(all_nodes['id'],all_nodes[['fullname','eigenvector','country','synonym','NrSynonym']].to_dict('records'))))

nodes = []
edges = []
therapeutic_areas = all_nodes_dupe[['synonym','synonym']].drop_duplicates()
therapeutic_areas.columns = ['label','value']
therapeutic_areas = therapeutic_areas.to_dict('records')
countries = all_nodes[['country','country']].drop_duplicates()
countries.columns = ['label','value']
countries = countries.to_dict('records')

def getNodesEdges(s,root):
    from_kols = [sub[0] for sub in s.edges] 
    to_kols = [sub[1] for sub in s.edges] 
    edges = [{'from':x,'to':y} for x,y in zip(from_kols,to_kols)] 
    nodes = pd.DataFrame({'id':s.nodes}).drop_duplicates()
    nodes['size'] = nodes.id.map(nx.get_node_attributes(s,'eigenvector'))
    nodes['size'] = nodes['size']/nodes['size'].max() * 25
    nodes['label'] = nodes.id.map(nx.get_node_attributes(s,'fullname'))
    nodes['specialty'] = nodes.id.map(nx.get_node_attributes(s,'synonym'))
    nodes['specialties'] = nodes.id.map(nx.get_node_attributes(s,'NrSynonym'))
    nodes['country'] = nodes.id.map(nx.get_node_attributes(s,'country'))
    nodes['color'] = '#acf1f9'
    nodes.loc[nodes.id==root,'color'] = '#ff0000'
    nodes['color.highlight'] = '#0f2427'
    nodes = [{'id':node.id,'size':node.size,'label':node.label, 'color':node.color, 'color.highlight':node['color.highlight'], 'specialty':node.specialty, 'specialties':node.specialties, 'country':node.country} for i,node in nodes.iterrows()] 
    return nodes, edges
    
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
app.layout = html.Div([
    html.Div(html.H4(["Stakeholder Mapping"], style={'textAlign':'center'}),style={'margin-top':15,'margin-bottom':15}), 
    html.Div(
        dbc.Row([
            dbc.Col(html.H6(["Stakeholder"]), width=1, style={'textAlign':'right','margin-top':7}),
            dbc.Col(html.Div(dcc.Dropdown(
                id='therapeutic_area_from',
                placeholder = 'Therapeutic Area',
                options=therapeutic_areas,
                value='HPV'
            )), width=2),
            dbc.Col(html.Div(dcc.Dropdown(
                id='country_from',
                placeholder = 'Country',
                options=countries,
                value='Malaysia'
            )), width=2),
            dbc.Col(html.Div(dcc.Loading(dcc.Dropdown( 
                id='kol_from',
                placeholder = 'Stakeholder',
                value=''
            ))), width=3),
            dbc.Col(html.Div(dcc.RadioItems(
                id='degree',
                options=[{'label':'1','value':1},
                          {'label':'2','value':2},
                          {'label':'3','value':3},
                          {'label':'4','value':4}],
                value=1)), width=1),
            dbc.Col(dcc.Loading(html.Div(html.Button('Display network', id='calc_network')))),
            ]),style={"margin-top":5,'margin-left':30}),
    html.Div(
        dbc.Row([
            dbc.Col(html.H6(["Connection"]), width=1, style={'textAlign':'right','margin-top':7}),
            dbc.Col(html.Div(dcc.Dropdown(
                id='therapeutic_area_to',
                placeholder = 'Therapeutic Area',
                options=therapeutic_areas,
                value=None
            )), width=2),
            dbc.Col(html.Div(dcc.Dropdown(
                id='country_to',
                placeholder = 'Country',
                options=countries,
                value=None
            )), width=2),
            dbc.Col(html.Div(dcc.Loading(dcc.Dropdown(
                id='kol_to',
                placeholder = 'Connection',
                value=''
            ))), width=7)
            ]),style={"margin-top":5,'margin-left':30}),
    html.Div(id = 'kol_from_id', hidden = True),
    html.Div(id = 'clicks', hidden = True),
    dcc.Loading(visdcc.Network(id = 'net',
                    data = {'nodes':nodes,'edges':edges},
                    options = {'height':'700px', 
                              'width':'100%', 
                                'nodes': {'chosen': True,
                                          'shape':'dot',
                                          'color':{ 'highlight': {
                                                        'border': '#2B7CE9',
                                                        'background': '#D2E5FF'
                                                    },
                                                    'hover': {
                                                        'border': '#2B7CE9',
                                                        'background': '#D2E5FF'
                                                    }}}
                              }))
    ],style={"border":"10px white solid",'font-size':'12px'}
    )
#app.run_server(debug=True, use_reloader=False)

@app.callback(Output('therapeutic_area_to','value'),
              [Input('therapeutic_area_from','value')])
def default_ta(therapeutic_area):
    return therapeutic_area

@app.callback(Output('kol_from','options'),
              [Input('therapeutic_area_from','value'),
              Input('country_from','value')])
def get_from_kols(therapeutic_area,country):
    kols = all_nodes_dupe.loc[((all_nodes_dupe.country==country)|(country==None))&((all_nodes_dupe.synonym==therapeutic_area)|(therapeutic_area==None))].sort_values('eigenvector',ascending=False)
    kols = [{'label':node.fullname,'value':node.fullname} for i,node in kols.iterrows()] 
    return kols

@app.callback([Output('calc_network','children'),
               Output('kol_from_id','children'),
               Output('kol_to','options'),
               Output('kol_to','value')],
              [Input('therapeutic_area_to','value'),
               Input('country_to','value'),
               Input('kol_from','value'),
               Input('degree','value')])
def get_to_kols(therapeutic_area,country,kol_from,degree):
    if pd.notna(kol_from) and kol_from != '':
        ids = all_nodes_dupe.loc[((all_nodes_dupe.country==country)|(country==None))&((all_nodes_dupe.synonym==therapeutic_area)|(therapeutic_area==None))&(all_nodes_dupe.fullname==kol_from)].sort_values('eigenvector',ascending=False).id.unique()
        kol_from_id = ids[0]
        length,path = nx.single_source_dijkstra(G,kol_from_id,cutoff=degree)
        s = G.subgraph(path)
        nodes, edges = getNodesEdges(s,kol_from_id)
        to_kols = [(sub['id'], length[sub['id']]*100-(s.edges[kol_from_id,sub['id']]['totalLinkages'] if length[sub['id']]==1 else 0), str(int(length[sub['id']])) + '-deg ' + ((str(int(s.edges[kol_from_id,sub['id']]['totalLinkages'])) + '-linkages: ' ) if length[sub['id']]==1 else ': ') + sub['label'] + ' (' + sub['country'] + ' - ' + str(sub['specialties']) + ' specialties, ' + ('both share ' + (str(int(s.edges[kol_from_id,sub['id']]['Shared_organization_link'])) + ' Orgs, ' + str(int(s.edges[kol_from_id,sub['id']]['Shared_clinical_trials_link'])) + ' Clin.Trials, ' + str(int(s.edges[kol_from_id,sub['id']]['Shared_articles_Link'])) + ' Articles') if length[sub['id']]==1 else '') + ')') for sub in nodes if (sub['country']==country or country==None) & (therapeutic_area in sub['specialty'] or therapeutic_area==None)] 
        to_kols = [{'label':n,'value':x,'order':i} for x,i,n in to_kols]
        to_kols = [{'label':y['label'],'value':y['value']} for y in sorted(to_kols, key=lambda x: x['order'])]
        information = 'Display network of ' + str(len(to_kols)) + ' Stakeholders'
    return [information, kol_from_id, to_kols, '']

@app.callback([Output('net', 'data'),
               Output('clicks', 'children')],
              [Input('therapeutic_area_to','value'),
               Input('country_to','value'),
               Input('kol_from_id','children'),
               Input('kol_to','options'),
               Input('kol_to','value'),
               Input('calc_network','n_clicks'),
               Input('clicks', 'children'),
               Input('degree','value')])
def get_network_graph(therapeutic_area,country,kol_from_id,kol_tos,kol_to_id,n_clicks,prev_clicks,degree):
    nodes = []
    edges = []
    if kol_to_id != None and kol_to_id != '':
        if nx.has_path(G,kol_from_id,kol_to_id):
            s = G.subgraph(nx.shortest_path(G,kol_from_id,kol_to_id))
            nodes_sub, edges_sub = getNodesEdges(s,kol_from_id)
            nodes = nodes + nodes_sub
            edges = edges + edges_sub
        nodes = [dict(tupleized) for tupleized in set(tuple(item.items()) for item in nodes)]
        edges = [dict(tupleized) for tupleized in set(tuple(item.items()) for item in edges)]
    elif (0 if n_clicks==None else n_clicks) > (0 if prev_clicks==None else prev_clicks):
        ids = all_nodes_dupe.loc[all_nodes_dupe.id.isin([x['value'] for x in kol_tos])].id.unique()
        for kol_to_id in ids:
            if nx.has_path(G,kol_from_id,kol_to_id):
                s = G.subgraph(nx.shortest_path(G,kol_from_id,kol_to_id))
                nodes_sub, edges_sub = getNodesEdges(s,kol_from_id)
                nodes = nodes + nodes_sub
                edges = edges + edges_sub
        nodes = [dict(tupleized) for tupleized in set(tuple(item.items()) for item in nodes)]
        edges = [dict(tupleized) for tupleized in set(tuple(item.items()) for item in edges)]
        #s = G.subgraph(nx.single_source_dijkstra_path(G,kol_from_id,degree))
        #nodes, edges = getNodesEdges(s,kol_from_id)
        #data = {'nodes':nodes,'edges':edges}
    data = {'nodes':nodes,'edges':edges}
    return [data, n_clicks]

#if __name__ == '__main__':
#app.run_server()
app.run_server(debug=True, use_reloader=False)


all_nodes_dupe[(all_nodes_dupe.fullname.str.find('Yin-ling')>-1)&(all_nodes_dupe.synonym=='HPV')].head()
all_nodes_dupe[(all_nodes_dupe.fullname.str.find('Axel Schafer')>-1)&(all_nodes_dupe.synonym=='HPV')].head()
kol_from = ' Murnira Othman'
kol_from_id = 256642515  # Yin Woo
kol_from_id = 231951463 # Yin-ling Woo
kol_to_id = 210077815 # Axel Schafer
degree = 3
root = 256642515
kol_from_id = 312845417  # LiPing Wong Ping
root = 312845417
country = 'Malaysia'
therapeutic_area = 'Health Technology Assessment'
kol_to = None
country = None
therapeutic_area = None
