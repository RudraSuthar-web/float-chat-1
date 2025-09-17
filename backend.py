import pandas as pd
import sqlalchemy
import re
import os
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_groq import ChatGroq
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from langchain.prompts import ChatPromptTemplate

# --- Configuration ---
DB_PATH = "sqlite:///argo.db"
CHROMA_PATH = "./chroma_db"
# --- THE ONLY CHANGE IS ON THIS LINE ---
MODEL_NAME = "openai/gpt-oss-20b" # Reverted to the model you are using
# -----------------------------------------
SCHEMA = """
Table: profiles
Columns:
- float_id (text), PRES (float), TEMP (float), PSAL (float), 
- LATITUDE (float), LONGITUDE (float), TIME (datetime), profile_id (integer)
"""

# --- Load API Key ---
groq_api_key = os.getenv("GROQ_API_KEY")
if not groq_api_key:
    raise ValueError("GROQ_API_KEY environment variable not set!")

# --- Pre-load all AI components ---
print("➡️ Initializing AI models via Groq API, please wait...")

embedding_function = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
vectorstore = Chroma(persist_directory=CHROMA_PATH, embedding_function=embedding_function)

llm = ChatGroq(
    groq_api_key=groq_api_key,
    model_name=MODEL_NAME,
    temperature=0
)
retriever = vectorstore.as_retriever(search_kwargs={"k": 3})

# --- Chain 1: SQL Generation RAG Chain ---
sql_prompt_template = """
You are an expert SQLite data analyst. Your goal is to write a single, valid SQLite query to answer the user's question based on the database schema.
Your queries should be performant. For queries that might return a very large number of rows, such as for plotting profiles or maps, add a 'LIMIT 500' clause to avoid overwhelming the system.
Here is the database schema: <schema>{schema}</schema>
Here are a few examples of questions and their corresponding SQL queries. Use them to learn the format and style. <examples>{examples}</examples>
Now, answer the following question. Return ONLY the SQL query and nothing else.
Question: {question}
SQL Query:
"""
sql_prompt = ChatPromptTemplate.from_template(sql_prompt_template)

def format_retrieved_docs(docs):
    return "\n\n".join(f"Question: {doc.page_content}\nSQL Query: {doc.metadata['sql_query']}" for doc in docs)

def clean_sql_query(query: str):
    cleaned_query = re.sub(r"```sql\n|```|sql", "", query, flags=re.IGNORECASE)
    select_match = re.search(r"SELECT.*?;", cleaned_query, re.DOTALL | re.IGNORECASE)
    return select_match.group(0).strip() if select_match else cleaned_query.strip()

sql_chain = (
    RunnablePassthrough.assign(examples=lambda x: format_retrieved_docs(retriever.get_relevant_documents(x["question"])))
    | sql_prompt | llm | StrOutputParser() | clean_sql_query
)

# --- Chain 2: Data Summarization Chains ---
summary_prompt_template = """
You are a helpful oceanography assistant. The user asked the following question: "{question}"
A database query returned the following data:
{data}
Based on this data, provide a brief, insightful summary for a non-technical person. Do not mention SQL or the database.
"""
summary_prompt = ChatPromptTemplate.from_template(summary_prompt_template)
summary_chain = summary_prompt | llm | StrOutputParser()

aggregate_summary_prompt_template = """
You are a helpful oceanography assistant. The user asked the following question: "{question}"
A database query returned a single value: {data}
Directly answer the user's question using this value. For example, if the question was "How many floats?" and the value is 138, the answer should be "There are 138 floats."
"""
aggregate_summary_prompt = ChatPromptTemplate.from_template(aggregate_summary_prompt_template)
aggregate_summary_chain = aggregate_summary_prompt | llm | StrOutputParser()


print("✅ AI models initialized successfully.")

# --- Main Backend Functions ---
def generate_sql_query_with_rag(user_question: str) -> str:
    return sql_chain.invoke({"question": user_question, "schema": SCHEMA})

def generate_summary(question: str, df: pd.DataFrame) -> str:
    if df.empty: return "No data was returned, so no summary can be generated."
    
    if df.shape == (1, 1):
        single_value = df.iloc[0, 0]
        return aggregate_summary_chain.invoke({"question": question, "data": str(single_value)})
    else:
        data_string = df.to_string(index=False, max_rows=10)
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