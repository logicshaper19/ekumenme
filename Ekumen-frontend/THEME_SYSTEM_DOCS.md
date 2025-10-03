# Ekumen Theme System Documentation

## Overview

The Ekumen theme system provides runtime theming with light and dark modes. It combines CSS variables for visual rendering with Zustand for state management, offering excellent performance and developer experience.

## Architecture

### Hybrid Approach

The theme system uses a hybrid architecture:

1. **CSS Variables** - Handle actual styling and visual updates
2. **Zustand Store** - Manages React state and persistence
3. **Feature Flag** - Allows enabling/disabling theme switching

**Benefits:**
- ⚡ **Performance**: CSS variables update instantly without React re-renders
- 🎨 **Smooth Transitions**: 0.2s ease transitions for professional UX
- 💾 **Persistence**: Automatic localStorage sync
- 🌓 **System Preference**: Respects `prefers-color-scheme` on first visit
- 🔒 **Type Safety**: Full TypeScript support
- 🎯 **Simple API**: Easy-to-use `useTheme()` hook

## Quick Start

### 1. Enable Theme Switching

Add to your `.env` file:

```bash
VITE_THEME_SWITCH_ENABLED=true
```

### 2. Use the Theme Hook

```tsx
import { useTheme } from '@hooks/useTheme';

function MyComponent() {
  const { theme, setTheme, toggleTheme, isEnabled } = useTheme();
  
  return (
    <div>
      <p>Current theme: {theme}</p>
      <button onClick={toggleTheme}>Toggle Theme</button>
    </div>
  );
}
```

### 3. Use Theme-Aware Classes

```tsx
// Semantic classes (recommended for theme support)
<div className="bg-card text-primary border-subtle">
  <h1 className="text-primary">Hello World</h1>
  <p className="text-secondary">This adapts to the theme</p>
</div>

// Or use CSS variables directly
<div style={{ backgroundColor: 'var(--bg-card)', color: 'var(--text-primary)' }}>
  Content
</div>
```

## File Structure

```
Ekumen-frontend/
├── src/
│   ├── config/
│   │   └── theme.config.ts          # Centralized theme configuration
│   ├── stores/
│   │   └── themeStore.ts            # Zustand state management
│   ├── hooks/
│   │   └── useTheme.ts              # Convenience hook
│   ├── components/
│   │   └── ThemeToggle/
│   │       ├── ThemeToggle.tsx      # Theme toggle button
│   │       └── index.ts
│   └── styles/
│       ├── theme.css                # CSS variables for light/dark
│       └── theme-utilities.css      # Semantic utility classes
├── .env                             # Environment variables
└── index.html                       # FOUC prevention script
```

## Configuration

### Theme Config (`src/config/theme.config.ts`)

```typescript
export type Theme = 'light' | 'dark';

export interface ThemeConfig {
  enabled: boolean;        // Feature flag
  defaultTheme: Theme;     // Default theme
  storageKey: string;      // localStorage key
  dataAttribute: string;   // HTML data attribute
}
```

### Environment Variables

```bash
# Enable/disable theme switching
VITE_THEME_SWITCH_ENABLED=true  # or 'false'
```

## CSS Variables

### Available Variables

#### Text Colors
- `--text-primary` - Primary text
- `--text-secondary` - Secondary text
- `--text-muted` - Muted/disabled text
- `--text-inverse` - Inverse text (for dark backgrounds)
- `--text-link` - Link color
- `--text-link-hover` - Link hover color

#### Backgrounds
- `--bg-app` - App background
- `--bg-card` - Card backgrounds
- `--bg-card-hover` - Card hover state
- `--bg-elevated` - Elevated surfaces (modals, dropdowns)
- `--bg-input` - Input backgrounds
- `--bg-input-disabled` - Disabled inputs

#### Borders
- `--border-subtle` - Subtle borders
- `--border-default` - Default borders
- `--border-strong` - Strong borders
- `--border-focus` - Focus rings

#### Brand Colors
- `--brand-50` through `--brand-900` - Brand color scale
- `--brand-500` - Primary brand color

#### Feedback Colors
- `--success-*` - Success states
- `--warning-*` - Warning states
- `--error-*` - Error states
- `--info-*` - Info states

#### Shadows
- `--shadow-sm` - Small shadow
- `--shadow-card` - Card shadow
- `--shadow-card-hover` - Card hover shadow
- `--shadow-lg` - Large shadow

#### Transitions
- `--transition-theme` - Standard theme transition (0.2s)
- `--transition-theme-fast` - Fast transition (0.15s)
- `--transition-theme-slow` - Slow transition (0.3s)

## Semantic Utility Classes

### Text Classes
```css
.text-primary      /* Primary text color */
.text-secondary    /* Secondary text color */
.text-muted        /* Muted text color */
.text-link         /* Link color with hover */
```

### Background Classes
```css
.bg-app            /* App background */
.bg-card           /* Card background */
.bg-card-hover     /* Card hover background */
.bg-elevated       /* Elevated surface */
```

### Border Classes
```css
.border-subtle     /* Subtle border */
.border-default    /* Default border */
.border-strong     /* Strong border */
```

### Component Classes
```css
.btn-primary       /* Primary button */
.btn-secondary     /* Secondary button */
.btn-ghost         /* Ghost button */
.card              /* Card container */
.card-interactive  /* Interactive card */
.input             /* Input field */
```

## API Reference

### `useTheme()` Hook

```typescript
interface UseThemeReturn {
  theme: Theme;                    // Current theme ('light' | 'dark')
  setTheme: (theme: Theme) => void; // Set theme
  toggleTheme: () => void;         // Toggle between themes
  isEnabled: boolean;              // Whether theme switching is enabled
}
```

**Example:**
```tsx
const { theme, setTheme, toggleTheme, isEnabled } = useTheme();

// Check current theme
if (theme === 'dark') {
  console.log('Dark mode is active');
}

// Change theme
setTheme('dark');

// Toggle theme
toggleTheme();

// Check if enabled
if (isEnabled) {
  // Show theme toggle button
}
```

### `useThemeStore` (Advanced)

Direct access to the Zustand store:

```typescript
import { useThemeStore } from '@/stores/themeStore';

// Get specific values
const theme = useThemeStore(state => state.theme);
const setTheme = useThemeStore(state => state.setTheme);

// Get all state
const { theme, setTheme, toggleTheme, initTheme, isEnabled } = useThemeStore();
```

## Migration Guide

### Migrating Existing Components

**Before:**
```tsx
<div className="bg-white text-gray-900 border-gray-200">
  <h1 className="text-gray-900">Title</h1>
  <p className="text-gray-600">Description</p>
</div>
```

**After:**
```tsx
<div className="bg-card text-primary border-subtle">
  <h1 className="text-primary">Title</h1>
  <p className="text-secondary">Description</p>
</div>
```

### Priority Order

1. **High Priority** - User-facing pages (Assistant, Chat)
2. **Medium Priority** - Layout components (Header, Sidebar)
3. **Low Priority** - Admin pages, settings

## Accessibility

### WCAG AA Compliance

All theme colors meet WCAG AA standards:
- **Body text**: Minimum 4.5:1 contrast ratio
- **Large text**: Minimum 3:1 contrast ratio
- **UI components**: Minimum 3:1 contrast ratio

### System Preferences

The theme system respects user system preferences:
- Detects `prefers-color-scheme: dark`
- Auto-applies on first visit
- User choice overrides system preference

### Reduced Motion

Transitions respect `prefers-reduced-motion`:
```css
@media (prefers-reduced-motion: reduce) {
  * {
    transition: none !important;
  }
}
```

## Troubleshooting

### Theme Not Changing

1. Check feature flag: `VITE_THEME_SWITCH_ENABLED=true`
2. Clear localStorage: `localStorage.clear()`
3. Check browser console for errors

### FOUC (Flash of Unstyled Content)

The inline script in `index.html` prevents FOUC by setting the theme before React mounts. If you see a flash:

1. Ensure the script is in `<head>` before other scripts
2. Check that `STORAGE_KEY` matches in both script and config

### Styles Not Updating

1. Ensure CSS files are imported in `index.css`
2. Check Tailwind content paths include `./src/styles/**/*.css`
3. Rebuild: `npm run dev` (restart dev server)

## Performance

### Bundle Size Impact

- **CSS Variables**: ~5KB (gzipped)
- **Zustand Store**: ~1KB (already included)
- **Theme Toggle Component**: ~0.5KB
- **Total**: ~6.5KB additional

### Runtime Performance

- **Theme Switch**: <16ms (instant)
- **CSS Variable Updates**: 0ms (browser-native)
- **React Re-renders**: 0 (only Zustand subscribers)

## Future Enhancements

Potential future additions:

1. **Brand Presets** - Partner/white-label themes
2. **Custom Colors** - User-defined color schemes
3. **High Contrast Mode** - Enhanced accessibility
4. **Auto Theme** - Time-based theme switching
5. **Theme Preview** - Live preview before applying

## Support

For questions or issues:
1. Check this documentation
2. Review `THEME_IMPLEMENTATION_TRACKER.md`
3. Check component examples in `/src/components`
4. Contact the frontend team

