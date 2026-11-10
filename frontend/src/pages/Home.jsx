import React, { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import LanguageSelector from '../components/LanguageSelector'
import './Home.css'

export default function Home() {
  const navigate = useNavigate()
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

  const handleCreate = async () => {
    if (!name.trim()) {
      setError('Please enter your name')
      return
    }
    setError('')
    setLoading(true)
    try {
      const res = await fetch('/api/rooms', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ participant_name: name.trim(), language }),
      })
      if (!res.ok) {
        const data = await res.json()
        throw new Error(data.detail || 'Failed to create room')
      }
      const data = await res.json()
      // Save session info
      sessionStorage.setItem('bharatvaani_session', JSON.stringify({
        roomId: data.room_id,
        roomCode: data.room_code,
        participantId: data.participant_id,
        participantToken: data.participant_token,
        participantName: name.trim(),
        language,
      }))
      navigate(`/room/${data.room_code}`, {
        state: {
          roomId: data.room_id,
          roomCode: data.room_code,
          participantId: data.participant_id,
          participantToken: data.participant_token,
          participantName: name.trim(),
          language,
        },
      })
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const handleJoin = async () => {
    if (!name.trim()) {
      setError('Please enter your name')
      return
    }
    if (!joinCode.trim() || joinCode.trim().length !== 6) {
      setError('Please enter a valid 6-character room code')
      return
    }
    setError('')
    setLoading(true)
    try {
      const code = joinCode.trim().toUpperCase()
      const res = await fetch(`/api/rooms/${code}/join`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ participant_name: name.trim(), language }),
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
        participantName: name.trim(),
        language,
      }))
      navigate(`/room/${data.room_code}`, {
        state: {
          roomId: data.room_id,
          roomCode: data.room_code,
          participantId: data.participant_id,
          participantToken: data.participant_token,
          participantName: name.trim(),
          language,
        },
      })
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="home-page">
      <div className="home-card">
        <div className="home-header">
          <h1 className="app-title">🇮🇳 BharatVaani Live</h1>
          <p className="app-tagline">Your Language. Your Voice. One Conversation.</p>
        </div>

        {error && <div className="error-banner">{error}</div>}

        <div className="form-group">
          <label htmlFor="name">Your Name</label>
          <input
            id="name"
            type="text"
            placeholder="Enter your name"
            value={name}
            onChange={(e) => setName(e.target.value)}
            maxLength={30}
          />
        </div>

        <LanguageSelector value={language} onChange={setLanguage} />

        {serviceStatus && (
          <p className="mode-notice" role="status">
            Configured providers: {[
              `speech recognition — ${serviceStatus.stt_provider === 'mock' ? 'Simulation' : 'Gnani Prisma'}`,
              `translation — ${serviceStatus.translation_provider === 'mock' ? 'Simulation' : 'Gemini'}`,
              `speech output — ${serviceStatus.tts_provider === 'mock' ? 'Simulation' : serviceStatus.tts_provider === 'gnani' ? 'Gnani Timbre' : 'Gemini'}`,
            ].join(' · ')}
            {serviceStatus.tts_fallback_provider && ` · speech output fallback — ${serviceStatus.tts_fallback_provider === 'gemini' ? 'Gemini' : serviceStatus.tts_fallback_provider}`}
            {' · Configuration only; not a live provider health check.'}
          </p>
        )}

        <button
          className="btn btn-primary btn-full"
          onClick={handleCreate}
          disabled={loading}
        >
          {loading ? 'Creating...' : 'Create New Room'}
        </button>

        <div className="divider">
          <span>or join an existing room</span>
        </div>

        <div className="join-section">
          <input
            type="text"
            placeholder="Enter 6-character room code"
            value={joinCode}
            onChange={(e) => setJoinCode(e.target.value.toUpperCase())}
            maxLength={6}
            className="code-input"
          />
          <button
            className="btn btn-secondary btn-full"
            onClick={handleJoin}
            disabled={loading}
          >
            {loading ? 'Joining...' : 'Join Room'}
          </button>
        </div>

        <p className="privacy-notice">
          Input audio is sent to the selected speech provider and not retained. Transcripts, verification details, and generated speech audio are temporarily stored for room resync; rooms expire automatically. Provider services process the audio or text needed for their task. Use “End session and delete” to remove the room data now.
        </p>
      </div>
    </div>
  )
}
