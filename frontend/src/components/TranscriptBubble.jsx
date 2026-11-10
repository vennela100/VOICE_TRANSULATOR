import React, { useEffect, useRef, useState } from 'react'
import './TranscriptBubble.css'

export const LANG_LABELS = {
  hi: 'Hindi',
  en: 'English',
  te: 'Telugu',
  ta: 'Tamil',
  kn: 'Kannada',
  ml: 'Malayalam',
  mr: 'Marathi',
  bn: 'Bengali',
  gu: 'Gujarati',
  pa: 'Punjabi',
  or: 'Odia',
  ur: 'Urdu',
}

export default function TranscriptBubble({ message, isOwn }) {
  const audioRef = useRef(null)
  const [playbackState, setPlaybackState] = useState('idle') // 'idle' | 'playing' | 'error'

  const {
    originalText,
    originalLanguage,
    translatedText,
    translatedLanguage,
    audioBase64,
    audioFormat,
    status,
    senderName,
  } = message

  const criticalEntities = [
    ...Object.values(message.verification?.entities_original || {}).flat(),
    ...Object.values(message.verification?.entities_translated || {}).flat(),
  ]
  const hasUnreviewedWordMapping = criticalEntities.some((entity) =>
    ['inferred', 'provisional', 'ambiguous'].includes(entity?.mapping_status),
  )

  useEffect(() => () => {
    if (audioRef.current) {
      audioRef.current.pause()
      audioRef.current.src = ''
      audioRef.current = null
    }
  }, [])

  const playAudio = async () => {
    if (!audioBase64) return
    const format = audioFormat || 'wav'
    const audio = new Audio(`data:audio/${format};base64,${audioBase64}`)
    if (audioRef.current) {
      audioRef.current.onended = null
      audioRef.current.onerror = null
      audioRef.current.pause()
    }
    audioRef.current = audio
    setPlaybackState('playing')
    audio.onended = () => setPlaybackState('idle')
    audio.onerror = () => setPlaybackState('error')
    try {
      await audio.play()
    } catch {
      setPlaybackState('error')
    }
  }

  return (
    <article className={`bubble-container ${isOwn ? 'is-own' : 'is-partner'}`}>
      <div className="bubble-card">
        {/* Header row: Sender name, language & status badge */}
        <div className="bubble-top-meta">
          <div className="speaker-info">
            <span className="speaker-avatar">
              {isOwn ? '👤' : '👥'}
            </span>
            <span className="speaker-name">{isOwn ? 'You' : senderName || 'Partner'}</span>
            <span className="speaker-lang-badge">
              {LANG_LABELS[originalLanguage] || originalLanguage}
            </span>
          </div>

          <div className="bubble-status-wrapper">
            {status === 'processing' && (
              <span className="bubble-badge processing">
                <span className="mini-spin" /> Transcribing...
              </span>
            )}
            {status === 'translating' && (
              <span className="bubble-badge processing">
                <span className="mini-spin" /> Translating...
              </span>
            )}
            {status === 'translated' && (
              <span className="bubble-badge processing">
                <span className="mini-spin" /> Synthesizing Voice...
              </span>
            )}
            {status === 'awaiting_confirmation' && (
              <span className="bubble-badge warning">
                ⚠️ {isOwn ? 'Confirmation Needed' : 'Checking with Speaker'}
              </span>
            )}
            {status === 'delivered' && (
              <span className="bubble-badge success">
                ✓ Delivered
              </span>
            )}
            {status === 'error' && (
              <span className="bubble-badge danger">
                ⚠ Error
              </span>
            )}
            {status === 'rejected' && (
              <span className="bubble-badge danger">
                Discarded
              </span>
            )}
          </div>
        </div>

        {/* Original Speech Segment */}
        {originalText && (
          <div className="speech-segment original-segment">
            <div className="segment-label-row">
              <span className="segment-label">Spoken ({LANG_LABELS[originalLanguage] || originalLanguage})</span>
            </div>
            <p className="speech-text original-text">{originalText}</p>
          </div>
        )}

        {/* Translated Speech Segment */}
        {translatedText && (
          <div className="speech-segment translated-segment">
            <div className="segment-label-row">
              <span className="segment-label">Translation ({LANG_LABELS[translatedLanguage] || translatedLanguage})</span>
            </div>
            <p className="speech-text translated-text">{translatedText}</p>
          </div>
        )}

        {/* Meaning Protection Alert / Badge */}
        {message.verification && (
          <div className="meaning-protection-box">
            {message.verification.status === 'needs_confirmation' ? (
              <div className="meaning-pill warning">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
                <span>Critical detail (number/date) requires speaker confirmation</span>
              </div>
            ) : hasUnreviewedWordMapping ? (
              <div className="meaning-pill info">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/><circle cx="12" cy="12" r="1"/></svg>
                <span>Spoken number interpreted from words · Preserved</span>
              </div>
            ) : (
              <div className="meaning-pill verified">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/><polyline points="9 12 11 14 15 10"/></svg>
                <span>Meaning Protection Active</span>
              </div>
            )}
          </div>
        )}

        {/* Audio Action Footer */}
        {audioBase64 && (
          <div className="bubble-action-footer">
            <button
              type="button"
              className={`voice-playback-btn ${playbackState === 'playing' ? 'is-playing' : ''}`}
              onClick={playAudio}
              aria-label="Play translated voice"
            >
              {playbackState === 'playing' ? (
                <>
                  <div className="mini-audio-bars" aria-hidden="true">
                    <span className="mini-bar b1" />
                    <span className="mini-bar b2" />
                    <span className="mini-bar b3" />
                  </div>
                  <span>Playing Voice...</span>
                </>
              ) : (
                <>
                  <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2">
                    <polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"/>
                    <path d="M19.07 4.93a10 10 0 0 1 0 14.14M15.54 8.46a5 5 0 0 1 0 7.07"/>
                  </svg>
                  <span>Play Translation Audio</span>
                </>
              )}
            </button>
          </div>
        )}

        {playbackState === 'error' && (
          <p className="playback-error-hint">⚠️ Could not play audio. Check device volume.</p>
        )}

        {message.audioError && (
          <p className="playback-error-hint">Subtitles only · Voice audio was unavailable.</p>
        )}
      </div>
    </article>
  )
}
