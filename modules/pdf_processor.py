import os
import tempfile
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.llms import Ollama
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory
import streamlit as st

def process_pdf(uploaded_file, add_to_existing=False, existing_conversation=None):
    """
    Process a PDF file and either create a new conversational chain or add to an existing one.
    
    Args:
        uploaded_file: The uploaded PDF file object
        add_to_existing: Whether to add documents to an existing conversation
        existing_conversation: The existing ConversationalRetrievalChain object
        
    Returns:
        ConversationalRetrievalChain: Either a new chain or the updated existing one
    """
    # Create a temporary file to store the uploaded PDF
    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
        tmp_file.write(uploaded_file.getvalue())
        tmp_path = tmp_file.name

    try:
        # Load and process the new PDF
        loader = PyPDFLoader(tmp_path)
        documents = loader.load()
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        chunks = text_splitter.split_documents(documents)
        
        # Always create embeddings for the new document chunks
        embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        
        # Decide whether to create a new vectorstore or add to existing one
        if add_to_existing and existing_conversation:
            # Extract the existing vectorstore from the conversation
            existing_retriever = existing_conversation.retriever
            existing_vectorstore = existing_retriever.vectorstore
            
            # Add new document chunks to the existing vectorstore
            existing_vectorstore.add_documents(chunks)
            
            # The existing conversation already has the updated vectorstore
            # since vectorstores are modified in-place
            conversation = existing_conversation
        else:
            # Create a new vectorstore and conversation
            vector_store = FAISS.from_documents(chunks, embeddings)
            memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)
            llm = Ollama(model="gemma3:4b", temperature=0.5)
            
            # Create a new conversational chain
            conversation = ConversationalRetrievalChain.from_llm(
                llm=llm,
                retriever=vector_store.as_retriever(search_kwargs={"k": 4}),
                memory=memory,
                verbose=False
            )
        
        # Clean up the temporary file
        os.unlink(tmp_path)
        
        return conversation
        
    except Exception as e:
        # Clean up in case of error
        st.error(f"Error processing PDF: {e}")
        os.unlink(tmp_path)
        return None