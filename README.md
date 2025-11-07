## Personal Library Management System - 

A web application to catalog and manage your family's book collection. The system uses Streamlit for the frontend interface, PostgreSQL database hosted on Neon for cloud storage, and integrates with OpenLibrary and Google Books APIs for automatic metadata retrieval via ISBN lookup. The application is deployed on Streamlit Cloud with features including dual view modes (card/table), pagination, search/filter capabilities, book editing with navigation continuity, PIN-protected deletion, and a read-only view mode. The system evolved from a local SQLite prototype to a production cloud application, following a structured five-phase development approach with modular file architecture for maintainability.

## Features
- View collection in table or card layout
- Add books via ISBN lookup (OpenLibrary API)
- Search and filter books
- Edit and delete entries
- Pagination support

## Database
PostgreSQL database with book metadata including title, author, ISBN, publisher, ratings, and cover images.

## Installation
```bash
pip install -r requirements.txt
streamlit run myLibrary.py
```

## Live Demo
...
