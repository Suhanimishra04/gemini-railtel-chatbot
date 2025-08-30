Gemini x RailTel Chatbot 🚉🤖

This project is a FastAPI + Gemini-powered chatbot designed for interacting with RailTel’s inventory data (e.g., POPs and equipment). It allows users to ask natural language questions like:

"Which location has the highest number of switches?"

"Show me all equipment from Odisha."

"Count of routers by OEM name."

The system interprets the query, maps it to database entities, and fetches results using REST API endpoints.

🔹 Features

FastAPI backend for handling POP and equipment data.

SQLite database with pop_view and equipment_view.

Gemini LLM integration to interpret natural language queries.

Dynamic intent + filter extraction (e.g., location-based queries).

Structured API calls from chatbot to FastAPI endpoints.

ORM-based queries for database interaction.

🔹 Tech Stack

Backend: FastAPI (Python)

Database: SQLite

LLM: Gemini API (Google)

ORM: SQLAlchemy

Frontend: CLI-based chatbot (can be extended to web UI)

🔹 Project Structure
📂 project-root
 ┣ 📂 app
 ┃ ┣ main.py                # FastAPI entry point
 ┃ ┣ chatbot_main.py        # Chatbot logic + Gemini integration
 ┃ ┣ country_fetcher.py     # Utility for country/location filters
 ┃ ┣ prompt_builder.py      # Constructs prompts for Gemini
 ┃ ┣ llm_handler.py         # Handles Gemini API responses
 ┃ ┣ models.py              # ORM models for pop & equipment
 ┃ ┣ database.py            # DB connection setup
 ┣ 📂 data
 ┃ ┣ equipment_view.csv     # Sample equipment data
 ┃ ┣ pop_view.csv           # Sample POP data
 ┣ .env                     # API keys and environment variables
 ┣ requirements.txt         # Python dependencies
 ┣ README.md                # Project documentation