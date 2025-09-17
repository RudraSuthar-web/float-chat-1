# FloatChat: AI-Powered ARGO Ocean Data Discovery

FloatChat is an AI-powered conversational interface that transforms how you interact with ARGO ocean data. Ask questions in natural language and get back instant summaries, tables, and interactive visualizations like maps and profile plots.

![FloatChat Dashboard Screenshot](https://i.imgur.com/r6s7i1O.png)

## The Problem

Oceanographic data, like the extensive dataset from the ARGO program, is vast, complex, and stored in specialized formats like NetCDF. Accessing and interpreting this data typically requires domain knowledge and technical skills, creating a barrier for researchers, students, and decision-makers.

## Our Solution

FloatChat bridges this gap by providing an intuitive chatbot interface. It leverages a Retrieval-Augmented Generation (RAG) pipeline to translate natural language questions into precise SQL queries. This allows non-technical users to effortlessly explore and visualize complex oceanographic data.

---

## Features

-   **Natural Language Queries**: Ask questions like "Plot all float locations" or "What is the average temperature deeper than 1000 dbar?".
-   **Intelligent Summaries**: Get concise, AI-generated summaries of the data returned by your query.
-   **Dynamic Visualizations**: Automatically generates interactive maps for location queries and profile plots for depth-based data.
-   **RAG-Powered Backend**: Uses a vector database with few-shot examples to help the LLM generate accurate SQL queries.
-   **Efficient Data Handling**: Processes raw NetCDF files into a query-optimized SQLite database with indexes for fast retrieval.

---

## Tech Stack

-   **Backend**: Python, Flask
-   **AI & Machine Learning**: LangChain, Groq API (Llama 3), ChromaDB, Sentence-Transformers
-   **Data Processing**: Pandas, Xarray, SQLAlchemy
-   **Frontend**: HTML, TailwindCSS, JavaScript
-   **Visualization**: Plotly.js

---

## Setup and Installation

Follow these steps to get FloatChat running on your local machine.

### 1. Clone the Repository

```bash
git clone [https://github.com/your-username/float-chat.git](https://github.com/your-username/float-chat.git)
cd float-chat
````

### 2\. Set Up Virtual Environment

This project uses `uv` for package management.

```bash
# Create a virtual environment
uv venv

# Activate the environment
source .venv/bin/activate
```

### 3\. Install Dependencies

```bash
uv pip install -r requirements.txt
```

### 4\. Set Up API Key

You need a Groq API key to run the AI backend.

  - Create a file named `.env`.
  - Add your API key to this file:

<!-- end list -->

```
GROQ_API_KEY="your_groq_api_key_here"
```

The application will automatically load this key.

### 5\. Prepare the Data

  - **Download ARGO Data**: Place your ARGO NetCDF (`.nc`) files into the root of the `float-chat` directory.

  - **Process Data into DB**: Run the `main.py` script to process the `.nc` files into a single `argo.db` database.

    ```bash
    python main.py
    ```

  - **Create Vector Store**: Run the `vector_db.py` script to create the ChromaDB vector store for the RAG system.

    ```bash
    python vector_db.py
    ```

  - **Add Database Indexes**: Run the `add_indexes.py` script to add indexes to the database for faster query performance.

    ```bash
    python add_indexes.py
    ```

### 6\. Run the Application

Start the Flask web server.

```bash
flask --app app run --port 5001
```

Open your browser and navigate to **`http://127.0.0.1:5001`** to start using FloatChat\!

-----

## Project Structure

```
float-chat/
├── app.py              # Main Flask application, handles routing and API endpoints.
├── backend.py            # Core logic for the RAG pipeline, LLM calls, and visualizations.
├── main.py               # Script to process .nc files into the SQLite database.
├── vector_db.py          # Script to create and populate the Chroma vector store.
├── add_indexes.py      # Script to add performance-boosting indexes to the database.
├── static/               # Contains frontend assets (CSS, JS, images).
│   ├── js/main.js        # Frontend logic for chat interface and Plotly rendering.
│   └── index.html        # The main landing page.
├── templates/
│   └── dashboard.html    # The chat dashboard interface.
├── argo.db               # (Generated) The SQLite database with ARGO data.
├── chroma_db/            # (Generated) The ChromaDB vector store.
├── requirements.txt      # List of Python dependencies.
└── .gitignore            # Specifies files and directories to be ignored by Git.