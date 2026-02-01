# Frontend Development Guidelines — Trading Dashboard

## 🎨 Design Philosophy

**Context:** Professional trading platform for algorithmic traders
**Audience:** Retail traders, algo developers, day traders
**Tone:** Professional, data-dense, confidence-inspiring (handling real money)

### Aesthetic Direction

**PRIMARY VISION: Financial Terminal Meets Modern Design**
- Dark mode as default (reduce eye strain for hours of monitoring)
- Data-first layouts (charts and numbers take priority)
- Subtle luxury (refined, not flashy - this handles money)
- Clear visual hierarchy (critical info ≠ secondary info)
- Real-time responsiveness (no lag in data updates)

**Color Strategy:**
- Background: Deep charcoal (#0F1419, #1a1d23) with subtle gradients
- Success: Green variants (#00C896, #22C55E) for profits/buy
- Danger: Red variants (#FF4444, #EF4444) for losses/sell
- Accent: Electric blue/cyan (#00D9FF, #06B6D4) for highlights
- Neutrals: Gray scales (#374151 → #E5E7EB) for non-critical data
- **AVOID:** Generic purple gradients, pastel colors, overly bright palettes

**Typography:**
- Display/Headers: **JetBrains Mono** or **IBM Plex Mono** (monospaced for data alignment)
- Body Text: **Inter** is acceptable for trading UIs (widely used in fintech)
- Data/Numbers: Monospaced fonts REQUIRED (align decimal points)
- Font Sizes: 12-14px for data grids, 16-18px for forms, 24-32px for headers
- **AVOID:** Decorative fonts, cursive, overly condensed fonts for numbers

### Layout Patterns

**Dashboard Structure:**
```
┌──────────────────────────────────────────────┐
│ Top Bar: Portfolio value, P&L, Alerts       │
├──────────────┬───────────────────────────────┤
│              │                               │
│  Sidebar:    │  Main Canvas:                │
│  - Watchlist │  - Price Charts (TradingView) │
│  - Positions │  - Order Entry Form           │
│  - Alerts    │  - Trade History Table        │
│  - Strategies│  - Performance Metrics        │
│              │                               │
└──────────────┴───────────────────────────────┘
```

**Grid Systems:**
- Use CSS Grid for dashboard layouts (precise control)
- Flexbox for component internals
- 12-column grid for responsive breakpoints
- Generous use of `gap` for breathing room

**Spacing:**
- Base unit: 4px or 8px scale
- Dense data grids: 8px padding
- Cards/panels: 16-24px padding
- Section spacing: 32-48px gaps

### Component Guidelines

**Cards/Panels:**
- Background: rgba(255,255,255,0.05) with backdrop-blur
- Border: 1px solid rgba(255,255,255,0.1)
- Border-radius: 8-12px (subtle rounding)
- Box-shadow: Subtle elevation (0 4px 24px rgba(0,0,0,0.4))
- Hover states: Slight glow or border color change

**Buttons:**
- Primary: Solid color with hover glow
- Secondary: Outline style with fill on hover
- Danger: Red with confirmation states
- Size: 36-44px height (accessible click targets)
- Icon + text combinations preferred

**Forms:**
- Input backgrounds: rgba(255,255,255,0.08)
- Focus states: Border glow with accent color
- Labels: Small caps or bold weight
- Validation: Inline error messages with icons
- Auto-formatting: Currency (₹), percentages (%), quantities

**Data Tables:**
- Striped rows (alternating subtle background)
- Sticky headers on scroll
- Sortable columns (click headers)
- Conditional formatting (green/red for P&L)
- Fixed-width columns for numbers (alignment)
- Pagination or virtual scrolling for large datasets

**Charts:**
- Primary: TradingView Lightweight Charts library
- Candlestick charts for OHLC data
- Line charts for equity curves
- Bar charts for volume
- Color coding: Green = up, Red = down
- Interactive crosshair and tooltips

### Motion & Interaction

**Animation Strategy:**
- Page load: Staggered fade-in (0.1s delay between cards)
- Data updates: Subtle flash effect (highlight new values)
- Transitions: 150-300ms easing (cubic-bezier)
- Hover states: Scale(1.02) or shadow increase
- Loading states: Skeleton screens or shimmer effects

**Real-time Updates:**
- WebSocket connections for live price data
- Optimistic UI updates (show immediately, rollback on error)
- Toast notifications for order fills, alerts
- Pulsing indicators for active positions

**CSS-only animations preferred:**
```css
@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.card {
  animation: fadeInUp 0.4s ease-out;
  animation-delay: calc(var(--index) * 0.1s);
}
```

### Accessibility Requirements

- WCAG 2.1 AA compliance minimum
- Keyboard navigation (tab order logical)
- Focus indicators visible (outline or ring)
- Color contrast ratios: 4.5:1 for text
- Screen reader labels for icons
- `aria-live` regions for real-time price updates

### Visual Details & Polish

**Backgrounds:**
- Subtle gradient overlays (top-to-bottom dark fade)
- Noise texture (1-2% opacity) for depth
- Radial gradients behind hero sections

**Borders & Dividers:**
- 1px solid with low opacity
- Gradient borders for premium features
- Decorative corner accents on cards

**Icons:**
- Heroicons or Lucide React (consistent style)
- 20-24px size for inline icons
- Duotone style for emphasis

**Shadows:**
- Layered shadows for depth
- Example: `0 1px 3px rgba(0,0,0,0.2), 0 4px 12px rgba(0,0,0,0.3)`

**Custom Cursors:**
- Crosshair on charts (trading precision)
- Pointer on interactive elements

### Technical Requirements

**Framework:** React 18+ with TypeScript
**State Management:** Zustand or Redux Toolkit
**Styling:** Tailwind CSS + CSS Modules for complex components
**Charts:** TradingView Lightweight Charts
**Tables:** TanStack Table (React Table v8)
**Forms:** React Hook Form + Zod validation
**Icons:** Lucide React
**Animations:** Framer Motion (for complex sequences)
**Build:** Vite

**Performance:**
- Code splitting by route
- Lazy load heavy components (charts)
- Memoize expensive calculations (useMemo, React.memo)
- Virtual scrolling for 100+ row tables
- Debounce search inputs (300ms)
- Throttle scroll events

### Integration with Backend

**API Communication:**
```typescript
// Use auth_manager.py token
const token = await fetch('/api/auth/token').then(r => r.json());

// All requests include Bearer token
const headers = {
  'Authorization': `Bearer ${token}`,
  'Content-Type': 'application/json'
};

// Error handling with retry from error_handler.py
fetch(url, { headers })
  .catch(err => {
    // Check if 429 rate limit, display user message
  });
```

**Database Queries:**
- Backend API endpoints query SQLite tables
- Frontend never directly accesses database
- Real-time updates via WebSocket or polling

**Key Endpoints to Build:**
- GET `/api/portfolio` - Current positions, P&L
- GET `/api/watchlist` - User's tracked symbols
- GET `/api/signals` - Trading signals from strategy_runner
- POST `/api/orders` - Place paper/live orders (via paper_trading.py)
- GET `/api/performance` - Metrics from performance_analytics.py
- GET `/api/alerts` - Active alerts from alert_system.py

### Component Priorities

**Phase 1: Core Dashboard** (Build First)
1. **Portfolio Summary Card** - Total value, day P&L, positions count
2. **Watchlist Panel** - Live prices, % change, add/remove symbols
3. **Chart Component** - Candlestick chart with TradingView
4. **Positions Table** - Open positions with unrealized P&L
5. **Top Nav** - User menu, notifications, account value

**Phase 2: Trading Interface**
6. **Order Entry Form** - Buy/sell, quantity, limit/market
7. **Order Book Display** - Bid/ask levels
8. **Trade History Table** - Past executions

**Phase 3: Analytics & Tools**
9. **Performance Dashboard** - Equity curve, Sharpe ratio, win rate
10. **Strategy Monitor** - Active strategies, signals generated
11. **Alert Manager** - Create/edit/delete alerts
12. **Settings Panel** - Risk limits, API config, preferences

### Design Anti-Patterns to AVOID

❌ **Generic Saas Landing Page Look:**
- Purple gradients everywhere
- Bento grid layouts (unless truly functional)
- "Hero section with CTA button" mindset
- Testimonials or marketing fluff

❌ **Poor Trading UX:**
- Small click targets for order buttons (dangerous!)
- Unclear buy/sell color coding
- Hidden risk parameters
- Delayed price updates
- Confusing P&L calculations (net vs gross)

❌ **Visual Clutter:**
- Too many animations competing for attention
- Overly decorative elements near data
- Inconsistent spacing/alignment
- Low contrast text on busy backgrounds

### Quality Checklist

Before completing a component:
- [ ] Dark mode works perfectly (default state)
- [ ] Numbers are monospaced and aligned
- [ ] Colors follow green=up, red=down convention
- [ ] Loading states implemented (skeleton or spinner)
- [ ] Error states handled gracefully
- [ ] Responsive down to 768px width minimum
- [ ] Keyboard navigation works
- [ ] No layout shift on data load
- [ ] API integration points clearly defined
- [ ] Performance: <100ms interactions, <1s page load

### Inspiration Sources

**Trading Platforms:**
- TradingView (charting excellence)
- Webull (modern dark UI)
- Interactive Brokers TWS (data density done right)
- Zerodha Kite (Indian market leader)

**Design Systems:**
- Stripe Dashboard (clean data layouts)
- Linear App (polished dark mode)
- Vercel Dashboard (professional SaaS UI)

**DO NOT copy directly - adapt principles to trading context**

---

## 🚀 Getting Started

When building a component:
1. **Understand the data source** (which backend script/table?)
2. **Sketch the layout** (where does it fit in dashboard?)
3. **Choose the aesthetic details** (colors, fonts, spacing)
4. **Implement with real data** (no lorem ipsum, use actual API)
5. **Add micro-interactions** (hover, focus, loading states)
6. **Test with edge cases** (empty states, errors, long numbers)
7. **Optimize performance** (memoization, lazy loading)

Remember: This platform handles real money. **Clarity and trust > cleverness**.
