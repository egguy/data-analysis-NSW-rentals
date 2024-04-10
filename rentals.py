from dash import Dash, dcc, html, Input, Output
import plotly.express as px

import pandas as pd
import duckdb

app = Dash(__name__)

# connect duckdb
con = duckdb.connect(database="rentals.duckdb", read_only=True)

# get the data
df = pd.read_sql("SELECT * FROM rentals", con)


app.layout = html.Div([
    html.Div([

        html.Div([
            dcc.Dropdown(
                df['Postcode'].unique(),
                'Postcode',
                id='xaxis-column'
            ),
            dcc.RadioItems(
                ['Linear', 'Log'],
                'Linear',
                id='xaxis-type',
                inline=True
            )
        ], style={'width': '48%', 'display': 'inline-block'}),

        html.Div([
            dcc.Dropdown(
                df['Dwelling Type'].unique(),
                'Dwelling type',
                id='yaxis-column'
            ),
            dcc.RadioItems(
                ['Linear', 'Log'],
                'Linear',
                id='yaxis-type',
                inline=True
            )
        ], style={'width': '48%', 'float': 'right', 'display': 'inline-block'})
    ]),

    dcc.Graph(id='indicator-graphic'),
    dcc.Graph(id='rentals-per-bedroom'),

    dcc.RangeSlider(
        df['Lodgement Date'].min().year,
        df['Lodgement Date'].max().year,
        step=None,
        id='year--slider',
        value=[df['Lodgement Date'].min().year, df['Lodgement Date'].max().year],
        marks={str(year): str(year) for year in df['Lodgement Date'].dt.year.unique()},
    )
])

@app.callback(
    Output('rentals-per-bedroom', 'figure'),
    Input('year--slider', 'value'),
)
def update_rentals_per_bedroom(date_range):
    '''Display the number of rentals per number of bedrooms

    :param date_range: The year range to take into account
    :return: The graph
    '''

    # filter the data by date_range
    dff = df[(df['Lodgement Date'].dt.year >= date_range[0]) & (df['Lodgement Date'].dt.year <= date_range[1]+1)]
    # convert the bedrooms to int
    dff['Bedrooms'] = pd.to_numeric(dff['Bedrooms'], errors='coerce')
    # aggregate the 5+ bedrooms into 5
    dff.loc[dff['Bedrooms'] >= 5, 'Bedrooms'] = 5

    # calculate the number of rentals per number of bedrooms, sorted by bedrooms index
    dff = dff.groupby(['Bedrooms'])['Weekly Rent'].count().sort_index().reset_index()
    # rename the columns
    dff.columns = ['Bedrooms', "Bonds"]
    print(dff.info())


    # display the ploty figure as a barchart, add the number of rentals as the color
    return px.bar(dff, x='Bedrooms', y='Bonds')

@app.callback(
    Output('indicator-graphic', 'figure'),
    Input('year--slider', 'value'),
)
def update_graph(date_range):
    print(date_range)
    # filter the data by date_range
    dff = df[(df['Lodgement Date'].dt.year >= date_range[0]) & (df['Lodgement Date'].dt.year <= date_range[1]+1)]
    # convert the bedrooms to int
    dff['Bedrooms'] = pd.to_numeric(dff['Bedrooms'], errors='coerce')
    # aggregate the 5+ bedrooms into 5
    dff.loc[dff['Bedrooms'] >= 5, 'Bedrooms'] = 5

    # calculate the average rent per number of bedrooms, sorted by bedrooms index.
    # Count the number of rentals per number of bedrooms
    dff = dff.groupby(['Bedrooms'])['Weekly Rent'].agg(['mean', 'count']).reset_index()
    # rename the columns
    dff.columns = ['Bedrooms', 'Mean weekly rent', 'count']

    # dff = dff.groupby(['Bedrooms'])['Weekly Rent'].mean().sort_index().reset_index()
    # dff = dff.groupby(['Bedrooms'])['Weekly Rent'].mean().reset_index()

    # display the ploty figure as a barchart, add the number of rentals as the color
    return px.bar(dff, x='Bedrooms', y='Mean weekly rent', color='count')



if __name__ == '__main__':
    app.run_server(debug=True)