import { useState } from 'react'
import './App.css'

const API_URL = import.meta.env.VITE_API_URL ?? ''

export default function App() {
  const [emailText, setEmailText] = useState('')
  const [prediction, setPrediction] = useState(null)
  const [confidence, setConfidence] = useState(null)
  const [label, setLabel] = useState(null)
  const [modelName, setModelName] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  async function handleAnalyze() {
    setError(null)
    setLoading(true)
    try {
      const res = await fetch(`${API_URL}/predict`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: emailText }),
      })
      const data = await res.json().catch(() => ({}))
      if (!res.ok) {
        setPrediction(null)
        setConfidence(null)
        setLabel(null)
        setModelName(null)
        setError(data.error || data.hint || `Request failed (${res.status})`)
        return
      }
      setPrediction(data.prediction)
      setConfidence(data.confidence)
      setLabel(data.label ?? null)
      setModelName(data.model ?? null)
    } catch (e) {
      setPrediction(null)
      setConfidence(null)
      setLabel(null)
      setModelName(null)
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
          Paste an email below. The backend uses a trained ML model (TF-IDF + classifier) on
          the CEAS dataset.
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
          {!error && prediction === null && !loading && (
            <p className="placeholder">
              Run an analysis to see the model prediction and confidence.
            </p>
          )}
          {loading && <p className="placeholder">Waiting for response…</p>}
          {!error && prediction !== null && !loading && (
            <>
              <p className="risk">
                <strong>Prediction:</strong> {prediction} ({label ?? '—'})
              </p>
              <p className="risk">
                <strong>Confidence:</strong> {confidence != null ? `${(confidence * 100).toFixed(2)}%` : '—'}
              </p>
              {modelName && (
                <p className="placeholder">
                  <strong>Model:</strong> {modelName}
                </p>
              )}
            </>
          )}
        </section>
      </main>
    </div>
  )
}
