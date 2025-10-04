# Ekumen Frontend – Theme Implementation Tracker

Owner: Frontend Team
Status: Draft (planning only)
Scope: Theming (light/dark + brand presets) for Ekumen Frontend and Design System

## 1) Goals
- Provide runtime theming without breaking existing UI
- Start with Light and Dark themes; allow future “brand” presets (e.g., partner colorways)
- Keep using our existing Tailwind + Design System; avoid heavy UI libraries
- No breaking changes to existing classes; introduce semantic theme utilities for gradual migration

## 2) Non‑Goals
- Rewriting all components at once
- Changing our design tokens structure in TypeScript (we’ll mirror them as CSS variables)
- Adding a new CSS framework

## 3) Current State (as of today)
- Tailwind configured in `Ekumen-frontend/tailwind.config.js` with an agricultural palette
- Design System tokens in `Ekumen-design-system/src/tokens` (colors/typography)
- Component styles use Tailwind utilities; no runtime theme switching; no `darkMode` set

## 4) Approach Summary
Prefer CSS variables for semantic tokens + a small Tailwind layer to expose semantic classes.
- Define CSS variables (e.g., `--color-primary-500`) for themeable values
- Provide theme scopes: `:root[data-theme="light"]` and `:root[data-theme="dark"]`
- Add a minimal utility stylesheet that maps semantic Tailwind-like classes to CSS variables
  - Example: `.text-primary { color: var(--text-primary); }`
- Add a simple Theme Switcher that toggles `data-theme` on `<html>` and persists in `localStorage`
- Keep existing hard-coded Tailwind colors working; migrate gradually to semantic classes

## 5) Rollout Plan (Phased)

### Phase 0 – Guardrails & Flag
- Add a feature toggle: `THEME_SWITCH_ENABLED` (env var) and fallbacks
- Default to `light` if user preference not set
- Create centralized theme configuration object

Deliverables:
- Config read helper and safe default
- `src/config/theme.config.ts` with typed constants:
  ```typescript
  // Add to your feature flag setup
  const THEME_CONFIG = {
    enabled: import.meta.env.VITE_THEME_SWITCH_ENABLED === 'true',
    defaultTheme: 'light' as const,
    storageKey: 'ekumen-theme',
    dataAttribute: 'data-theme'
  } as const;

  export type Theme = 'light' | 'dark';
  export default THEME_CONFIG;
  ```

### Phase 1 – CSS Variable Tokens
- Create `src/styles/theme.css` with semantic tokens:
  - Text: `--text-primary`, `--text-secondary`, `--text-muted`
  - Surfaces: `--bg-app`, `--bg-card`, `--border-subtle`
  - Brand: `--brand-50..900` (maps to our primary)
  - Feedback: `--success-*`, `--warning-*`, `--error-*`, `--info-*`
  - **Transitions**: `--transition-theme` for smooth theme switching
- Define two scopes: `:root[data-theme="light"]` and `:root[data-theme="dark"]`
- Map values using current palette for light; derive accessible dark values
- Add smooth transitions for theme changes:
  ```css
  :root {
    /* Transition tokens for smooth theme switching */
    --transition-theme: background-color 0.2s ease, border-color 0.2s ease, color 0.2s ease;
  }

  /* Apply smooth transitions to all elements */
  * {
    transition: var(--transition-theme);
  }
  ```

Deliverables:
- `theme.css` with variables for light/dark and transition tokens
- Accessibility note with contrast checks (WCAG AA for body text)

### Phase 2 – Tailwind + Utilities Bridge
- Add `src/styles/theme-utilities.css` with minimal semantic classes that reference variables:
  - Colors: `.text-primary`, `.bg-app`, `.border-subtle`, `.btn-primary` (composed via `@apply` and `var()`)
- Optionally enable `darkMode: ["class"]` and attach `.dark` to `<html>` OR continue with `data-theme` only
- Ensure Purge/Content paths include these new files
- Extend Tailwind config with transition utilities:
  ```js
  theme: {
    extend: {
      transitionProperty: {
        'theme': 'background-color, border-color, color',
      }
    }
  }
  ```

Deliverables:
- Utilities file loaded after Tailwind (via `src/index.css`)
- Verified build tree‑shaking keeps bundle lean
- Updated `tailwind.config.js` with theme transition utilities

### Phase 3 – Theme Switcher Component
- Add small toggle (header) that sets `data-theme` on `<html>`
- Persist in `localStorage` and read `prefers-color-scheme` on first visit
- Provide programmatic API: `setTheme('light'|'dark')`, `getTheme()`
- **Integrate with Zustand** for state management while keeping CSS variable approach:
  ```typescript
  // Combines CSS approach with Zustand state management
  export const useThemeStore = create<ThemeState>()(
    persist(
      (set, get) => ({
        theme: 'light',
        setTheme: (theme) => {
          document.documentElement.setAttribute('data-theme', theme);
          set({ theme });
        },
        toggleTheme: () => {
          const newTheme = get().theme === 'light' ? 'dark' : 'light';
          get().setTheme(newTheme);
        },
        initTheme: () => {
          const stored = localStorage.getItem(THEME_CONFIG.storageKey);
          const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
          const theme = stored || (prefersDark ? 'dark' : THEME_CONFIG.defaultTheme);
          get().setTheme(theme);
        }
      }),
      { name: THEME_CONFIG.storageKey }
    )
  );
  ```

Deliverables:
- `src/stores/themeStore.ts` with Zustand integration
- `useTheme` hook wrapper for convenience
- `<ThemeToggle />` component
- Documentation for usage

### Phase 4 – Incremental Migration
- Start with Assistant chat pages (highest traffic)
- Replace a small set of hard-coded utilities with semantic classes:
  - Backgrounds, text, cards, buttons
- Keep all existing Tailwind utility classes where not migrated

Deliverables:
- PR 1: Chat container + message bubbles
- PR 2: Layout header/footer + menus
- PR 3: Forms (login/register) and toasts

### Phase 5 – Accessibility & QA
- Contrast checks in dark mode
- Visual regression snapshots (Vitest + @testing-library + story-based screenshots optional)
- Manual checks on macOS/Windows high‑contrast and reduced motion

Deliverables:
- Checklist results in this document

### Phase 6 – Feature Flag Rollout
- Enable by default for dev/staging
- Controlled rollout in prod; add kill‑switch (force `light`)

Deliverables:
- Rollout note + monitoring plan

## 6) Risks & Mitigations
- FOUC on theme change
  - Mitigation: inline a tiny script in `index.html` to set `data-theme` before React mounts
- Purge removing semantic classes
  - Mitigation: ensure `content` in Tailwind config includes `src/styles/**/*.css`
- Contrast failures in dark theme
  - Mitigation: documented AA targets; run checks on key components

## 7) Acceptance Criteria
- Theme can be toggled at runtime without page reload
- Choice persists and respects `prefers-color-scheme` on first load
- Chat interface, header, buttons, cards adapt to theme
- No regressions in light theme compared to current UI

## 8) Affected/Added Files (planned)
- Add: `Ekumen-frontend/src/config/theme.config.ts` (centralized theme configuration)
- Add: `Ekumen-frontend/src/styles/theme.css` (CSS variables + transitions)
- Add: `Ekumen-frontend/src/styles/theme-utilities.css`
- Edit: `Ekumen-frontend/src/index.css` (import utilities)
- Edit: `Ekumen-frontend/index.html` (inline preference bootstrap)
- Add: `Ekumen-frontend/src/stores/themeStore.ts` (Zustand state management)
- Add: `Ekumen-frontend/src/hooks/useTheme.ts` (convenience hook)
- Add: `Ekumen-frontend/src/components/ThemeToggle.tsx`
- Edit: `Ekumen-frontend/tailwind.config.js` (transition utilities)
- Optional: set `darkMode` in `tailwind.config.js`

## 9) Testing Plan
- Unit: `themeStore` (initial preference, toggle, persistence, localStorage sync)
- Unit: `useTheme` hook wrapper
- Component: `<ThemeToggle />` renders and toggles attribute
- Visual spot checks in both themes for Assistant page, forms, toasts
- Transition smoothness testing (verify 0.2s ease transitions work correctly)
- System preference detection (`prefers-color-scheme`) testing

## 10) Timeline (rough)
- Phase 0–2: 1–2 days
- Phase 3: 0.5 day
- Phase 4: 1–2 days (incremental PRs)
- Phase 5: 0.5 day

## 11) Open Questions
- Do we need brand presets in v1 (e.g., partner themes)?
- Preference on `data-theme` vs `.dark` class? (plan assumes `data-theme`)
- Any constraints from design/branding on dark palette hues?

## 12) Implementation Enhancements

### Centralized Configuration (Phase 0)
Using a typed configuration object provides:
- Single source of truth for theme settings
- Type safety for theme values
- Easy feature flag management
- Consistent naming across the application

### Smooth Transitions (Phase 1)
CSS transition tokens provide:
- Professional user experience during theme switches
- Consistent animation timing across all themed elements
- Performance-optimized transitions (only animating necessary properties)
- Easy customization via CSS variables

### Zustand Integration (Phase 3)
Combining Zustand with CSS variables provides:
- **State Management**: Zustand handles React state and persistence
- **Visual Updates**: CSS variables handle actual styling
- **Best of Both**: React components can subscribe to theme changes while CSS handles rendering
- **Developer Experience**: Simple API with `useTheme()` hook
- **Persistence**: Automatic localStorage sync via Zustand persist middleware
- **System Preference**: Respects `prefers-color-scheme` on first visit

Benefits of this hybrid approach:
1. **Performance**: CSS variables update instantly without React re-renders
2. **Simplicity**: Components can use theme state without prop drilling
3. **Flexibility**: Easy to add theme-dependent logic in components
4. **Maintainability**: Clear separation between state (Zustand) and presentation (CSS)

## 13) Sign‑off & Next Steps
- Await product/design sign‑off on dark palette and semantic token names
- After approval, proceed with Phase 0–2 PRs under feature flag
- Consider A/B testing transition duration (0.2s vs 0.15s vs 0.3s) for optimal UX

