import streamlit as st
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import get_book_by_isbn

# # Hide auto-generated page navigation
# st.markdown("""
# <style>
# div[data-testid="stSidebarNav"] {display: none;}
# </style>
# """, unsafe_allow_html=True)

# # Hide auto-generated page navigation and Streamlit UI elements
# st.markdown("""
# <style>
# div[data-testid="stSidebarNav"] {display: none;}
# div.block-container {padding-top: 1rem;}
# #MainMenu {visibility: hidden;}
# footer {visibility: hidden;}
# header {visibility: hidden;}
# </style>
# """, unsafe_allow_html=True)


def show_view_book_page():
    """Display the View Book page (read-only)"""
    
    st.title("View Book")
    
    # Check if we have an ISBN to view
    if 'edit_isbn' not in st.session_state:
        st.error("No book selected for viewing")
        if st.button("Return to Library"):
            st.switch_page("myLibrary.py")
        return
    
    # Get the book data from database
    isbn = st.session_state.edit_isbn
    book_data = get_book_by_isbn(isbn)
    
    if not book_data:
        st.error(f"Book with ISBN {isbn} not found in database")
        if st.button("Return to Library"):
            if 'edit_isbn' in st.session_state:
                del st.session_state.edit_isbn
            st.switch_page("myLibrary.py")
        return
    
    # Show the book information (read-only)
    show_book_info(book_data)
    
    # Return to Library button
    if st.button("Return to Library"):
        # Set the book to show first when returning
        st.session_state.show_book_first = st.session_state.edit_isbn
        # Clean up session state
        if 'edit_isbn' in st.session_state:
            del st.session_state.edit_isbn
        if 'view_mode' in st.session_state:
            del st.session_state.view_mode
        st.switch_page("myLibrary.py")

def show_book_info(book_data):
    """Display book data in read-only format"""
    
    st.subheader("Book Information")
    
    # Display book cover if available
    if book_data.get('imageurl'):
        col_img, col_info = st.columns([1, 3])
        with col_img:
            try:
                st.image(book_data['imageurl'], width=200)
            except:
                st.caption("Cover image could not be loaded")
        with col_info:
            display_book_details(book_data)
    else:
        display_book_details(book_data)
    
    # Display longer text fields separately
    st.markdown("---")
    
    if book_data.get('memo'):
        st.markdown("**Personal Notes:**")
        st.info(book_data.get('memo', ''))
    
    if book_data.get('excerpt'):
        st.markdown("**Book Excerpt:**")
        st.text_area("", value=book_data.get('excerpt', ''), height=150, disabled=True, label_visibility="collapsed")
    
    if book_data.get('description'):
        st.markdown("**Description:**")
        st.info(book_data.get('description', ''))

def display_book_details(book_data):
    """Display book details in a structured format"""
    
    # Title and Subtitle
    st.markdown(f"### {book_data.get('title', 'Unknown Title')}")
    if book_data.get('subtitle'):
        st.markdown(f"*{book_data.get('subtitle')}*")
    
    st.markdown("---")
    
    # Create two columns for structured info
    col1, col2 = st.columns(2)
    
    with col1:
        if book_data.get('author'):
            st.markdown(f"**Author:** {book_data.get('author')}")
        if book_data.get('isbn' or book_data.get('isbncode')):
            st.markdown(f"**ISBN:** {book_data.get('isbncode')}")
        if book_data.get('publisher'):
            st.markdown(f"**Publisher:** {book_data.get('publisher')}")
    
    with col2:
        if book_data.get('publisheddate'):
            st.markdown(f"**Published:** {book_data.get('publisheddate')}")
        if book_data.get('length') and book_data.get('length') != 0:
            st.markdown(f"**Pages:** {book_data.get('length')}")
        if book_data.get('rating') and book_data.get('rating') != 0:
            rating_val = float(book_data.get('rating'))
            stars = "⭐" * int(rating_val)
            if rating_val % 1 == 0.5:
                stars += "½"
            st.markdown(f"**Rating:** {stars} ({rating_val})")

# Run the page
if __name__ == "__main__":
    show_view_book_page()