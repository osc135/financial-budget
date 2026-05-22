import { createContext, useContext, useEffect, useState } from 'react';

const API_BASE = import.meta.env.VITE_API_URL || '';

const DEFAULT_CURRENCY = {
  code: 'USD',
  symbol: '$',
  position: 'prefix',
  decimal_places: 2,
  thousands_sep: ',',
  decimal_sep: '.',
};

const CurrencyContext = createContext(DEFAULT_CURRENCY);

export function CurrencyProvider({ children }) {
  const [currency, setCurrency] = useState(DEFAULT_CURRENCY);

  useEffect(() => {
    fetch(`${API_BASE}/config/currency`)
      .then((res) => (res.ok ? res.json() : null))
      .then((data) => data && setCurrency(data))
      .catch(() => {});
  }, []);

  return (
    <CurrencyContext.Provider value={currency}>{children}</CurrencyContext.Provider>
  );
}

export function useCurrency() {
  return useContext(CurrencyContext);
}

export function formatCurrency(amount, c) {
  const value = Number(amount) || 0;
  const fixed = value.toFixed(c.decimal_places);
  const [whole, dec] = fixed.split('.');
  const withSep = whole.replace(/\B(?=(\d{3})+(?!\d))/g, c.thousands_sep);
  const num = dec ? `${withSep}${c.decimal_sep}${dec}` : withSep;
  return c.position === 'prefix' ? `${c.symbol}${num}` : `${num} ${c.symbol}`;
}
