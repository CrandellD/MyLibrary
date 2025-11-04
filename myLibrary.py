#!Python 3

import streamlit as st
import sqlite3
import pandas as pd
from database import get_db_connection, get_all_books
from pages.view_library import display_books_with_images, display_books_table, filter_books

# Page configuration
st.set_page_config(page_title="Personal Library", page_icon="📚", layout="wide")

# Hide auto-generated page navigation and Streamlit UI elements
st.markdown("""
<style>
div[data-testid="stSidebarNav"] {display: none;}
div.block-container {padding-top: 1rem;}
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

def main():
    st.title("📚 My Library")
    
    # Sidebar
    if st.sidebar.button("Add Book", use_container_width=True):
        st.switch_page("pages/add_book.py")
    
    # Get books
    books_df = get_all_books()
    
    if books_df.empty:
        st.warning("No books found in database.")
    else:
        # Compact search and display options in one row
        col1, col2, col3, col4, col5 = st.columns([3, 1, 1, 1, 1])
        
        with col1:
            search_term = st.text_input("Search:", placeholder="Enter search term...", label_visibility="collapsed")
        with col2:
            search_field = st.selectbox("In:", ["All", "Title", "Author", "ISBN"], label_visibility="collapsed")
        with col3:
            show_images = st.checkbox("Images", value=True)
        with col4:
            books_per_page = st.selectbox("Per page:", [10, 25, 50], index=1, label_visibility="visible")
        
        # Filter books
        filtered_df = filter_books(books_df, search_term, search_field)
        
        if filtered_df.empty:
            st.info("No books match your search.")
        else:
            # Calculate pagination
            total_books = len(filtered_df)
            total_pages = (total_books - 1) // books_per_page + 1
            
            # Page selector in col5
            if total_pages > 1:
                with col5:
                    page_num = st.selectbox("Page:", range(1, total_pages + 1), label_visibility="visible")
            else:
                page_num = 1
            
            # Calculate page slice
            start_idx = (page_num - 1) * books_per_page
            end_idx = min(start_idx + books_per_page, total_books)
            
            # Show book count
            st.caption(f"Showing books {start_idx + 1}-{end_idx} of {total_books}")
            
            # Display books for current page
            df_page = filtered_df.iloc[start_idx:end_idx]
            
            if show_images:
                display_books_with_images(df_page)
            else:
                display_books_table(df_page)

if __name__ == "__main__":
    main()