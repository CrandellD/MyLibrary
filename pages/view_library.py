import streamlit as st
import pandas as pd
from database import get_all_books

def display_books_table(df):
    """Display books in table format"""
    display_cols = ['Title', 'Author', 'Rating']
    available_cols = [col for col in display_cols if col in df.columns]
    
    selected = st.dataframe(
        df[available_cols], 
        use_container_width=True, 
        hide_index=True,
        on_select="rerun",
        selection_mode="single-row"
    )
    
    # Handle selection for edit
    if selected and selected.selection.rows:
        selected_idx = selected.selection.rows[0]
        selected_book = df.iloc[selected_idx]
        
        # Show selected book and edit button in sidebar
        st.sidebar.success(f"Selected: {selected_book['Title']}")
        if st.sidebar.button("Edit Selected Book"):
            st.session_state.edit_mode = True
            st.session_state.edit_isbn = selected_book['ISBNCode']
            st.switch_page("pages/edit_book.py")
def display_books_with_images(df):
    """Display books with cover images in card format"""
    cols_per_row = 3
    for i in range(0, len(df), cols_per_row):
        cols = st.columns(cols_per_row)
        for j in range(cols_per_row):
            if i + j < len(df):
                book = df.iloc[i + j]
                with cols[j]:
                    display_book_card(book)

def display_book_card(book):
    """Display individual book card"""
    with st.container():
        st.markdown("---")
        
        # Book cover
        if pd.notna(book.get('ImageURL')) and book['ImageURL']:
            try:
                st.image(book['ImageURL'], width=120)
            except:
                st.write("📖 No image")
        else:
            st.write("📖 No image")
        
        # Book info
        st.write(f"**{book['Title'] if pd.notna(book['Title']) else 'Unknown Title'}**")
        if pd.notna(book.get('Author')) and book['Author']:
            st.write(f"*by {book['Author']}*")
        
        # Rating
        if pd.notna(book.get('Rating')) and book['Rating'] and book['Rating'] != '':
            rating_val = float(book['Rating'])
            stars = "⭐" * int(rating_val)
            if rating_val % 1 == 0.5:
                stars += "½"
            st.write(f"{stars} ({rating_val})")
        else:
            st.write("")  # Blank for no rating
        
        # Additional info
        info_items = []
        if pd.notna(book.get('PublishedDate')) and book['PublishedDate']:
            info_items.append(f"Published: {book['PublishedDate']}")
        if pd.notna(book.get('Language')) and book['Language']:
            info_items.append(f"Language: {book['Language']}")
        if pd.notna(book.get('Length')) and book['Length']:
            info_items.append(f"Pages: {int(book['Length'])}")
        
        if info_items:
            st.caption(" | ".join(info_items))
        
        # Edit button
        if st.button(f"Edit", key=f"edit_{book['ISBNCode']}"):
            st.session_state.edit_mode = True
            st.session_state.edit_isbn = book['ISBNCode']
            st.switch_page("pages/edit_book.py")

def filter_books(df, search_term, search_field):
    """Filter dataframe based on search criteria"""
    if not search_term:
        return df # <-- Returns full DataFrame if search is empty
    
    search_term = search_term.lower()
    
    if search_field == "All":
        mask = (
            df['Title'].str.lower().str.contains(search_term, na=False) |
            df['Author'].str.lower().str.contains(search_term, na=False) |
            df['ISBNCode'].str.lower().str.contains(search_term, na=False)
        )
    elif search_field == "Title":
        mask = df['Title'].str.lower().str.contains(search_term, na=False)
    elif search_field == "Author":
        mask = df['Author'].str.lower().str.contains(search_term, na=False)
    elif search_field == "ISBN":
        mask = df['ISBNCode'].str.lower().str.contains(search_term, na=False)
    
    return df[mask]