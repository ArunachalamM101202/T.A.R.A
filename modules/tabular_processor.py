# modules/tabular_processor.py

import pandas as pd
import tempfile
import os
import json
from langchain.schema import Document
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.memory import ConversationBufferMemory
from langchain_community.llms import Ollama
from langchain.chains import ConversationalRetrievalChain
import streamlit as st

def process_tabular_file(uploaded_file):
    """
    Process CSV or Excel files without chunking them.
    
    Args:
        uploaded_file: The uploaded file object
        
    Returns:
        ConversationalRetrievalChain or None if processing fails
    """
    file_extension = os.path.splitext(uploaded_file.name)[1].lower()
    
    try:
        # Create temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as tmp_file:
            tmp_file.write(uploaded_file.getvalue())
            tmp_path = tmp_file.name
        
        # Load data into DataFrame
        if file_extension == '.csv':
            df = pd.read_csv(tmp_path)
        elif file_extension in ['.xlsx', '.xls']:
            df = pd.read_excel(tmp_path)
        else:
            raise ValueError(f"Unsupported file extension: {file_extension}")
        
        # Process each sheet as a document (for Excel with multiple sheets)
        documents = []
        
        # For single dataframe (CSV or single sheet Excel)
        # Create metadata with schema information
        schema = {col: str(dtype) for col, dtype in df.dtypes.items()}
        
        # Create statistical summary
        stats = {}
        for col in df.columns:
            if pd.api.types.is_numeric_dtype(df[col]):
                stats[col] = {
                    "min": float(df[col].min()) if not pd.isna(df[col].min()) else None,
                    "max": float(df[col].max()) if not pd.isna(df[col].max()) else None,
                    "mean": float(df[col].mean()) if not pd.isna(df[col].mean()) else None,
                    "median": float(df[col].median()) if not pd.isna(df[col].median()) else None
                }
        
        # Convert first 10 rows to string for preview
        preview_rows = df.head(10).to_string()
        
        # Create a document for table schema and info
        table_info_doc = Document(
            page_content=f"""
            Filename: {uploaded_file.name}
            Total rows: {len(df)}
            Total columns: {len(df.columns)}
            Column names: {', '.join(df.columns)}
            Column types: {json.dumps(schema)}
            Statistics: {json.dumps(stats)}
            
            Preview:
            {preview_rows}
            """,
            metadata={
                "source": uploaded_file.name,
                "type": "table_info",
                "rows": len(df),
                "columns": len(df.columns),
                "column_names": list(df.columns)
            }
        )
        documents.append(table_info_doc)
        
        # Create a document for each column with its description
        for column in df.columns:
            unique_values = df[column].nunique()
            sample_values = df[column].dropna().sample(min(5, len(df))).tolist() if len(df) > 0 else []
            
            column_doc = Document(
                page_content=f"""
                Column: {column}
                From file: {uploaded_file.name}
                Data type: {df[column].dtype}
                Number of unique values: {unique_values}
                Number of missing values: {df[column].isna().sum()}
                Sample values: {sample_values}
                """,
                metadata={
                    "source": uploaded_file.name,
                    "type": "column_info",
                    "column_name": column,
                    "data_type": str(df[column].dtype)
                }
            )
            documents.append(column_doc)
        
        # Save the full dataframe as a JSON string in a document
        # This allows querying the entire dataset
        df_json = df.to_json(orient="records", date_format="iso")
        full_data_doc = Document(
            page_content=f"""
            Complete data from {uploaded_file.name}:
            {df_json}
            """,
            metadata={
                "source": uploaded_file.name,
                "type": "full_data",
                "format": "json"
            }
        )
        documents.append(full_data_doc)
        
        # Create embeddings and vector store
        embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        vector_store = FAISS.from_documents(documents, embeddings)
        
        # Clean up the temporary file
        os.unlink(tmp_path)
        
        # Create conversation chain
        memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)
        llm = Ollama(model="gemma3:4b", temperature=0.5)
        
        return ConversationalRetrievalChain.from_llm(
            llm=llm,
            retriever=vector_store.as_retriever(search_kwargs={"k": 4}),
            memory=memory,
            verbose=False
        )
    
    except Exception as e:
        st.error(f"Error processing tabular file: {e}")
        if 'tmp_path' in locals():
            os.unlink(tmp_path)
        return None