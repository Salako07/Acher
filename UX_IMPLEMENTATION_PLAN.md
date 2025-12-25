# UX SPECIFICATION IMPLEMENTATION PLAN

**Date:** December 25, 2025
**Engineer:** Senior Software Engineer
**Estimated Time:** 4-6 hours (P0 + P1 fixes)

---

## EXECUTION STRATEGY

### Phase 1: P0 — Blocking Issues (2-3 hours)
Lock the UI during PENDING state to enforce obligation-first behavior.

### Phase 2: P1 — High Priority (1-2 hours)
Remove distractions and add rule visibility.

### Phase 3: P2 — Medium Priority (1 hour)
Polish dashboard and participant list.

---

## PHASE 1: P0 BLOCKING FIXES

### Task 1.1: Implement Locked State Logic in Project Page

**File:** `frontend/src/pages/Project.tsx`

**Requirements:**
- Detect user's check-in status: `PENDING`, `DONE`, or `MISSED`
- Conditionally render content based on status
- Lock all content below check-in button when `PENDING`

**Implementation:**

```tsx
// Add state detection helper
const isLocked = canCheckin; // true when PENDING

// Modify return JSX structure:
return (
  <div className="min-h-screen bg-neutral-50">
    <div className="max-w-2xl mx-auto px-6 py-12">
      {/* Back link - always visible */}
      <div className="mb-8">
        <Link to="/dashboard">← Projects</Link>
      </div>

      {/* LOCKED STATE: Show only title + countdown + CTA */}
      {isLocked ? (
        <>
          <h1 className="text-3xl font-medium text-neutral-900 mb-2">Today</h1>
          <Countdown resetHour={project.daily_reset_hour} timezone={project.timezone} />

          <div className="mt-12">
            <button
              onClick={handleCheckin}
              disabled={checkinLoading}
              className="w-full px-6 py-4 bg-neutral-900 text-white text-lg font-semibold"
            >
              {checkinLoading ? 'Marking...' : 'Mark done today'}
            </button>
            {error && <p className="mt-3 text-sm text-neutral-600">{error}</p>}
          </div>
        </>
      ) : (
        /* UNLOCKED STATE: Show full project context */
        <>
          <h1 className="text-3xl font-medium text-neutral-900 mb-2">{project.name}</h1>
          {project.description && <p className="text-neutral-600">{project.description}</p>}

          <div className="mb-12 mt-8">
            <p className="text-sm text-neutral-500 mb-2">Today</p>
            {userStatus?.status === CheckinStatus.DONE && (
              <div className="px-6 py-4 border border-neutral-300 bg-white text-center">
                <p className="text-neutral-900">Checked in at {formatTime(userStatus.checked_at)}</p>
              </div>
            )}
            {userStatus?.status === CheckinStatus.MISSED && (
              <div className="px-6 py-4 border border-neutral-300 bg-white text-center">
                <p className="font-bold text-neutral-900">MISSED</p>
                <p className="text-sm text-neutral-600 mt-1">
                  Check-in window closed at {formatResetTime(project.daily_reset_hour)}
                </p>
              </div>
            )}
          </div>

          {/* Participant list - only visible after check-in */}
          <ParticipantSection project={project} user={user} />

          {/* Analytics link - de-emphasized, bottom */}
          <div className="mt-12">
            <Link
              to={`/projects/${project.id}/analytics`}
              className="text-xs text-neutral-500 hover:text-neutral-700"
            >
              View analytics
            </Link>
          </div>
        </>
      )}
    </div>
  </div>
);
```

**Estimated Time:** 1 hour

---

### Task 1.2: Create Countdown Timer Component

**File:** `frontend/src/components/Countdown.tsx` (new file)

**Requirements:**
- Calculate time remaining until reset hour in project timezone
- Display: "Check-in closes in 3h 42m"
- Update every minute
- Increase contrast when <1 hour remains

**Implementation:**

```tsx
import { useState, useEffect } from 'react';

interface CountdownProps {
  resetHour: number;
  timezone: string;
}

export function Countdown({ resetHour, timezone }: CountdownProps) {
  const [timeRemaining, setTimeRemaining] = useState<string>('');
  const [isUrgent, setIsUrgent] = useState(false);

  useEffect(() => {
    const calculateRemaining = () => {
      const now = new Date();

      // Get current time in project timezone
      // Note: This is simplified - you may need a library like date-fns-tz
      const currentHour = now.getHours();

      let hoursUntilReset = resetHour - currentHour;
      if (hoursUntilReset < 0) hoursUntilReset += 24;

      const minutesUntilReset = 60 - now.getMinutes();

      const totalMinutes = hoursUntilReset * 60 + minutesUntilReset;
      const hours = Math.floor(totalMinutes / 60);
      const minutes = totalMinutes % 60;

      setIsUrgent(totalMinutes < 60);

      if (hours > 0) {
        setTimeRemaining(`${hours}h ${minutes}m`);
      } else {
        setTimeRemaining(`${minutes}m`);
      }
    };

    calculateRemaining();
    const interval = setInterval(calculateRemaining, 60000); // Update every minute

    return () => clearInterval(interval);
  }, [resetHour]);

  return (
    <p className={`text-sm mb-6 ${isUrgent ? 'text-neutral-900 font-medium' : 'text-neutral-600'}`}>
      Check-in closes in {timeRemaining}
    </p>
  );
}
```

**Estimated Time:** 45 minutes

---

### Task 1.3: Fix MISSED Status Visual Hierarchy

**File:** `frontend/src/pages/Project.tsx`

**Requirements:**
- MISSED text should be bold and high contrast
- Must interrupt scanning

**Changes:**

In participant list (line ~150):
```tsx
{status.status === CheckinStatus.MISSED && (
  <span className="font-bold text-neutral-900">MISSED</span>  // Changed from text-neutral-500
)}
```

In user status display (line ~113):
```tsx
{userStatus?.status === CheckinStatus.MISSED && (
  <div className="px-6 py-4 border-2 border-neutral-900 bg-white text-center">  // Added border-2
    <p className="font-bold text-neutral-900 text-lg">MISSED</p>
    <p className="text-sm text-neutral-600 mt-1">
      Check-in window closed at {formatResetTime(project.daily_reset_hour)}
    </p>
  </div>
)}
```

**Estimated Time:** 15 minutes

---

## PHASE 2: P1 HIGH PRIORITY FIXES

### Task 2.1: Hide Dashboard Actions When User Has Pending Check-ins

**File:** `frontend/src/pages/Dashboard.tsx`

**Requirements:**
- Show "New project" button only when `projects.length === 0`
- Hide "Join project" button when user has PENDING check-ins
- Don't allow distraction from obligation

**Implementation:**

```tsx
// Add helper to detect pending check-ins
const hasPendingCheckins = projects.some(p => p.user_status_today === null);

// Modify button rendering:
{projects.length === 0 ? (
  <div className="text-center py-12">
    <button
      onClick={() => setShowCreate(true)}
      className="px-6 py-3 bg-neutral-900 text-white font-medium hover:bg-neutral-800"
    >
      Create Project
    </button>
  </div>
) : (
  <>
    {!hasPendingCheckins && (
      <div className="mb-6 flex gap-4">
        <button onClick={() => setShowCreate(!showCreate)}>New project</button>
        <button onClick={() => setShowJoin(!showJoin)}>Join project</button>
      </div>
    )}

    {/* Show forms only if no pending check-ins */}
    {!hasPendingCheckins && showCreate && <CreateProjectForm ... />}
    {!hasPendingCheckins && showJoin && <JoinProjectForm ... />}

    {/* Project list */}
    <div className="space-y-1">
      {projects.map(...)}
    </div>
  </>
)}
```

**Estimated Time:** 30 minutes

---

### Task 2.2: Add Rule Visibility Bar

**File:** `frontend/src/App.tsx` or create `frontend/src/components/RuleBar.tsx`

**Requirements:**
- Always visible at top or bottom
- Show project-specific rules
- Neutral styling, no icons

**Implementation:**

Create `frontend/src/components/RuleBar.tsx`:

```tsx
interface RuleBarProps {
  resetHour?: number;
}

export function RuleBar({ resetHour = 0 }: RuleBarProps) {
  const formatHour = (hour: number) => {
    if (hour === 0) return 'midnight';
    if (hour === 12) return 'noon';
    if (hour < 12) return `${hour}:00 AM`;
    return `${hour - 12}:00 PM`;
  };

  return (
    <div className="fixed bottom-0 left-0 right-0 bg-neutral-100 border-t border-neutral-300 px-6 py-2">
      <p className="text-xs text-neutral-700 text-center">
        One check-in per day · Actions are final · Check-in closes at {formatHour(resetHour)}
      </p>
    </div>
  );
}
```

Add to `Project.tsx`:
```tsx
import { RuleBar } from '../components/RuleBar';

// Inside return, at the end:
<RuleBar resetHour={project.daily_reset_hour} />
```

**Estimated Time:** 30 minutes

---

### Task 2.3: Hide Analytics Link During PENDING State

**Already covered in Task 1.1** - analytics link only shown in unlocked state.

---

### Task 2.4: Hide Project Description During PENDING State

**Already covered in Task 1.1** - description only shown in unlocked state.

---

## PHASE 3: P2 MEDIUM PRIORITY FIXES

### Task 3.1: Add "X Missed Today" Summary

**File:** `frontend/src/pages/Project.tsx`

**Requirements:**
- Count MISSED statuses in participant list
- Display above participant list if any exist

**Implementation:**

```tsx
// In ParticipantSection or main Project component:
const missedCount = project.today_statuses.filter(
  s => s.status === CheckinStatus.MISSED
).length;

// Display above participant list:
{missedCount > 0 && (
  <div className="mb-2 px-4 py-2 bg-neutral-100 border border-neutral-300">
    <p className="text-sm font-medium text-neutral-900">
      {missedCount} missed today
    </p>
  </div>
)}
```

**Estimated Time:** 15 minutes

---

### Task 3.2: Remove Member Count from Dashboard Cards

**File:** `frontend/src/pages/Dashboard.tsx`

**Requirements:**
- Remove member count from project cards
- Show only project name and status

**Changes:**

Remove lines 92-93:
```tsx
// DELETE THIS:
<p className="text-sm text-neutral-500 mt-1">{project.member_count} members</p>
```

**Estimated Time:** 5 minutes

---

## FILE CREATION CHECKLIST

### New Files to Create:
- [ ] `frontend/src/components/Countdown.tsx`
- [ ] `frontend/src/components/RuleBar.tsx`

### Files to Modify:
- [ ] `frontend/src/pages/Project.tsx` (major refactor)
- [ ] `frontend/src/pages/Dashboard.tsx` (moderate changes)
- [ ] `frontend/src/App.tsx` (add RuleBar if not component-level)

---

## TESTING CHECKLIST

### Phase 1 Testing:
- [ ] PENDING state locks all content below check-in button
- [ ] Countdown timer displays correctly
- [ ] Countdown increases contrast when <1 hour remains
- [ ] MISSED status is bold and high-contrast
- [ ] Check-in button works in locked state

### Phase 2 Testing:
- [ ] Dashboard hides "New project" when projects exist
- [ ] Dashboard hides "Join project" when pending check-ins exist
- [ ] Rule bar displays correct reset time
- [ ] Analytics link only visible after check-in

### Phase 3 Testing:
- [ ] Missed count summary displays when applicable
- [ ] Member count removed from dashboard cards

---

## DEPLOYMENT STEPS

1. **Backend:** No changes required
2. **Frontend:**
   - Create new components
   - Modify existing pages
   - Test all states (PENDING, DONE, MISSED)
3. **Build:** `npm run build`
4. **Deploy:** Standard frontend deployment

---

## ROLLBACK PLAN

If issues arise:
1. Revert `Project.tsx` to previous version
2. Remove new component files
3. Revert `Dashboard.tsx` changes

Git commands:
```bash
git checkout HEAD~1 frontend/src/pages/Project.tsx
git checkout HEAD~1 frontend/src/pages/Dashboard.tsx
```

---

## SUCCESS CRITERIA

✓ User with PENDING check-in sees ONLY:
  - "Today" title
  - Countdown timer
  - "Mark done today" button
  - Back link

✓ User with DONE check-in sees:
  - Full project context
  - Participant list
  - Analytics link (de-emphasized)

✓ User with MISSED check-in sees:
  - Bold, high-contrast "MISSED" message
  - Full project context
  - Participant list with MISSED emphasis

✓ Dashboard shows obligations first, exploration never

---

## TIME ESTIMATE SUMMARY

| Phase | Tasks | Time |
|-------|-------|------|
| P0 | Locked state + countdown + MISSED styling | 2-3 hours |
| P1 | Dashboard hiding + rule bar | 1-2 hours |
| P2 | Polish | 1 hour |
| **Total** | | **4-6 hours** |

---

## NEXT STEPS

1. Review this plan with stakeholders
2. Create feature branch: `git checkout -b ux-spec-enforcement`
3. Begin Phase 1: Task 1.1 (Locked state logic)
4. Test each task incrementally
5. Commit after each phase
6. Deploy after P0+P1 completion

---

## NOTES

- The visual design (minimal, neutral, Apple-caliber) is already correct
- This implementation focuses on **behavioral enforcement**, not aesthetics
- All changes are frontend-only, no backend modifications required
- Changes are backward-compatible with existing API

---

## APPROVAL

Ready to begin implementation?

- [ ] Plan reviewed
- [ ] Time estimate acceptable
- [ ] Ready to proceed

**Approval Date:** _________________
**Approved By:** _________________
