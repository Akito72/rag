import os
from uuid import uuid4

import requests
import streamlit as st


API_URL = os.getenv("API_URL", "http://localhost:8000/api/v1")

st.set_page_config(page_title="Production RAG", layout="wide")
st.title("Production RAG Chat")
st.caption("Upload documents, index them, and chat against retrieved context.")

if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid4())
if "messages" not in st.session_state:
    st.session_state.messages = []
if "last_job_id" not in st.session_state:
    st.session_state.last_job_id = None

workspace_id = st.text_input("Workspace ID", value="default-workspace")

with st.sidebar:
    st.subheader("Upload Documents")
    files = st.file_uploader(
        "Supported: PDF, DOCX, TXT, MD",
        type=["pdf", "docx", "txt", "md"],
        accept_multiple_files=True,
    )
    if st.button("Upload and Index", use_container_width=True):
        if not files:
            st.warning("Select at least one file.")
        else:
            response = requests.post(
                f"{API_URL}/documents/upload",
                data={"workspace_id": workspace_id},
                files=[("files", (uploaded.name, uploaded.getvalue(), uploaded.type)) for uploaded in files],
                timeout=120,
            )
            if response.ok:
                payload = response.json()
                st.session_state.last_job_id = payload["job_id"]
                st.success(f"{payload['message']} Job ID: {payload['job_id']}")
            else:
                st.error(response.text)
    if st.session_state.last_job_id and st.button("Check Index Job", use_container_width=True):
        response = requests.get(f"{API_URL}/documents/jobs/{st.session_state.last_job_id}", timeout=30)
        if response.ok:
            payload = response.json()
            st.info(f"Job {payload['job_id']} status: {payload['status']} | chunks: {payload['chunk_count']}")
            if payload.get("error_message"):
                st.error(payload["error_message"])
        else:
            st.error(response.text)

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if message.get("sources"):
            for source in message["sources"]:
                st.caption(f"{source['source_name']} | score={source['score']:.3f}")

question = st.chat_input("Ask a question about your uploaded documents")
if question:
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)

    response = requests.post(
        f"{API_URL}/chat/query",
        json={
            "workspace_id": workspace_id,
            "session_id": st.session_state.session_id,
            "question": question,
        },
        timeout=120,
    )
    if response.ok:
        payload = response.json()
        assistant_message = {
            "role": "assistant",
            "content": payload["answer"],
            "sources": payload["sources"],
        }
        st.session_state.messages.append(assistant_message)
        with st.chat_message("assistant"):
            st.markdown(payload["answer"])
            for source in payload["sources"]:
                st.caption(f"{source['source_name']} | score={source['score']:.3f}")
    else:
        st.error(response.text)
