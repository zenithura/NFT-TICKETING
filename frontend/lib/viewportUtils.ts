// File header: Viewport utilities for preventing UI clipping.
// Provides functions to calculate safe positioning for floating elements.

// Purpose: Calculate safe position for dropdown to prevent viewport clipping.
// Params: triggerRect (DOMRect) - Trigger element bounding rect, dropdownWidth (number) - Dropdown width, dropdownHeight (number) - Dropdown height, gap (number) - Gap between trigger and dropdown.
// Returns: Object with top, left, right, and side properties.
// Side effects: None (pure function).
export const calculateDropdownPosition = (
  triggerRect: DOMRect,
  dropdownWidth: number,
  dropdownHeight: number,
  gap: number = 8
): { top: number; left?: number; right?: number; bottom?: number; side: 'top' | 'bottom' | 'left' | 'right' } => {
  const viewportWidth = window.innerWidth;
  const viewportHeight = window.innerHeight;
  const scrollY = window.scrollY;
  const scrollX = window.scrollX;

  // Calculate available space
  const spaceBelow = viewportHeight - (triggerRect.bottom - scrollY);
  const spaceAbove = triggerRect.top - scrollY;
  const spaceRight = viewportWidth - (triggerRect.right - scrollX);
  const spaceLeft = triggerRect.left - scrollX;

  // Determine vertical position (prefer below, fallback to above)
  let top: number;
  let bottom: number | undefined;
  let side: 'top' | 'bottom' | 'left' | 'right' = 'bottom';

  if (spaceBelow >= dropdownHeight + gap || spaceBelow >= spaceAbove) {
    // Position below
    top = triggerRect.bottom + gap;
    side = 'bottom';
  } else {
    // Position above
    bottom = viewportHeight - (triggerRect.top - scrollY) + gap;
    side = 'top';
  }

  // Determine horizontal position (prefer right alignment, adjust if needed)
  let left: number | undefined;
  let right: number | undefined;

  if (triggerRect.right - scrollX + dropdownWidth <= viewportWidth) {
    // Enough space on right, align to left edge of trigger
    left = triggerRect.left - scrollX;
  } else if (spaceRight >= dropdownWidth) {
    // Align to right edge of viewport
    right = 0;
  } else if (spaceLeft >= dropdownWidth) {
    // Align to left edge of viewport
    left = 0;
  } else {
    // Center if neither side has enough space
    left = (viewportWidth - dropdownWidth) / 2;
  }

  return { top, left, right, bottom, side };
};

// Purpose: Check if element would be clipped by viewport.
// Params: elementRect (DOMRect) - Element bounding rect.
// Returns: Boolean indicating if element is clipped.
// Side effects: None (pure function).
export const isElementClipped = (elementRect: DOMRect): boolean => {
  const viewportWidth = window.innerWidth;
  const viewportHeight = window.innerHeight;
  const scrollX = window.scrollX;
  const scrollY = window.scrollY;

  return (
    elementRect.left - scrollX < 0 ||
    elementRect.right - scrollX > viewportWidth ||
    elementRect.top - scrollY < 0 ||
    elementRect.bottom - scrollY > viewportHeight
  );
};

// Purpose: Clamp value between min and max.
// Params: value (number) - Value to clamp, min (number) - Minimum value, max (number) - Maximum value.
// Returns: Clamped value.
// Side effects: None (pure function).
export const clamp = (value: number, min: number, max: number): number => {
  return Math.min(Math.max(value, min), max);
};

