'use client';

import * as React from 'react';

const baseStyles =
  'inline-flex items-center justify-center gap-2 font-mono font-medium tracking-wider transition-colors focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-white disabled:cursor-not-allowed disabled:opacity-60';

const sizeStyles: Record<'sm' | 'md' | 'lg', string> = {
  sm: 'px-3 py-1.5 text-xs',
  md: 'px-5 py-2.5 text-sm',
  lg: 'px-6 py-3 text-base',
};

const variantStyles: Record<'primary' | 'secondary' | 'ghost', string> = {
  primary: 'bg-white text-black hover:bg-gray-200 border border-white',
  secondary: 'border border-white/40 bg-transparent text-white hover:border-white hover:bg-white hover:text-black',
  ghost: 'text-white hover:bg-white/10',
};

type ButtonVariant = keyof typeof variantStyles;
type ButtonSize = keyof typeof sizeStyles;

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  size?: ButtonSize;
  isLoading?: boolean;
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
}

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  (
    {
      variant = 'primary',
      size = 'md',
      isLoading = false,
      disabled,
      leftIcon,
      rightIcon,
      className = '',
      children,
      ...rest
    },
    ref
  ) => {
    const isDisabled = disabled || isLoading;
    return (
      <button
        ref={ref}
        className={`${baseStyles} ${variantStyles[variant]} ${sizeStyles[size]} ${className}`}
        disabled={isDisabled}
        {...rest}
      >
        {isLoading && <SpinnerDot />}
        {!isLoading && leftIcon}
        <span>{children}</span>
        {!isLoading && rightIcon}
      </button>
    );
  }
);
Button.displayName = 'Button';

const SpinnerDot = () => (
  <span className="inline-block h-2 w-2 animate-ping rounded-full bg-white" aria-hidden="true" />
);
