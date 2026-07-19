import { Link, useNavigate } from 'react-router-dom'
import { useState } from 'react'

function Register() {
    const navigate = useNavigate()
    const [error, setError] = useState('')

    const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
        e.preventDefault()
        setError('')

        const formData = new FormData(e.currentTarget)
        const password = formData.get('password') as string
        const passwordRepeat = formData.get('password_repeat') as string

        if (password !== passwordRepeat) {
            setError('Passwords do not match')
            return
        }

        try {
            const res = await fetch('http://localhost:8000/register', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    username: formData.get('username'),
                    password: password,
                }),
            })

            if (!res.ok) {
                const err = await res.json()
                setError(err.detail || 'Registration failed')
                return
            }

            navigate('/login')
        } catch {
            setError('Network error')
        }
    }

    return (
        <div className='page-center'>
        <div className="login-container">
            <h1>SIGN UP</h1>
            <form onSubmit={handleSubmit}>
                <div className="input-group">
                    <label>
                        Login: <input name="username" placeholder="Login" required minLength={3} maxLength={20}/>
                    </label>
                </div>
                <div className="input-group">
                    <label>
                        Password: <input type="password" name="password" placeholder="••••••••" required minLength={6}/>
                    </label>
                </div>
                <div className="input-group">
                    <label>
                        Repeat Password: <input type="password" name="password_repeat" placeholder="••••••••" required/>
                    </label>
                </div>
                {error && <p style={{color: 'red'}}>{error}</p>}
                <button type="submit">SIGN UP</button>
                <div className="footer">
                    Have an account? <Link to="/login">Sign in</Link>
                </div>
            </form>
        </div>
        </div>
    )
}

export default Register