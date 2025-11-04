import psycopg2
from psycopg2.extras import RealDictCursor
import pandas as pd
import streamlit as st
from datetime import datetime
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def get_db_connection():
    """Create standard database connection (for pandas)"""
    conn = psycopg2.connect(os.getenv('NEON_CONNECTION_STRING'))
    return conn

def get_db_connection_dict():
    """Create database connection with dict cursor (for individual operations)"""
    conn = psycopg2.connect(
        os.getenv('NEON_CONNECTION_STRING'),
        cursor_factory=RealDictCursor
    )
    return conn

def get_all_books():
    """Retrieve all books from database"""
    conn = None
    try:
        conn = get_db_connection()
        query = "SELECT * FROM MyBooks ORDER BY title"
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
        cursor.execute("SELECT COUNT(*) FROM MyBooks WHERE ISBNCode = %s", (book_data.get('isbncode'),))
        if cursor.fetchone()[0] > 0:
            conn.close()
            return False, f"Book with ISBN {book_data.get('isbncode')} already exists in database"
        
        # Prepare insert statement
        insert_sql = """
            INSERT INTO MyBooks (
                Title, Subtitle, Author, ISBNCode, Publisher, PublishedDate, 
                Length, Memo, Rating, Description, ImageURL, Excerpt,
                DateAdded, LastModified
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        # Get current timestamp
        current_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Prepare values tuple
        values = (
            book_data.get('title'),
            book_data.get('subtitle'),
            book_data.get('author'),
            book_data.get('isbncode'),
            book_data.get('publisher'),
            book_data.get('publisheddate'),
            book_data.get('length'),
            book_data.get('memo'),
            book_data.get('rating'),
            book_data.get('description'),
            book_data.get('imageurl'),
            book_data.get('excerpt'),
            current_timestamp,
            current_timestamp
        )
        
        # Execute insert
        cursor.execute(insert_sql, values)
        conn.commit()
        conn.close()
        
        return True, f"Successfully added '{book_data.get('title')}' to library"

    except Exception as e:
        return False, f"Database error: {str(e)}"

def get_book_by_isbn(isbn):
    """Get a single book by ISBN"""
    conn = get_db_connection_dict()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM MyBooks WHERE ISBNCode = %s", (isbn,))
    row = cursor.fetchone()
    
    if row:
        book_dict = dict(row)
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
            SET Title = %s, 
                Subtitle = %s, 
                Author = %s, 
                Publisher = %s, 
                PublishedDate = %s, 
                Length = %s, 
                Memo = %s, 
                Rating = %s, 
                Description = %s, 
                ImageURL = %s, 
                Excerpt = %s,
                LastModified = CURRENT_TIMESTAMP
            WHERE ISBNCode = %s
        """, (
            book_data.get('title'),
            book_data.get('subtitle'),
            book_data.get('author'),
            book_data.get('publisher'),
            book_data.get('publisheddate'),
            book_data.get('length'),
            book_data.get('memo'),
            book_data.get('rating'),
            book_data.get('description'),
            book_data.get('imageurl'),
            book_data.get('excerpt'),
            book_data.get('isbncode')
        ))
        
        conn.commit()
        conn.close()
        
        return True, f"Successfully updated '{book_data.get('title')}'"
        
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
        conn = get_db_connection_dict()
        cursor = conn.cursor()
        
        cursor.execute("SELECT PIN FROM Settings WHERE ID = %s", (1,))
        result = cursor.fetchone()
        
        if result:
            return result['pin']
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
        conn = get_db_connection_dict()
        cursor = conn.cursor()
        
        # First get the book title for the confirmation message
        cursor.execute("SELECT Title FROM MyBooks WHERE ISBNCode = %s", (isbn,))
        result = cursor.fetchone()
        
        if not result:
            return False, f"No book found with ISBN {isbn}"
        
        book_title = result['title']
        
        # Permanently delete the book record
        cursor.execute("DELETE FROM MyBooks WHERE ISBNCode = %s", (isbn,))
        conn.commit()
        
        # Verify the book was actually deleted
        cursor.execute("SELECT COUNT(*) FROM MyBooks WHERE ISBNCode = %s", (isbn,))
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