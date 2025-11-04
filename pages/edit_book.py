import streamlit as st
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api_calls import get_openlibrary_book_data
from database import get_book_by_isbn, update_book_in_database, delete_book_from_database, get_delete_pin

# Hide auto-generated page navigation
st.markdown("""
<style>
div[data-testid="stSidebarNav"] {display: none;}
</style>
""", unsafe_allow_html=True)

def show_edit_book_page():
    """Display the Edit Book page"""
    
    st.title("Edit Book")
    
    # Check if we just completed an update
    if 'save_success' in st.session_state and st.session_state.save_success:
        st.success(st.session_state.save_message)
        st.info("Book successfully updated! You can return to the library to see your changes.")
        if st.button("Return to Library"):
            # Clear ALL edit-related state
            for key in ['save_success', 'save_message', 'edit_isbn', 'edit_book_data']:
                if key in st.session_state:
                    del st.session_state[key]
            st.switch_page("myLibrary.py")
        return
    
    # Check if we have an ISBN to edit
    if 'edit_isbn' not in st.session_state:
        st.error("No book selected for editing")
        if st.button("Return to Library"):
            st.switch_page("myLibrary.py")
        return
    
    # Get the book data from database
    isbn = st.session_state.edit_isbn
    
    # Clear old book data if editing a different book
    if 'edit_book_data' in st.session_state:
        if st.session_state.edit_book_data.get('isbncode') != isbn:
            del st.session_state.edit_book_data
    
    book_data = get_book_by_isbn(isbn)
    
    if not book_data:
        st.error(f"Book with ISBN {isbn} not found in database")
        if st.button("Return to Library"):
            del st.session_state.edit_isbn
            st.switch_page("myLibrary.py")
        return

    # Store book data in session state for form
    if 'edit_book_data' not in st.session_state:
        st.session_state.edit_book_data = book_data
    
   # Show the edit form - unique container key forces scroll reset
    with st.container(key=f"edit_form_{isbn}"):
        show_edit_form(st.session_state.edit_book_data)
        
    # Cancel button
    if st.button("Cancel Edit"):
        # Clean up session state
        if 'edit_isbn' in st.session_state:
            del st.session_state.edit_isbn
        if 'edit_book_data' in st.session_state:
            del st.session_state.edit_book_data
        if 'save_success' in st.session_state:
            del st.session_state.save_success
        if 'save_message' in st.session_state:
            del st.session_state.save_message
        st.switch_page("myLibrary.py")

def show_edit_form(book_data):
    """Display book data in editable form"""
    
    st.subheader("Edit Book Information")
    
    # ADD THIS SECTION - Initialize delete confirmation states
    # These track whether user clicked delete and entered PIN
    if 'show_delete_confirm' not in st.session_state:
        st.session_state.show_delete_confirm = False  # Whether to show PIN input
    if 'delete_success' not in st.session_state:
        st.session_state.delete_success = False  # Whether deletion worked
    if 'delete_message' not in st.session_state:
        st.session_state.delete_message = ""  # Success/error message

    # Callback function that runs BEFORE the rerun
    def update_book_callback():
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
        
        # Update in database
        success, message = update_book_in_database(updated_book_data)
        
        # Store results in session state for display after rerun
        st.session_state.save_success = success
        st.session_state.save_message = message
        
        # Clear edit data if successful
        if success:
            if 'edit_isbn' in st.session_state:
                del st.session_state.edit_isbn

    def trigger_delete_confirmation():
        """Callback that runs when Delete Book button is clicked"""
        # This sets the flag to show the PIN input field
        # Callback runs BEFORE the page reruns, so state is set properly
        st.session_state.show_delete_confirm = True
    
    with st.form("book_edit_form"):
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
        
        # Display book cover if available
        if book_data.get('imageurl'):
            st.markdown("**Book Cover:**")
            try:
                st.image(book_data['imageurl'], width=200)
            except:
                st.caption("Cover image could not be loaded")
        
        # Submit button
        st.form_submit_button("Update Book", on_click=update_book_callback)
    
    # ADD THIS SECTION HERE - at the same indentation as the comment below
    # We put this outside the form because forms can only have one submit button
    st.markdown("---")  # Visual separator line
    st.markdown("**Delete Book**")
    
    # Delete button with callback - this will trigger the PIN confirmation
    if st.button("Delete Book", type="secondary", help="Permanently delete this book", 
                on_click=trigger_delete_confirmation):
        pass  # The callback handles everything, so button body can be empty

        # This only appears when show_delete_confirm flag is True
    if st.session_state.get('show_delete_confirm', False):
        st.markdown("### ⚠️ Confirm Deletion")
        st.warning("This action cannot be undone!")
        
        # PIN input field
        pin_input = st.text_input("Enter PIN to confirm deletion:", 
                                 type="password", 
                                 key="delete_pin_input")
        
        # Two buttons: Confirm and Cancel
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🗑️ Confirm Delete", type="primary"):
                # Check if PIN was entered
                if not pin_input:
                    st.error("Please enter PIN to confirm deletion")
                else:
                    # Get the correct PIN from database
                    correct_pin = get_delete_pin()
                    
                    # Verify PIN matches
                    if pin_input == correct_pin:
                        # PIN is correct - delete the book
                        isbn = st.session_state.edit_isbn
                        success, message = delete_book_from_database(isbn)
                        
                        # Store results for display
                        st.session_state.delete_success = success
                        st.session_state.delete_message = message
                        st.session_state.show_delete_confirm = False  # Hide PIN input
                        st.rerun()
                    else:
                        st.error("Incorrect PIN")
                        
        with col2:
            if st.button("❌ Cancel", type="secondary"):
                st.session_state.show_delete_confirm = False
                st.rerun()


    # Display results after form submission
    if 'save_success' in st.session_state:
        if st.session_state.save_success:
            st.success(st.session_state.save_message)
            # Clear all edit-related session state
            for key in ['save_success', 'save_message', 'edit_isbn', 'edit_book_data']:
                if key in st.session_state:
                    del st.session_state[key]
            # Go straight to main library page
            st.switch_page("myLibrary.py")
        else:
            st.error(st.session_state.save_message)
            # Clear only the result states, keep book data for retry
            del st.session_state.save_success
            del st.session_state.save_message

# Run the page
if __name__ == "__main__":
    show_edit_book_page()