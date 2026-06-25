import React, { forwardRef, useId, useState, useRef, useEffect, useCallback } from "react";
import clsx from "clsx";

export interface SelectOption {
  value: string;
  label: string;
  disabled?: boolean;
}

export interface SelectProps {
  label?: string;
  options: SelectOption[];
  value?: string;
  onChange?: (value: string) => void;
  placeholder?: string;
  error?: string;
  helperText?: string;
  searchable?: boolean;
  disabled?: boolean;
  className?: string;
  wrapperClassName?: string;
}

export function Select({
  label,
  options,
  value,
  onChange,
  placeholder = "Select...",
  error,
  helperText,
  searchable = false,
  disabled = false,
  className,
  wrapperClassName,
}: SelectProps) {
  const autoId = useId();
  const selectId = `select-${autoId}`;
  const [isOpen, setIsOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [activeIndex, setActiveIndex] = useState(-1);
  const containerRef = useRef<HTMLDivElement>(null);
  const searchInputRef = useRef<HTMLInputElement>(null);

  const selectedOption = options.find((opt) => opt.value === value);
  const filteredOptions = searchable
    ? options.filter((opt) =>
        opt.label.toLowerCase().includes(searchQuery.toLowerCase())
      )
    : options;

  const close = useCallback(() => {
    setIsOpen(false);
    setSearchQuery("");
    setActiveIndex(-1);
  }, []);

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        close();
      }
    };
    if (isOpen) document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, [isOpen, close]);

  useEffect(() => {
    if (isOpen && searchable) {
      requestAnimationFrame(() => searchInputRef.current?.focus());
    }
  }, [isOpen, searchable]);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    switch (e.key) {
      case "Enter":
      case " ":
        e.preventDefault();
        if (isOpen && activeIndex >= 0 && filteredOptions[activeIndex]) {
          onChange?.(filteredOptions[activeIndex].value);
          close();
        } else {
          setIsOpen((p) => !p);
        }
        break;
      case "ArrowDown":
        e.preventDefault();
        setActiveIndex((p) => (p < filteredOptions.length - 1 ? p + 1 : 0));
        break;
      case "ArrowUp":
        e.preventDefault();
        setActiveIndex((p) => (p > 0 ? p - 1 : filteredOptions.length - 1));
        break;
      case "Escape":
        e.preventDefault();
        close();
        break;
      case "Tab":
        close();
        break;
    }
  };

  return (
    <div className={clsx("w-full", wrapperClassName)} ref={containerRef}>
      {label && (
        <label
          htmlFor={selectId}
          className="mb-1.5 block text-sm font-medium text-gray-700 dark:text-gray-300"
        >
          {label}
        </label>
      )}

      <div className="relative">
        <button
          id={selectId}
          type="button"
          className={clsx(
            "flex w-full items-center justify-between rounded-lg border bg-white px-3 py-2 text-sm transition-colors duration-150 dark:bg-gray-800",
            error
              ? "border-red-500 focus:ring-red-500/20"
              : "border-gray-300 dark:border-gray-600",
            "focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500",
            "disabled:opacity-50 disabled:cursor-not-allowed",
            className
          )}
          aria-expanded={isOpen}
          aria-haspopup="listbox"
          aria-activedescendant={
            activeIndex >= 0 ? `option-${filteredOptions[activeIndex]?.value}` : undefined
          }
          disabled={disabled}
          onClick={() => setIsOpen((p) => !p)}
          onKeyDown={handleKeyDown}
        >
          <span className={clsx(!selectedOption && "text-gray-400 dark:text-gray-500")}>
            {selectedOption ? selectedOption.label : placeholder}
          </span>
          <svg
            className={clsx("h-4 w-4 text-gray-400 transition-transform", isOpen && "rotate-180")}
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            aria-hidden="true"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
        </button>

        {isOpen && (
          <div className="absolute z-20 mt-1 w-full rounded-lg border border-gray-200 bg-white shadow-lg dark:border-gray-700 dark:bg-gray-800">
            {searchable && (
              <div className="border-b border-gray-200 p-2 dark:border-gray-700">
                <input
                  ref={searchInputRef}
                  type="text"
                  className="w-full rounded-md border border-gray-300 bg-transparent px-2 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/20 dark:border-gray-600"
                  placeholder="Search..."
                  value={searchQuery}
                  onChange={(e) => {
                    setSearchQuery(e.target.value);
                    setActiveIndex(0);
                  }}
                  onKeyDown={handleKeyDown}
                />
              </div>
            )}
            <ul
              role="listbox"
              aria-label={label || "Options"}
              className="max-h-60 overflow-auto py-1"
            >
              {filteredOptions.length === 0 ? (
                <li className="px-3 py-2 text-sm text-gray-400">No results</li>
              ) : (
                filteredOptions.map((opt, idx) => (
                  <li
                    id={`option-${opt.value}`}
                    key={opt.value}
                    role="option"
                    aria-selected={opt.value === value}
                    className={clsx(
                      "cursor-pointer px-3 py-2 text-sm transition-colors",
                      opt.value === value && "bg-blue-50 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300",
                      idx === activeIndex && "bg-gray-100 dark:bg-gray-700",
                      "hover:bg-gray-100 dark:hover:bg-gray-700"
                    )}
                    onClick={() => {
                      onChange?.(opt.value);
                      close();
                    }}
                  >
                    {opt.label}
                  </li>
                ))
              )}
            </ul>
          </div>
        )}
      </div>

      {error && (
        <p role="alert" className="mt-1.5 text-xs text-red-600 dark:text-red-400">
          {error}
        </p>
      )}
      {helperText && !error && (
        <p className="mt-1.5 text-xs text-gray-500 dark:text-gray-400">{helperText}</p>
      )}
    </div>
  );
}
