import { useCurrency, formatCurrency } from '../context/CurrencyContext';

export default function SpendingProgress({ dashboard }) {
  const currency = useCurrency();
  if (!dashboard) return null;

  const categories = [
    { key: 'needs', label: 'Needs', color: 'var(--needs)' },
    { key: 'wants', label: 'Wants', color: 'var(--wants)' },
    { key: 'savings', label: 'Savings', color: 'var(--savings)' },
  ];

  return (
    <div className="card">
      <h2 className="card-title">Spending Progress</h2>
      {categories.map((cat) => {
        const target = dashboard[`${cat.key}_target`];
        const spent = dashboard[`${cat.key}_spent`];
        const ratio = target > 0 ? spent / target : 0;
        const pct = Math.min(ratio * 100, 100);
        const over = spent > target;

        return (
          <div key={cat.key} className="progress-item">
            <div className="progress-header">
              <span>{cat.label}</span>
              <span style={{ color: over ? '#d0021b' : 'inherit' }}>
                {formatCurrency(spent, currency)} / {formatCurrency(target, currency)}
              </span>
            </div>
            <div className="progress-track">
              <div
                className="progress-fill"
                style={{
                  width: `${pct}%`,
                  background: over ? '#d0021b' : cat.color,
                }}
              />
            </div>
          </div>
        );
      })}
    </div>
  );
}
