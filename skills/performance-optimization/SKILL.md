---
name: performance-optimization
version: 1.0.0
author: addyosmani (ported to Agent Zero by a0_agent_skills)
description: >-
  Optimizes application performance. Use when performance requirements exist,
  when you suspect performance regressions, or when Core Web Vitals or load
  times need improvement. Use when profiling reveals bottlenecks that need fixing.
tags:
  - performance
  - optimization
  - core-web-vitals
  - profiling
  - caching
trigger_patterns:
  - performance-optimization
  - too slow
  - optimize performance
  - core web vitals
  - n+1 query
  - improve load time
  - profile the app
  - performance regression
  - bundle size
  - slow api response
  - improve response time
  - api response time
  - api performance
  - optimize api performance
  - response time optimization
  - api too slow
  - reduce latency
  - response time this api
  - improve the response time
---

# Performance Optimization

> **Supporting files:** This skill has a companion performance checklist. Use
> `text_editor:read` with the full path shown in the file tree when this skill
> is loaded to open `performance-checklist.md` (sibling to this SKILL.md).

## Overview

Measure before optimizing. Performance work without measurement is guessing — and guessing leads to premature optimization that adds complexity without improving what matters. Profile first, identify the actual bottleneck, fix it, measure again. Optimize only what measurements prove matters.

## When to Use

- Performance requirements exist in the spec (load time budgets, response time SLAs)
- Users or monitoring report slow behavior
- Core Web Vitals scores are below thresholds
- You suspect a change introduced a regression
- Building features that handle large datasets or high traffic

**When NOT to use:** Don't optimize before you have evidence of a problem. Premature optimization adds complexity that costs more than the performance it gains.

## Core Web Vitals Targets

| Metric | Good | Needs Improvement | Poor |
|--------|------|-------------------|------|
| **LCP** (Largest Contentful Paint) | ≤ 2.5s | ≤ 4.0s | > 4.0s |
| **INP** (Interaction to Next Paint) | ≤ 200ms | ≤ 500ms | > 500ms |
| **CLS** (Cumulative Layout Shift) | ≤ 0.1 | ≤ 0.25 | > 0.25 |

## The Optimization Workflow

```
1. MEASURE  → Establish baseline with real data
2. IDENTIFY → Find the actual bottleneck (not assumed)
3. FIX      → Address the specific bottleneck
4. VERIFY   → Measure again, confirm improvement
5. GUARD    → Add monitoring or tests to prevent regression
```

### Step 1: Measure

**Frontend — using Agent Zero's `browser` tool:**
```
1. browser: open → navigate to the page
2. browser: evaluate → inject web-vitals library or read performance entries
3. browser: screenshot → capture visual state
4. Use browser: action=content to read console output for perf logs
```

For synthetic Lighthouse-style profiling:
```bash
# Run via code_execution_tool
npx lighthouse https://localhost:3000 --output=json --quiet
```

**Backend:**
```bash
# Response time logging via code_execution_tool
# Add timing to server code
console.time('db-query');
const result = await db.query(...);
console.timeEnd('db-query');
```

### Where to Start Measuring

```
What is slow?
├── First page load
│   ├── Large bundle? → Measure bundle size, check code splitting
│   ├── Slow server response? → Measure TTFB in network tab
│   │   ├── DNS long? → Add dns-prefetch / preconnect
│   │   └── Waiting (server) long? → Profile backend, check queries
│   └── Render-blocking resources? → Check network waterfall
├── Interaction feels sluggish
│   ├── UI freezes on click? → Profile main thread, long tasks (>50ms)
│   └── Animation jank? → Check layout thrashing, forced reflows
├── Page after navigation
│   ├── Data loading? → Measure API response times, check waterfalls
│   └── Client rendering? → Profile component render time, N+1 fetches
└── Backend / API
    ├── Single endpoint slow? → Profile database queries, check indexes
    ├── All endpoints slow? → Check connection pool, memory, CPU
    └── Intermittent slowness? → Check for lock contention, GC pauses
```

### Step 2: Identify the Bottleneck

**Frontend:**

| Symptom | Likely Cause | Investigation |
|---------|-------------|---------------|
| Slow LCP | Large images, render-blocking resources | Check network waterfall, image sizes |
| High CLS | Images without dimensions, late-loading content | Check layout shift attribution |
| Poor INP | Heavy JavaScript on main thread | Check long tasks in Performance trace |
| Slow initial load | Large bundle, many network requests | Check bundle size, code splitting |

**Backend:**

| Symptom | Likely Cause | Investigation |
|---------|-------------|---------------|
| Slow API responses | N+1 queries, missing indexes | Check database query log |
| Memory growth | Leaked references, unbounded caches | Heap snapshot analysis |
| CPU spikes | Synchronous heavy computation | CPU profiling |
| High latency | Missing caching, redundant computation | Trace requests through the stack |

### Step 3: Fix Common Anti-Patterns

#### N+1 Queries (Backend)

```typescript
// BAD: N+1 — one query per task for the owner
const tasks = await db.tasks.findMany();
for (const task of tasks) {
  task.owner = await db.users.findUnique({ where: { id: task.ownerId } });
}

// GOOD: Single query with join/include
const tasks = await db.tasks.findMany({
  include: { owner: true },
});
```

#### Unbounded Data Fetching

```typescript
// BAD: Fetching all records
const allTasks = await db.tasks.findMany();

// GOOD: Paginated with limits
const tasks = await db.tasks.findMany({
  take: 20,
  skip: (page - 1) * 20,
  orderBy: { createdAt: 'desc' },
});
```

#### Missing Image Optimization (Frontend)

```html
<!-- BAD: No dimensions, no format optimization -->
<img src="/hero.jpg" />

<!-- GOOD: Responsive image with proper dimensions -->
<picture>
  <source
    srcset="/hero-800.avif 800w, /hero-1200.avif 1200w"
    sizes="(max-width: 1200px) 100vw, 1200px"
    type="image/avif"
  />
  <img
    src="/hero.jpg"
    width="1200"
    height="600"
    fetchpriority="high"
    alt="Hero image description"
  />
</picture>

<!-- Below-the-fold: lazy loaded -->
<img
  src="/content.webp"
  width="800"
  height="400"
  loading="lazy"
  decoding="async"
  alt="Content image"
/>
```

#### Unnecessary Re-renders (React)

```tsx
// BAD: Creates new object on every render
function TaskList() {
  return <TaskFilters options={{ sortBy: 'date', order: 'desc' }} />;
}

// GOOD: Stable reference
const DEFAULT_OPTIONS = { sortBy: 'date', order: 'desc' } as const;
function TaskList() {
  return <TaskFilters options={DEFAULT_OPTIONS} />;
}

// Use React.memo for expensive components
const TaskItem = React.memo(function TaskItem({ task }: Props) {
  return <div>{/* expensive render */}</div>;
});

// Use useMemo for expensive computations
function TaskStats({ tasks }: Props) {
  const stats = useMemo(() => calculateStats(tasks), [tasks]);
  return <div>{stats.completed} / {stats.total}</div>;
}
```

#### Large Bundle Size

```typescript
// GOOD: Dynamic import for heavy, rarely-used features
const ChartLibrary = lazy(() => import('./ChartLibrary'));

// GOOD: Route-level code splitting
const SettingsPage = lazy(() => import('./pages/Settings'));

function App() {
  return (
    <Suspense fallback={<Spinner />}>
      <SettingsPage />
    </Suspense>
  );
}
```

#### Missing Caching (Backend)

```typescript
const CACHE_TTL = 5 * 60 * 1000; // 5 minutes
let cachedConfig: AppConfig | null = null;
let cacheExpiry = 0;

async function getAppConfig(): Promise<AppConfig> {
  if (cachedConfig && Date.now() < cacheExpiry) {
    return cachedConfig;
  }
  cachedConfig = await db.config.findFirst();
  cacheExpiry = Date.now() + CACHE_TTL;
  return cachedConfig;
}

// HTTP caching headers for static assets
app.use('/static', express.static('public', {
  maxAge: '1y',
  immutable: true,
}));
```

## Performance Budget

Set budgets and enforce them via `code_execution_tool`:

```
JavaScript bundle: < 200KB gzipped (initial load)
CSS: < 50KB gzipped
Images: < 200KB per image (above the fold)
Fonts: < 100KB total
API response time: < 200ms (p95)
Time to Interactive: < 3.5s on 4G
Lighthouse Performance score: ≥ 90
```

**Enforce in CI:**
```bash
# Bundle size check
npx bundlesize --config bundlesize.config.json

# Lighthouse CI
npx lhci autorun
```

## See Also

For detailed performance checklists, optimization commands, and anti-pattern reference, use
`text_editor:read` on the `performance-checklist.md` file in this skill's directory
(path shown in the file tree when this skill is loaded).

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "We'll optimize later" | Performance debt compounds. Fix obvious anti-patterns now, defer micro-optimizations. |
| "It's fast on my machine" | Your machine isn't the user's. Profile on representative hardware and networks. |
| "This optimization is obvious" | If you didn't measure, you don't know. Profile first. |
| "Users won't notice 100ms" | Research shows 100ms delays impact conversion rates. Users notice more than you think. |
| "The framework handles performance" | Frameworks prevent some issues but can't fix N+1 queries or oversized bundles. |

## Red Flags

- Optimization without profiling data to justify it
- N+1 query patterns in data fetching
- List endpoints without pagination
- Images without dimensions, lazy loading, or responsive sizes
- Bundle size growing without review
- No performance monitoring in production
- `React.memo` and `useMemo` everywhere (overusing is as bad as underusing)

## Verification

After any performance-related change:

- [ ] Before and after measurements exist (specific numbers)
- [ ] The specific bottleneck is identified and addressed
- [ ] Core Web Vitals are within "Good" thresholds
- [ ] Bundle size hasn't increased significantly
- [ ] No N+1 queries in new data fetching code
- [ ] Performance budget passes in CI (if configured)
- [ ] Existing tests still pass (optimization didn't break behavior)
