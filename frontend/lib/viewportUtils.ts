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
  gap: number = 2  // Reduced gap from 8px to 2px to minimize flickering
): { top: number; left?: number; right?: number; bottom?: number; side: 'top' | 'bottom' | 'left' | 'right' } => {
  const viewportWidth = window.innerWidth;
  const viewportHeight = window.innerHeight;

  // getBoundingClientRect() already returns viewport-relative coordinates
  // For fixed positioning, we use these coordinates directly without scroll adjustments
  
  // Calculate available space (viewport-relative)
  const spaceBelow = viewportHeight - triggerRect.bottom;
  const spaceAbove = triggerRect.top;
  const spaceRight = viewportWidth - triggerRect.right;
  const spaceLeft = triggerRect.left;

  // Determine vertical position (prefer below, fallback to above)
  let top: number;
  let bottom: number | undefined;
  let side: 'top' | 'bottom' | 'left' | 'right' = 'bottom';

  if (spaceBelow >= dropdownHeight + gap || spaceBelow >= spaceAbove) {
    // Position below - use 0 gap to eliminate flickering (overlap handled via negative top offset in style)
    top = triggerRect.bottom;
    side = 'bottom';
  } else {
    // Position above
    bottom = viewportHeight - triggerRect.top;
    side = 'top';
  }

  // Determine horizontal position
  // For user menu on far right, prefer right-aligned dropdown
  let left: number | undefined;
  let right: number | undefined;

  // Check if dropdown would overflow on the right
  if (triggerRect.right + dropdownWidth > viewportWidth) {
    // Not enough space on right, align to right edge of trigger (right-align dropdown)
    right = viewportWidth - triggerRect.right;
  } else {
    // Enough space on right, align to left edge of trigger
    left = triggerRect.left;
  }

  // Ensure dropdown doesn't go off-screen on the left
  if (left !== undefined && left < 0) {
    right = viewportWidth - triggerRect.right;
    left = undefined;
  }

  // Final safety check: if dropdown would still overflow, use right alignment
  if (left !== undefined && left + dropdownWidth > viewportWidth) {
    right = Math.max(0, viewportWidth - triggerRect.right);
    left = undefined;
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

