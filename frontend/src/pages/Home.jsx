import React, { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import LanguageSelector, { LANGUAGES } from '../components/LanguageSelector'
import './Home.css'

export default function Home() {
  const navigate = useNavigate()
  const [tab, setTab] = useState('create') // 'create' | 'join'
  const [name, setName] = useState('')
  const [language, setLanguage] = useState('hi')
  const [joinCode, setJoinCode] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const [serviceStatus, setServiceStatus] = useState(null)

  useEffect(() => {
    fetch('/api/status')
      .then((response) => response.ok ? response.json() : null)
      .then((status) => status && setServiceStatus(status))
      .catch(() => {})
  }, [])

  const handleCreate = async (e) => {
    e?.preventDefault()
    const participantName = name.trim() || 'Speaker 1'
    setError('')
    setLoading(true)
    try {
      const res = await fetch('/api/rooms', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ participant_name: participantName, language }),
      })
      if (!res.ok) {
        const data = await res.json()
        throw new Error(data.detail || 'Failed to create room')
      }
      const data = await res.json()
      sessionStorage.setItem('bharatvaani_session', JSON.stringify({
        roomId: data.room_id,
        roomCode: data.room_code,
        participantId: data.participant_id,
        participantToken: data.participant_token,
        participantName: participantName,
        language,
      }))
      navigate(`/room/${data.room_code}`, {
        state: {
          roomId: data.room_id,
          roomCode: data.room_code,
          participantId: data.participant_id,
          participantToken: data.participant_token,
          participantName: participantName,
          language,
        },
      })
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const handleJoin = async (e) => {
    e?.preventDefault()
    const participantName = name.trim() || 'Speaker 2'
    if (!joinCode.trim() || joinCode.trim().length !== 6) {
      setError('Please enter the 6-character room code')
      return
    }
    setError('')
    setLoading(true)
    try {
      const code = joinCode.trim().toUpperCase()
      const res = await fetch(`/api/rooms/${code}/join`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ participant_name: participantName, language }),
      })
      if (!res.ok) {
        const data = await res.json()
        throw new Error(data.detail || 'Failed to join room')
      }
      const data = await res.json()
      sessionStorage.setItem('bharatvaani_session', JSON.stringify({
        roomId: data.room_id,
        roomCode: data.room_code,
        participantId: data.participant_id,
        participantToken: data.participant_token,
        participantName: participantName,
        language,
      }))
      navigate(`/room/${data.room_code}`, {
        state: {
          roomId: data.room_id,
          roomCode: data.room_code,
          participantId: data.participant_id,
          participantToken: data.participant_token,
          participantName: participantName,
          language,
        },
      })
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const selectedLangObj = LANGUAGES.find((l) => l.code === language) || LANGUAGES[0]

  return (
    <main className="home-layout">
      {/* Background ambient accents */}
      <div className="ambient-blob blob-1" aria-hidden="true" />
      <div className="ambient-blob blob-2" aria-hidden="true" />
      
      <div className="home-container">
        {/* Top Header & Brand */}
        <header className="hero-header">
          <div className="badge-pill">
            <span className="badge-pulse" />
            <span className="badge-text">Gnani AI Voice Architecture · Live Cross-Language</span>
          </div>

          <h1 className="hero-title">
            <span className="flag-icon">🇮🇳</span> BharatVaani <span className="gradient-text">Live</span>
          </h1>
          <p className="hero-subtitle">
            Speak naturally in your native tongue. Hear your conversation partner in theirs.
          </p>

          <div className="hero-feature-tags">
            <span className="feature-tag">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>
              Meaning Protection
            </span>
            <span className="feature-tag">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"/><path d="M19 10v2a7 7 0 0 1-14 0v-2"/><line x1="12" y1="19" x2="12" y2="23"/><line x1="8" y1="23" x2="16" y2="23"/></svg>
              Gnani Prisma & Timbre
            </span>
            <span className="feature-tag">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>
              Low-Latency WebSocket
            </span>
          </div>
        </header>

        {/* Main Interactive Card */}
        <div className="main-card">
          {/* Tab navigation */}
          <div className="tab-bar" role="tablist">
            <button
              type="button"
              role="tab"
              aria-selected={tab === 'create'}
              className={`tab-btn ${tab === 'create' ? 'active' : ''}`}
              onClick={() => { setTab('create'); setError('') }}
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="16"/><line x1="8" y1="12" x2="16" y2="12"/>
              </svg>
              Create New Room
            </button>
            <button
              type="button"
              role="tab"
              aria-selected={tab === 'join'}
              className={`tab-btn ${tab === 'join' ? 'active' : ''}`}
              onClick={() => { setTab('join'); setError('') }}
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/>
                <path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/>
              </svg>
              Join with Code
            </button>
          </div>

          {error && (
            <div className="alert-box error" role="alert">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/>
              </svg>
              <span>{error}</span>
            </div>
          )}

          <form onSubmit={tab === 'create' ? handleCreate : handleJoin} className="form-content">
            {/* Participant Name Input */}
            <div className="input-group">
              <label htmlFor="name-input" className="input-label">
                Your Name
              </label>
              <div className="input-field-wrapper">
                <span className="input-icon">
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/>
                  </svg>
                </span>
                <input
                  id="name-input"
                  type="text"
                  placeholder="e.g. Rahul Sharma or Vennela"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  maxLength={30}
                  className="text-input"
                  autoComplete="name"
                />
              </div>
            </div>

            {/* Room Code Input (Join Tab Only) */}
            {tab === 'join' && (
              <div className="input-group">
                <label htmlFor="code-input" className="input-label">
                  6-Character Room Code
                </label>
                <div className="input-field-wrapper">
                  <span className="input-icon">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <line x1="4" y1="9" x2="20" y2="9"/><line x1="4" y1="15" x2="20" y2="15"/><line x1="10" y1="3" x2="8" y2="21"/><line x1="16" y1="3" x2="14" y2="21"/>
                    </svg>
                  </span>
                  <input
                    id="code-input"
                    type="text"
                    placeholder="e.g. AB12CD"
                    value={joinCode}
                    onChange={(e) => setJoinCode(e.target.value.toUpperCase())}
                    maxLength={6}
                    className="text-input code-input"
                    autoCapitalize="characters"
                    autoComplete="off"
                    spellCheck="false"
                  />
                </div>
              </div>
            )}

            {/* Language Selection Grid */}
            <LanguageSelector value={language} onChange={setLanguage} />

            {/* Action Submit Button */}
            <button
              type="submit"
              className="primary-action-btn"
              disabled={loading}
            >
              {loading ? (
                <span className="btn-loading-content">
                  <span className="spinner-icon" />
                  {tab === 'create' ? 'Initializing Secure Room...' : 'Connecting to Room...'}
                </span>
              ) : (
                <span className="btn-content">
                  {tab === 'create' ? 'Start Conversation Room' : 'Join Conversation'}
                  <span className="action-lang-pill">
                    Speaking {selectedLangObj.labelEn} ({selectedLangObj.label})
                  </span>
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                    <line x1="5" y1="12" x2="19" y2="12"/><polyline points="12 5 19 12 12 19"/>
                  </svg>
                </span>
              )}
            </button>
          </form>

          {/* Engine Status Bar */}
          {serviceStatus && (
            <div className="engine-status-footer">
              <div className="status-indicator-dot" />
              <div className="engine-meta">
                <span className="engine-label">Engine Config:</span>
                <span className="engine-tag">
                  STT: {serviceStatus.stt_provider === 'mock' ? 'Sim' : 'Gnani Prisma v2'}
                </span>
                <span className="engine-separator">·</span>
                <span className="engine-tag">
                  Translate: {serviceStatus.translation_provider === 'mock' ? 'Sim' : 'Gemini AI'}
                </span>
                <span className="engine-separator">·</span>
                <span className="engine-tag">
                  TTS: {serviceStatus.tts_provider === 'gnani' ? 'Gnani Timbre v2.5' : 'Gemini'}
                </span>
              </div>
            </div>
          )}
        </div>

        {/* Security & Privacy Notice */}
        <footer className="home-footer">
          <div className="privacy-pill">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <rect x="3" y="11" width="18" height="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/>
            </svg>
            <span>Real-time voice processing is ephemeral. Audio streams and transcripts are discarded when the session ends.</span>
          </div>
        </footer>
      </div>
    </main>
  )
}
