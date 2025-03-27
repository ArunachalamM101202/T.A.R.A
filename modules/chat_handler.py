# modules/chat_handler.py

import streamlit as st
from modules.tabular_analyzer import TabularAnalyzer
import os

# Initialize tabular analyzer in session state if not present
if "tabular_analyzer" not in st.session_state:
    st.session_state.tabular_analyzer = TabularAnalyzer()

# Define role-specific instruction prompts
STUDENT_INSTRUCTIONS = """
You are a helpful teaching assistant responding to a student. Focus on:
- Explaining concepts clearly using simple language
- Breaking down complex ideas into manageable parts
- Providing relevant examples that illustrate key points
- Guiding the learning process without directly solving homework problems
- Encouraging critical thinking and deeper understanding of the material
- Using a supportive and encouraging tone
"""

PROFESSOR_INSTRUCTIONS = """
You are a teaching assistant supporting a professor. Focus on:
- Providing in-depth analysis of academic topics
- Suggesting effective teaching approaches for complex concepts
- Offering research-informed perspectives on the subject matter
- Discussing pedagogical strategies and assessment options
- Referencing relevant academic literature when appropriate
- Using a collegial, professional tone
"""

def handle_chat_input():
    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.write(message["content"])

    user_question = st.chat_input("Ask a question:")
    if user_question:
        st.chat_message("user").write(user_question)
        st.session_state.chat_history.append({"role": "user", "content": user_question})
        
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                # Check if the question is about data analysis
                is_analysis_query = should_generate_analysis_code(user_question)
                has_tabular_data = len(st.session_state.tabular_analyzer.dataframes) > 0
                
                if is_analysis_query and has_tabular_data:
                    # Use Gemini for data analysis
                    with st.spinner("Analyzing data..."):
                        result = st.session_state.tabular_analyzer.analyze_with_gemini(user_question)
                        
                        if result["success"]:
                            # Display the analysis results
                            st.write(result["output"])
                            
                            # Add to chat history
                            st.session_state.chat_history.append({
                                "role": "assistant", 
                                "content": result["output"]
                            })
                        else:
                            # Display the error
                            st.error(f"Analysis failed: {result['error']}")
                            
                            # Add error to chat history
                            error_message = f"I encountered an issue while analyzing the data: {result['error']}"
                            st.session_state.chat_history.append({
                                "role": "assistant", 
                                "content": error_message
                            })
                else:
                    # Select instruction prompt based on user role
                    if st.session_state.user_role == "student":
                        instruction_prompt = STUDENT_INSTRUCTIONS
                    else:  # professor
                        instruction_prompt = PROFESSOR_INSTRUCTIONS
                    
                    # Use standard RAG approach for non-analysis queries
                    enhanced_question = f"{instruction_prompt}\n\nUser question: {user_question}"
                    response = st.session_state.conversation({"question": enhanced_question})
                    answer = response["answer"]
                    st.write(answer)
                    
                    # Add to chat history
                    st.session_state.chat_history.append({
                        "role": "assistant", 
                        "content": answer
                    })

def should_generate_analysis_code(query):
    """
    Determine if a query requires data analysis code generation.
    Returns True only for queries that clearly need computational analysis.
    """
    # Keywords that strongly indicate need for analysis
    analysis_keywords = [
        "calculate", "compute", "analyze data", "run analysis", 
        "plot", "graph", "chart", "visualize", "visualization",
        "statistics", "metrics", "average", "mean", "median", "sum", 
        "correlation", "trend", "compare data", "percentage", 
        "distribution", "histogram", "bar chart", "pie chart", 
        "standard deviation", "variance", "maximum", "minimum"
    ]
    
    # Analysis action verbs
    analysis_verbs = [
        "analyze", "calculate", "compute", "count", "summarize", 
        "plot", "chart", "graph", "compare"
    ]
    
    # Data metric nouns
    data_metrics = [
        "average", "mean", "median", "mode", "sum", "total",
        "minimum", "maximum", "count", "frequency", "percentage",
        "growth", "trend", "distribution", "correlation", "variance"
    ]
    
    query_lower = query.lower()
    
    # Check for strong indicators - direct analysis requests
    for keyword in analysis_keywords:
        if keyword in query_lower:
            return True
    
    # Check for combinations of analysis verbs and data metrics
    for verb in analysis_verbs:
        for metric in data_metrics:
            if f"{verb} {metric}" in query_lower or f"{verb} the {metric}" in query_lower:
                return True
    
    # Check for specific request patterns
    if "how many" in query_lower and any(term in query_lower for term in ["rows", "entries", "records", "data points"]):
        return True
        
    if any(phrase in query_lower for phrase in ["group by", "filter by", "sort by"]):
        return True
        
    # Look for questions about highest/lowest values
    highest_lowest = ["highest", "lowest", "greatest", "smallest", "most", "least", "top", "bottom"]
    if any(term in query_lower for term in highest_lowest) and any(metric in query_lower for metric in data_metrics):
        return True
    
    # Default to using RAG for anything else
    return False