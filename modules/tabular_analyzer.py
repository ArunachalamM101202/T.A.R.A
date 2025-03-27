# modules/tabular_analyzer.py

import pandas as pd
import tempfile
import os
import io
import base64
import streamlit as st
from google import genai
from google.genai import types

class TabularAnalyzer:
    """Class to handle tabular data analysis using Gemini API."""
    
    def __init__(self):
        self.dataframes = {}  # Store loaded dataframes by filename
        # Initialize Gemini API client if API key is available
        if "GEMINI_API_KEY" in os.environ:
            self.client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
            self.model = "gemini-2.0-flash"  # You can change to other Gemini models as needed
        else:
            self.client = None
    
    def load_file(self, uploaded_file):
        """Load a tabular file into a dataframe and store it."""
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
            
            # Store the dataframe with the filename as key
            self.dataframes[uploaded_file.name] = df
            
            # Clean up temp file
            os.unlink(tmp_path)
            return True
            
        except Exception as e:
            if 'tmp_path' in locals():
                os.unlink(tmp_path)
            raise e
    
    def get_dataframe_info(self, filename):
        """Get information about a dataframe."""
        if filename not in self.dataframes:
            return None
        
        df = self.dataframes[filename]
        
        # Basic information
        info = {
            "filename": filename,
            "shape": df.shape,
            "columns": list(df.columns),
            "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()},
        }
        
        return info
    
    def analyze_with_gemini(self, user_query):
        """
        Analyze tabular data using Gemini API.
        
        Args:
            user_query: The user's question about the data
            
        Returns:
            Dictionary with response text and success status
        """
        # Check if Gemini API is configured
        if not self.client:
            return {
                "success": False,
                "error": "Gemini API key not configured. Set the GEMINI_API_KEY environment variable.",
                "output": ""
            }
        
        # Check if we have dataframes loaded
        if not self.dataframes:
            return {
                "success": False,
                "error": "No tabular data has been loaded yet.",
                "output": ""
            }
        
        try:
            # Prepare data context for Gemini
            data_context = []
            
            for filename, df in self.dataframes.items():
                # Convert dataframe to CSV
                csv_data = df.to_csv(index=False)
                
                # Get basic info
                info = self.get_dataframe_info(filename)
                
                # Add to context
                data_context.append(f"""
File: {filename}
Shape: {info['shape'][0]} rows, {info['shape'][1]} columns
Columns: {', '.join(info['columns'])}
Column types: {info['dtypes']}

CSV DATA:
{csv_data}
                """)
            
            # Create the full prompt
            prompt = f"""You are an expert data analyst assistant. Analyze the following tabular data based on the user's query.

DATA:
{''.join(data_context)}

USER QUERY:
{user_query}

Please provide a detailed analysis with relevant statistics, insights, and explanations. If the query involves calculations, perform them accurately and show your work. If appropriate, describe what visualizations would be helpful for this data.
"""
            
            # Create Gemini content
            contents = [
                types.Content(
                    role="user",
                    parts=[
                        types.Part.from_text(text=prompt),
                    ],
                ),
            ]
            
            # Configure Gemini request
            generate_content_config = types.GenerateContentConfig(
                response_mime_type="text/plain",
            )
            
            # Send request to Gemini
            response = self.client.models.generate_content(
                model=self.model,
                contents=contents,
                config=generate_content_config,
            )
            
            # Extract the response text
            result = {
                "success": True,
                "output": response.text,
                "error": ""
            }
            
            return result
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Error analyzing data with Gemini: {str(e)}",
                "output": ""
            }