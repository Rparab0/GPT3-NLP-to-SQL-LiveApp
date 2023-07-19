import pandas as pd
import openai
import streamlit as st
import traceback
from sqlalchemy import create_engine, text

# Set up OpenAI API key
openai.api_key = "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"

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

# Helper function for NLP-to-SQL conversion
def convert_text_to_sql(nlp_text, csv_file):
    try:
        # Retrieve the input data from the request
        if not csv_file:
            return {'error': 'No CSV file selected.'}, 400

        # Read the CSV file
        try:
            df = pd.read_csv(csv_file)
            print("DataFrame Contents:", df.head())  # Add this line to check the DataFrame

        except Exception as e:
            traceback.print_exc()
            return {'error': 'Failed to read CSV file.'}, 400

        if df.empty:
            return {'error': 'The DataFrame is empty.'}, 400

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

        # Return the SQL query and table HTML as a dictionary
        return {'sql_query': sql_query, 'results': results}

    except Exception as e:
        traceback.print_exc()
        return {'error': 'An error occurred during the conversion process.'}, 500

# Define the Streamlit app
def main():
    st.title('NLP-to-SQL Conversion App')
    st.write('Enter your query and upload a CSV file to generate SQL queries and view results.')

    # Input Form
    nlp_text = st.text_area('Enter your query:')
    csv_file = st.file_uploader('Upload CSV file:', type=['csv'])

    if st.button('Submit'):
        if csv_file is None:
            st.error('Please upload a CSV file.')
        else:
            # Send the user input to the Streamlit app for processing
            response = convert_text_to_sql(nlp_text, csv_file)

            if 'error' in response:
                st.error(response['error'])
            else:
                st.write('Generated SQL Query:')
                st.code(response['sql_query'], language='sql')

                st.write('Results:')
                st.dataframe(response['results'])

if __name__ == '__main__':
    main()
