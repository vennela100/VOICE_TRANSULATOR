import React, { useState, useEffect, useRef, useCallback } from 'react'
import { useParams, useLocation, useNavigate } from 'react-router-dom'
import { useWebSocket } from '../hooks/useWebSocket'
import { useAudioRecorder } from '../hooks/useAudioRecorder'
import { WS_EVENTS, generateMessageId } from '../api/ws'
import PushToTalk from '../components/PushToTalk'
import TranscriptBubble, { LANG_LABELS } from '../components/TranscriptBubble'
import './Conversation.css'

const MAX_RECORDING_SECONDS = 28

export default function Conversation() {
  const { roomCode } = useParams()
  const location = useLocation()
  const navigate = useNavigate()

  // Get session info from router state or sessionStorage
  const getSession = () => {
    if (location.state?.roomId) return location.state
    const stored = sessionStorage.getItem('bharatvaani_session')
    if (stored) {
      const parsed = JSON.parse(stored)
      if (parsed.roomCode === roomCode) return parsed
    }
    return null
  }

  const session = getSession()

  useEffect(() => {
    if (!session) {
      navigate('/', { replace: true })
    }
  }, [session, navigate])

  if (!session) return null

  return <ConversationInner session={session} roomCode={roomCode} />
}

function ConversationInner({ session, roomCode }) {
  const { roomId, participantId, participantToken, participantName, language } = session
  const navigate = useNavigate()

  const [messages, setMessages] = useState({})
  const [messageOrder, setMessageOrder] = useState([])
  const [participants, setParticipants] = useState([])
  const [isProcessing, setIsProcessing] = useState(false)
  const [error, setError] = useState(null)
  const [clarification, setClarification] = useState(null)
  const [pendingAudio, setPendingAudio] = useState(null)
  const [outcome, setOutcome] = useState(null)
  const [showOutcome, setShowOutcome] = useState(false)
  const [copied, setCopied] = useState(false)
  
  const messagesEndRef = useRef(null)
  const recordingTimerRef = useRef(null)
  const stopInProgressRef = useRef(false)

  const ws = useWebSocket(roomId, participantId, participantToken)
  const recorder = useAudioRecorder()

  // Scroll to bottom on new messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messageOrder])

  // Update message state helper
  const updateMessage = useCallback((messageId, updates) => {
    setMessages((prev) => ({
      ...prev,
      [messageId]: { ...(prev[messageId] || {}), id: messageId, ...updates },
    }))
    setMessageOrder((prev) => {
      if (!prev.includes(messageId)) return [...prev, messageId]
      return prev
    })
  }, [])

  // Register WS handlers
  useEffect(() => {
    ws.on(WS_EVENTS.AUDIO_STARTED, (data) => {
      updateMessage(data.message_id, {
        senderId: data.sender_id,
        status: 'processing',
        senderName: data.sender_id === participantId ? participantName : 'Partner',
      })
    })

    ws.on('room.state', (data) => {
      setParticipants(data.participants || [])
      for (const item of data.messages || []) {
        updateMessage(item.message_id, {
          senderId: item.sender_id,
          senderName: item.sender_id === participantId ? participantName : 'Partner',
          originalText: item.original_text,
          originalLanguage: item.original_language,
          translatedText: item.translated_text,
          translatedLanguage: item.translated_language,
          status: item.status,
          verification: item.verification,
          confirmed: item.confirmed,
          audioBase64: item.audio_base64,
          audioFormat: item.audio_format || 'wav',
        })
        if (item.status === 'awaiting_confirmation' && item.sender_id === participantId) {
          setClarification({
            messageId: item.message_id,
            prompt: item.verification?.prompt_to_speaker || 'Please confirm the critical detail or re-record.',
          })
        }
      }
    })

    ws.on(WS_EVENTS.TRANSCRIPT_FINAL, (data) => {
      updateMessage(data.message_id, {
        originalText: data.text,
        originalLanguage: data.language,
        senderId: data.sender_id,
        senderName: data.sender_id === participantId ? participantName : 'Partner',
        status: 'translating',
      })
    })

    ws.on(WS_EVENTS.TRANSLATION_COMPLETED, (data) => {
      updateMessage(data.message_id, {
        translatedText: data.text,
        translatedLanguage: data.target_language,
        verification: data.verification,
        status: 'translated',
      })
    })

    ws.on(WS_EVENTS.AUDIO_READY, (data) => {
      updateMessage(data.message_id, {
        audioBase64: data.audio_base64,
        audioFormat: data.audio_format,
      })
    })

    ws.on(WS_EVENTS.MESSAGE_DELIVERED, (data) => {
      updateMessage(data.message_id, { status: 'delivered', audioError: data.audio_error })
      if (data.sender_id === participantId) {
        setIsProcessing(false)
      }
    })

    ws.on(WS_EVENTS.VERIFICATION_REQUIRED, (data) => {
      setClarification({ messageId: data.message_id, prompt: data.prompt_text })
      updateMessage(data.message_id, { status: 'awaiting_confirmation', verification: data.verification })
      setIsProcessing(false)
    })

    ws.on('verification.pending', (data) => {
      updateMessage(data.message_id, { status: 'awaiting_confirmation', waitingForSpeaker: true })
    })

    ws.on(WS_EVENTS.VERIFICATION_CONFIRMED, (data) => {
      setClarification(null)
      updateMessage(data.message_id, { confirmed: true })
    })

    ws.on(WS_EVENTS.VERIFICATION_REJECTED, (data) => {
      setClarification(null)
      updateMessage(data.message_id, { status: 'rejected' })
    })

    ws.on(WS_EVENTS.MESSAGE_FAILED, (data) => {
      updateMessage(data.message_id, { status: 'error', error: data.error })
      setError(data.error)
      setIsProcessing(false)
    })

    ws.on(WS_EVENTS.ERROR, (data) => {
      if (data.message_id) {
        updateMessage(data.message_id, { status: 'error', error: data.error })
      }
      setError(data.error)
      setIsProcessing(false)
      setTimeout(() => setError(null), 5000)
    })

    ws.on(WS_EVENTS.PARTICIPANT_JOINED, (data) => {
      setParticipants((prev) => [
        ...prev.filter((p) => p.id !== data.participant_id),
        { id: data.participant_id, name: data.name, language: data.language },
      ])
    })

    ws.on(WS_EVENTS.PARTICIPANT_LEFT, (data) => {
      setParticipants((prev) => prev.filter((p) => p.id !== data.participant_id))
    })

    ws.on('session.deleted', () => {
      sessionStorage.removeItem('bharatvaani_session')
      ws.disconnect()
      navigate('/')
    })

    ws.connect()
    return () => ws.disconnect()
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  // Handle push-to-talk
  const handleStartRecording = useCallback(async () => {
    setError(null)
    await recorder.startRecording()
  }, [recorder.startRecording])

  const handleStopRecording = useCallback(async () => {
    if (stopInProgressRef.current) return
    stopInProgressRef.current = true
    if (recordingTimerRef.current) {
      clearTimeout(recordingTimerRef.current)
      recordingTimerRef.current = null
    }
    try {
      const result = await recorder.stopRecording()
      if (!result || !result.base64) {
        setError('No audio recorded. Please speak clearly into your mic.')
        return
      }

      setIsProcessing(true)
      const messageId = generateMessageId()
      setPendingAudio({ messageId, base64: result.base64 })

      ws.send({
        type: WS_EVENTS.AUDIO_DATA,
        message_id: messageId,
        audio_base64: result.base64,
      })
    } finally {
      stopInProgressRef.current = false
    }
  }, [recorder.stopRecording, ws.send])

  useEffect(() => {
    if (!recorder.isRecording) return undefined
    recordingTimerRef.current = window.setTimeout(() => {
      recordingTimerRef.current = null
      handleStopRecording()
    }, MAX_RECORDING_SECONDS * 1000)

    return () => {
      if (recordingTimerRef.current) {
        clearTimeout(recordingTimerRef.current)
        recordingTimerRef.current = null
      }
    }
  }, [recorder.isRecording, handleStopRecording])

  const respondToVerification = (confirmed) => {
    if (!clarification) return
    ws.send({
      type: confirmed ? WS_EVENTS.VERIFICATION_CONFIRMED : WS_EVENTS.VERIFICATION_REJECTED,
      message_id: clarification.messageId,
    })
    if (!confirmed) setClarification(null)
    else setIsProcessing(true)
  }

  const retryMessage = () => {
    if (!pendingAudio) return
    setError(null)
    setIsProcessing(true)
    ws.send({
      type: WS_EVENTS.AUDIO_DATA,
      message_id: pendingAudio.messageId,
      audio_base64: pendingAudio.base64,
    })
  }

  const loadOutcome = async () => {
    try {
      const response = await fetch(`/api/rooms/${roomCode}/outcome`, {
        headers: { Authorization: `Bearer ${participantToken}` },
      })
      if (!response.ok) throw new Error('Could not load outcome summary')
      setOutcome(await response.json())
      setShowOutcome(true)
    } catch (err) {
      setError(err.message)
    }
  }

  const saveOutcome = async () => {
    const response = await fetch(`/api/rooms/${roomCode}/outcome`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${participantToken}` },
      body: JSON.stringify(outcome),
    })
    if (response.ok) setShowOutcome(false)
    else setError('Could not save outcome summary')
  }

  const copyRoomCode = () => {
    navigator.clipboard?.writeText(roomCode)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  const handleLeave = async () => {
    if (!window.confirm('End conversation and delete all session messages?')) return
    await fetch(`/api/rooms/${roomCode}`, {
      method: 'DELETE',
      headers: { Authorization: `Bearer ${participantToken}` },
    })
    ws.disconnect()
    sessionStorage.removeItem('bharatvaani_session')
    navigate('/')
  }

  const otherParticipant = participants.find((p) => p.id !== participantId)
  const otherLang = otherParticipant ? otherParticipant.language : (language === 'hi' ? 'en' : 'hi')

  return (
    <div className="conversation-screen">
      {/* Top Application Bar */}
      <header className="conv-nav-bar">
        <div className="nav-col-left">
          <div className="brand-badge" onClick={() => navigate('/')} title="Back to home">
            <span className="brand-flag">🇮🇳</span>
            <span className="brand-text">BharatVaani</span>
          </div>

          <div className="room-code-chip" onClick={copyRoomCode} title="Click to copy room code">
            <span className="chip-label">Room</span>
            <span className="chip-code">{roomCode}</span>
            <span className="chip-copy-icon">
              {copied ? (
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#10b981" strokeWidth="2.5"><polyline points="20 6 9 17 4 12"/></svg>
              ) : (
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>
              )}
            </span>
          </div>
        </div>

        {/* Center: Language Pair Exchange Pill */}
        <div className="nav-col-center">
          <div className="lang-exchange-pill">
            <span className="exchange-tag own" title="Your language">
              {LANG_LABELS[language]}
            </span>
            <span className="exchange-arrow" aria-hidden="true">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2"><path d="M7 16l-4-4m0 0l4-4m-4 4h18m-4 4l4-4m0 0l-4-4"/></svg>
            </span>
            <span className="exchange-tag partner" title="Partner's language">
              {LANG_LABELS[otherLang]}
            </span>
          </div>
        </div>

        {/* Right: Connection Status & Exit */}
        <div className="nav-col-right">
          <div className={`status-pill ${ws.isConnected ? 'is-connected' : 'is-disconnected'}`}>
            <span className="status-jewel" />
            <span className="status-text">
              {ws.isConnected ? (participants.length > 1 ? 'Live · 2 in Room' : 'Live · Waiting') : 'Reconnecting...'}
            </span>
          </div>

          <button className="nav-icon-btn exit-btn" onClick={handleLeave} title="End conversation and delete room">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><polyline points="16 17 21 12 16 7"/><line x1="21" y1="12" x2="9" y2="12"/></svg>
          </button>
        </div>
      </header>

      {/* Partner Joined Announcement Strip */}
      {participants.length > 0 && (
        <div className="presence-banner">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>
          <span>
            Connected Participants: {participants.map((p) => `${p.name} (${LANG_LABELS[p.language]})`).join(' · ')}
          </span>
        </div>
      )}

      {/* Error notification banner */}
      {(ws.connectionError || error || recorder.error) && (
        <div className="conv-alert-strip">
          <span className="alert-strip-text">{ws.connectionError || error || recorder.error}</span>
          {pendingAudio && (
            <button className="alert-retry-btn" onClick={retryMessage}>
              Retry Send
            </button>
          )}
        </div>
      )}

      {/* Meaning Protection Confirmation Modal / Card */}
      {clarification && (
        <aside className="confirmation-modal" role="dialog" aria-labelledby="confirm-heading">
          <div className="modal-shield-header">
            <span className="shield-icon">🛡️</span>
            <div>
              <h3 id="confirm-heading" className="modal-heading">Meaning Protection Verification</h3>
              <p className="modal-subheading">A critical number, quantity, or financial amount was detected.</p>
            </div>
          </div>

          <div className="modal-prompt-content">
            <p className="modal-prompt-text">{clarification.prompt}</p>
          </div>

          <div className="modal-actions">
            <button className="modal-btn confirm" onClick={() => respondToVerification(true)}>
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><polyline points="20 6 9 17 4 12"/></svg>
              Confirm & Deliver Speech
            </button>
            <button className="modal-btn discard" onClick={() => respondToVerification(false)}>
              Discard & Re-record
            </button>
          </div>
        </aside>
      )}

      {/* Messages Scroll View */}
      <main className="messages-scroll-area">
        {messageOrder.length === 0 ? (
          <div className="conversation-empty-state">
            <div className="empty-state-glow">
              <span className="empty-state-icon">🎙️</span>
            </div>
            <h2 className="empty-state-title">Ready for Voice Conversation</h2>
            <p className="empty-state-desc">
              Share your room code <strong className="empty-room-tag">{roomCode}</strong> with your partner.
            </p>
            <div className="empty-instructions-card">
              <div className="instruction-step">
                <span className="step-num">1</span>
                <span>Tap the microphone button below to record in <strong>{LANG_LABELS[language]}</strong>.</span>
              </div>
              <div className="instruction-step">
                <span className="step-num">2</span>
                <span>Gnani AI transcribes your voice, verifies critical numbers, and Gemini translates.</span>
              </div>
              <div className="instruction-step">
                <span className="step-num">3</span>
                <span>Your partner immediately hears native speech in <strong>{LANG_LABELS[otherLang]}</strong>.</span>
              </div>
            </div>
          </div>
        ) : (
          <div className="bubbles-wrapper">
            {messageOrder.map((msgId) => {
              const msg = messages[msgId]
              if (!msg) return null
              return (
                <TranscriptBubble
                  key={msgId}
                  message={msg}
                  isOwn={msg.senderId === participantId}
                />
              )
            })}
          </div>
        )}
        <div ref={messagesEndRef} />
      </main>

      {/* Floating Bottom Control Dock */}
      <footer className="conv-control-dock">
        <PushToTalk
          isRecording={recorder.isRecording}
          onStart={handleStartRecording}
          onStop={handleStopRecording}
          disabled={isProcessing || !ws.isConnected}
        />

        <div className="dock-utility-row">
          <button className="utility-link-btn" onClick={loadOutcome}>
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/><polyline points="10 9 9 9 8 9"/></svg>
            Summary & Outcome Card
          </button>
        </div>
      </footer>

      {/* Outcome Modal */}
      {showOutcome && outcome && (
        <div className="outcome-modal-backdrop" onClick={() => setShowOutcome(false)}>
          <div className="outcome-modal-sheet" onClick={(e) => e.stopPropagation()}>
            <div className="sheet-header">
              <h3>Conversation Outcome Summary</h3>
              <button className="sheet-close-btn" onClick={() => setShowOutcome(false)}>✕</button>
            </div>
            
            <p className="sheet-status">{outcome.summary_status}</p>

            <div className="sheet-body">
              {(outcome.items || []).map((item, index) => (
                <div className="outcome-item-row" key={`${item.message_id}-${index}`}>
                  <span className="outcome-item-badge">{item.kind} · {item.status}</span>
                  <input
                    className="outcome-item-input"
                    value={item.value || ''}
                    onChange={(e) => {
                      const val = e.target.value
                      setOutcome((old) => ({
                        ...old,
                        items: old.items.map((entry, i) => i === index ? { ...entry, value: val } : entry),
                      }))
                    }}
                  />
                </div>
              ))}

              {['decisions', 'next_steps'].map((key) => (
                <section key={key} className="outcome-section">
                  <h4 className="outcome-section-title">{key === 'decisions' ? 'Decisions & Agreements' : 'Next Steps'}</h4>
                  {(outcome[key] || []).map((entry, index) => (
                    <div className="outcome-item-row" key={`${key}-${index}`}>
                      <span className="outcome-item-badge">{entry.ai_generated ? 'AI Inferred' : 'Verified'}</span>
                      <input
                        className="outcome-item-input"
                        value={entry.text || ''}
                        onChange={(e) => {
                          const val = e.target.value
                          setOutcome((old) => ({
                            ...old,
                            [key]: old[key].map((item, i) => i === index ? { ...item, text: val } : item),
                          }))
                        }}
                      />
                    </div>
                  ))}
                </section>
              ))}
            </div>

            <div className="sheet-footer">
              <button className="modal-btn confirm" onClick={saveOutcome}>Save Outcome Card</button>
              <button className="modal-btn secondary" onClick={() => setShowOutcome(false)}>Close</button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
