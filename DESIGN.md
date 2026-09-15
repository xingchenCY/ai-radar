# Design

## Overview

AI Radar uses a restrained editorial product interface: off-white neutral surface, ink typography, compact chrome, and one electric blue accent for active state and primary affordance. The design should feel premium because the hierarchy is disciplined, not because it is decorative.

## Theme

Light theme only for this interview build. The product behaves like a daily reading desk, not a cinematic landing page.

## Tokens

Use semantic CSS variables.

```css
--bg: #f6f7f5;
--surface: #ffffff;
--surface-subtle: #eef2ff;
--ink: #101413;
--muted: #65706c;
--line: #d9dfdc;
--accent: #315bff;
--accent-ink: #1737b9;
--warning: #9b6230;
```

## Typography

Use the existing system stack: Helvetica Neue, PingFang SC, Avenir Next, Arial, sans-serif. Keep headings sans-serif, compact, and balanced. Avoid oversized display typography in controls and data rows.

## Layout

Top navigation is a single-line 64-72px editorial toolbar. The first viewport should show the brand, today summary, and the beginning of the highlighted content.

The hero is compact and task-oriented. The right side is a signal ledger, not a metric card cluster.

Today's highlights use an asymmetric editorial block: one main story plus two supporting stories when available.

Filters become a sticky reading toolbar below the highlights. Search is visually dominant; date, source, language, and topic controls are pill groups.

The main feed uses list rows with strong titles, quiet metadata, and an explicit original-link affordance.

## Components

Buttons use one shape vocabulary: 10px primary buttons, full-pill filter chips, 12-16px featured story surfaces. Do not place cards inside cards.

Loading states use skeletons matching final content shape. Empty and error states remain inline and do not replace the whole page when cached data exists.

## Motion

Use 150-220ms transitions for hover, active, and filter state changes. Motion communicates feedback only. Disable movement under reduced motion.

## Responsive Rules

At widths below 768px, the hero, highlights, and feed collapse to one column. Filter chips scroll horizontally without causing page overflow. Article summaries clamp to four lines with optional expansion in implementation.

## Preflight

No em dashes in visible copy. No purple glow, no gradient text, no decorative status dots except one real data status indicator. Keep article links safe with external-link attributes.
