import { useState, useRef, useCallback } from 'react'

const TARGET_SAMPLE_RATE = 16000

function encodeMonoPcmWav(audioBuffer) {
  const samples = audioBuffer.getChannelData(0)
  const bytes = new ArrayBuffer(44 + samples.length * 2)
  const view = new DataView(bytes)
  const writeText = (offset, value) => {
    for (let i = 0; i < value.length; i += 1) view.setUint8(offset + i, value.charCodeAt(i))
  }

  writeText(0, 'RIFF')
  view.setUint32(4, 36 + samples.length * 2, true)
  writeText(8, 'WAVE')
  writeText(12, 'fmt ')
  view.setUint32(16, 16, true)
  view.setUint16(20, 1, true)
  view.setUint16(22, 1, true)
  view.setUint32(24, audioBuffer.sampleRate, true)
  view.setUint32(28, audioBuffer.sampleRate * 2, true)
  view.setUint16(32, 2, true)
  view.setUint16(34, 16, true)
  writeText(36, 'data')
  view.setUint32(40, samples.length * 2, true)

  for (let i = 0; i < samples.length; i += 1) {
    const sample = Math.max(-1, Math.min(1, samples[i]))
    view.setInt16(44 + i * 2, sample < 0 ? sample * 0x8000 : sample * 0x7fff, true)
  }
  return new Blob([bytes], { type: 'audio/wav' })
}

async function convertRecordingToWav(blob) {
  const AudioContextClass = window.AudioContext || window.webkitAudioContext
  const OfflineAudioContextClass = window.OfflineAudioContext || window.webkitOfflineAudioContext
  if (!AudioContextClass || !OfflineAudioContextClass) {
    throw new Error('This browser cannot convert microphone audio to the WAV format required by speech recognition.')
  }

  const context = new AudioContextClass()
  try {
    const decoded = await context.decodeAudioData(await blob.arrayBuffer())
    const frameCount = Math.ceil(decoded.duration * TARGET_SAMPLE_RATE)
    const offline = new OfflineAudioContextClass(1, frameCount, TARGET_SAMPLE_RATE)
    const source = offline.createBufferSource()
    source.buffer = decoded
    source.connect(offline.destination)
    source.start(0)
    return encodeMonoPcmWav(await offline.startRendering())
  } finally {
    await context.close()
  }
}

export function useAudioRecorder() {
  const [isRecording, setIsRecording] = useState(false)
  const [error, setError] = useState(null)
  const mediaRecorderRef = useRef(null)
  const chunksRef = useRef([])

  const startRecording = useCallback(async () => {
    try {
      setError(null)
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          channelCount: { ideal: 1 },
          echoCancellation: true,
          noiseSuppression: true,
        },
      })

      const supportedType = [
        'audio/webm;codecs=opus',
        'audio/ogg;codecs=opus',
        'audio/mp4',
      ].find((type) => MediaRecorder.isTypeSupported(type))
      const mediaRecorder = supportedType
        ? new MediaRecorder(stream, { mimeType: supportedType })
        : new MediaRecorder(stream)
      chunksRef.current = []

      mediaRecorder.ondataavailable = (e) => {
        if (e.data.size > 0) {
          chunksRef.current.push(e.data)
        }
      }

      mediaRecorderRef.current = mediaRecorder
      mediaRecorder.start()
      setIsRecording(true)
    } catch (err) {
      if (err.name === 'NotAllowedError') {
        setError('Microphone access denied. Please allow microphone access in your browser settings.')
      } else {
        setError('Could not access microphone: ' + err.message)
      }
      console.error('Mic error:', err)
    }
  }, [])

  const stopRecording = useCallback(() => {
    return new Promise((resolve) => {
      const mediaRecorder = mediaRecorderRef.current
      if (!mediaRecorder || mediaRecorder.state === 'inactive') {
        resolve(null)
        return
      }

      mediaRecorder.onstop = async () => {
        const recordedBlob = new Blob(chunksRef.current, { type: mediaRecorder.mimeType })
        chunksRef.current = []

        // Stop all tracks to release mic
        mediaRecorder.stream.getTracks().forEach((t) => t.stop())

        try {
          const blob = await convertRecordingToWav(recordedBlob)
          const reader = new FileReader()
          reader.onerror = () => {
            setError('Could not prepare the recording. Please try again.')
            resolve(null)
          }
          reader.onloadend = () => {
            const base64 = String(reader.result || '').split(',')[1]
            resolve(base64 ? { blob, base64 } : null)
          }
          reader.readAsDataURL(blob)
        } catch (err) {
          setError(`Could not prepare the recording: ${err.message}`)
          resolve(null)
        } finally {
          setIsRecording(false)
        }
      }

      mediaRecorder.stop()
    })
  }, [])

  return { isRecording, startRecording, stopRecording, error }
}
