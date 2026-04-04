import { useState } from 'react'
import './App.css'

const API_URL = import.meta.env.VITE_API_URL ?? ''

export default function App() {
  const [emailText, setEmailText] = useState('')
  const [riskScore, setRiskScore] = useState(null)
  const [flags, setFlags] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  async function handleAnalyze() {
    setError(null)
    setLoading(true)
    try {
      const res = await fetch(`${API_URL}/analyze`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: emailText }),
      })
      const data = await res.json().catch(() => ({}))
      if (!res.ok) {
        setRiskScore(null)
        setFlags([])
        setError(data.error || `Request failed (${res.status})`)
        return
      }
      setRiskScore(data.risk_score)
      setFlags(Array.isArray(data.flags) ? data.flags : [])
    } catch (e) {
      setRiskScore(null)
      setFlags([])
      setError(e.message || 'Could not reach the server.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="app">
      <header className="header">
        <h1>Phishing Email Analyzer</h1>
        <p className="subtitle">
          Paste an email below and run a quick risk check (mock results for now).
        </p>
      </header>

      <main className="main">
        <label className="label" htmlFor="email-input">
          Email content
        </label>
        <textarea
          id="email-input"
          className="textarea"
          rows={12}
          placeholder="Paste headers and body here..."
          value={emailText}
          onChange={(e) => setEmailText(e.target.value)}
          disabled={loading}
        />

        <button
          type="button"
          className="analyze-btn"
          onClick={handleAnalyze}
          disabled={loading}
        >
          {loading ? 'Analyzing…' : 'Analyze'}
        </button>

        <section className="results" aria-live="polite">
          <h2>Results</h2>
          {error && <p className="error">{error}</p>}
          {!error && riskScore === null && !loading && (
            <p className="placeholder">Run an analysis to see the risk score and flags.</p>
          )}
          {loading && <p className="placeholder">Waiting for response…</p>}
          {!error && riskScore !== null && !loading && (
            <>
              <p className="risk">
                <strong>Risk score:</strong> {riskScore}
              </p>
              <div>
                <strong>Flagged issues</strong>
                {flags.length === 0 ? (
                  <p className="placeholder">None reported.</p>
                ) : (
                  <ul className="flags">
                    {flags.map((item) => (
                      <li key={item}>{item}</li>
                    ))}
                  </ul>
                )}
              </div>
            </>
          )}
        </section>
      </main>
    </div>
  )
}
