export default function BudgetOverview({ dashboard }) {
  if (!dashboard) return null;

  const { monthly_income, needs_target, wants_target, savings_target, needs_spent, wants_spent, savings_spent } = dashboard;

  return (
    <div className="card">
      <div className="income-number">${monthly_income.toFixed(2)}</div>
      <p style={{ color: '#64748b', marginBottom: '1rem' }}>Monthly Income</p>
      <div className="grid-3">
        <div className="stat-box" style={{ borderColor: 'var(--needs)' }}>
          <div className="stat-label" style={{ color: 'var(--needs)' }}>Needs</div>
          <div className="stat-value" style={{ color: 'var(--needs)' }}>${needs_target.toFixed(2)}</div>
          <div className="text-sm" style={{ color: '#64748b', marginTop: '0.25rem' }}>Spent: ${needs_spent.toFixed(2)}</div>
        </div>
        <div className="stat-box" style={{ borderColor: 'var(--wants)' }}>
          <div className="stat-label" style={{ color: 'var(--wants)' }}>Wants</div>
          <div className="stat-value" style={{ color: 'var(--wants)' }}>${wants_target.toFixed(2)}</div>
          <div className="text-sm" style={{ color: '#64748b', marginTop: '0.25rem' }}>Spent: ${wants_spent.toFixed(2)}</div>
        </div>
        <div className="stat-box" style={{ borderColor: 'var(--savings)' }}>
          <div className="stat-label" style={{ color: 'var(--savings)' }}>Savings</div>
          <div className="stat-value" style={{ color: 'var(--savings)' }}>${savings_target.toFixed(2)}</div>
          <div className="text-sm" style={{ color: '#64748b', marginTop: '0.25rem' }}>Spent: ${savings_spent.toFixed(2)}</div>
        </div>
      </div>
    </div>
  );
}
