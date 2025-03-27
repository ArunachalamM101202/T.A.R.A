import streamlit as st
from modules.pdf_processor import process_pdf
from modules.chat_handler import handle_chat_input
from modules.document_processor import process_document
import os

# Set Streamlit page config
st.set_page_config(
    page_title="TARA - Teaching Assistant & Research Aide",
    page_icon="🎓",
    layout="centered",
    initial_sidebar_state="expanded"
)

# Title and introduction
st.title("🎓 T.A.R.A: Teaching Assistant & Research Assistant")
st.subheader("Supporting students and faculty with course materials and research")

# Initialize session state
if "conversation" not in st.session_state:
    st.session_state.conversation = None
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "document_processed" not in st.session_state:
    st.session_state.document_processed = False
if "processing_status" not in st.session_state:
    st.session_state.processing_status = {}
if "processed_files" not in st.session_state:
    st.session_state.processed_files = set()
if "temp_dir" not in st.session_state:
    import tempfile
    st.session_state.temp_dir = tempfile.mkdtemp()
if "user_role" not in st.session_state:
    st.session_state.user_role = "student"  # Default to student role

# Function to save uploaded file to temp directory
def save_uploaded_file(uploaded_file):
    file_path = os.path.join(st.session_state.temp_dir, uploaded_file.name)
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    return file_path

# Role selection in sidebar
with st.sidebar:
    st.header("👤 Select Your Role")
    
    role = st.radio(
        "I'll adapt my assistance based on your needs:",
        ["Student", "Professor"],
        index=0 if st.session_state.user_role == "student" else 1,
        horizontal=True
    )
    
    # Update role in session state
    st.session_state.user_role = role.lower()
    
    st.divider()
    
    # Materials section title changes based on role
    if st.session_state.user_role == "student":
        st.header("📚 Course Materials")
        uploader_text = "Upload lecture notes, textbook chapters, etc."
    else:
        st.header("📚 Knowledge Repository")
        uploader_text = "Upload course materials, research papers, etc."
    
    # Allow multiple file uploads
    uploaded_files = st.file_uploader(
        uploader_text,
          type=["pdf","csv","xlsx","xls"], accept_multiple_files=True)
    
    # Show currently processed files
    if st.session_state.processed_files:
        st.write("**Materials in my knowledge base:**")
        for file_name in sorted(st.session_state.processed_files):
            st.write(f"• {file_name}")
    
    if uploaded_files:
        # Identify new files not yet processed
        current_upload_names = {file.name for file in uploaded_files}
        new_files = [f for f in uploaded_files if f.name not in st.session_state.processed_files]
        
        if new_files:
            st.write("**New materials to process:**")
            for file in new_files:
                st.write(f"• {file.name}")
            
            if st.button("Process these materials"):
                # Reset processing status for new batch
                st.session_state.processing_status = {}
                
                # Save all files to temp directory first
                for file in new_files:
                    file_path = save_uploaded_file(file)
                    file_key = file.name
                    # Mark as processing
                    st.session_state.processing_status[file_key] = "processing"
                
                # Force UI update
                st.rerun()
        else:
            st.success("All uploaded files have been processed!")
    
    # Display processing status after rerun
    if "processing_status" in st.session_state and st.session_state.processing_status:
        st.divider()
        st.subheader("Processing Status")
        
        all_files_processed = True
        for file_name, status in list(st.session_state.processing_status.items()):
            if status == "processing":
                with st.spinner(f"Processing {file_name}..."):
                    # Find file object from the current uploads
                    file_obj = next((f for f in uploaded_files if f.name == file_name), None)
                    
                    # if file_obj:
                        # try:
                        #     # If this is the first document, just process it normally
                        #     if st.session_state.conversation is None:
                        #         st.session_state.conversation = process_pdf(file_obj)
                        #         if st.session_state.conversation:
                        #             st.session_state.processed_files.add(file_name)
                        #             st.session_state.processing_status[file_name] = "complete"
                        #             st.session_state.document_processed = True
                        #         else:
                        #             st.session_state.processing_status[file_name] = "failed"
                        #             all_files_processed = False
                        #     else:
                        #         # For subsequent documents, use add_to_existing
                        #         st.session_state.conversation = process_pdf(
                        #             file_obj, 
                        #             add_to_existing=True,
                        #             existing_conversation=st.session_state.conversation
                        #         )
                                
                        #         if st.session_state.conversation:
                        #             st.session_state.processed_files.add(file_name)
                        #             st.session_state.processing_status[file_name] = "complete"
                        #             st.session_state.document_processed = True
                        #         else:
                        #             st.session_state.processing_status[file_name] = "failed"
                        #             all_files_processed = False
                        # except Exception as e:
                        #     st.error(f"Error processing {file_name}: {str(e)}")
                        #     st.session_state.processing_status[file_name] = "failed"
                        #     all_files_processed = False
                    # app.py (simplified processing section)

                    if file_obj:
                        try:
                            # Use the unified processor
                            st.session_state.conversation = process_document(
                                file_obj,
                                add_to_existing=(st.session_state.conversation is not None),
                                existing_conversation=st.session_state.conversation
                            )
                            
                            if st.session_state.conversation:
                                st.session_state.processed_files.add(file_name)
                                st.session_state.processing_status[file_name] = "complete"
                                st.session_state.document_processed = True
                            else:
                                st.session_state.processing_status[file_name] = "failed"
                                all_files_processed = False
                        except Exception as e:
                            st.error(f"Error processing {file_name}: {str(e)}")
                            st.session_state.processing_status[file_name] = "failed"
                            all_files_processed = False


            elif status == "failed":
                st.error(f"Failed to process {file_name}")
                all_files_processed = False
            elif status == "complete":
                st.success(f"Successfully processed {file_name}")
        
        # Final success message if all completed in this batch
        if all_files_processed and all(status == "complete" for status in st.session_state.processing_status.values()):
            processed_count = len([s for s in st.session_state.processing_status.values() if s == "complete"])
            st.success(f"All new document(s) have been added to the knowledge base!")

    # Knowledge base management
    if st.session_state.processed_files:
        st.divider()
        st.subheader("Knowledge Base Management")
        st.write(f"Total documents: **{len(st.session_state.processed_files)}**")
        
        # Option to clear knowledge base
        if st.button("Clear Knowledge Base"):
            st.session_state.conversation = None
            st.session_state.processed_files = set()
            st.session_state.document_processed = False
            st.session_state.chat_history = []
            st.success("Knowledge base cleared successfully.")
            st.rerun()

    st.divider()
    
    # User guide based on role
    if st.session_state.user_role == "student":
        st.subheader("Student Guide")
        st.write("""
            1. Upload course materials provided by your professor
            2. Process the materials to build the knowledge base
            3. Ask questions about specific topics you're studying
            4. Get explanations based on your course materials
        """)
    else:
        st.subheader("Professor Guide")
        st.write("""
            1. Upload course materials, lecture notes, and resources
            2. Process the materials to build the knowledge base
            3. Students can then interact with this assistant
            4. You can also use it to create teaching materials or answer common questions
        """)

    st.divider()
    st.caption("Powered by Streamlit, LangChain, Ollama, and FAISS")

# Main chat area
if st.session_state.document_processed:
    # Custom greeting based on role
    if "chat_started" not in st.session_state:
        if st.session_state.user_role == "student":
            st.info("I'm your study assistant ready to help with your course materials. What questions do you have about the content?")
        else:
            st.info("I'm your teaching assistant ready to support your course delivery. I can help create content, answer common questions, or assist with research based on the uploaded materials.")
        st.session_state.chat_started = True
        
    handle_chat_input()
else:
    if st.session_state.user_role == "student":
        st.info("Upload and process your course materials to start getting help with your studies.")
    else:
        st.info("Upload and process course materials to build a knowledge base for your students and teaching support.")
    
    st.write("👈 Upload PDFs in the sidebar to get started")



