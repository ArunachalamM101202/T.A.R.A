# modules/document_processor.py

import os
from modules.pdf_processor import process_pdf
import streamlit as st

def process_document(uploaded_file, add_to_existing=False, existing_conversation=None):
    """
    Process any supported document type (PDF, CSV, Excel).
    
    Args:
        uploaded_file: The uploaded file object
        add_to_existing: Whether to add to existing conversation
        existing_conversation: The existing conversation object
        
    Returns:
        ConversationalRetrievalChain object or None if processing fails
    """
    file_extension = os.path.splitext(uploaded_file.name)[1].lower()
    
    if file_extension == '.pdf':
        # Process PDF with existing PDF processor
        if add_to_existing and existing_conversation:
            return process_pdf(uploaded_file, add_to_existing=True, existing_conversation=existing_conversation)
        else:
            return process_pdf(uploaded_file)
    
    elif file_extension in ['.csv', '.xlsx', '.xls']:
        # Load tabular file into the analyzer
        try:
            # Load file into tabular analyzer
            st.session_state.tabular_analyzer.load_file(uploaded_file)
            
            # If this is the first document, create a conversation chain
            if not add_to_existing or existing_conversation is None:
                # Create minimal vectorstore for interacting with non-analysis questions
                from langchain.schema import Document
                from langchain_community.vectorstores import FAISS
                from langchain_community.embeddings import HuggingFaceEmbeddings
                from langchain.memory import ConversationBufferMemory
                from langchain_community.llms import Ollama
                from langchain.chains import ConversationalRetrievalChain
                
                # Create a simple document about the file
                doc = Document(
                    page_content=f"This is a tabular data file named {uploaded_file.name}. Use data analysis techniques to query its contents.",
                    metadata={"source": uploaded_file.name, "type": "tabular"}
                )
                
                # Create embeddings and vectorstore
                embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
                vector_store = FAISS.from_documents([doc], embeddings)
                
                # Create conversation chain
                memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)
                llm = Ollama(model="gemma3:4b", temperature=0.5)
                
                return ConversationalRetrievalChain.from_llm(
                    llm=llm,
                    retriever=vector_store.as_retriever(search_kwargs={"k": 1}),
                    memory=memory,
                    verbose=False
                )
            else:
                # Just return the existing conversation
                return existing_conversation
                
        except Exception as e:
            st.error(f"Error processing tabular file: {e}")
            return None
    
    else:
        # Unsupported file type
        raise ValueError(f"Unsupported file extension: {file_extension}")