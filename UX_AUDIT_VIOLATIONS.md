# UX SPECIFICATION AUDIT — VIOLATIONS & GAPS

**Date:** December 25, 2025
**Auditor:** Senior Software Engineer
**Status:** CRITICAL VIOLATIONS FOUND

---

## EXECUTIVE SUMMARY

The current frontend implementation **violates the core UX principle** in multiple critical areas:

> "At any moment, the user must know exactly one thing: What does the system expect of me right now?"

**Severity:** The current UX allows browsing, exploration, and distraction BEFORE obligation fulfillment.

**Impact:** Users can avoid accountability by navigating away from their pending check-in.

---

## CRITICAL VIOLATIONS

### ❌ VIOLATION 1: Dashboard Shows "New project" + "Join project" Buttons When Projects Exist

**Spec:** STATE B — User HAS projects
```
What the user sees:
- Vertical list of project cards
- Each card shows ONLY: Project name, Today's status
- Behavior: Entire card is clickable, No secondary buttons
```

**Current Implementation:** `Dashboard.tsx:61-74`
```tsx
<div className="mb-6 flex gap-4">
  <button onClick={() => setShowCreate(!showCreate)}>New project</button>
  <button onClick={() => setShowJoin(!showJoin)}>Join project</button>
</div>
```

**Violation:**
- Two action buttons compete with the primary obligation (projects list)
- User can create/join projects instead of fulfilling today's check-in
- Violates "Single Primary Action per screen"

**Required Fix:**
- Hide these buttons when user has pending check-ins
- Only show "Create Project" button when projects.length === 0
- Join functionality should be accessible elsewhere (settings/profile)

---

### ❌ VIOLATION 2: Project Page Shows ALL Content Regardless of Check-in Status

**Spec:** STATE 1 — TODAY = PENDING (THE LOCKED STATE)
```
ABOVE-THE-FOLD UI (ONLY THESE):
- Title: "Today"
- Subtext: "Check-in closes in 3h 42m"
- Primary CTA: Mark Done Today

No participant list.
No analytics.
No project description.
No navigation distractions.
```

**Current Implementation:** `Project.tsx:71-169`
```tsx
return (
  <div>
    <h1>{project.name}</h1>          // ✓ OK
    <p>{project.description}</p>      // ❌ VIOLATION
    <button>Mark done today</button>  // ✓ OK
    <h2>Participants</h2>             // ❌ VIOLATION
    {/* participant list */}          // ❌ VIOLATION
    <Link to="analytics">...</Link>   // ❌ VIOLATION
  </div>
);
```

**Violation:**
- Project description visible during PENDING state
- Participant list visible during PENDING state
- Analytics link visible during PENDING state
- User can browse instead of deciding

**Required Fix:**
- Conditional rendering based on `userStatus.status`
- When PENDING: Lock everything below the check-in button
- Only unlock participant list/analytics AFTER check-in

---

### ❌ VIOLATION 3: No Countdown Timer to Reset Hour

**Spec:** RULE BAR (ALWAYS VISIBLE)
```
Text: "One check-in per day. Actions are final. Check-in closes at 00:00."

COUNTDOWN LOGIC:
- Visible timer to reset
- When <1 hour remains: Slight increase in contrast
```

**Current Implementation:** None

**Violation:**
- No countdown visible anywhere
- User has no sense of urgency
- No awareness of when the day ends

**Required Fix:**
- Add global countdown component
- Calculate time until `daily_reset_hour`
- Display: "Check-in closes in 3h 42m"
- Increase contrast when <1 hour remains

---

### ❌ VIOLATION 4: MISSED Status Not Visually Distinct Enough

**Spec:** STATUS HIERARCHY (TYPOGRAPHIC)
```
DONE → normal weight
PENDING → light gray
MISSED → bold, high contrast

MISSED must interrupt scanning
```

**Current Implementation:** `Project.tsx:150-151`
```tsx
{status.status === CheckinStatus.MISSED && (
  <span className="text-neutral-500">Missed</span>  // ❌ Same weight as DONE
)}
```

**Violation:**
- MISSED is `text-neutral-500` (light gray) - not high contrast
- No bold weight
- Does not interrupt scanning

**Required Fix:**
```tsx
{status.status === CheckinStatus.MISSED && (
  <span className="font-bold text-neutral-900">MISSED</span>
)}
```

---

### ❌ VIOLATION 5: Participant List Shows MISSED Without Summary

**Spec:** LIST STRUCTURE
```
If any MISSED exists:
- Show "X missed today" at top
```

**Current Implementation:** `Project.tsx:137-159`

Participant list shows individual statuses but no summary count.

**Violation:**
- User must scan entire list to understand failure rate
- No immediate "X missed today" callout

**Required Fix:**
- Calculate missed count
- Display above participant list: "2 missed today" (if any)

---

### ❌ VIOLATION 6: Analytics Link Too Prominent

**Spec:** ANALYTICS (REFLECTION MODE)
```
ACCESS RULE:
- Analytics are never primary
- Always secondary
- De-emphasized link
```

**Current Implementation:** `Project.tsx:162-169`
```tsx
<div className="flex gap-4">
  <Link to={`/projects/${project.id}/analytics`}>
    View analytics
  </Link>
</div>
```

**Violation:**
- Analytics link visible even during PENDING state
- Competes with check-in obligation
- Enables browsing/distraction

**Required Fix:**
- Only show analytics link AFTER check-in (DONE or MISSED)
- Make it smaller, less prominent
- Move to bottom of page

---

### ❌ VIOLATION 7: Project Description Shown During PENDING State

**Spec:** STATE 1 — LOCKED STATE
```
No project description.
```

**Current Implementation:** `Project.tsx:84-86`
```tsx
{project.description && (
  <p className="text-neutral-600">{project.description}</p>
)}
```

**Violation:**
- Description is context, not obligation
- Creates distraction during PENDING state

**Required Fix:**
- Only show description when status is DONE or MISSED
- Hide during PENDING

---

### ❌ VIOLATION 8: Member Count Shown on Dashboard Cards

**Spec:** STATE B — Dashboard Cards
```
Each card shows ONLY:
- Project name
- Today's status (DONE / PENDING / MISSED)
```

**Current Implementation:** `Dashboard.tsx:92`
```tsx
<p className="text-sm text-neutral-500 mt-1">
  {project.member_count} members
</p>
```

**Violation:**
- Member count is not obligation-related
- Adds visual noise
- Violates "ONLY project name and status"

**Required Fix:**
- Remove member count from dashboard cards
- If needed, show in project detail page (after check-in)

---

## MODERATE VIOLATIONS

### ⚠️ VIOLATION 9: No Rule Visibility

**Spec:** RULE BAR (ALWAYS VISIBLE)
```
Text: "One check-in per day. Actions are final. Check-in closes at 00:00."
Behavior: Neutral styling, No icons, No warnings
```

**Current Implementation:** None

**Impact:** User doesn't know the rules at a glance

**Required Fix:**
- Add fixed top bar or footer with rule text
- Adjust reset time dynamically based on project

---

### ⚠️ VIOLATION 10: Error Messages Too Friendly

**Spec:** FINAL UX TRUTH
```
If the UX ever feels friendly, expressive, or flexible — it's wrong.
```

**Current Implementation:** `Dashboard.tsx:128`
```tsx
setError('Failed to create project');  // Neutral ✓
```

**Status:** Acceptable but could be more direct

---

## DESIGN VIOLATIONS

### ⚠️ VIOLATION 11: Navigation Competes with Obligation

**Spec:** NAVIGATION RULES (GLOBAL)
```
One back action only
No menus
No tabs
No footer

Navigation must never compete with obligation.
```

**Current Implementation:** `Project.tsx:75-77`
```tsx
<Link to="/dashboard">← Projects</Link>
```

**Status:** Acceptable — single back link is within spec

---

## MISSING FEATURES

### 🔴 MISSING 1: Countdown Timer Component

**Required:** Global countdown to reset hour

**Status:** Not implemented

---

### 🔴 MISSING 2: Locked/Unlocked State Logic

**Required:** Conditional rendering based on check-in status

**Status:** Partially implemented but not enforced

---

### 🔴 MISSING 3: MISSED Visual Hierarchy

**Required:** Bold, high-contrast MISSED text

**Status:** Using light gray instead

---

## SEVERITY SUMMARY

| Severity | Count | Issues |
|----------|-------|--------|
| 🔴 CRITICAL | 8 | Violations 1-8 |
| ⚠️ MODERATE | 3 | Violations 9-11 |
| 🔵 MISSING | 3 | Missing features |

**Total Issues:** 14

---

## PRIORITY FIXES (RANKED)

### P0 — BLOCKING (Must fix before any user testing)

1. **Violation 2:** Lock project page content during PENDING state
2. **Violation 3:** Add countdown timer to reset hour
3. **Violation 4:** Make MISSED status visually distinct (bold + high contrast)

### P1 — HIGH (Breaks core UX principle)

4. **Violation 1:** Hide "New project" / "Join project" when user has pending check-ins
5. **Violation 6:** Hide analytics link during PENDING state
6. **Violation 7:** Hide project description during PENDING state
7. **Violation 9:** Add rule visibility bar

### P2 — MEDIUM (Violates spec but not core principle)

8. **Violation 5:** Add "X missed today" summary
9. **Violation 8:** Remove member count from dashboard cards

### P3 — LOW (Polish)

10. **Violation 10:** Review error message tone

---

## RECOMMENDED IMPLEMENTATION ORDER

1. **Phase 1 (P0):** Locked state logic + countdown timer + MISSED styling
2. **Phase 2 (P1):** Hide distractions during PENDING + rule bar
3. **Phase 3 (P2):** Dashboard polish + missed summary
4. **Phase 4 (P3):** Final polish

---

## CODE IMPACT ESTIMATE

| File | Lines to Modify | Complexity |
|------|----------------|------------|
| `Project.tsx` | ~100 | High (state logic) |
| `Dashboard.tsx` | ~40 | Medium |
| `types.ts` | ~10 | Low (add countdown) |
| `App.tsx` or layout | ~30 | Medium (rule bar) |

**Total estimated changes:** ~180 lines

---

## CONCLUSION

The current implementation has the **visual aesthetic** correct (minimal, neutral, Apple-caliber) but **fails the behavioral contract** specified in the UX flow.

**Core Issue:** Users can browse and explore BEFORE fulfilling their obligation.

**Fix:** Implement state-based conditional rendering that locks all context/exploration until check-in is completed.

**Timeline Estimate:** 4-6 hours for P0+P1 fixes
