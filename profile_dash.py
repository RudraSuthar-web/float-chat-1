from dash import Dash, html, dcc, Input, Output
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import backend

# Initialize Dash app with Bootstrap and Google Fonts
app = Dash(__name__, external_stylesheets=[
    dbc.themes.DARKLY,
    "https://fonts.googleapis.com/css2?family=Roboto:wght@400;700&display=swap"
])

# Layout
app.layout = html.Div([
    # Header
    html.Header(
        style={'backgroundColor': '#1A2A44', 'padding': '15px 20px', 'borderBottom': '2px solid #00C4B4'},
        children=[
            html.Div([
                html.H3("FloatChat Profiles", style={'color': '#FFFFFF', 'margin': '0', 'fontFamily': 'Roboto, sans-serif', 'fontWeight': '700'}),
                html.Span("", style={'fontSize': '1.5em', 'color': '#00C4B4', 'marginLeft': '10px'})
            ], style={'display': 'flex', 'alignItems': 'center', 'maxWidth': '1200px', 'margin': '0 auto'})
        ]
    ),
    # Main Content
    dbc.Container(
        fluid=True,
        style={'padding': '20px', 'maxWidth': '1200px', 'margin': '0 auto'},
        children=[
            html.Div([
                dcc.Dropdown(
                    id='float-dropdown',
                    multi=False,
                    placeholder="Select a Float ID...",
                    style={
                        'width': '100%', 'maxWidth': '400px', 'marginBottom': '25px', 'backgroundColor': '#2E4057',
                        'color': "#030303", 'border': '1px solid #465C71', 'borderRadius': '8px', 'padding': '12px',
                        'fontFamily': 'Roboto, sans-serif', 'fontSize': '16px', 'boxShadow': '0 2px 4px rgba(0,0,0,0.1)'
                    }
                ),
                dcc.Graph(
                    id='profile-graph',
                    style={'height': '600px', 'border': '1px solid #465C71', 'borderRadius': '8px', 'backgroundColor': '#2E4057', 'padding': '15px'}
                )
            ], style={'backgroundColor': '#1F2A44', 'padding': '30px', 'borderRadius': '10px', 'boxShadow': '0 4px 6px rgba(0,0,0,0.1)'}),
            html.Div(id='profile-status', style={
                'marginTop': '20px', 'fontFamily': 'Roboto, sans-serif', 'fontSize': '14px', 'color': '#B0BEC5'
            })
        ]
    ),
    # Footer
    html.Footer(
        style={'backgroundColor': '#1A2A44', 'padding': '10px', 'textAlign': 'center', 'color': '#B0BEC5', 'fontFamily': 'Roboto, sans-serif', 'fontSize': '12px', 'borderTop': '1px solid #00C4B4'},
        children=[
            "© 2025 FloatChat"
        ]
    )
], style={'backgroundColor': '#152238', 'minHeight': '100vh', 'display': 'flex', 'flexDirection': 'column'})

# Callback to update dropdown options and plot
@app.callback(
    [Output('float-dropdown', 'options'),
     Output('profile-graph', 'figure'),
     Output('profile-status', 'children')],
    Input('float-dropdown', 'value')
)
def update_profile_page(selected_float):
    try:
        float_ids = backend.fetch_all_float_ids()
        options = [{'label': fid, 'value': fid} for fid in float_ids] if float_ids else []

        if not selected_float:
            return options, go.Figure(), "Please select a Float ID to view profiles."

        df = backend.fetch_comparison_data([selected_float])
        if df.empty:
            return options, go.Figure(), f"No data available for Float {selected_float}."

        fig = go.Figure()
        float_data = df[df['float_id'] == selected_float]
        fig.add_trace(go.Scatter(x=float_data['TEMP'], y=float_data['PRES'], mode='lines+markers',
                                name='Temperature', line=dict(color='#FF6B6B')))
        fig.add_trace(go.Scatter(x=float_data['PSAL'], y=float_data['PRES'], mode='lines+markers',
                                name='Salinity', line=dict(color='#4ECDC4')))

        fig.update_layout(
            title=f'Depth Profiles for Float {selected_float}',
            xaxis_title='Value',
            yaxis_title='Pressure (dbar)',
            template='plotly_dark',
            yaxis=dict(autorange="reversed"),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            margin=dict(l=50, r=50, t=80, b=50),
            font=dict(family="Roboto, sans-serif", size=12),
            plot_bgcolor='rgba(46,64,87,0.8)',
            paper_bgcolor='rgba(46,64,87,0.8)'
        )

        return options, fig, f"Displaying profile for Float {selected_float}."
    except Exception as e:
        return [], go.Figure(), f"Error: {str(e)}. Please check the database or contact support."

if __name__ == '__main__':
    app.run(debug=True, port=5500)