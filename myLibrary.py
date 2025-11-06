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
div[data-testid="stSidebarNav"] ul {display: none;}
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
    
    ## Get books
    books_df = get_all_books()
    
    if books_df.empty:
        st.warning("No books found in database.")
    else:
        # Check if we need to show a specific book first (from Add/Edit/View)
        if 'show_book_first' in st.session_state:
            target_isbn = st.session_state.show_book_first
            # Rotate the dataframe to start at the target book
            target_idx = books_df[books_df['isbncode'] == target_isbn].index
            if len(target_idx) > 0:
                idx = target_idx[0]
                books_df = pd.concat([books_df.iloc[idx:], books_df.iloc[:idx]]).reset_index(drop=True)
            # Clear the flag after using it
            del st.session_state.show_book_first

        # Capture return position state before widgets modify session state
        returning_view_mode = st.session_state.get('return_view_mode', None)
        returning_isbn = st.session_state.get('return_book_isbn', None)
        
        # Compact search and display options in one row
        col1, col2, col3, col4, col5 = st.columns([3, 1, 1, 1, 1])
        
        with col1:
            search_term = st.text_input("Search:", placeholder="Enter search term...", label_visibility="collapsed")
        with col2:
            search_field = st.selectbox("In:", ["All", "Title", "Author", "ISBN"], label_visibility="collapsed")
        with col3:
            # Restore view mode from session state if returning
            default_show_images = (returning_view_mode == 'card') if returning_view_mode else True
            show_images = st.checkbox("Images", value=default_show_images)
        with col4:
            books_per_page_option = st.selectbox("Per page:", [25, 50, 100, "All"], index=1, label_visibility="visible")
        
        # Filter books
        filtered_df = filter_books(books_df, search_term, search_field)
        
        if filtered_df.empty:
            st.info("No books match your search.")
        else:
            # Handle "All" option for books per page
            books_per_page = len(filtered_df) if books_per_page_option == "All" else books_per_page_option
            
            # Calculate pagination
            total_books = len(filtered_df)
            total_pages = (total_books - 1) // books_per_page + 1
            
            # Calculate default page if returning to a specific book
            default_page_idx = 0
            if returning_isbn:
                try:
                    # Find book position in filtered results
                    book_rows = filtered_df[filtered_df['isbncode'] == returning_isbn]
                    if not book_rows.empty:
                        # Get the position in filtered dataframe
                        book_position = filtered_df.index.get_loc(book_rows.index[0])
                        # Calculate which page this book is on (0-indexed)
                        default_page_idx = book_position // books_per_page
                except:
                    default_page_idx = 0
            
            # Page selector in col5
            if total_pages > 1:
                with col5:
                    page_num = st.selectbox("Page:", range(1, total_pages + 1), index=default_page_idx, label_visibility="visible")
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
                display_books_with_images(df_page, returning_isbn)
            else:
                display_books_table(df_page, returning_isbn)
        
        # Clear return state AFTER everything is displayed and widgets have used the values
        for key in ['return_view_mode', 'return_selected_idx', 'return_book_isbn']:
            if key in st.session_state:
                del st.session_state[key]

if __name__ == "__main__":
    main()