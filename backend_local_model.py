import pandas as pd
import sqlalchemy
import re
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_ollama import ChatOllama
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from langchain.prompts import ChatPromptTemplate

# --- Configuration ---
DB_PATH = "sqlite:///argo.db"
CHROMA_PATH = "./chroma_db"
MODEL_NAME = 'phi3:3.8b-mini-4k-instruct-q4_K_M'
SCHEMA = """
Table: profiles
Columns:
- float_id (text): Float identifier
- PRES (float): Pressure/depth in dbar
- TEMP (float): Temperature in Celsius
- PSAL (float): Salinity in PSU
- LATITUDE (float): Latitude in degrees
- LONGITUDE (float): Longitude in degrees
- TIME (datetime): Measurement time
- profile_id (integer): Profile index
"""

# --- Connections ---
embedding_function = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
vectorstore = Chroma(persist_directory=CHROMA_PATH, embedding_function=embedding_function)
retriever = vectorstore.as_retriever(search_kwargs={"k": 3})
llm = ChatOllama(model=MODEL_NAME, temperature=0)

# --- Chain 1: SQL Generation RAG Chain ---
sql_prompt_template = """
You are an expert SQLite data analyst. Your goal is to write a single, valid SQLite query to answer the user's question based on the database schema.

Here is the database schema:
<schema>
{schema}
</schema>

Here are a few examples of questions and their corresponding SQL queries. Use them to learn the format and style.
<examples>
{examples}
</examples>

Now, answer the following question. Return ONLY the SQL query. Do not include any other text, explanations, or markdown formatting.

Question: {question}
SQL Query:
"""
sql_prompt = ChatPromptTemplate.from_template(sql_prompt_template)

def format_retrieved_docs(docs):
    return "\n\n".join(f"Question: {doc.page_content}\nSQL Query: {doc.metadata['sql_query']}" for doc in docs)

def clean_sql_query(query: str) -> str:
    """NEW: Aggressively cleans the LLM's SQL output."""
    # Remove markdown backticks and the word 'sql'
    cleaned_query = re.sub(r"```sql\n|```|sql", "", query, flags=re.IGNORECASE)
    # Find the first SELECT statement, as the LLM might add conversational text before it.
    select_match = re.search(r"SELECT.*?;", cleaned_query, re.DOTALL | re.IGNORECASE)
    if select_match:
        return select_match.group(0).strip()
    return cleaned_query.strip() # Fallback to simple stripping

sql_chain = (
    RunnablePassthrough.assign(
        examples=lambda x: format_retrieved_docs(retriever.get_relevant_documents(x["question"]))
    )
    | sql_prompt
    | llm
    | StrOutputParser()
    | clean_sql_query # NEW: Add the cleaning step to the chain
)

# --- Chain 2: Data Summarization Chain ---
summary_prompt_template = """
You are a helpful oceanography assistant. The user asked the following question:
"{question}"

A database query returned the following data:
{data}

Based on this data, provide a brief, insightful summary for a non-technical person.
If the data is a single value (like an average), state it clearly.
If the data has locations, mention the general area.
If the data is a table of results, describe the key findings.
Do not mention SQL or the database. Just explain what the data means.
"""
summary_prompt = ChatPromptTemplate.from_template(summary_prompt_template)

summary_chain = summary_prompt | llm | StrOutputParser()

# --- Main Backend Functions ---
def generate_sql_query_with_rag(user_question: str) -> str:
    response = sql_chain.invoke({
        "question": user_question,
        "schema": SCHEMA
    })
    return response

def generate_summary(question: str, df: pd.DataFrame) -> str:
    """NEW: Generates a summary of the dataframe."""
    if df.empty:
        return "No data was returned, so no summary can be generated."
    # Convert dataframe to a string format suitable for the LLM
    data_string = df.to_string(index=False, max_rows=10)
    response = summary_chain.invoke({
        "question": question,
        "data": data_string
    })
    return response

def execute_sql_query(query: str) -> pd.DataFrame:
    """Modified to raise exceptions on failure."""
    engine = sqlalchemy.create_engine(DB_PATH)
    try:
        result_df = pd.read_sql(query, engine)
        return result_df
    except Exception as e:
        print(f"Error executing SQL query: {e}")
        # Let the exception propagate to the Flask app for better error handling
        raise e

def get_visualization_suggestion(df: pd.DataFrame) -> str:
    columns = {col.lower() for col in df.columns}
    if 'latitude' in columns and 'longitude' in columns and len(df) > 1:
        return 'map'
    if 'pres' in columns and ('temp' in columns or 'psal' in columns):
        return 'profile_plot'
    return 'table'