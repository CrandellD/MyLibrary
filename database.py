import sqlite3
import pandas as pd
import streamlit as st
from datetime import datetime

def get_db_connection():
    """Create database connection"""
    conn = sqlite3.connect('myLibrary.db')
    conn.row_factory = sqlite3.Row
    return conn

def get_all_books():
    """Retrieve all books from database"""
    conn = None
    try:
        conn = get_db_connection()
        query = "SELECT * FROM MyBooks ORDER BY Title"
        books_df = pd.read_sql_query(query, conn)

        return books_df
    except Exception as e:
        st.error(f"Database error: {e}")
        return pd.DataFrame()
    finally:
        if conn:
            conn.close()

def add_book_to_database(book_data):
    """
    Insert a new book into the MyBooks table
    
    Args:
        book_data (dict): Dictionary containing book information with keys matching database columns
        
    Returns:
        tuple: (success: bool, message: str)
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check for duplicate ISBN
        cursor.execute("SELECT COUNT(*) FROM MyBooks WHERE ISBNCode = ?", (book_data.get('ISBNCode'),))
        if cursor.fetchone()[0] > 0:
            conn.close()
            return False, f"Book with ISBN {book_data.get('ISBNCode')} already exists in database"
        
        # Prepare insert statement
        insert_sql = """
            INSERT INTO MyBooks (
                Title, Subtitle, Author, ISBNCode, Publisher, PublishedDate, 
                Length, Memo, Rating, Description, ImageURL, Excerpt,
                DateAdded, LastModified
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        # Get current timestamp
        from datetime import datetime
        current_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Prepare values tuple
        values = (
            book_data.get('Title'),
            book_data.get('Subtitle'),
            book_data.get('Author'),
            book_data.get('ISBNCode'),
            book_data.get('Publisher'),
            book_data.get('PublishedDate'),
            book_data.get('Length'),
            book_data.get('Memo'),
            book_data.get('Rating'),  # Will be None for new entries
            book_data.get('Description'),
            book_data.get('ImageURL'),
            book_data.get('Excerpt'),  # First excerpt only
            current_timestamp,  # DateAdded
            current_timestamp   # LastModified
        )
        
        # Execute insert
        cursor.execute(insert_sql, values)
        conn.commit()
        conn.close()
        
        return True, f"Successfully added '{book_data.get('Title')}' to library"

    except Exception as e:
        return False, f"Database error: {str(e)}"

def get_book_by_isbn(isbn):
    """Get a single book by ISBN"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM MyBooks WHERE ISBNCode = ?", (isbn,))
    row = cursor.fetchone()
    
    if row:
        # Convert row to dictionary using column names
        columns = [description[0] for description in cursor.description]
        book_dict = dict(zip(columns, row))
    else:
        book_dict = None
    
    conn.close()
    return book_dict

def update_book_in_database(book_data):
    """Update an existing book in the database"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Update query - using ISBNCode to identify the record
        cursor.execute("""
            UPDATE MyBooks 
            SET Title = ?, 
                Subtitle = ?, 
                Author = ?, 
                Publisher = ?, 
                PublishedDate = ?, 
                Length = ?, 
                Memo = ?, 
                Rating = ?, 
                Description = ?, 
                ImageURL = ?, 
                Excerpt = ?,
                LastModified = datetime('now')
            WHERE ISBNCode = ?
        """, (
            book_data.get('Title'),
            book_data.get('Subtitle'),
            book_data.get('Author'),
            book_data.get('Publisher'),
            book_data.get('PublishedDate'),
            book_data.get('Length'),
            book_data.get('Memo'),
            book_data.get('Rating'),
            book_data.get('Description'),
            book_data.get('ImageURL'),
            book_data.get('Excerpt'),
            book_data.get('ISBNCode')
        ))
        
        conn.commit()
        conn.close()
        
        return True, f"Successfully updated '{book_data.get('Title')}'"
        
    except Exception as e:
        return False, f"Error updating book: {str(e)}"

def get_delete_pin():
    """
    Retrieve the deletion PIN from the Settings table
    
    Returns:
        str: The PIN as a string, or None if not found
    """
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Query only the PIN column from Settings table where ID=1
        # Table has ID, PIN, DateModified columns but we only need PIN
        cursor.execute("SELECT PIN FROM Settings WHERE ID = 1")
        result = cursor.fetchone()
        
        if result:
            # result[0] contains the PIN value from our SELECT query
            return result[0]
        else:
            return None
            
    except Exception as e:
        st.error(f"Error retrieving PIN: {e}")
        return None
    finally:
        if conn:
            conn.close()

def delete_book_from_database(isbn):
    """
    Permanently delete a book from the database using its ISBN
    This is a hard delete - the record is completely removed
    
    Args:
        isbn (str): The ISBN of the book to delete
        
    Returns:
        tuple: (success: bool, message: str)
    """
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # First get the book title for the confirmation message
        cursor.execute("SELECT Title FROM MyBooks WHERE ISBNCode = ?", (isbn,))
        result = cursor.fetchone()
        
        if not result:
            return False, f"No book found with ISBN {isbn}"
        
        # result[0] contains the Title from our SELECT query
        book_title = result[0]
        
        # Permanently delete the book record
        cursor.execute("DELETE FROM MyBooks WHERE ISBNCode = ?", (isbn,))
        conn.commit()
        
        # Verify the book was actually deleted
        cursor.execute("SELECT COUNT(*) FROM MyBooks WHERE ISBNCode = ?", (isbn,))
        count = cursor.fetchone()[0]
        
        if count == 0:
            return True, f"Successfully deleted '{book_title}'"
        else:
            return False, f"Failed to delete '{book_title}' - book still exists"
            
    except Exception as e:
        return False, f"Database error during deletion: {str(e)}"
    finally:
        if conn:
            conn.close()