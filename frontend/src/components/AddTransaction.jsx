import { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';

const API_BASE = import.meta.env.VITE_API_URL || '';

export default function AddTransaction({ onSuccess }) {
  const { token } = useAuth();
  const [category, setCategory] = useState('needs');
  const [customCategory, setCustomCategory] = useState('');
  const [amount, setAmount] = useState('');
  const [description, setDescription] = useState('');
  const [error, setError] = useState('');
  const [entitlements, setEntitlements] = useState({ custom_category_enabled: false });

  // Fetch license entitlements on mount
  useEffect(() => {
    async function fetchEntitlements() {
      try {
        const res = await fetch(`${API_BASE}/license/entitlements`, {
          headers: { Authorization: `Bearer ${token}` },
        });
        if (res.ok) {
          const data = await res.json();
          setEntitlements(data);
        }
      } catch (err) {
        console.error('Failed to fetch entitlements:', err);
      }
    }
    fetchEntitlements();
  }, [token]);

  async function handleSubmit(e) {
    e.preventDefault();
    setError('');
    try {
      const finalCategory = category === 'custom' ? customCategory.trim() : category;
      if (category === 'custom' && !finalCategory) {
        throw new Error('Please enter a custom category name');
      }

      const res = await fetch(`${API_BASE}/budget/transactions`, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          category: finalCategory,
          amount: parseFloat(amount),
          description: description || undefined,
        }),
      });

      if (!res.ok) {
        const data = await res.json();
        throw new Error(data.detail || 'Failed to add transaction');
      }

      setAmount('');
      setDescription('');
      setCategory('needs');
      setCustomCategory('');
      onSuccess();
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <div className="card">
      <h2 className="card-title">Add Transaction</h2>
      <form onSubmit={handleSubmit}>
        <div className="form-grid">
          <div className="form-group">
            <label>Category</label>
            <select
              value={category}
              onChange={(e) => setCategory(e.target.value)}
            >
              <option value="needs">Needs</option>
              <option value="wants">Wants</option>
              <option value="savings">Savings</option>
              {entitlements.custom_category_enabled && (
                <option value="custom">Custom</option>
              )}
            </select>
          </div>
          <div className="form-group">
            <label>Amount</label>
            <input
              type="number"
              step="0.01"
              min="0"
              value={amount}
              onChange={(e) => setAmount(e.target.value)}
              placeholder="0.00"
              required
            />
          </div>
          <div className="form-group">
            <label>&nbsp;</label>
            <button type="submit" className="btn btn-primary">
              Add
            </button>
          </div>
        </div>
        {category === 'custom' && (
          <div className="form-group mt-2">
            <label>Custom Category</label>
            <input
              type="text"
              value={customCategory}
              onChange={(e) => setCustomCategory(e.target.value)}
              placeholder="e.g. Groceries, Travel"
              required
            />
          </div>
        )}
        <div className="form-group mt-2">
          <label>Description</label>
          <input
            type="text"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="e.g. Weekly grocery run"
          />
        </div>
        {error && <div className="error">{error}</div>}
      </form>
    </div>
  );
}
