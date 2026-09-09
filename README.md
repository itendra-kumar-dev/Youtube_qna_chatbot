# NOVA

NOVA is a Chrome extension that adds an optional chat rail to YouTube. It reads the current video ID in the browser, sends a question to the API, retrieves relevant transcript chunks, and answers from that context.

## Run locally

1. Create `api/.env` and add your new OpenAI key. NOVA is strictly RAG-based: it embeds transcript chunks, retrieves relevant context, and generates answers only from that context.
2. Start the API: `cd api && python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt && uvicorn main:app --reload`.
3. Start the Streamlit UI: `streamlit run streamlit_app.py` and open `http://localhost:8501`.
4. Build the extension: `cd extension && npm run build`.
5. Open `chrome://extensions`, enable Developer mode, choose **Load unpacked**, and select `extension/dist`.

The Streamlit UI is browser-independent and works in Chrome, Safari, Firefox, Edge, and other modern browsers. For a hosted Streamlit deployment, set the `NOVA_API_URL` environment variable to the deployed FastAPI URL, then deploy `streamlit_app.py` from the repository root using `requirements.txt`.

## Deploy

The API includes `render.yaml` support for Render. Deploy the `api` service, set `OPENAI_API_KEY`, then build the extension with `VITE_API_URL=https://your-api.onrender.com npm run build` and reload the unpacked extension.

The extension is intentionally opt-in per YouTube page and stores only its enabled state in browser storage.