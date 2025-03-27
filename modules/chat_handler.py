# import streamlit as st

# def handle_chat_input():
#     for message in st.session_state.chat_history:
#         with st.chat_message(message["role"]):
#             st.write(message["content"])

#     user_question = st.chat_input("Ask a question:")
#     if user_question:
#         st.chat_message("user").write(user_question)
#         st.session_state.chat_history.append({"role": "user", "content": user_question})
#         with st.chat_message("assistant"):
#             with st.spinner("Thinking..."):
#                 response = st.session_state.conversation({"question": user_question})
#                 answer = response["answer"]
#                 st.write(answer)
#         st.session_state.chat_history.append({"role": "assistant", "content": answer})


import streamlit as st

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
        
        # Select instruction prompt based on user role
        if st.session_state.user_role == "student":
            instruction_prompt = STUDENT_INSTRUCTIONS
        else:  # professor
            instruction_prompt = PROFESSOR_INSTRUCTIONS
        
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                # Combine the instruction with the question to create a single input
                enhanced_question = f"{instruction_prompt}\n\nUser question: {user_question}"
                
                # Pass only the enhanced question to the conversation object
                response = st.session_state.conversation({"question": enhanced_question})
                answer = response["answer"]
                st.write(answer)
        
        st.session_state.chat_history.append({"role": "assistant", "content": answer})