
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import itertools
import plotly.express as px
from dash import Dash, dcc, html, Input, Output, dash_table, callback, Patch
import pymysql

# Database connection
connection = pymysql.connect(
    host='s462.loopia.se',
    user='hedvigs',
    password='!tFyjRseukk9',
    database='espbc_se'
)


app = Dash(__name__)
server = app.server
sum_file = 'sum_file.csv'



df = pd.read_csv(sum_file)
df.drop(columns=['Unnamed: 0'], inplace=True)

op = [{'label': i, 'value': i} for i in df.columns]
numerical_cols = df.select_dtypes(include=[np.number]).columns.tolist()
numerical_cols.remove('fold')
cols_few_unique = [col for col in df.columns if df[col].nunique() < 10]

fig = px.box(df, x='model', y='auc_prob', color='gen')
yaxis_dict = dict(
                autorange=True,
                showgrid=True,
                zeroline=True,
                dtick=5,
                gridcolor='rgb(255, 255, 255)',
                gridwidth=0.1,
                zerolinecolor='rgb(255, 255, 255)',
                zerolinewidth=20,
                )
margin_dict = dict(
                l=40,
                r=10,
                b=80,
                t=100,
                )
paper_color = 'rgb(243, 243, 243)'
plot_color = 'rgba(215, 234, 256, 0.5)'

app.layout = html.Div([
    html.Div([
        html.H2("Metrics by configuration", style={'textAlign': 'center'}),
        html.P("Filter by:"),
        dcc.Checklist(
            id='filter-by', 
            options=[{'label': i, 'value': i} for i in ["subset", "gen", "model"]], 
            value=[], 
            inline=True
        ),
        dcc.Dropdown(id='filter-options', options=[], multi=False),
        html.P("x-axis:"),
        dcc.Dropdown(
            id='x-axis', 
            options=op,
            value='model', 
        ),
        html.P("y-axis (metric):"),
        dcc.Dropdown(
            id='y-axis', 
            options=numerical_cols, 
            value='auc_prob', 
        ),
        html.P("color:"),
        dcc.Dropdown(
            id='color', 
            options=cols_few_unique, 
            value='gen', 
        )
    ], style={'padding': 10,'width':'20%'}),
    html.Div([
        dcc.Graph(id="graph", figure=fig),
        dcc.Tooltip(id="graph-tooltip"),
        dash_table.DataTable(
            id='table', 
            data=df.to_dict('records'),
            sort_action='native',
            fixed_rows={'headers': True}, 
            style_table={'height': '300px', 'overflowY': 'auto',},
                         #    'width':'1200px',
                         # #    'overflowX': 'auto', 
                         # 'backgroundColor':'dodgerblue'},
                         style_as_list_view=True,
                         style_cell={'padding': '20px'},
                         style_data_conditional=[
                             {
                                 'if': {'row_index': 'odd'},
                                 'backgroundColor': 'rgb(220, 220, 220)',
                                 }
                             ],
                         style_header={
                             'backgroundColor': 'white',
                             'fontWeight': 'bold'
                             },),
    ], style={'width': '70%'}),
], style={'display': 'flex', 'flexDirection': 'row'})

@app.callback(
    Output("filter-options", "options"),
    Input("filter-by", "value")
)
def update_filter_options(filter_by):
    if filter_by:
       filter_options=np.unique(df[filter_by])
       return filter_options
    else:
        return []

@app.callback(
    Output("table", "data"), 
    Output("graph", "figure"), 
    Input("x-axis", "value"), 
    Input("y-axis", "value"),
    Input("color", "value"),
    Input("filter-by", "value"),
    Input("filter-options", "value")
)

def update_output(x, y, color, filter_by, filter_value):
    if filter_value:
        patched_fig = Patch()
        filter_value=str(filter_value)
        filter_by= filter_by[0]
        # Filter rows where the selected column equals the selected value
        filtered_df = df[df[filter_by] == filter_value]
        patched_fig = px.box(data_frame=filtered_df, x=x, y=y, color=color, color_discrete_sequence=px.colors.qualitative.Vivid)
        fdf = filtered_df
        pfig = patched_fig
    else:
        fig = px.box(data_frame=df, x=x, y=y, color=color,color_discrete_sequence=px.colors.qualitative.Vivid)
        fdf=df
        pfig = fig
    if 'lr' in y:
        pfig.add_shape(
            type='line', line=dict(dash='dash'),
            x0=-1, x1=9, y0=1, y1=1)
    elif 'auc' in y:
        pfig.add_shape(
            type='line', line=dict(dash='dash', color=px.colors.qualitative.Vivid[4], width=3),
            name=f'Average {y} for all {color}', showlegend=True, opacity=0.5,
            x0=-1, x1=9, y0=fdf[y].mean(),y1=fdf[y].mean() )
        for i, cname in enumerate(fdf[color].unique()):
            cname_df = fdf[fdf[color]==cname]
            mean_cname = cname_df[y].mean()
            pfig.add_shape(
                type='line', line=dict(dash='dash', color=px.colors.qualitative.Vivid[i]), name=f'Average {y} for {cname}',
                x0=-1, x1=9, y0=mean_cname,y1=mean_cname, showlegend=True, opacity=0.7 )
    pfig.update_layout(
        title=f'{y} by {x}',
        margin=margin_dict,
        paper_bgcolor=paper_color,
        plot_bgcolor=plot_color,
        showlegend=True)
    return fdf.to_dict('records'), pfig

if __name__ == '__main__':
    app.run_server(debug=True)

