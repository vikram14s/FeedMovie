import type { ButtonHTMLAttributes, ReactNode } from 'react';

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'link';
  children: ReactNode;
}

export function Button({
  variant = 'primary',
  children,
  className = '',
  disabled,
  ...props
}: ButtonProps) {
  const baseClass = {
    primary: 'btn-primary',
    secondary: 'btn-secondary',
    link: 'btn-link',
  }[variant];

  return (
    <button
      className={`${baseClass} ${className}`}
      disabled={disabled}
      {...props}
    >
      {children}
    </button>
  );
}
