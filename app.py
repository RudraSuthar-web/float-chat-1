from flask import Flask, render_template, request, jsonify, send_from_directory
import pandas as pd
import plotly.express as px
import plotly.utils
import json
import backend

app = Flask(__name__)

@app.route('/')
def index():
    return send_from_directory('static', 'index.html')

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

@app.route('/chat', methods=['POST'])
def chat():
    user_question = request.json.get('question')
    if not user_question:
        return jsonify({'error': 'No question provided'}), 400

    sql_query = ""
    try:
        # --- THIS LINE HAS CHANGED ---
        sql_query = backend.get_sql_query(user_question)
        # --------------------------

        result_df = backend.execute_sql_query(sql_query)
        response_payload = {'sql_query': sql_query}

        if result_df.empty:
            response_payload.update({
                'response_type': 'message',
                'message': 'Your query returned no results. Please try a different question.'
            })
            return jsonify(response_payload)

        summary = backend.generate_summary(user_question, result_df)
        response_payload['summary'] = summary

        viz_suggestion = backend.get_visualization_suggestion(result_df)

        if viz_suggestion == 'map':
            fig = px.scatter_geo(result_df, lat='LATITUDE', lon='LONGITUDE', hover_name='float_id', title='ARGO Float Locations', template='plotly_dark')
            fig.update_layout(margin={"r":0,"t":40,"l":0,"b":0}, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
            response_payload['response_type'] = 'plot'
            response_payload['chart'] = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
        elif viz_suggestion == 'profile_plot':
            y_axis_col = 'TEMP' if 'TEMP' in result_df.columns else 'PSAL'
            fig = px.line(result_df, x=y_axis_col, y='PRES', title=f'Depth Profile ({y_axis_col})', template='plotly_dark', labels={'PRES': 'Pressure (dbar)', y_axis_col: y_axis_col.title()})
            fig.update_yaxes(autorange="reversed")
            fig.update_layout(margin={"r":20,"t":40,"l":20,"b":20}, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
            response_payload['response_type'] = 'plot'
            response_payload['chart'] = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
        else:
            response_payload['response_type'] = 'table'
            response_payload['table_html'] = result_df.to_html(classes='min-w-full divide-y divide-slate-700 bg-slate-900', border=0)

        return jsonify(response_payload)

    except Exception as e:
        error_message = f"An error occurred: {str(e)}"
        if sql_query:
            error_message += f"\n\nAttempted SQL Query:\n{sql_query}"

        return jsonify({
            'sql_query': sql_query,
            'response_type': 'error',
            'message': error_message
        }), 500

if __name__ == '__main__':
    app.run(debug=True, port=5001)

# from flask import Flask, render_template, request, jsonify, send_from_directory
# import pandas as pd
# import plotly.express as px
# import plotly.utils
# import json
# import backend

# # --- Flask App Initialization ---
# # The 'static_folder' points to the directory where your index.html and other assets are.
# app = Flask(__name__, static_folder='static', static_url_path='')

# # --- Route for the Landing Page ---
# @app.route('/')
# def index():
#     # Serves your existing, professional-looking index.html from the 'static' folder.
#     return send_from_directory('static', 'index.html')

# # --- Route for the Dashboard Page ---
# @app.route('/dashboard')
# def dashboard():
#     # Renders the HTML template that will host our chat interface and results.
#     return render_template('dashboard.html')

# # --- Main API Endpoint for Chat Logic ---
# @app.route('/chat', methods=['POST'])
# def chat():
#     user_question = request.json.get('question')
#     if not user_question:
#         return jsonify({'error': 'No question provided'}), 400

#     sql_query = ""
#     try:
#         # 1. Generate SQL from user question
#         sql_query = backend.get_sql_query(user_question)
        
#         # 2. Execute SQL query
#         result_df = backend.execute_sql_query(sql_query)
#         response_payload = {'sql_query': sql_query}

#         # Handle empty results gracefully
#         if result_df.empty:
#             response_payload.update({
#                 'response_type': 'message',
#                 'message': 'Your query returned no results. Please try a different question.'
#             })
#             return jsonify(response_payload)

#         # 3. Generate a natural language summary
#         summary = backend.generate_summary(user_question, result_df)
#         response_payload['summary'] = summary

#         # 4. Determine the best visualization type
#         viz_suggestion = backend.get_visualization_suggestion(result_df)

#         if viz_suggestion == 'map':
#             # Create a map plot with a theme that matches the landing page
#             fig = px.scatter_geo(
#                 result_df, lat='LATITUDE', lon='LONGITUDE', hover_name='float_id',
#                 title='ARGO Float Locations', template='plotly_dark'
#             )
#             fig.update_layout(
#                 margin={"r":0, "t":40, "l":0, "b":0},
#                 paper_bgcolor="rgba(0,0,0,0)",
#                 plot_bgcolor="rgba(0,0,0,0)"
#             )
#             response_payload['response_type'] = 'plot'
#             response_payload['chart'] = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

#         elif viz_suggestion == 'time_series_plot':
#             # Create a time-series plot
#             y_axis_col = next((col for col in ['TEMP', 'PSAL', 'PRES'] if col in result_df.columns), 'TEMP')
#             fig = px.line(
#                 result_df, x='TIME', y=y_axis_col,
#                 title=f'{y_axis_col.title()} over Time', template='plotly_dark', markers=True
#             )
#             fig.update_layout(
#                 margin={"r":20, "t":40, "l":20, "b":20},
#                 paper_bgcolor="rgba(0,0,0,0)",
#                 plot_bgcolor="rgba(0,0,0,0)"
#             )
#             response_payload['response_type'] = 'plot'
#             response_payload['chart'] = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

#         elif viz_suggestion == 'profile_plot':
#             # Create a depth profile plot
#             y_axis_col = 'TEMP' if 'TEMP' in result_df.columns else 'PSAL'
#             fig = px.line(
#                 result_df, x=y_axis_col, y='PRES',
#                 title=f'Depth Profile ({y_axis_col})', template='plotly_dark',
#                 labels={'PRES': 'Pressure (dbar)', y_axis_col: y_axis_col.title()}
#             )
#             fig.update_yaxes(autorange="reversed")
#             fig.update_layout(
#                 margin={"r":20, "t":40, "l":20, "b":20},
#                 paper_bgcolor="rgba(0,0,0,0)",
#                 plot_bgcolor="rgba(0,0,0,0)"
#             )
#             response_payload['response_type'] = 'plot'
#             response_payload['chart'] = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
            
#         else: # Default to a table if no other visualization fits
#             response_payload['response_type'] = 'table'
#             # UI/UX ENHANCEMENT: Use Tailwind CSS classes for a professional table style.
#             # These classes match the dark, clean aesthetic of your landing page.
#             table_classes = (
#                 "w-full text-sm text-left text-slate-400 "
#                 "border-collapse border border-slate-700"
#             )
#             response_payload['table_html'] = result_df.to_html(
#                 classes=table_classes, border=0, index=False
#             )

#         return jsonify(response_payload)

#     except Exception as e:
#         # Provide detailed error messages for easier debugging
#         error_message = f"An error occurred: {str(e)}"
#         if sql_query:
#             error_message += f"\n\nAttempted SQL Query:\n{sql_query}"

#         return jsonify({
#             'sql_query': sql_query,
#             'response_type': 'error',
#             'message': error_message
#         }), 500

# # --- Run the Application ---
# if __name__ == '__main__':
#     app.run(debug=True, port=5501)
# from flask import Flask, render_template, request, jsonify, send_from_directory
# import pandas as pd
# import plotly.express as px
# import plotly.graph_objects as go
# import plotly.utils
# import json
# import backend

# try:
#     from profile_dash import app as profile_dash_app
# except ImportError as e:
#     print(f"Warning: Could not import profile_dash: {e}. Profile page will not be available.")
#     profile_dash_app = None

# # --- Flask App Initialization ---
# server = Flask(__name__, static_folder='static', static_url_path='', template_folder='templates')

# # --- Dash App Initialization (Fallback if profile_dash fails) ---
# from dash import Dash, html, dcc, Input, Output, State, exceptions
# import dash_bootstrap_components as dbc
# dash_app = Dash(__name__, server=server, url_base_pathname='/dash/', external_stylesheets=[dbc.themes.DARKLY])

# if profile_dash_app:
#     server = profile_dash_app.server
#     dash_app = profile_dash_app

# # --- Flask Routes ---
# @server.route('/')
# def index():
#     return send_from_directory('static', 'index.html')

# @server.route('/dashboard')
# def dashboard():
#     return render_template('dashboard.html')

# @server.route('/profiles')
# def profiles():
#     return render_template('profiles.html')

# @server.route('/chat', methods=['POST'])
# def chat():
#     user_question = request.json.get('question')
#     if not user_question:
#         return jsonify({'error': 'No question provided'}), 400

#     sql_query = ""
#     try:
#         sql_query = backend.get_sql_query(user_question)
#         result_df = backend.execute_sql_query(sql_query)
#         response_payload = {'sql_query': sql_query}

#         if result_df.empty:
#             response_payload.update({
#                 'response_type': 'message',
#                 'message': 'Your query returned no results. Please try a different question.'
#             })
#             return jsonify(response_payload)

#         summary = backend.generate_summary(user_question, result_df)
#         response_payload['summary'] = summary

#         viz_suggestion = backend.get_visualization_suggestion(result_df)

#         if viz_suggestion == 'map':
#             fig = px.scatter_geo(
#                 result_df, lat='LATITUDE', lon='LONGITUDE', hover_name='float_id',
#                 title='ARGO Float Locations', template='plotly_dark'
#             )
#             fig.update_layout(
#                 margin={"r":0, "t":40, "l":0, "b":0},
#                 paper_bgcolor="rgba(0,0,0,0)",
#                 plot_bgcolor="rgba(0,0,0,0)"
#             )
#             response_payload['response_type'] = 'plot'
#             response_payload['chart'] = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
#         elif viz_suggestion == 'time_series_plot':
#             y_axis_col = next((col for col in ['TEMP', 'PSAL', 'PRES'] if col in result_df.columns), 'TEMP')
#             fig = px.line(
#                 result_df, x='TIME', y=y_axis_col,
#                 title=f'{y_axis_col.title()} over Time', template='plotly_dark', markers=True
#             )
#             fig.update_layout(
#                 margin={"r":20, "t":40, "l":20, "b":20},
#                 paper_bgcolor="rgba(0,0,0,0)",
#                 plot_bgcolor="rgba(0,0,0,0)"
#             )
#             response_payload['response_type'] = 'plot'
#             response_payload['chart'] = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
#         elif viz_suggestion == 'profile_plot':
#             y_axis_col = 'TEMP' if 'TEMP' in result_df.columns else 'PSAL'
#             fig = px.line(
#                 result_df, x=y_axis_col, y='PRES',
#                 title=f'Depth Profile ({y_axis_col})', template='plotly_dark',
#                 labels={'PRES': 'Pressure (dbar)', y_axis_col: y_axis_col.title()}
#             )
#             fig.update_yaxes(autorange="reversed")
#             fig.update_layout(
#                 margin={"r":20, "t":40, "l":20, "b":20},
#                 paper_bgcolor="rgba(0,0,0,0)",
#                 plot_bgcolor="rgba(0,0,0,0)"
#             )
#             response_payload['response_type'] = 'plot'
#             response_payload['chart'] = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
#         else:
#             table_classes = (
#                 "w-full text-sm text-left text-slate-400 "
#                 "border-collapse border border-slate-700"
#             )
#             response_payload['response_type'] = 'table'
#             response_payload['table_html'] = result_df.to_html(
#                 classes=table_classes, border=0, index=False
#             )

#         return jsonify(response_payload)

#     except Exception as e:
#         error_message = f"An error occurred: {str(e)}"
#         if sql_query:
#             error_message += f"\n\nAttempted SQL Query:\n{sql_query}"
#         return jsonify({
#             'sql_query': sql_query,
#             'response_type': 'error',
#             'message': error_message
#         }), 500

# if __name__ == '__main__':
#     server.run(debug=True, port=5501)