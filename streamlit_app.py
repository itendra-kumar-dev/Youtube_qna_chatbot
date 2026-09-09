import os
import re
from urllib.parse import parse_qs, urlparse

import requests
import streamlit as st


API_URL = os.getenv("NOVA_API_URL", "http://127.0.0.1:8000").rstrip("/")


def extract_video_id(value: str) -> str:
    value = value.strip()
    if re.fullmatch(r"[A-Za-z0-9_-]{11}", value):
        return value
    parsed = urlparse(value)
    if parsed.hostname in {"youtube.com", "www.youtube.com", "m.youtube.com"}:
        return parse_qs(parsed.query).get("v", [""])[0]
    if parsed.hostname == "youtu.be":
        return parsed.path.strip("/").split("/")[0]
    return ""


def ask_api(video_id: str, question: str) -> dict:
    response = requests.post(
        f"{API_URL}/api/ask",
        json={"video_id": video_id, "question": question},
        timeout=90,
    )
    if response.status_code >= 400:
        detail = response.json().get("detail", "The RAG service could not answer.")
        raise RuntimeError(detail)
    return response.json()


st.set_page_config(page_title="NOVA | Ask your video", page_icon="N", layout="centered")
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=Fraunces:opsz,wght@9..144,400;9..144,600&display=swap');
:root { --ink: #28231f; --muted: #756b61; --paper: #f6f0e6; --rust: #a2593f; }
.stApp { background: radial-gradient(circle at 90% 0%, #edd08f 0, transparent 25%), var(--paper); color: var(--ink); }
[data-testid="stHeader"] { background: transparent; }
.nova-brand { display: flex; justify-content: space-between; align-items: center; padding: 1.2rem 0 2.6rem; border-bottom: 1px solid #d8cdbd; font: 500 .72rem 'DM Mono', monospace; letter-spacing: .18em; }
.nova-mark { display: inline-grid; place-items: center; width: 28px; height: 28px; margin-right: .6rem; border-radius: 50%; color: var(--paper); background: var(--ink); font: 600 1rem Fraunces, serif; letter-spacing: 0; }
.nova-hero h1 { margin: 2.8rem 0 .8rem; color: var(--ink); font: 400 clamp(3rem, 8vw, 5rem)/.95 Fraunces, serif; letter-spacing: -.045em; }
.nova-hero em { color: var(--rust); font-style: normal; }.nova-hero p { max-width: 28rem; color: var(--muted); font: 1rem/1.5 sans-serif; }
.stTextInput label, .stTextArea label { color: var(--muted); font: 500 .68rem 'DM Mono', monospace; letter-spacing: .12em; text-transform: uppercase; }
div.stButton > button { border: 1px solid #cbbdac; border-radius: 999px; color: var(--muted); background: transparent; }.stButton > button:hover { border-color: var(--rust); color: var(--rust); }
[data-testid="stChatMessage"] { border: 1px solid #ded3c4; border-radius: 3px 16px 16px 16px; background: #eee6da; }.nova-foot { margin-top: 2rem; color: #9c9185; font: .7rem 'DM Mono', monospace; }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="nova-brand"><span><span class="nova-mark">N</span>NOVA</span><span>TRANSCRIPT RAG</span></div>', unsafe_allow_html=True)
st.markdown('<div class="nova-hero"><h1>Make the ideas<br><em>stick.</em></h1><p>Ask grounded questions about any YouTube video. NOVA retrieves the relevant transcript context before it answers.</p></div>', unsafe_allow_html=True)

with st.sidebar:
    st.markdown("### Video context")
    video_input = st.text_input("YouTube URL or video ID", placeholder="youtube.com/watch?v=...")
    video_id = extract_video_id(video_input)
    if video_id:
        st.success(f"Connected: `{video_id}`")
    else:
        st.info("Add an 11-character YouTube video ID or URL.")
    st.caption(f"API: {API_URL}")

if "messages" not in st.session_state:
    st.session_state.messages = []
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if not st.session_state.messages:
    st.markdown("#### Start with a useful question")
    suggestions = st.columns(2)
    suggested_question = None
    if suggestions[0].button("Key takeaways"):
        suggested_question = "What are the key takeaways from this video?"
    if suggestions[1].button("Explain simply"):
        suggested_question = "Explain the main idea simply."
else:
    suggested_question = None

question = st.chat_input("Ask anything about this video...") or suggested_question
if question:
    if not video_id:
        st.error("Add a valid YouTube URL or video ID first.")
    else:
        st.session_state.messages.append({"role": "user", "content": question})
        with st.chat_message("user"):
            st.markdown(question)
        with st.chat_message("assistant"):
            with st.spinner("Retrieving transcript context..."):
                try:
                    result = ask_api(video_id, question)
                    answer = result["answer"]
                    st.markdown(answer)
                    st.caption(f"RAG context: {result.get('sources', 0)} transcript chunks")
                    st.session_state.messages.append({"role": "assistant", "content": answer})
                except (requests.RequestException, RuntimeError) as error:
                    st.error(str(error))

st.markdown('<div class="nova-foot">NOVA answers only from retrieved transcript context · private by default</div>', unsafe_allow_html=True)