import React, { forwardRef, useId } from "react";
import clsx from "clsx";

export interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  helperText?: string;
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
  wrapperClassName?: string;
  floatingLabel?: boolean;
}

const Input = forwardRef<HTMLInputElement, InputProps>(
  (
    {
      label,
      error,
      helperText,
      leftIcon,
      rightIcon,
      className,
      wrapperClassName,
      floatingLabel = false,
      id: externalId,
      ...rest
    },
    ref
  ) => {
    const autoId = useId();
    const inputId = externalId || autoId;
    const errorId = error ? `${inputId}-error` : undefined;
    const helperId = helperText && !error ? `${inputId}-helper` : undefined;

    const baseInputStyles =
      "block w-full rounded-lg border bg-white px-3 py-2 text-sm text-gray-900 placeholder-gray-400 transition-colors duration-150 dark:bg-gray-800 dark:text-gray-100 dark:placeholder-gray-500";
    const borderStyles = error
      ? "border-red-500 focus:border-red-500 focus:ring-red-500/20"
      : "border-gray-300 focus:border-blue-500 focus:ring-blue-500/20 dark:border-gray-600 dark:focus:border-blue-400";
    const focusStyles =
      "focus:outline-none focus:ring-2";
    const disabledStyles = "disabled:opacity-50 disabled:cursor-not-allowed disabled:bg-gray-50 dark:disabled:bg-gray-900";
    const iconPaddingLeft = leftIcon ? "pl-10" : "";
    const iconPaddingRight = rightIcon ? "pr-10" : "";

    return (
      <div className={clsx("w-full", wrapperClassName)}>
        {label && !floatingLabel && (
          <label
            htmlFor={inputId}
            className="mb-1.5 block text-sm font-medium text-gray-700 dark:text-gray-300"
          >
            {label}
          </label>
        )}

        <div className="relative">
          {leftIcon && (
            <div className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3 text-gray-400 dark:text-gray-500">
              {leftIcon}
            </div>
          )}

          <input
            ref={ref}
            id={inputId}
            className={clsx(
              baseInputStyles,
              borderStyles,
              focusStyles,
              disabledStyles,
              iconPaddingLeft,
              iconPaddingRight,
              className
            )}
            aria-invalid={!!error}
            aria-required={rest.required}
            aria-describedby={errorId || helperId}
            aria-errormessage={errorId}
            {...rest}
          />

          {rightIcon && (
            <div className="absolute inset-y-0 right-0 flex items-center pr-3 text-gray-400 dark:text-gray-500">
              {rightIcon}
            </div>
          )}
        </div>

        {floatingLabel && label && (
          <label
            htmlFor={inputId}
            className={clsx(
              "absolute left-3 transition-all duration-150 pointer-events-none",
              rest.value || rest.placeholder
                ? "-top-2.5 text-xs bg-white px-1 dark:bg-gray-800"
                : "top-2.5 text-sm text-gray-400"
            )}
          >
            {label}
          </label>
        )}

        {error && (
          <p id={errorId} role="alert" className="mt-1.5 text-xs text-red-600 dark:text-red-400">
            {error}
          </p>
        )}
        {helperText && !error && (
          <p id={helperId} className="mt-1.5 text-xs text-gray-500 dark:text-gray-400">
            {helperText}
          </p>
        )}
      </div>
    );
  }
);

Input.displayName = "Input";

export { Input };
