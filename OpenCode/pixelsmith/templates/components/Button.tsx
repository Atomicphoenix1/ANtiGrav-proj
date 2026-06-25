import React, { forwardRef } from "react";
import clsx from "clsx";
import { motion } from "framer-motion";

export type ButtonVariant = "primary" | "secondary" | "outline" | "ghost" | "danger" | "link";
export type ButtonSize = "sm" | "md" | "lg" | "xl";

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  size?: ButtonSize;
  icon?: React.ReactNode;
  iconPosition?: "left" | "right";
  isLoading?: boolean;
  href?: string;
}

const variantStyles: Record<ButtonVariant, string> = {
  primary:
    "bg-blue-600 text-white hover:bg-blue-700 focus-visible:ring-blue-500 active:bg-blue-800 dark:bg-blue-500 dark:hover:bg-blue-600",
  secondary:
    "bg-gray-100 text-gray-900 hover:bg-gray-200 focus-visible:ring-gray-400 active:bg-gray-300 dark:bg-gray-700 dark:text-gray-100 dark:hover:bg-gray-600",
  outline:
    "border border-gray-300 bg-transparent text-gray-700 hover:bg-gray-50 focus-visible:ring-gray-400 active:bg-gray-100 dark:border-gray-600 dark:text-gray-300 dark:hover:bg-gray-800",
  ghost:
    "bg-transparent text-gray-700 hover:bg-gray-100 focus-visible:ring-gray-400 active:bg-gray-200 dark:text-gray-300 dark:hover:bg-gray-800",
  danger:
    "bg-red-600 text-white hover:bg-red-700 focus-visible:ring-red-500 active:bg-red-800 dark:bg-red-500 dark:hover:bg-red-600",
  link:
    "bg-transparent text-blue-600 underline-offset-2 hover:underline focus-visible:ring-blue-500 dark:text-blue-400",
};

const sizeStyles: Record<ButtonSize, string> = {
  sm: "px-2.5 py-1.5 text-xs gap-1 rounded",
  md: "px-4 py-2 text-sm gap-1.5 rounded-md",
  lg: "px-5 py-2.5 text-base gap-2 rounded-lg",
  xl: "px-6 py-3 text-lg gap-2.5 rounded-xl",
};

const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  (
    {
      variant = "primary",
      size = "md",
      className,
      children,
      disabled,
      icon,
      iconPosition = "left",
      isLoading = false,
      href,
      ...rest
    },
    ref
  ) => {
    const baseStyles =
      "inline-flex items-center justify-center font-medium transition-all duration-150 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 disabled:opacity-50 disabled:pointer-events-none select-none";

    const vStyles = variantStyles[variant] || variantStyles.primary;
    const sStyles = sizeStyles[size] || sizeStyles.md;

    const iconElement = icon ? (
      <span
        className={clsx(
          iconPosition === "right" ? "order-1 ml-1.5" : "-ml-0.5 mr-1.5"
        )}
        aria-hidden="true"
      >
        {icon}
      </span>
    ) : null;

    if (isLoading) {
      return (
        <button
          disabled
          className={clsx(
            baseStyles,
            vStyles,
            sStyles,
            "opacity-60 cursor-not-allowed",
            className
          )}
          aria-busy="true"
          {...rest}
        >
          <svg
            className="animate-spin h-4 w-4"
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 24 24"
            aria-hidden="true"
          >
            <circle
              className="opacity-25"
              cx="12"
              cy="12"
              r="10"
              stroke="currentColor"
              strokeWidth="4"
            />
            <path
              className="opacity-75"
              fill="currentColor"
              d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
            />
          </svg>
          <span>{children}</span>
        </button>
      );
    }

    const content = (
      <>
        {icon && iconPosition === "left" && iconElement}
        {children}
        {icon && iconPosition === "right" && iconElement}
      </>
    );

    if (href) {
      return (
        <a
          href={href}
          className={clsx(baseStyles, vStyles, sStyles, "no-underline", className)}
          ref={ref as React.Ref<HTMLAnchorElement>}
        >
          {content}
        </a>
      );
    }

    return (
      <motion.button
        ref={ref}
        className={clsx(baseStyles, vStyles, sStyles, className)}
        disabled={disabled}
        aria-disabled={disabled || undefined}
        whileHover={{ scale: 1.02 }}
        whileTap={{ scale: 0.98 }}
        transition={{ type: "spring", stiffness: 400, damping: 17 }}
        {...rest}
      >
        {content}
      </motion.button>
    );
  }
);

Button.displayName = "Button";

export { Button };
