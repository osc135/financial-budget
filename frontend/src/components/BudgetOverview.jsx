import { useCurrency, formatCurrency } from '../context/CurrencyContext';

export default function BudgetOverview({ dashboard }) {
  const currency = useCurrency();
  if (!dashboard) return null;

  const { monthly_income, needs_target, wants_target, savings_target, needs_spent, wants_spent, savings_spent } = dashboard;
  const fmt = (v) => formatCurrency(v, currency);

  return (
    <div className="card">
      <div className="income-number">{fmt(monthly_income)}</div>
      <p style={{ color: '#64748b', marginBottom: '1rem' }}>Monthly Income</p>
      <div className="grid-3">
        <div className="stat-box" style={{ borderColor: 'var(--needs)' }}>
          <div className="stat-label" style={{ color: 'var(--needs)' }}>Needs</div>
          <div className="stat-value" style={{ color: 'var(--needs)' }}>{fmt(needs_target)}</div>
          <div className="text-sm" style={{ color: '#64748b', marginTop: '0.25rem' }}>Spent: {fmt(needs_spent)}</div>
        </div>
        <div className="stat-box" style={{ borderColor: 'var(--wants)' }}>
          <div className="stat-label" style={{ color: 'var(--wants)' }}>Wants</div>
          <div className="stat-value" style={{ color: 'var(--wants)' }}>{fmt(wants_target)}</div>
          <div className="text-sm" style={{ color: '#64748b', marginTop: '0.25rem' }}>Spent: {fmt(wants_spent)}</div>
        </div>
        <div className="stat-box" style={{ borderColor: 'var(--savings)' }}>
          <div className="stat-label" style={{ color: 'var(--savings)' }}>Savings</div>
          <div className="stat-value" style={{ color: 'var(--savings)' }}>{fmt(savings_target)}</div>
          <div className="text-sm" style={{ color: '#64748b', marginTop: '0.25rem' }}>Spent: {fmt(savings_spent)}</div>
        </div>
      </div>
    </div>
  );
}
