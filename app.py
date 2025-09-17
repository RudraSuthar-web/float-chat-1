from flask import Flask, render_template, request, jsonify, send_from_directory
import pandas as pd
import plotly.express as px
import plotly.utils
import json
import backend

app = Flask(__name__)

@app.route('/')
def index():
    """Serves the landing page."""
    return send_from_directory('static', 'index.html')

@app.route('/dashboard')
def dashboard():
    """Serves the main chat dashboard."""
    return render_template('dashboard.html')

@app.route('/chat', methods=['POST'])
def chat():
    user_question = request.json.get('question')
    if not user_question:
        return jsonify({'error': 'No question provided'}), 400

    sql_query = ""
    try:
        # Step 1: Generate SQL Query
        sql_query = backend.generate_sql_query_with_rag(user_question)

        # Step 2: Execute the query
        result_df = backend.execute_sql_query(sql_query)

        response_payload = {'sql_query': sql_query}

        if result_df.empty:
            response_payload.update({
                'response_type': 'message',
                'message': 'Your query returned no results. Please try a different question.'
            })
            return jsonify(response_payload)

        # Step 3: Generate a summary of the results
        summary = backend.generate_summary(user_question, result_df)
        response_payload['summary'] = summary

        # Step 4: Determine visualization type and generate plot/data
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