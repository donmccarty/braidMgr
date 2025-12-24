# Sequence 6: PWA

*Parent: [USER_STORIES.md](../USER_STORIES.md)*

Progressive Web App capabilities.

**Depends on**: Sequences 4, 5
**Stories**: 3
**Priority**: MVP

---

## S6-001: Service Worker

**Story**: As a user, I want the app to work offline, so that I can access data without internet.

**Acceptance Criteria**:
- Service worker caches app shell
- Previously viewed data available offline
- Offline indicator visible
- Sync when connection restored

**Traces**: WEB-001

---

## S6-002: App Manifest

**Story**: As a user, I want to install the app, so that I can launch it like a native app.

**Acceptance Criteria**:
- manifest.json with name, icons, colors
- Install prompt appears on supported browsers
- App launches in standalone mode
- Icons display correctly on all platforms

**Traces**: WEB-001

---

## S6-003: Responsive Design

**Story**: As a user, I want the app to work on any device, so that I can use it on mobile.

**Acceptance Criteria**:
- Desktop, tablet, mobile layouts work
- Navigation adapts (sidebar collapses)
- Touch-friendly controls on mobile
- Tables scroll horizontally on narrow screens

**Traces**: WEB-002
