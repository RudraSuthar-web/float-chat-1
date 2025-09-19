# import pandas as pd
# import sqlalchemy
# import re
# import os
# from langchain_chroma import Chroma
# from langchain_huggingface import HuggingFaceEmbeddings
# from langchain_groq import ChatGroq
# from langchain_core.runnables import RunnablePassthrough
# from langchain_core.output_parsers import StrOutputParser
# from langchain.prompts import ChatPromptTemplate
# from thefuzz import process

# # --- Configuration ---
# DB_PATH = "sqlite:///argo.db"
# CHROMA_PATH = "./chroma_db"
# MODEL_NAME = "openai/gpt-oss-20b"
# SCHEMA = """
# Table: profiles
# Columns:
# - float_id (text), PRES (float), TEMP (float), PSAL (float),
# - LATITUDE (float), LONGITUDE (float), TIME (datetime), profile_id (integer)
# """

# # --- 1. PRE-DEFINED, GUARANTEED-TO-WORK QUERIES ---
# PREDEFINED_QUERIES = {
#     "plot all float locations": "SELECT float_id, LATITUDE, LONGITUDE FROM profiles GROUP BY float_id;",
#     "how many unique floats are there": "SELECT COUNT(DISTINCT float_id) as unique_floats FROM profiles;",
#     "what is the average temperature": "SELECT AVG(TEMP) as average_temperature FROM profiles;",
#     "show me the five deepest measurements": "SELECT * FROM profiles ORDER BY PRES DESC LIMIT 5;",
#     "show temperature and salinity profiles deeper than 1000 dbar": "SELECT PRES, TEMP, PSAL FROM profiles WHERE PRES > 1000 LIMIT 500;",
#     "where is float 1900085": "SELECT float_id, LATITUDE, LONGITUDE FROM profiles WHERE float_id = '1900085' GROUP BY float_id;",
#     "list all data for float 1900085": "SELECT * FROM profiles WHERE float_id = '1900085' LIMIT 500;",
#     "what is the maximum salinity": "SELECT MAX(PSAL) as max_salinity FROM profiles;",
#     "what were the coordinates for the shallowest measurement": "SELECT LATITUDE, LONGITUDE, PRES FROM profiles ORDER BY PRES ASC LIMIT 1;"
# }


# # --- Load API Key ---
# groq_api_key = os.getenv("GROQ_API_KEY")
# if not groq_api_key:
#     raise ValueError("GROQ_API_KEY environment variable not set!")

# # --- Pre-load all AI components (for fallback) ---
# print("➡️ Initializing AI models for fallback...")
# llm = ChatGroq(groq_api_key=groq_api_key, model_name=MODEL_NAME, temperature=0)
# embedding_function = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
# vectorstore = Chroma(persist_directory=CHROMA_PATH, embedding_function=embedding_function)
# # --- THIS IS THE FIX ---
# retriever = vectorstore.as_retriever(search_kwargs={"k": 3})
# # -----------------------

# # --- AI Chain (Now only used as a fallback) ---
# sql_prompt_template = """
# You are an expert SQLite data analyst. Your goal is to write a single, valid, and simple SQLite query to answer the user's question.
# - **CRITICAL RULE**: You MUST generate only ONE single `SELECT` statement.
# - **CRITICAL RULE**: Do NOT use `UNION` or `WITH` clauses.
# - For queries that might return many rows, add a 'LIMIT 500' clause.
# Here is the database schema: <schema>{schema}</schema>
# Here are a few examples of good, simple queries. <examples>{examples}</examples>
# Return ONLY the SQL query and nothing else.
# Question: {question}
# SQL Query:
# """
# sql_prompt = ChatPromptTemplate.from_template(sql_prompt_template)

# def format_retrieved_docs(docs):
#     return "\n\n".join(f"Question: {doc.page_content}\nSQL Query: {doc.metadata['sql_query']}" for doc in docs)

# def clean_sql_query(query: str):
#     cleaned_query = re.sub(r"```sql\n|```|sql", "", query, flags=re.IGNORECASE).strip()
#     if not cleaned_query.endswith(';'):
#         cleaned_query += ';'
#     return cleaned_query

# sql_chain = (
#     RunnablePassthrough.assign(examples=lambda x: format_retrieved_docs(retriever.get_relevant_documents(x["question"])))
#     | sql_prompt | llm | StrOutputParser() | clean_sql_query
# )
# print("✅ AI models initialized.")

# # --- Main Backend Functions ---
# def get_sql_query(user_question: str) -> str:
#     """
#     NEW HYBRID LOGIC:
#     1. Tries to find a matching pre-defined query.
#     2. If no good match, falls back to the AI.
#     """
#     # Sanitize user input
#     question = user_question.lower().strip()

#     # Use fuzzy matching to find the best pre-defined question
#     best_match, score = process.extractOne(question, PREDEFINED_QUERIES.keys())

#     # If the match is good enough (score > 80), use the guaranteed query.
#     if score > 80:
#         print(f"➡️ Found pre-defined match with score {score}: '{best_match}'")
#         return PREDEFINED_QUERIES[best_match]
    
#     # Otherwise, fall back to the AI
#     print("➡️ No pre-defined match found. Falling back to AI model...")
#     query = sql_chain.invoke({"question": question, "schema": SCHEMA})
    
#     # Final safety checks on the AI's output
#     if "union" in query.lower():
#         raise ValueError("The AI generated a complex query that is not supported. Please ask a simpler question.")
#     if not query or query.strip() == ';':
#         raise ValueError("I could not understand your question. Please try rephrasing it.")
        
#     return query

# def generate_summary(question: str, df: pd.DataFrame) -> str:
#     if df.empty: return "No data was returned, so no summary can be generated."

#     if df.shape == (1, 1):
#         single_value = df.iloc[0, 0]
#         # Use a simple f-string for summaries of single values to avoid another AI call
#         return f"The answer to your question is: {single_value}"
#     else:
#         # For tables, we still use the AI for a nice summary
#         data_string = df.to_string(index=False, max_rows=10)
#         summary_chain = (ChatPromptTemplate.from_template(
#             'You are a helpful oceanography assistant. The user asked: "{question}". The data is:\n{data}\nProvide a brief, insightful summary.'
#         ) | llm | StrOutputParser())
#         return summary_chain.invoke({"question": question, "data": data_string})

# def execute_sql_query(query: str) -> pd.DataFrame:
#     engine = sqlalchemy.create_engine(DB_PATH)
#     try:
#         return pd.read_sql(query, engine)
#     except Exception as e:
#         print(f"Error executing SQL query: {e}")
#         raise e

# def get_visualization_suggestion(df: pd.DataFrame) -> str:
#     columns = {col.lower() for col in df.columns}
#     if 'latitude' in columns and 'longitude' in columns:
#         return 'map'
#     if 'pres' in columns and ('temp' in columns or 'psal' in columns):
#         return 'profile_plot'
#     return 'table'

import pandas as pd
import sqlalchemy
from sqlalchemy import create_engine
import numpy as np
import re
import os
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_groq import ChatGroq
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from langchain.prompts import ChatPromptTemplate
from thefuzz import process
from dotenv import load_dotenv

# --- Load environment variables ---
load_dotenv()  # Load variables from .env file

# --- Configuration ---
DB_PATH = "sqlite:///argo.db"
CHROMA_PATH = "./chroma_db"
MODEL_NAME = "openai/gpt-oss-20b"
SCHEMA = """
Table: profiles
Columns:
- float_id (text), PRES (float), TEMP (float), PSAL (float),
- LATITUDE (float), LONGITUDE (float), TIME (datetime), profile_id (integer)
"""

# --- 1. PRE-DEFINED, GUARANTEED-TO-WORK QUERIES ---
PREDEFINED_QUERIES = {
    "plot all float locations": "SELECT float_id, LATITUDE, LONGITUDE FROM profiles GROUP BY float_id;",
    "how many unique floats are there": "SELECT COUNT(DISTINCT float_id) as unique_floats FROM profiles;",
    "what is the average temperature": "SELECT AVG(TEMP) as average_temperature FROM profiles;",
    "show me the five deepest measurements": "SELECT * FROM profiles ORDER BY PRES DESC LIMIT 5;",
    "show temperature and salinity profiles deeper than 1000 dbar": "SELECT PRES, TEMP, PSAL FROM profiles WHERE PRES > 1000 LIMIT 500;",
    "where is float 1900085": "SELECT float_id, LATITUDE, LONGITUDE FROM profiles WHERE float_id = '1900085' GROUP BY float_id;",
    "list all data for float 1900085": "SELECT * FROM profiles WHERE float_id = '1900085' LIMIT 500;",
    "what is the maximum salinity": "SELECT MAX(PSAL) as max_salinity FROM profiles;",
    "what were the coordinates for the shallowest measurement": "SELECT LATITUDE, LONGITUDE, PRES FROM profiles ORDER BY PRES ASC LIMIT 1;"
}

# --- Load API Key ---
groq_api_key = os.getenv("GROQ_API_KEY")
if not groq_api_key:
    raise ValueError("GROQ_API_KEY environment variable not set!")

# --- Pre-load all AI components (for fallback) ---
print("➡️ Initializing AI models for fallback...")
llm = ChatGroq(groq_api_key=groq_api_key, model_name=MODEL_NAME, temperature=0)
embedding_function = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
vectorstore = Chroma(persist_directory=CHROMA_PATH, embedding_function=embedding_function)
# --- THIS IS THE FIX ---
retriever = vectorstore.as_retriever(search_kwargs={"k": 3})
# -----------------------

# --- AI Chain (Now only used as a fallback) ---
sql_prompt_template = """
You are an expert SQLite data analyst. Your goal is to write a single, valid, and simple SQLite query to answer the user's question.
- **CRITICAL RULE**: You MUST generate only ONE single `SELECT` statement.
- **CRITICAL RULE**: Do NOT use `UNION` or `WITH` clauses.
- For queries that might return many rows, add a 'LIMIT 500' clause.
Here is the database schema: <schema>{schema}</schema>
Here are a few examples of good, simple queries. <examples>{examples}</examples>
Return ONLY the SQL query and nothing else.
Question: {question}
SQL Query:
"""
sql_prompt = ChatPromptTemplate.from_template(sql_prompt_template)

def format_retrieved_docs(docs):
    return "\n\n".join(f"Question: {doc.page_content}\nSQL Query: {doc.metadata['sql_query']}" for doc in docs)

def clean_sql_query(query: str):
    cleaned_query = re.sub(r"```sql\n|```|sql", "", query, flags=re.IGNORECASE).strip()
    if not cleaned_query.endswith(';'):
        cleaned_query += ';'
    return cleaned_query

sql_chain = (
    RunnablePassthrough.assign(examples=lambda x: format_retrieved_docs(retriever.get_relevant_documents(x["question"])))
    | sql_prompt | llm | StrOutputParser() | clean_sql_query
)
print("✅ AI models initialized.")

# --- Main Backend Functions ---
def get_sql_query(user_question: str) -> str:
    """
    NEW HYBRID LOGIC:
    1. Tries to find a matching pre-defined query.
    2. If no good match, falls back to the AI.
    """
    # Sanitize user input
    question = user_question.lower().strip()

    # Use fuzzy matching to find the best pre-defined question
    best_match, score = process.extractOne(question, PREDEFINED_QUERIES.keys())

    # If the match is good enough (score > 80), use the guaranteed query.
    if score > 80:
        print(f"➡️ Found pre-defined match with score {score}: '{best_match}'")
        return PREDEFINED_QUERIES[best_match]
    
    # Otherwise, fall back to the AI
    print("➡️ No pre-defined match found. Falling back to AI model...")
    query = sql_chain.invoke({"question": question, "schema": SCHEMA})
    
    # Final safety checks on the AI's output
    if "union" in query.lower():
        raise ValueError("The AI generated a complex query that is not supported. Please ask a simpler question.")
    if not query or query.strip() == ';':
        raise ValueError("I could not understand your question. Please try rephrasing it.")
        
    return query

def generate_summary(question: str, df: pd.DataFrame) -> str:
    if df.empty: return "No data was returned, so no summary can be generated."

    if df.shape == (1, 1):
        single_value = df.iloc[0, 0]
        # Use a simple f-string for summaries of single values to avoid another AI call
        return f"The answer to your question is: {single_value}"
    else:
        # For tables, we still use the AI for a nice summary
        data_string = df.to_string(index=False, max_rows=10)
        summary_chain = (ChatPromptTemplate.from_template(
            'You are a helpful oceanography assistant. The user asked: "{question}". The data is:\n{data}\nProvide a brief, insightful summary.'
        ) | llm | StrOutputParser())
        return summary_chain.invoke({"question": question, "data": data_string})

def execute_sql_query(query: str) -> pd.DataFrame:
    engine = sqlalchemy.create_engine(DB_PATH)
    try:
        return pd.read_sql(query, engine)
    except Exception as e:
        print(f"Error executing SQL query: {e}")
        raise e

def get_visualization_suggestion(df: pd.DataFrame) -> str:
    columns = {col.lower() for col in df.columns}
    if 'latitude' in columns and 'longitude' in columns:
        return 'map'
    if 'pres' in columns and ('temp' in columns or 'psal' in columns):
        return 'profile_plot'
    return 'table'

def fetch_all_float_ids():
    """
    Fetch all unique float IDs from the database.
    """
    engine = create_engine('sqlite:///argo.db')
    query = "SELECT DISTINCT float_id FROM profiles"
    df = pd.read_sql(query, engine)
    return df['float_id'].tolist()

def fetch_comparison_data(float_ids):
    """
    Fetch temperature, salinity, and pressure data for given float IDs.
    float_ids: List of float IDs or a single float ID.
    """
    engine = create_engine('sqlite:///argo.db')
    if not isinstance(float_ids, list):
        float_ids = [float_ids]
    placeholders = '?' * len(float_ids)
    query = f"""
    SELECT float_id, PRES AS PRES, TEMP AS TEMP, PSAL AS PSAL
    FROM profiles
    WHERE float_id IN ({placeholders})
    """
    params = tuple(float_ids)
    df = pd.read_sql(query, engine, params=params)
    return df