import React from "react";
import clsx from "clsx";
import { motion } from "framer-motion";

export interface CardProps {
  image?: string;
  imageAlt?: string;
  title?: React.ReactNode;
  description?: React.ReactNode;
  footer?: React.ReactNode;
  children?: React.ReactNode;
  className?: string;
  hoverEffect?: boolean;
  onClick?: () => void;
  as?: "article" | "div" | "section";
}

export function Card({
  image,
  imageAlt = "",
  title,
  description,
  footer,
  children,
  className,
  hoverEffect = true,
  onClick,
  as: Component = "article",
}: CardProps) {
  const isClickable = !!onClick;

  return (
    <motion.div
      whileHover={hoverEffect ? { y: -4, scale: 1.01 } : undefined}
      transition={{ type: "spring", stiffness: 300, damping: 20 }}
    >
      <Component
        className={clsx(
          "rounded-xl border border-gray-200 bg-white shadow-sm overflow-hidden dark:border-gray-700 dark:bg-gray-800",
          isClickable && "cursor-pointer",
          className
        )}
        onClick={onClick}
        role={isClickable ? "button" : undefined}
        tabIndex={isClickable ? 0 : undefined}
        onKeyDown={
          isClickable
            ? (e) => {
                if (e.key === "Enter" || e.key === " ") {
                  e.preventDefault();
                  onClick?.();
                }
              }
            : undefined
        }
      >
        {image && (
          <div className="aspect-video overflow-hidden">
            <img
              src={image}
              alt={imageAlt}
              className="h-full w-full object-cover transition-transform duration-300 hover:scale-105"
              loading="lazy"
            />
          </div>
        )}
        <div className="p-5">
          {title && (
            <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
              {title}
            </h3>
          )}
          {description && (
            <p className="mt-2 text-sm text-gray-600 dark:text-gray-400">
              {description}
            </p>
          )}
          {children}
        </div>
        {footer && (
          <div className="border-t border-gray-100 px-5 py-3 dark:border-gray-700">
            {footer}
          </div>
        )}
      </Component>
    </motion.div>
  );
}

export type { CardProps as CardType };
