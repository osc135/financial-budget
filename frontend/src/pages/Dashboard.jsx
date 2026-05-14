import { useEffect, useState, useCallback } from 'react';
import { useAuth } from '../context/AuthContext';
import BudgetOverview from '../components/BudgetOverview';
import SpendingProgress from '../components/SpendingProgress';
import AddTransaction from '../components/AddTransaction';

const API_BASE = import.meta.env.VITE_API_URL || '';

export default function Dashboard() {
  const { token, logout } = useAuth();
  const [budget, setBudget] = useState(null);
  const [dashboard, setDashboard] = useState(null);
  const [incomeInput, setIncomeInput] = useState('');
  const [error, setError] = useState('');
  const [bundleStatus, setBundleStatus] = useState('');
  const [bundleLoading, setBundleLoading] = useState(false);

  const authHeaders = {
    Authorization: `Bearer ${token}`,
    'Content-Type': 'application/json',
  };

  const fetchBudget = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE}/budget`, { headers: { Authorization: `Bearer ${token}` } });
      if (res.ok) {
        const data = await res.json();
        setBudget(data);
      } else {
        setBudget(null);
      }
    } catch {
      setBudget(null);
    }
  }, [token]);

  const fetchDashboard = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE}/budget/dashboard`, { headers: { Authorization: `Bearer ${token}` } });
      if (res.ok) {
        const data = await res.json();
        setDashboard(data);
      }
    } catch {
      // ignore
    }
  }, [token]);

  useEffect(() => {
    fetchBudget();
  }, [fetchBudget]);

  useEffect(() => {
    if (budget) {
      fetchDashboard();
    }
  }, [budget, fetchDashboard]);

  async function createBudget(e) {
    e.preventDefault();
    setError('');
    try {
      const res = await fetch(`${API_BASE}/budget`, {
        method: 'POST',
        headers: authHeaders,
        body: JSON.stringify({ monthly_income: parseFloat(incomeInput) }),
      });
      if (!res.ok) {
        const data = await res.json();
        throw new Error(data.detail || 'Failed to create budget');
      }
      await fetchBudget();
    } catch (err) {
      setError(err.message);
    }
  }

  async function generateSupportBundle() {
    setBundleStatus('');
    setBundleLoading(true);
    try {
      const res = await fetch(`${API_BASE}/support-bundle/generate`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` },
      });
      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || 'Failed to start support bundle generation');
      }
      setBundleStatus(data.message || 'Support bundle collection started.');
    } catch (err) {
      setBundleStatus(`Error: ${err.message}`);
    } finally {
      setBundleLoading(false);
      setTimeout(() => setBundleStatus(''), 8000);
    }
  }

  async function deleteTransaction(id) {
    try {
      const res = await fetch(`${API_BASE}/budget/transactions/${id}`, {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        await fetchDashboard();
      }
    } catch {
      // ignore
    }
  }

  return (
    <div className="container">
      <div className="header">
        <h1>Financial Budget</h1>
        <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
          <button
            className="btn btn-secondary"
            onClick={generateSupportBundle}
            disabled={bundleLoading}
            title="Collect a support bundle and upload it to the Vendor Portal"
          >
            {bundleLoading ? 'Generating…' : 'Generate Support Bundle'}
          </button>
          <button className="btn btn-secondary" onClick={logout}>
            Logout
          </button>
        </div>
      </div>
      {bundleStatus && (
        <div className="card" style={{ marginBottom: '1rem' }}>
          <p className="text-sm" style={{ margin: 0, color: '#475569' }}>{bundleStatus}</p>
        </div>
      )}

      {!budget ? (
        <div className="card">
          <h2 className="card-title">Set Up Your Budget</h2>
          <p className="text-sm" style={{ marginBottom: '1rem', color: '#64748b' }}>
            Enter your monthly income to get started with the 50/30/20 rule.
          </p>
          <form onSubmit={createBudget}>
            <div className="form-group">
              <label>Monthly Income</label>
              <input
                type="number"
                step="0.01"
                min="0"
                value={incomeInput}
                onChange={(e) => setIncomeInput(e.target.value)}
                placeholder="e.g. 5000"
                required
              />
            </div>
            {error && <div className="error">{error}</div>}
            <button type="submit" className="btn btn-primary mt-2">
              Create Budget
            </button>
          </form>
        </div>
      ) : (
        <>
          <BudgetOverview dashboard={dashboard} />
          <SpendingProgress dashboard={dashboard} />
          <AddTransaction onSuccess={fetchDashboard} />

          <div className="card">
            <h2 className="card-title">Transaction History</h2>
            {dashboard && dashboard.transactions.length > 0 ? (
              <div>
                {dashboard.transactions.map((tx) => (
                  <div key={tx.id} className="tx-item">
                    <div className="tx-meta">
                      <span className={`badge badge-${tx.category}`}>{tx.category}</span>
                      <span className="tx-desc">{tx.description || 'No description'}</span>
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center' }}>
                      <span className="tx-amount">${tx.amount.toFixed(2)}</span>
                      <button className="btn btn-danger btn-sm" onClick={() => deleteTransaction(tx.id)}>
                        Delete
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-sm" style={{ color: '#64748b' }}>No transactions yet.</p>
            )}
          </div>
        </>
      )}
    </div>
  );
}
