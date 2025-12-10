# BRAID Manager Qt App - Remaining Work

**Last Updated:** 2025-12-10

## Completed This Session

- [x] Dashboard stats click-through to filtered All Items view
- [x] Edit Task modal dialog (`src/ui_qt/dialogs.py`)
- [x] All Items table row double-click → Edit modal
- [x] Timeline row double-click → Edit modal
- [x] Timeline axis header date markers (week ticks, day numbers, "Today" with date)

## Remaining from Plan

### Phase 1: Color Consolidation (Partially Done)
- [ ] Remove duplicate `TYPE_COLORS` from `dashboard.py` (lines 24-30)
- [ ] Remove duplicate `TYPE_COLORS` from `timeline.py` (lines 18-26)
- [ ] Update both files to import colors from `styles.py`
- [ ] Unify warning color (`#ffc107` vs `#f39c12`)
- [ ] Unify active blue (`#0d6efd` vs `#3498db`)

### Phase 2: UI Consistency
- [ ] Standardize button sizes: Primary (14px), Secondary (12px)
- [ ] Standardize padding: 8px 16px for buttons, 4px 8px for pills
- [ ] Implement 8px spacing grid (8, 16, 24, 32)
- [ ] Consistent border-radius: 8px buttons, 4px pills

### Phase 3: Export Functions
- [ ] Add "Export YAML" button to sidebar
- [ ] Add "Export Snapshot" button (read-only HTML)
- [ ] Add "Client Snapshot" button (filtered export)
- [ ] Implement export logic in core module

### Phase 4: Edit Capability Enhancements
- [x] Item Detail view/modal (basic Edit dialog done)
- [ ] Create **Add Item** dialog
- [ ] Add "Add Item" button to sidebar
- [ ] Wire up new item creation to YAML

### Phase 5: Metric Verification
- [ ] Compare dashboard numbers with HTML version using same data
- [ ] Verify health score calculation matches
- [ ] Verify velocity calculation matches
- [ ] Test critical/warning/active counts match

## Feature Gaps (Qt vs HTML)

| Priority | Feature | Status |
|----------|---------|--------|
| HIGH | Global Search | Not started |
| HIGH | Item Detail View | Done (Edit dialog) |
| HIGH | Add/Edit Item | Edit done, Add not started |
| MEDIUM | Export YAML | Not started |
| MEDIUM | Snapshot Export | Not started |
| MEDIUM | Client Snapshot | Not started |
| MEDIUM | Per-column Filters | Not started |
| LOW | Presentation Mode | Not started |
| LOW | Cost Trend Chart | Not started |
| LOW | Resource Burn Chart | Not started |

## Files Modified This Session

- `src/ui_qt/views/dashboard.py` - StatCard click signals
- `src/ui_qt/views/items.py` - Signal, apply_filter(), double-click handler
- `src/ui_qt/views/timeline.py` - Click signals, date markers in axis header
- `src/ui_qt/dialogs.py` - NEW: EditItemDialog class
- `src/ui_qt/app.py` - Connected signals, _show_edit_dialog, _save_item

## Quick Start Tomorrow

```bash
cd raid_manager
.venv/bin/python -m src.ui_qt.app
```

Test the new features:
1. Click Dashboard stat cards → should navigate to filtered All Items
2. Double-click any row in All Items → Edit dialog opens
3. Double-click any row in Timeline → Edit dialog opens
4. Timeline header shows week tick marks with day numbers
