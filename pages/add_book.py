import streamlit as st
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api_calls import get_openlibrary_book_data
from database import add_book_to_database, get_book_by_isbn, update_book_in_database

# Hide auto-generated page navigation
st.markdown("""
<style>
div[data-testid="stSidebarNav"] {display: none;}
div.block-container {padding-top: 1rem;}
</style>
""", unsafe_allow_html=True)

# Save to add back a piece at a time
# #MainMenu {visibility: hidden;}
# footer {visibility: hidden;}
# header {visibility: hidden;}

def show_add_book_page():
    """Display the Add Book page with ISBN lookup and form"""
    
    # Cncel and return to home page
    if st.sidebar.button("Cancel", use_container_width=True):
        st.switch_page("myLibrary.py")

    # Handle navigation flags FIRST
    if st.session_state.get('navigate_to_library'):
        del st.session_state.navigate_to_library
        st.switch_page("myLibrary.py")
    
    if st.session_state.get('add_another_book'):
        del st.session_state.add_another_book
        st.rerun()
    
    # Preserve edit mode across page switch
    for key in ['edit_mode', 'edit_isbn']:
        if key in st.session_state:
            st.session_state[key] = st.session_state[key]
    
    # Check for edit mode
    if 'edit_mode' in st.session_state and st.session_state.edit_mode and 'edit_isbn' in st.session_state:
        st.title("Edit Book")
        
        # Get book from database using ISBN
        isbn = st.session_state.edit_isbn
        book_data = get_book_by_isbn(isbn)
        
        if book_data:
            # Go straight to form with existing data
            show_book_review_form(book_data, edit_mode=True)
        else:
            st.error(f"Book with ISBN {isbn} not found")
        
        # Clear edit mode
        if st.button("Cancel Edit"):
            del st.session_state.edit_mode
            del st.session_state.edit_isbn
            st.switch_page("myLibrary.py")
        return  # Skip the rest of the function
    
    # Normal add book flow
    st.title("Add New Book")
    
    # ISBN Input Section
    st.subheader("Book Lookup")
    isbn = st.text_input("Enter ISBN:", placeholder="9780805210576")
    
    if st.button("Look Up Book"):
        if isbn:
            with st.spinner("Looking up book..."):
                book_data = get_openlibrary_book_data(isbn)
                
            if book_data:
                st.success("Book found!")
                st.session_state.book_data = book_data
            else:
                st.error("Book not found. Please check the ISBN or enter manually.")
        else:
            st.error("Please enter an ISBN")
    
    # Show form if book data exists in session state
    if 'book_data' in st.session_state:
        show_book_review_form(st.session_state.book_data)

def show_book_review_form(book_data, edit_mode=False):
    """Display book data in editable form for user review"""
    
    if edit_mode:
        st.subheader("Edit Book Information")
    else:
        st.subheader("Review Book Information")
    
    # Callback function that runs BEFORE the rerun
    def save_book_callback():
        # Access form values via session state using widget keys
        updated_book_data = {
            'title': st.session_state.form_title,
            'subtitle': st.session_state.form_subtitle if st.session_state.form_subtitle else None,
            'author': st.session_state.form_author,
            'isbncode': st.session_state.form_isbn,
            'publisher': st.session_state.form_publisher if st.session_state.form_publisher else None,
            'publisheddate': st.session_state.form_published_date if st.session_state.form_published_date else None,
            'length': st.session_state.form_length if st.session_state.form_length and st.session_state.form_length > 0 else None,
            'memo': st.session_state.form_memo if st.session_state.form_memo else None,
            'rating': st.session_state.form_rating if st.session_state.form_rating and st.session_state.form_rating > 0 else None,
            'description': book_data.get('description'),
            'imageurl': book_data.get('imageurl'),
            'excerpt': st.session_state.form_excerpt if st.session_state.form_excerpt else None
        }
        
        # Save to database - check if update or add
        if edit_mode:
            success, message = update_book_in_database(updated_book_data)
        else:
            success, message = add_book_to_database(updated_book_data)
        
        # Store results in session state for display after rerun
        st.session_state.save_success = success
        st.session_state.save_message = message
        
        # Store ISBN to show book at top of library when returning
        if success:
            st.session_state.show_book_first = updated_book_data['isbncode']
        
        # Clear edit mode if successful update
        if edit_mode and success:
            if 'edit_mode' in st.session_state:
                del st.session_state.edit_mode
            if 'edit_isbn' in st.session_state:
                del st.session_state.edit_isbn
    
    with st.form("book_review_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.text_input("Book Title:", value=book_data.get('title', ''), key='form_title')
            st.text_input("Author:", value=book_data.get('author', ''), key='form_author') 
            st.text_input("ISBN:", value=book_data.get('isbncode', ''), key='form_isbn')
            st.text_input("Publisher:", value=book_data.get('publisher', ''), key='form_publisher')
            
        with col2:
            st.text_input("Subtitle:", value=book_data.get('subtitle', ''), key='form_subtitle')
            st.text_input("Publication Date:", value=book_data.get('publisheddate', ''), key='form_published_date')
            # Handle Length field - convert to int if it's not already
            length_value = book_data.get('length', 0)
            if length_value and length_value != '':
                try:
                    length_value = int(length_value)
                except:
                    length_value = 0
            else:
                length_value = 0
            st.number_input("Pages:", value=length_value, min_value=0, key='form_length')
            # Handle Rating field - convert to float
            rating_value = book_data.get('rating', 0.0)
            if rating_value and rating_value != '':
                try:
                    rating_value = float(rating_value)
                except:
                    rating_value = 0.0
            else:
                rating_value = 0.0
            st.slider("Your Rating:", min_value=0.0, max_value=5.0, value=rating_value, step=0.5, key='form_rating')
        
        st.text_area("Personal Notes:", value=book_data.get('memo', ''), key='form_memo')
        st.text_area("Book Excerpt:", value=book_data.get('excerpt', ''), key='form_excerpt', height=150)
        
        # Use callback instead of conditional processing
        button_text = "Update Book" if edit_mode else "Add Book to Library"
        st.form_submit_button(button_text, on_click=save_book_callback)
    
    # Display results after form submission
    if 'save_success' in st.session_state:
        if st.session_state.save_success:
            st.success(st.session_state.save_message)
            
            if not edit_mode:
                # Callback functions for navigation
                def go_to_library():
                    if 'book_data' in st.session_state:
                        del st.session_state.book_data
                    st.session_state.navigate_to_library = True
                
                def add_another():
                    if 'book_data' in st.session_state:
                        del st.session_state.book_data
                    # Clear show_book_first so it doesn't interfere with next add
                    if 'show_book_first' in st.session_state:
                        del st.session_state.show_book_first
                    st.session_state.add_another_book = True
                
                # Show navigation options after adding
                col1, col2 = st.columns(2)
                with col1:
                    st.button("Add Another Book", use_container_width=True, on_click=add_another)
                with col2:
                    st.button("View Library", use_container_width=True, type="primary", on_click=go_to_library)
            
            # Clear success flags after displaying message
            del st.session_state.save_success
            del st.session_state.save_message
        else:
            st.error(st.session_state.save_message)
            # Clear only the result states, keep book_data for retry
            del st.session_state.save_success
            del st.session_state.save_message

# Run the page
if __name__ == "__main__":
    show_add_book_page()