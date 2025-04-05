import streamlit as st
import requests
import base64

st.set_page_config(page_title="Chat with PDF", layout="wide")

API_URL = "http://localhost:5000"

st.markdown("<h1 style='text-align: left;'>LegalAI</h1>", unsafe_allow_html=True)

if 'pdf_uploaded' not in st.session_state:
    st.session_state.pdf_uploaded = False
    st.session_state.pdf_base64 = ""
    st.session_state.chat_history = []

with st.sidebar:
    st.header("Upload Document")
    uploaded_file = st.file_uploader("Choose a PDF file", type=['pdf'])
    
    if uploaded_file is not None:
        file_details = {"Filename": uploaded_file.name, "File size": f"{uploaded_file.size} bytes"}
        st.write(file_details)
        
        if st.button("Process PDF"):
            with st.spinner("Uploading and processing PDF..."):
                files = {"file": (uploaded_file.name, uploaded_file.getbuffer(), "application/pdf")}
                try:
                    response = requests.post(f"{API_URL}/upload_pdf", files=files)
                    if response.status_code == 200:
                        st.success("PDF uploaded and processed successfully!")
                        st.session_state.pdf_uploaded = True
                        response_data = response.json()
                        st.write(f"File size on server: {response_data.get('size_bytes', 'unknown')} bytes")
                        
                        pdf_bytes = uploaded_file.read()
                        st.session_state.pdf_base64 = base64.b64encode(pdf_bytes).decode("utf-8")
                    else:
                        st.error(f" Error: {response.json().get('error', 'Unknown error')}")
                except Exception as e:
                    st.error(f"Error connecting to server: {str(e)}")

    if st.button("Check Server Status"):
        try:
            response = requests.get(f"{API_URL}/status")
            if response.status_code == 200:
                status_data = response.json()
                st.sidebar.write("Server Status:")
                st.sidebar.write(f"- PDF Loaded: {status_data.get('pdf_loaded', False)}")
                st.sidebar.write(f"- Upload Folder: {status_data.get('upload_folder', 'N/A')}")
                st.sidebar.write(f"- Files in folder: {len(status_data.get('files', []))}")
            else:
                st.sidebar.error("Could not retrieve server status")
        except Exception as e:
            st.sidebar.error(f"Error connecting to server: {str(e)}")

col1, col2 = st.columns([1, 1]) 

with col1:
    st.markdown("<h3 style='text-decoration: underline;'>PDF Preview</h3>", unsafe_allow_html=True)

    if st.session_state.pdf_uploaded:
        pdf_display = f"""
        <div>
            <iframe src="data:application/pdf;base64,{st.session_state.pdf_base64}" 
            width="100%" height="900px"></iframe>
        </div>
        """
        st.markdown(pdf_display, unsafe_allow_html=True)
    else:
        st.info("Please upload a PDF document using the sidebar.")

with col2:
    st.markdown("<h3 style='text-decoration: underline;'>Chat</h3>", unsafe_allow_html=True)
    chat_container = st.container()
    user_query = st.text_input("(______________________)",placeholder="Ask anything")    
    if user_query:
        with st.spinner("Processing your question..."):
            try:
                response = requests.post(
                    f"{API_URL}/chat",
                    json={"message": user_query},
                    headers={"Content-Type": "application/json"}
                )
                if response.status_code == 200:
                    ai_response = response.json().get("response", "No response from server")
                    
   
                    st.session_state.chat_history.append((user_query, ai_response))
            
                else:
                    st.error(f"Error: {response.json().get('error', 'Unknown error')}")
            except Exception as e:
                st.error(f"Error connecting to server: {str(e)}")
    

    with chat_container:
        for user_msg, ai_msg in st.session_state.chat_history:
            st.markdown(f"<b style='font-size:18px;'>👤 You:</b> {user_msg}", unsafe_allow_html=True)
            st.markdown(f"<b style='font-size:18px;'>LegalAI:</b> {ai_msg}", unsafe_allow_html=True)