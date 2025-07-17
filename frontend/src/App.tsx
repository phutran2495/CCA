import { useState } from 'react';

interface CCA {
  cca_name: string;
  signup_link?: string;
}

const API_URL = (import.meta.env.VITE_API_URL || '').replace(/\/$/, '');

function App() {
  const [address, setAddress] = useState('');
  const [results, setResults] = useState<CCA[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    setResults([]);
    try {
      const resp = await fetch(`${API_URL}/eligible_ccas`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ address }),
      });
      if (!resp.ok) throw new Error('API error');
      const data = await resp.json();
      setResults(data);
    } catch (err) {
      setError('Failed to fetch results.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ minHeight: '100vh', width: '100vw', background: 'linear-gradient(120deg, #f8fafc 0%, #e0e7ef 100%)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
      <div style={{ background: '#fff', borderRadius: 16, boxShadow: '0 4px 24px rgba(0,0,0,0.08)', padding: '2.5rem 2rem', width: '100%', maxWidth: 420 }}>
        <h1 style={{ textAlign: 'center', fontWeight: 700, fontSize: '2rem', marginBottom: '1.5rem', color: '#1e293b', letterSpacing: '-1px' }}>CCA Finder</h1>
        <form onSubmit={handleSubmit} style={{ display: 'flex', gap: 8, marginBottom: 24 }}>
          <input
            type="text"
            value={address}
            onChange={e => setAddress(e.target.value)}
            placeholder="Enter address, city, or zip"
            style={{ flex: 1, padding: '0.75rem 1rem', borderRadius: 8, border: '1px solid #cbd5e1', fontSize: 16, outline: 'none', background: '#f1f5f9', transition: 'border 0.2s', color: '#111' }}
            required
          />
          <button
            type="submit"
            style={{ padding: '0.75rem 1.5rem', borderRadius: 8, border: 'none', background: '#2563eb', color: '#fff', fontWeight: 600, fontSize: 16, cursor: 'pointer', transition: 'background 0.2s' }}
            disabled={loading}
          >
            {loading ? 'Searching...' : 'Search'}
          </button>
        </form>
        {error && <div style={{ color: '#dc2626', marginBottom: 16, textAlign: 'center' }}>{error}</div>}
        {results.length > 0 ? (
          <div>
            <h2 style={{ fontSize: 18, fontWeight: 600, marginBottom: 12, color: '#334155' }}>Eligible CCAs</h2>
            <ul style={{ listStyle: 'none', padding: 0, margin: 0 }}>
              {results.map((cca, idx) => (
                <li key={idx} style={{ marginBottom: 14, padding: '0.75rem 1rem', borderRadius: 8, background: '#f8fafc', boxShadow: '0 1px 4px rgba(0,0,0,0.03)' }}>
                  <div style={{ fontWeight: 500, color: '#1e293b', fontSize: 16 }}>{cca.cca_name}</div>
                  {cca.signup_link ? (
                    <a
                      href={cca.signup_link}
                      target="_blank"
                      rel="noopener noreferrer"
                      style={{ color: '#2563eb', textDecoration: 'none', fontWeight: 500, fontSize: 15 }}
                    >
                      Signup Link ↗
                    </a>
                  ) : (
                    <span style={{ color: '#64748b', fontSize: 15 }}>No signup link available</span>
                  )}
                </li>
              ))}
            </ul>
          </div>
        ) : (
          !loading && <div style={{ color: '#64748b', textAlign: 'center', fontSize: 15 }}>No eligible CCAs found.</div>
        )}
      </div>
    </div>
  );
}

export default App;
