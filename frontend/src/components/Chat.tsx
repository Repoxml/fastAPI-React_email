import { useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'


type Message = {
  id: number
  sender: string
  title: string
  context: string
  date: string
  recipients: string[]
}

function Chat() {
    const [selectedRecipients, setSelectedRecipients] = useState<string[]>([])
    const [users, setUsers] = useState<string[]>([])
    const navigate = useNavigate()
    const [messages, setMessages] = useState<Message[]>([])
    const [input, setInput] = useState('')
    const wsRef = useRef<WebSocket | null>(null)
    const [me, setMe] = useState<string>('')

  useEffect(() => {
    const token = localStorage.getItem('token')
    if (!token) {
      navigate('/login')
      fetchMessages()
      return
    }

    fetch('http://localhost:8000/me', {
        headers: { Authorization: `Bearer ${token}` }
    })
        .then(res => res.json())
        .then(data => setMe(data.username))
        .catch(err => console.error('Failed to fetch me:', err))

        fetch('http://localhost:8000/messages', {
          headers: { Authorization: `Bearer ${token}` }
      })
          .then(res => res.json())
          .then(data => setMessages(data))
          .catch(err => console.error('Failed to fetch messages:', err))

    fetch('http://localhost:8000/users', {
        headers: { Authorization: `Bearer ${token}` }
    })
        .then(res => res.json())
        .then(data => setUsers(data))
        .catch(err => console.error('Failed to fetch users:', err))

    const ws = new WebSocket(`ws://localhost:8000/ws?token=${token}`)
    wsRef.current = ws

    ws.onopen = () => console.log('connected to Chat')

    ws.onmessage = (event) => {
      const data: Message = JSON.parse(event.data)
      setMessages((prev) => [...prev, data])
    }

    ws.onerror = (error) => console.error('Websocket error:', error)
    ws.onclose = () => console.log('Websocket conn closed')

    return () => ws.close()
  }, [navigate])

  const fetchMessages = async () => {
    const token = localStorage.getItem('token')
    try {
        const res = await fetch('http://localhost:8000/messages', {
            headers: { Authorization: `Bearer ${token}` }
        })
        const data = await res.json()
        setMessages(data)
    } catch (err) {
        console.error('Failed to fetch messages:', err)
    }
}

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!input.trim() || !title.trim()) return
    if (selectedRecipients.length === 0) {
        alert('Wybierz przynajmniej jednego odbiorcę')
        return
    }
    
    const token = localStorage.getItem('token')
    
    try {
        const res = await fetch('http://localhost:8000/messages', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                Authorization: `Bearer ${token}`,
            },
            body: JSON.stringify({
                title: title,
                context: input,
                recipients: selectedRecipients,
            }),
        })
        
        if (!res.ok) {
            alert('Failed to send message')
            return
        }
        
        setTitle('')
        setInput('')
        setSelectedRecipients([])
        await fetchMessages() 
    } catch (err) {
        console.error('Failed to send:', err)
    }
}

  const toggleRecipient = (username: string) => {
    setSelectedRecipients(prev => {
        if (prev.includes(username)) {
            return prev.filter(u => u !== username)
        } else {
            return [...prev, username]
        }
    })
}

  const handleLogout = () => {
    localStorage.removeItem('token')
    navigate('/login')
    
  }
const [title, setTitle] = useState('')
return (
    <div className="chat-page">
        <header className="chat-header">
            <h1>chat</h1>
            <div>
                Zalogowany jako: <strong>{me}</strong>
                <button onClick={handleLogout}>Wyloguj</button>
            </div>
        </header>

        <div className="chat-layout">
            <aside className="chat-sidebar">
                <h2>Nowa wiadomość</h2>
                <form onSubmit={handleSubmit}>
                    <div className="input-group">
                        <label htmlFor="title">Tytuł</label>
                        <input
                            id="title"
                            type="text"
                            value={title}
                            onChange={(e) => setTitle(e.target.value)}
                            required
                        />
                    </div>
                    <div className="input-group">
                        <label htmlFor="message">Treść</label>
                        <textarea
                            id="message"
                            value={input}
                            onChange={(e) => setInput(e.target.value)}
                            required
                        />
                    </div>
                    <div className="input-group">
                        <label>Odbiorcy</label>
                        <ul className="recipients-list">
                            {users.map(u => (
                                <li key={u}>
                                    <label>
                                        <input
                                            type="checkbox"
                                            checked={selectedRecipients.includes(u)}
                                            onChange={() => toggleRecipient(u)}
                                        />
                                        {u}
                                    </label>
                                </li>
                            ))}
                        </ul>
                    </div>
                    <button type="submit">Wyślij</button>
                </form>
            </aside>

            <main className="chat-main">
                <h2>Skrzynka</h2>
                {messages.length === 0 && <p>Brak wiadomości</p>}
                <div className="messages-list">
                    {messages.map(msg => (
                        <article key={msg.id} className="message-card">
                            <header className="message-card-header">
                                <span className="message-participants">
                                    {msg.sender} → {msg.recipients.join(', ')}
                                </span>
                                <span className="message-date">{msg.date}</span>
                            </header>
                            <h3 className="message-title">{msg.title}</h3>
                            <p className="message-context">{msg.context}</p>
                        </article>
                    ))}
                </div>
            </main>
        </div>
    </div>
)
}

export default Chat