import { useState } from 'react'
import type { FormEvent } from 'react'
import './App.css'

type Message = { role: 'assistant' | 'user'; text: string }
const apiBase = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'

function App() {
  const params = new URLSearchParams(window.location.search)
  const videoId = params.get('videoId') ?? 'Gfr50f6ZBvo'
  const [question, setQuestion] = useState('')
  const [loading, setLoading] = useState(false)
  const [messages, setMessages] = useState<Message[]>([
    { role: 'assistant', text: 'I have this video open. Ask me to explain, summarize, or find a moment.' },
  ])

  async function ask(event: FormEvent) {
    event.preventDefault()
    const trimmed = question.trim()
    if (!trimmed || loading) return
    setQuestion('')
    setMessages((current) => [...current, { role: 'user', text: trimmed }])
    setLoading(true)
    try {
      const response = await fetch(`${apiBase}/api/ask`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ video_id: videoId, question: trimmed }) })
      const data = await response.json()
      setMessages((current) => [...current, { role: 'assistant', text: data.answer ?? data.detail ?? 'I could not answer that yet.' }])
    } catch {
      setMessages((current) => [...current, { role: 'assistant', text: 'The NOVA service is offline. Start the API or set VITE_API_URL to your deployed endpoint.' }])
    } finally { setLoading(false) }
  }

  return (
    <main className="panel">
      <header className="topbar"><div className="brand"><span className="brand-mark">N</span><span>NOVA</span></div><span className="live"><i /> video context</span></header>
      <section className="intro"><p className="eyebrow">ASK YOUR VIDEO</p><h1>Make the ideas<br /><em>stick.</em></h1><p className="subhead">A calm, contextual copilot for the video you are watching.</p></section>
      <section className="messages" aria-live="polite">{messages.map((message, index) => <div className={`message ${message.role}`} key={`${message.role}-${index}`}><span className="avatar">{message.role === 'assistant' ? 'N' : '↗'}</span><p>{message.text}</p></div>)}{loading && <div className="message assistant"><span className="avatar">N</span><p className="thinking">Searching the transcript<span>...</span></p></div>}</section>
      <div className="suggestions"><button onClick={() => setQuestion('Give me the key takeaways')}>Key takeaways</button><button onClick={() => setQuestion('Explain this simply')}>Explain simply</button></div>
      <form className="composer" onSubmit={ask}><input value={question} onChange={(event) => setQuestion(event.target.value)} placeholder="Ask anything about this video..." aria-label="Ask anything about this video" /><button type="submit" aria-label="Send question">↑</button></form>
      <footer><span>Powered by transcript RAG</span><span className="secure">● private by default</span></footer>
    </main>
  )
}

export default App
