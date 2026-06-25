"use client";

// ... rest of the code
import { useEffect, useState, useRef } from "react";

export function useAdminCombo(onTrigger: () => void) {
  const [isChordActive, setIsChordActive] = useState(false);
  const activeKeys = useRef<Set<string>>(new Set());
  const inputSequence = useRef<string[]>([]);
  const timeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const TARGET_SEQUENCE = [
    "ArrowUp",
    "ArrowUp",
    "ArrowDown",
    "ArrowDown",
    "ArrowLeft",
    "ArrowRight",
  ];

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      activeKeys.current.add(e.key);

      if (
        activeKeys.current.has("ArrowUp") &&
        activeKeys.current.has("ArrowLeft") &&
        activeKeys.current.has("ArrowRight")
      ) {
        if (!isChordActive) {
          setIsChordActive(true);
          inputSequence.current = [];

          if (timeoutRef.current) clearTimeout(timeoutRef.current);
          timeoutRef.current = setTimeout(() => {
            setIsChordActive(false);
            inputSequence.current = [];
          }, 3000);
        }
      }

      if (isChordActive) {
        if (["ArrowUp", "ArrowDown", "ArrowLeft", "ArrowRight"].includes(e.key)) {
          e.preventDefault();
        }

        if (
          inputSequence.current.length === 0 ||
          inputSequence.current[inputSequence.current.length - 1] !== e.key ||
          activeKeys.current.size === 1
        ) {
          inputSequence.current.push(e.key);
        }

        const currentLength = inputSequence.current.length;
        if (currentLength >= TARGET_SEQUENCE.length) {
          const recentInputs = inputSequence.current.slice(-TARGET_SEQUENCE.length);
          const matches = recentInputs.every((val, index) => val === TARGET_SEQUENCE[index]);

          if (matches) {
            onTrigger();
            setIsChordActive(false);
            inputSequence.current = [];
            if (timeoutRef.current) clearTimeout(timeoutRef.current);
          }
        }
      }
    };

    const handleKeyUp = (e: KeyboardEvent) => {
      activeKeys.current.delete(e.key);
    };

    window.addEventListener("keydown", handleKeyDown);
    window.addEventListener("keyup", handleKeyUp);
    return () => {
      window.removeEventListener("keydown", handleKeyDown);
      window.removeEventListener("keyup", handleKeyUp);
    };
  }, [isChordActive, onTrigger]);

  return { isChordActive };
}
