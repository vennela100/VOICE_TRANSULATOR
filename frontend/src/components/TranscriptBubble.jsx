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
  const [playbackState, setPlaybackState] = useState('idle')
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
    <div className={`transcript-bubble ${isOwn ? 'own' : 'other'}`}>
      <div className="bubble-header">
        <span className="sender-name">{isOwn ? 'You' : senderName || 'Partner'}</span>
        <span className="sender-lang">{LANG_LABELS[originalLanguage] || originalLanguage}</span>
        {status === 'processing' && <span className="status-badge processing">Processing...</span>}
        {status === 'translating' && <span className="status-badge processing">Transcript ready - Translating...</span>}
        {status === 'translated' && <span className="status-badge processing">Translation ready - Preparing audio...</span>}
        {status === 'awaiting_confirmation' && <span className="status-badge processing">{isOwn ? 'Needs your confirmation' : 'Waiting for speaker'}</span>}
      </div>

      {originalText && (
        <div className="bubble-original">
          <span className="text-label">Original</span>
          <p>{originalText}</p>
        </div>
      )}

      {translatedText && (
        <div className="bubble-translated">
          <span className="text-label">Translation ({LANG_LABELS[translatedLanguage] || translatedLanguage})</span>
          <p>{translatedText}</p>
        </div>
      )}

      {message.verification?.overall_meaning_verified === false && (
        <p className={`meaning-check-note ${message.verification.status === 'needs_confirmation' ? 'needs-confirmation' : ''}`}>
          {message.verification.status === 'needs_confirmation'
            ? 'A supported critical detail needs confirmation.'
            : 'Supported critical-detail checks passed. The full translation is not verified.'}
        </p>
      )}
      {hasUnreviewedWordMapping && (
        <p className="meaning-check-note needs-confirmation">
          A spoken number was interpreted from words. Check it with the speaker before acting on it.
        </p>
      )}

      {audioBase64 && (
        <button className="play-audio-btn" onClick={playAudio} title="Play translation audio" aria-label="Play translated speech">
          {playbackState === 'playing' ? 'Playing audio...' : '🔊 Play translated audio'}
        </button>
      )}
      {playbackState === 'error' && <span className="status-badge error" role="alert">Audio could not play. Check your device volume and try again.</span>}

      {status === 'delivered' && (
        <span className="status-badge delivered">✓ Delivered</span>
      )}
      {status === 'error' && (
        <span className="status-badge error">⚠ Error</span>
      )}
      {status === 'rejected' && <span className="status-badge error">Not sent. Please re-record.</span>}
      {message.confirmed && <span className="status-badge delivered">Critical details confirmed</span>}
      {message.audioError && <span className="status-badge error">Subtitles only. Audio unavailable.</span>}
    </div>
  )
}
