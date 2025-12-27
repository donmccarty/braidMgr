// =============================================================================
// Indicator Utilities Tests
// =============================================================================

import { describe, it, expect } from "vitest"
import {
  indicatorConfig,
  getIndicatorConfig,
  getIndicatorVariant,
  getIndicatorSeverity,
  sortByIndicatorSeverity,
  groupByIndicator,
} from "./indicators"
import type { Indicator } from "@/types"

// =============================================================================
// indicatorConfig Tests
// =============================================================================

describe("indicatorConfig", () => {
  it("has all 10 indicator types", () => {
    const indicators = Object.keys(indicatorConfig)
    expect(indicators).toHaveLength(10)
  })

  it("has Beyond Deadline as highest severity", () => {
    expect(indicatorConfig["Beyond Deadline!!!"].severity).toBe(10)
  })

  it("has Completed as lowest severity", () => {
    expect(indicatorConfig["Completed"].severity).toBe(1)
  })

  it("has destructive variant for critical indicators", () => {
    expect(indicatorConfig["Beyond Deadline!!!"].variant).toBe("destructive")
    expect(indicatorConfig["Late Finish!!"].variant).toBe("destructive")
    expect(indicatorConfig["Late Start!!"].variant).toBe("destructive")
  })

  it("has warning variant for attention indicators", () => {
    expect(indicatorConfig["Trending Late!"].variant).toBe("warning")
    expect(indicatorConfig["Finishing Soon!"].variant).toBe("warning")
  })

  it("has success variant for completed recently", () => {
    expect(indicatorConfig["Completed Recently"].variant).toBe("success")
  })
})

// =============================================================================
// getIndicatorConfig Tests
// =============================================================================

describe("getIndicatorConfig", () => {
  it("returns config for valid indicator", () => {
    const config = getIndicatorConfig("In Progress")
    expect(config.variant).toBe("default")
    expect(config.severity).toBe(4)
    expect(config.description).toBe("Work is ongoing")
  })

  it("returns fallback config for null indicator", () => {
    const config = getIndicatorConfig(null)
    expect(config.variant).toBe("muted")
    expect(config.severity).toBe(0)
    expect(config.description).toBe("No status")
  })

  it("returns correct config for each indicator type", () => {
    const indicators: Indicator[] = [
      "Beyond Deadline!!!",
      "Late Finish!!",
      "Late Start!!",
      "Trending Late!",
      "Finishing Soon!",
      "Starting Soon!",
      "In Progress",
      "Not Started",
      "Completed Recently",
      "Completed",
    ]

    for (const indicator of indicators) {
      const config = getIndicatorConfig(indicator)
      expect(config).toBeDefined()
      expect(config.variant).toBeDefined()
      expect(config.severity).toBeGreaterThan(0)
    }
  })
})

// =============================================================================
// getIndicatorVariant Tests
// =============================================================================

describe("getIndicatorVariant", () => {
  it("returns variant for valid indicator", () => {
    expect(getIndicatorVariant("Beyond Deadline!!!")).toBe("destructive")
    expect(getIndicatorVariant("In Progress")).toBe("default")
    expect(getIndicatorVariant("Completed")).toBe("muted")
  })

  it("returns muted for null indicator", () => {
    expect(getIndicatorVariant(null)).toBe("muted")
  })
})

// =============================================================================
// getIndicatorSeverity Tests
// =============================================================================

describe("getIndicatorSeverity", () => {
  it("returns severity for valid indicator", () => {
    expect(getIndicatorSeverity("Beyond Deadline!!!")).toBe(10)
    expect(getIndicatorSeverity("In Progress")).toBe(4)
    expect(getIndicatorSeverity("Completed")).toBe(1)
  })

  it("returns 0 for null indicator", () => {
    expect(getIndicatorSeverity(null)).toBe(0)
  })

  it("returns decreasing severities in order", () => {
    const severities = [
      getIndicatorSeverity("Beyond Deadline!!!"),
      getIndicatorSeverity("Late Finish!!"),
      getIndicatorSeverity("Late Start!!"),
      getIndicatorSeverity("Trending Late!"),
      getIndicatorSeverity("Finishing Soon!"),
      getIndicatorSeverity("Starting Soon!"),
      getIndicatorSeverity("In Progress"),
      getIndicatorSeverity("Not Started"),
      getIndicatorSeverity("Completed Recently"),
      getIndicatorSeverity("Completed"),
    ]

    for (let i = 1; i < severities.length; i++) {
      expect(severities[i]!).toBeLessThan(severities[i - 1]!)
    }
  })
})

// =============================================================================
// sortByIndicatorSeverity Tests
// =============================================================================

describe("sortByIndicatorSeverity", () => {
  it("sorts items by severity (highest first)", () => {
    const items = [
      { id: 1, indicator: "Completed" as Indicator },
      { id: 2, indicator: "Beyond Deadline!!!" as Indicator },
      { id: 3, indicator: "In Progress" as Indicator },
    ]

    const sorted = sortByIndicatorSeverity(items)

    expect(sorted[0]!.indicator).toBe("Beyond Deadline!!!")
    expect(sorted[1]!.indicator).toBe("In Progress")
    expect(sorted[2]!.indicator).toBe("Completed")
  })

  it("handles null indicators", () => {
    const items = [
      { id: 1, indicator: null },
      { id: 2, indicator: "In Progress" as Indicator },
    ]

    const sorted = sortByIndicatorSeverity(items)

    expect(sorted[0]!.indicator).toBe("In Progress")
    expect(sorted[1]!.indicator).toBe(null)
  })

  it("does not mutate original array", () => {
    const items = [
      { id: 1, indicator: "Completed" as Indicator },
      { id: 2, indicator: "Beyond Deadline!!!" as Indicator },
    ]
    const original = [...items]

    sortByIndicatorSeverity(items)

    expect(items).toEqual(original)
  })

  it("returns empty array for empty input", () => {
    const sorted = sortByIndicatorSeverity([])
    expect(sorted).toEqual([])
  })
})

// =============================================================================
// groupByIndicator Tests
// =============================================================================

describe("groupByIndicator", () => {
  it("groups items by indicator", () => {
    const items = [
      { id: 1, indicator: "In Progress" as Indicator },
      { id: 2, indicator: "Completed" as Indicator },
      { id: 3, indicator: "In Progress" as Indicator },
    ]

    const groups = groupByIndicator(items)

    expect(groups.get("In Progress")).toHaveLength(2)
    expect(groups.get("Completed")).toHaveLength(1)
  })

  it("handles null indicators", () => {
    const items = [
      { id: 1, indicator: null },
      { id: 2, indicator: null },
    ]

    const groups = groupByIndicator(items)

    expect(groups.get(null)).toHaveLength(2)
  })

  it("returns empty map for empty input", () => {
    const groups = groupByIndicator([])
    expect(groups.size).toBe(0)
  })

  it("preserves item order within groups", () => {
    const items = [
      { id: 1, indicator: "In Progress" as Indicator },
      { id: 2, indicator: "In Progress" as Indicator },
      { id: 3, indicator: "In Progress" as Indicator },
    ]

    const groups = groupByIndicator(items)
    const inProgress = groups.get("In Progress")!

    expect(inProgress[0]!.id).toBe(1)
    expect(inProgress[1]!.id).toBe(2)
    expect(inProgress[2]!.id).toBe(3)
  })
})
