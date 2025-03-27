import streamlit as st
import os
import tempfile
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.llms import Ollama
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory

# Set page configuration
st.set_page_config(page_title="Document RAG Chatbot", page_icon="📚", layout="wide")

# App title and description
st.title("Document RAG Chatbot")
st.subheader("Upload a PDF, click 'Learn', and start asking questions!")

# Initialize session state variables
if "conversation" not in st.session_state:
    st.session_state.conversation = None
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "document_processed" not in st.session_state:
    st.session_state.document_processed = False

# Function to process the uploaded PDF document
def process_document(uploaded_file):
    # Create a temporary file
    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
        tmp_file.write(uploaded_file.getvalue())
        tmp_path = tmp_file.name
    
    try:
        # Load the PDF
        loader = PyPDFLoader(tmp_path)
        documents = loader.load()
        st.info(f"Loaded {len(documents)} pages from the PDF.")
        
        # Split the document into chunks
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len
        )
        chunks = text_splitter.split_documents(documents)
        st.info(f"Split into {len(chunks)} chunks of text for processing.")
        
        # Create embeddings and store in vector database
        # Using HuggingFace embeddings (which run locally)
        embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        vector_store = FAISS.from_documents(chunks, embeddings)
        st.success("Document processed and indexed successfully!")
        
        # Initialize the conversation memory
        memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True
        )
        
        # Initialize the Ollama LLM
        llm = Ollama(model="gemma3:4b", temperature=0.5)
        
        # Create the conversation chain
        conversation_chain = ConversationalRetrievalChain.from_llm(
            llm=llm,
            retriever=vector_store.as_retriever(search_kwargs={"k": 4}),
            memory=memory,
            verbose=True
        )
        
        # Clean up the temporary file
        os.unlink(tmp_path)
        
        return conversation_chain
    
    except Exception as e:
        st.error(f"Error processing document: {e}")
        # Clean up the temporary file
        os.unlink(tmp_path)
        return None

# Sidebar for uploading document
with st.sidebar:
    st.header("Upload Document")
    uploaded_file = st.file_uploader("Choose a PDF document", type="pdf")
    
    if uploaded_file is not None:
        st.session_state.file_name = uploaded_file.name
        learn_button = st.button("Learn")
        
        if learn_button:
            with st.spinner("Processing document..."):
                conversation_chain = process_document(uploaded_file)
                if conversation_chain:
                    st.session_state.conversation = conversation_chain
                    st.session_state.document_processed = True
                    st.success(f"Processed {uploaded_file.name} successfully!")
                    st.rerun()

# Main area for chat interaction
if st.session_state.document_processed:
    # Display chat messages
    for message in st.session_state.chat_history:
        if message["role"] == "user":
            with st.chat_message("user"):
                st.write(message["content"])
        else:
            with st.chat_message("assistant"):
                st.write(message["content"])
    
    # Chat input
    user_question = st.chat_input("Ask a question about your document:")
    if user_question:
        with st.chat_message("user"):
            st.write(user_question)
        
        # Add user message to chat history
        st.session_state.chat_history.append({"role": "user", "content": user_question})
        
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                # Get the response from the conversation chain
                response = st.session_state.conversation({"question": user_question})
                ai_response = response["answer"]
                st.write(ai_response)
        
        # Add AI response to chat history
        st.session_state.chat_history.append({"role": "assistant", "content": ai_response})
else:
    st.info("Please upload a PDF document and click 'Learn' to start chatting!")

# Add instructions at the bottom
with st.expander("How to use this app"):
    st.write("""
    1. Upload a PDF document using the sidebar.
    2. Click the 'Learn' button to process the document.
    3. Once processing is complete, you can ask questions about the document in the chat.
    4. The AI will respond based on the content of your document.
    """)

# Display app information
with st.sidebar:
    st.markdown("---")
    st.markdown("### About")
    st.markdown("This app uses LangChain, Ollama with Gemma 4B, and in-memory vector storage to create a RAG-based chatbot for your documents.")
    st.markdown("Made with ❤️ using Streamlit")