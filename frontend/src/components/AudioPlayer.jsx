import React, { useRef } from 'react'

export default function AudioPlayer({ audioBase64, format = 'wav' }) {
  const audioRef = useRef(null)

  if (!audioBase64) return null

  const src = `data:audio/${format};base64,${audioBase64}`

  return (
    <div className="audio-player">
      <audio ref={audioRef} src={src} controls preload="auto" style={{ width: '100%', maxWidth: '300px' }} />
    </div>
  )
}
