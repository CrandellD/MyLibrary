"""
API calls for Personal Library Management System
Handles external API integrations for book metadata retrieval
"""

import requests
import json
from typing import Optional, Dict, Any

def get_openlibrary_book_data(isbn: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve book data from OpenLibrary API using ISBN
    
    Args:
        isbn (str): ISBN-10 or ISBN-13 of the book
        
    Returns:
        dict: Book data dictionary with standardized field names, or None if not found
    """
    url = f"https://openlibrary.org/api/books?bibkeys=ISBN:{isbn}&format=json&jscmd=data"
    
    try:
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            book_key = f"ISBN:{isbn}"
            
            if book_key in data and data[book_key]:
                raw_data = data[book_key]
                return extract_book_fields(raw_data, isbn)
                
    except requests.RequestException as e:
        print(f"OpenLibrary API request failed: {e}")
    except json.JSONDecodeError as e:
        print(f"Failed to decode OpenLibrary response: {e}")
    
    return None

def extract_book_fields(data: Dict[str, Any], isbn: str) -> Dict[str, Any]:
    """
    Extract and standardize book fields from OpenLibrary response
    Enhanced with Google Books fallback for missing data
    
    Args:
        data (dict): Raw OpenLibrary book data
        isbn (str): ISBN for Google Books fallback calls
        
    Returns:
        dict: Standardized book data matching database schema
    """
    # Get OpenLibrary thumbnail first
    image_url = extract_cover_url(data)
    
    # If no OpenLibrary thumbnail, try Google Books
    if not image_url:
        image_url = get_google_books_thumbnail(isbn)
    
    # Always get description from Google Books (OpenLibrary doesn't provide descriptions)
    description = get_google_books_description(isbn)
    length_value = data.get('number_of_pages') or data.get('pagination')
    if length_value:
        try:
            length_value = int(length_value)
        except ValueError:
            length_value = 0
    else:
        length_value = 0
    return {
        'title': data.get('title'),
        'subtitle': data.get('subtitle'),
        'author': extract_first_author(data),
        'isbncode': isbn,
        'publisher': extract_first_publisher(data),
        'publisheddate': data.get('publish_date'),
        'length': length_value,  # ← Use the processed int value
        'memo': None,
        'rating': None,
        'description': description,
        'imageurl': image_url,
        'excerpt': extract_first_excerpt(data)
    }

def extract_first_author(data: Dict[str, Any]) -> Optional[str]:
    """Extract first author name from authors array"""
    if 'authors' in data and isinstance(data['authors'], list) and len(data['authors']) > 0:
        author = data['authors'][0]
        if isinstance(author, dict) and 'name' in author:
            return author['name']
    return None

def extract_first_publisher(data: Dict[str, Any]) -> Optional[str]:
    """Extract first publisher name from publishers array"""
    if 'publishers' in data and isinstance(data['publishers'], list) and len(data['publishers']) > 0:
        publisher = data['publishers'][0]
        if isinstance(publisher, dict) and 'name' in publisher:
            return publisher['name']
        elif isinstance(publisher, str):
            return publisher
    return None

def extract_cover_url(data: Dict[str, Any]) -> Optional[str]:
    """Extract cover image URL from cover object"""
    if 'cover' in data and isinstance(data['cover'], dict):
        cover = data['cover']
        # Try different sizes: small, medium, large
        for size in ['medium', 'small', 'large']:
            if size in cover:
                return cover[size]
    return None

def extract_first_excerpt(data: Dict[str, Any]) -> Optional[str]:
    """Extract first excerpt text - OpenLibrary's unique feature"""
    if 'excerpts' in data and isinstance(data['excerpts'], list) and len(data['excerpts']) > 0:
        excerpt = data['excerpts'][0]
        if isinstance(excerpt, dict) and 'text' in excerpt:
            return excerpt['text']
        elif isinstance(excerpt, str):
            return excerpt
    return None

def get_google_books_description(isbn: str) -> Optional[str]:
    """Get description from Google Books API by ISBN"""
    url = f"https://www.googleapis.com/books/v1/volumes?q=isbn:{isbn}"
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if data.get('totalItems', 0) > 0:
            book_info = data['items'][0]['volumeInfo']
            return book_info.get('description')
        else:
            return None
            
    except requests.RequestException as e:
        print(f"Error fetching from Google Books: {e}")
        return None
    except json.JSONDecodeError as e:
        print(f"Error parsing Google Books response: {e}")
        return None

def get_google_books_thumbnail(isbn: str) -> Optional[str]:
    """Get thumbnail URL from Google Books API by ISBN"""
    url = f"https://www.googleapis.com/books/v1/volumes?q=isbn:{isbn}"
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if data.get('totalItems', 0) > 0:
            book_info = data['items'][0]['volumeInfo']
            return book_info.get('imageLinks', {}).get('thumbnail')
        else:
            return None
            
    except requests.RequestException as e:
        print(f"Error fetching from Google Books: {e}")
        return None
    except json.JSONDecodeError as e:
        print(f"Error parsing Google Books response: {e}")
        return None
