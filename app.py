import pandas as pd
from flask import Flask, request, jsonify, render_template
from sqlalchemy import create_engine, text
import openai
import traceback

app = Flask(__name__)

# Set up OpenAI API key
openai.api_key = "Your Open api key"

# Prompt to define table structure for GPT


def create_table_definition_prompt(df):
    columns = ",".join(f"`{column}` TEXT" for column in df.columns)
    prompt = f"### sqlite SQL table, with its properties:\n\n# Data({columns})\n\n"
    return prompt

# Combine prompts for GPT


def combine_prompts(df, query_prompt):
    definition = create_table_definition_prompt(df)
    query_init_string = f"### A query to answer: {query_prompt}\nSELECT"
    return definition + query_init_string

# Handle GPT response


def handle_response(response):
    query = response["choices"][0]["text"]
    if query.startswith(" "):
        query = "SELECT" + query
    return query

# Flask route to render the HTML template


@app.route('/')
def index():
    return render_template('index.html')

# Flask route to handle NLP-to-SQL conversion


@app.route('/convert', methods=['POST'])
def convert_text_to_sql():
    try:
        # Retrieve the input data from the request
        nlp_text = request.form.get('text')
        csv_file = request.files.get('csv')

        if not csv_file:
            return jsonify({'error': 'No CSV file selected.'}), 400

        # Read the CSV file
        try:
            df = pd.read_csv(csv_file)
        except Exception as e:
            traceback.print_exc()
            return jsonify({'error': 'Failed to read CSV file.'}), 400

        # Set up SQL database
        temp_db = create_engine('sqlite:///:memory:', echo=True)
        df.to_sql(name='Data', con=temp_db, index=False)

        # Set up GPT prompt
        prompt = combine_prompts(df, nlp_text)

        # Call OpenAI API to generate SQL query
        response = openai.Completion.create(
            model="text-davinci-003",
            prompt=prompt,
            temperature=0,
            max_tokens=150,
            top_p=1.0,
            frequency_penalty=0.0,
            presence_penalty=0.0,
            stop=["#", ";"]
        )

        # Convert GPT response to SQL query
        sql_query = handle_response(response)

        # Execute SQL query in the database
        with temp_db.connect() as conn:
            result = conn.execute(text(sql_query))
            rows = result.fetchall()

        # Convert rows to list of dictionaries
        columns = result.keys()
        results = [dict(zip(columns, row)) for row in rows]

        # Create an HTML table
        table_html = '<table>'
        table_html += '<tr><th>' + '</th><th>'.join(columns) + '</th></tr>'
        for result in results:
            table_html += '<tr>'
            for column in columns:
                table_html += '<td>' + str(result[column]) + '</td>'
            table_html += '</tr>'
        table_html += '</table>'

        # Return the SQL query and table HTML as a JSON response
        return jsonify({'sql_query': sql_query, 'results': results, 'table_html': table_html})

    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': 'An error occurred during the conversion process.'}), 500


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)
