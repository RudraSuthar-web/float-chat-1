import chromadb
from langchain_community.embeddings import HuggingFaceEmbeddings

print("Initializing vector store...")

# These are high-quality examples of natural language questions and their corresponding SQL queries.
# This is the "knowledge" our RAG system will draw from.
examples = [
    {
        "question": "Show me the five deepest measurements.",
        "query": "SELECT * FROM profiles ORDER BY PRES DESC LIMIT 5;"
    },
    {
        "question": "What is the average temperature?",
        "query": "SELECT AVG(TEMP) as average_temperature FROM profiles;"
    },
    {
        "question": "List all data for float with ID 1900085.",
        "query": "SELECT * FROM profiles WHERE float_id = '1900085';"
    },
    {
        "question": "Find the maximum salinity recorded.",
        "query": "SELECT MAX(PSAL) as max_salinity FROM profiles;"
    },
    {
        "question": "How many unique floats are there?",
        "query": "SELECT COUNT(DISTINCT float_id) as unique_floats FROM profiles;"
    },
    {
        "question": "Show me temperature and salinity profiles deeper than 1000 dbar.",
        "query": "SELECT PRES, TEMP, PSAL FROM profiles WHERE PRES > 1000 LIMIT 100;"
    },
    {
        "question": "Plot all float locations.",
        "query": "SELECT float_id, LATITUDE, LONGITUDE FROM profiles GROUP BY float_id;"
    },
    {
        "question": "What were the coordinates for the shallowest measurement?",
        "query": "SELECT LATITUDE, LONGITUDE, PRES FROM profiles ORDER BY PRES ASC LIMIT 1;"
    }
]

# Use a local embedding model
embedding_function = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

# Initialize ChromaDB client. This will create the DB in a folder named 'chroma_db'
client = chromadb.PersistentClient(path="./chroma_db")
collection = client.get_or_create_collection(
    name="float-chat-rag-examples",
    embedding_function=None # We will handle embedding manually for clarity
)

print(f"Embedding {len(examples)} examples...")

# Embed each question and store it with the SQL query as metadata
ids = [str(i) for i in range(len(examples))]
questions = [ex["question"] for ex in examples]
queries = [ex["query"] for ex in examples]

# Generate embeddings for all questions in a batch
embeddings = embedding_function.embed_documents(questions)

# Add to the collection
collection.add(
    ids=ids,
    embeddings=embeddings,
    documents=questions,
    metadatas=[{"sql_query": q} for q in queries]
)

print("✅ Vector database created successfully with few-shot examples.")