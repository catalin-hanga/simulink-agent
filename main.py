from utils import llm
from tools import tools
from prompts import prompt

import streamlit as st
import speech_recognition as sr

from langchain.agents import AgentExecutor, create_react_agent
from langchain_community.callbacks.streamlit import StreamlitCallbackHandler

#----------------------------------------------------

st.set_page_config(page_title = "SimuLang", page_icon = ":robot_face:")

st.markdown("""
        <style>
               .block-container {
                    padding-top:    2.8rem;
                    padding-bottom: 0.5rem;
                }
        </style>
        """, unsafe_allow_html = True)

def stream_data(answer : str):
    import time
    for word in answer.split(" "):
        yield word + " "
        time.sleep(0.02)

#----------------------------------------------------

agent  = create_react_agent(llm, tools, prompt)

agent_executor = AgentExecutor(
                                agent = agent,
                                tools = tools,
                                verbose = True,
                                handle_parsing_errors = True,
                                stream_runnable = True,
                                max_execution_time = 180,
                                max_iterations = 20,
                            )

#----------------------------------------------------

@st.fragment
def main_loop():

    container = st.container(border = True, height = 550)

    if "messages" not in st.session_state:
        st.session_state["messages"] = []
    else:
        with container:
            for message in st.session_state["messages"]:
                with st.chat_message(name = message["role"]):
                    st.markdown(body = message["content"])


    (col1, col2) = st.columns([0.9, 0.1])

    with col1:
        user_messge = st.chat_input(placeholder = "Please enter your query here")

    with col2:
        if st.button(label = ":studio_microphone:"):
            recognizer = sr.Recognizer()
            with sr.Microphone() as source:
#                recognizer.adjust_for_ambient_noise(source)
                audio = recognizer.listen(source)
            user_messge = recognizer.recognize_whisper(audio_data = audio, model = "base", language = "english")
    #        user_messge = recognizer.recognize_whisper_api(audio)


    if user_messge:
        with container:

            with st.chat_message(name = "user"):
                st.markdown(body = user_messge)

            with st.chat_message(name = "assistant"):
                st_callback = StreamlitCallbackHandler(
                                                        parent_container = st.container(),
                                                        expand_new_thoughts = False,
                                                        collapse_completed_thoughts = True,                                   
                                                    )
            
                response = agent_executor.invoke(
                        {"input": user_messge, "chat_history": st.session_state["messages"]}, 
                        {"callbacks": [st_callback]},
                    )
                
                st.write_stream(stream_data(response["output"]))

            st.session_state["messages"].append({"role": "user",      "content": response["input"]})    
            st.session_state["messages"].append({"role": "assistant", "content": response["output"]})

main_loop()