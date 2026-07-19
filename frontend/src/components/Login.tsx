import { Link, useNavigate } from 'react-router-dom'
import { useState } from 'react'

function Login() {
    const navigate = useNavigate()
    const [error, setError] = useState('')

    const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
        e.preventDefault()
        setError('')

        const formData = new FormData(e.currentTarget)
        
        const body = new URLSearchParams()
        body.append('username', formData.get('username') as string)
        body.append('password', formData.get('password') as string)

        try {
            const res = await fetch('http://localhost:8000/login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                body: body,
            })

            if (!res.ok) {
                const err = await res.json()
                setError(err.detail || 'Login failed')
                return
            }

            const data = await res.json()
            localStorage.setItem('token', data.access_token)
            navigate('/chat')
        } catch {
            setError('Network error')
        }
    }

    return (
        <div className='page-center'>
        <div className="login-container">
            <h1>LOGIN</h1>
            <form onSubmit={handleSubmit}>
                <div className="input-group">
                    <label>
                        Login: <input name="username" placeholder="Login" required/>
                    </label>
                </div>
                <div className="input-group">
                    <label>
                        Password: <input type="password" name="password" placeholder="••••••••" required/>
                    </label>
                </div>
                {error && <p style={{color: 'red'}}>{error}</p>}
                <button type="submit">SIGN IN</button>
                <div className="footer">
                    Don't have an account? <Link to="/register">Sign up</Link>
                </div>
            </form>
        </div>
        </div>
    )
}

export default Login