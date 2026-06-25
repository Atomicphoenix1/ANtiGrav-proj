import React, { forwardRef } from "react";
import clsx from "clsx";
import { motion } from "framer-motion";

interface SelectProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'default'
  size?: 'md'
  className?: string
}

const variantStyles: Record<string, string> = {
      'default': 'bg-blue-600 text-white hover:bg-blue-700 focus-visible:ring-blue-500 active:bg-blue-800',
};

const sizeStyles: Record<string, string> = {
      'md': 'px-4 py-2 text-sm gap-1.5 rounded-md',
};

const Select = forwardRef<HTMLButtonElement, SelectProps>(
  (
    {
      variant = "default",
      size = "md",
      className,
      children,
      disabled,
      
      
      
      ...rest
    },
    ref
  ) => {
    const baseStyles =
      "inline-flex items-center justify-center font-medium transition-all duration-150 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 disabled:opacity-50 disabled:pointer-events-none select-none";
    const vStyles = variantStyles[variant] || variantStyles["default"];
    const sStyles = sizeStyles[size] || sizeStyles["md"];
    
    

    return (
      <MotionButton
        ref={ref}
        className={clsx(baseStyles, vStyles, sStyles, className)}
        disabled={disabled || isLoading}
        aria-disabled={disabled || isLoading || undefined}
        {...rest}
        {motion_wrapper_end}
      >
        False
        {children}
        False
      </MotionButton>
    );
  }
);

Select.displayName = "Select";

export default Select;
export type { SelectProps };
