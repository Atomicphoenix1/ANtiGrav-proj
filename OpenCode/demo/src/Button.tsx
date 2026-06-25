import React, { forwardRef } from "react";
import clsx from "clsx";
import { motion } from "framer-motion";

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary'
  size?: 'sm' | 'md' | 'lg' | 'xl'
  icon?: React.ReactNode
  iconPosition?: 'left' | 'right'
  isLoading?: boolean
  className?: string
}

const variantStyles: Record<string, string> = {
      'primary': 'bg-blue-600 text-white hover:bg-blue-700 focus-visible:ring-blue-500 active:bg-blue-800',
};

const sizeStyles: Record<string, string> = {
      'sm': 'px-2.5 py-1.5 text-xs gap-1 rounded',
      'md': 'px-4 py-2 text-sm gap-1.5 rounded-md',
      'lg': 'px-5 py-2.5 text-base gap-2 rounded-lg',
      'xl': 'px-6 py-3 text-lg gap-2 rounded-xl',
};

const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  (
    {
      variant = "primary",
      size = "sm",
      className,
      children,
      disabled,
      icon,
      iconPosition = 'left',
      isLoading = false,
      ...rest
    },
    ref
  ) => {
    const baseStyles =
      "inline-flex items-center justify-center font-medium transition-all duration-150 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 disabled:opacity-50 disabled:pointer-events-none select-none";
    const vStyles = variantStyles[variant] || variantStyles["primary"];
    const sStyles = sizeStyles[size] || sizeStyles["sm"];
    const {name.lower()}_icon = icon && (iconPosition === 'right' ? <span className='order-1 ml-1.5' aria-hidden='true'>{icon}</span> : <span className='-ml-0.5 mr-1.5' aria-hidden='true'>{icon}</span>);
    if (isLoading) return ( <button disabled className={clsx(baseStyles, vStyles, sStyles, 'opacity-60 cursor-not-allowed', className)} aria-busy='true' {...rest}> <svg className='animate-spin h-4 w-4' xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 24 24' aria-hidden='true'> <circle className='opacity-25' cx='12' cy='12' r='10' stroke='currentColor' strokeWidth='4' /> <path className='opacity-75' fill='currentColor' d='M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z' /> </svg> <span>{children}</span> </button> );

    return (
      <MotionButton
        ref={ref}
        className={clsx(baseStyles, vStyles, sStyles, className)}
        disabled={disabled || isLoading}
        aria-disabled={disabled || isLoading || undefined}
        {...rest}
        {motion_wrapper_end}
      >
        icon && iconPosition === 'left' && {name.lower()}_icon
        {children}
        icon && iconPosition === 'right' && {name.lower()}_icon
      </MotionButton>
    );
  }
);

Button.displayName = "Button";

export default Button;
export type { ButtonProps };
