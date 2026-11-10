import { Routes, Route } from 'react-router-dom'
import Home from './pages/Home'
import Conversation from './pages/Conversation'

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Home />} />
      <Route path="/room/:roomCode" element={<Conversation />} />
    </Routes>
  )
}
