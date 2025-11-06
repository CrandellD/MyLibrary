import streamlit as st
import pandas as pd
from database import get_all_books

def save_position_state(view_mode, selected_idx=None, book_isbn=None):
    """Save current position state before navigation"""
    st.session_state.return_view_mode = view_mode
    if selected_idx is not None:
        st.session_state.return_selected_idx = selected_idx
    if book_isbn is not None:
        st.session_state.return_book_isbn = book_isbn

def navigate_to_view(book_isbn, view_mode, selected_idx=None):
    """Navigate to view page with position tracking"""
    save_position_state(view_mode, selected_idx, book_isbn)
    st.session_state.view_mode = True
    st.session_state.edit_isbn = book_isbn
    st.switch_page("pages/view_book.py")

def navigate_to_edit(book_isbn, view_mode, selected_idx=None):
    """Navigate to edit page with position tracking"""
    save_position_state(view_mode, selected_idx, book_isbn)
    st.session_state.edit_mode = True
    st.session_state.edit_isbn = book_isbn
    st.switch_page("pages/edit_book.py")

def display_books_table(df, returning_isbn=None):
    """Display books in table format"""
    display_cols = ['title', 'author', 'rating']
    available_cols = [col for col in display_cols if col in df.columns]
    
    selected = st.dataframe(
        df[available_cols], 
        use_container_width=True, 
        hide_index=True,
        on_select="rerun",
        selection_mode="single-row"
    )
    
    # Handle selection for view/edit
    if selected and selected.selection.rows:
        selected_idx = selected.selection.rows[0]
        selected_book = df.iloc[selected_idx]
        
        # Show selected book and buttons in sidebar
        st.sidebar.success(f"Selected: {selected_book['title']}")
        
        col1, col2 = st.sidebar.columns(2)
        with col1:
            if st.button("View", key="view_table"):
                navigate_to_view(selected_book['isbncode'], 'table', selected_idx)
        with col2:
            if st.button("Edit", key="edit_table"):
                navigate_to_edit(selected_book['isbncode'], 'table', selected_idx)

def display_books_with_images(df, returning_isbn=None):
    """Display books with cover images in card format"""
    cols_per_row = 3
    for i in range(0, len(df), cols_per_row):
        cols = st.columns(cols_per_row) 
        for j in range(cols_per_row):
            if i + j < len(df):
                book = df.iloc[i + j]
                book_position = i + j
                with cols[j]:
                    display_book_card(book, book_position)
def display_book_card(book, position):
    """Display individual book card"""
    st.markdown("---")
    
    # Book cover ONLY in fixed-height container
    with st.container(height=200, border=False):
        if pd.notna(book.get('imageurl')) and book['imageurl']:
            try:
                st.image(book['imageurl'], width=120)
            except:
                st.write("📖 No image")
        else:
            st.write("📖 No image")
    
    # Everything else OUTSIDE container - back to normal indentation
    # Book info
    st.write(f"**{book['title'] if pd.notna(book['title']) else 'Unknown Title'}**")
    if pd.notna(book.get('author')) and book['author']:
        st.write(f"*by {book['author']}*")
    
    # Rating
    if pd.notna(book.get('rating')) and book['rating'] and book['rating'] != '':
        rating_val = float(book['rating'])
        stars = "⭐" * int(rating_val)
        if rating_val % 1 == 0.5:
            stars += "½"
        st.write(f"{stars} ({rating_val})")
    else:
        st.write("Not rated")
    
    # Additional info
    info_items = []
    if pd.notna(book.get('publisheddate')) and book['publisheddate']:
        info_items.append(f"Published: {book['publisheddate']}")
    if pd.notna(book.get('language')) and book['language']:
        info_items.append(f"Language: {book['language']}")
    if pd.notna(book.get('length')) and book['length']:
        info_items.append(f"Pages: {int(book['length'])}")
    
    if info_items:
        st.caption(" | ".join(info_items))
    
    # View and Edit buttons
    col1, col2 = st.columns(2)
    with col1:
        if st.button("View", key=f"view_{book['isbncode']}"):
            navigate_to_view(book['isbncode'], 'card', position)
    with col2:
        if st.button("Edit", key=f"edit_{book['isbncode']}"):
            navigate_to_edit(book['isbncode'], 'card', position)

def filter_books(df, search_term, search_field):
    """Filter dataframe based on search criteria"""
    if not search_term:
        return df
    
    search_term = search_term.lower()
    
    if search_field == "All":
        mask = (
            df['title'].str.lower().str.contains(search_term, na=False) |
            df['author'].str.lower().str.contains(search_term, na=False) |
            df['isbncode'].str.lower().str.contains(search_term, na=False)
        )
    elif search_field == "Title":
        mask = df['title'].str.lower().str.contains(search_term, na=False)
    elif search_field == "Author":
        mask = df['author'].str.lower().str.contains(search_term, na=False)
    elif search_field == "ISBN":
        mask = df['isbncode'].str.lower().str.contains(search_term, na=False)
    
    return df[mask]