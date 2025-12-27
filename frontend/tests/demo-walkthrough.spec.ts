import { test, Page } from "@playwright/test";

/**
 * braidMgr - Comprehensive Demo Walkthrough
 *
 * Run with video recording:
 *   npx playwright test tests/demo-walkthrough.spec.ts --project=demo-recording
 *
 * Target duration: ~4-5 minutes
 *
 * BRAID = Budget, Risks, Actions, Issues, Decisions
 * Plus: Deliverables and Plan Items
 */

// =============================================================================
// NARRATION HELPER
// =============================================================================

async function showNarration(
  page: Page,
  title: string,
  subtitle?: string
): Promise<void> {
  await page.evaluate(
    ({ title, subtitle }) => {
      const existing = document.getElementById("demo-narration");
      if (existing) existing.remove();

      const container = document.createElement("div");
      container.id = "demo-narration";
      container.style.cssText = `
      position: fixed;
      bottom: 100px;
      left: 50%;
      transform: translateX(-50%);
      background: linear-gradient(135deg, rgba(15, 23, 42, 0.95), rgba(30, 41, 59, 0.95));
      color: white;
      padding: 24px 48px;
      border-radius: 16px;
      z-index: 999999;
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
      text-align: center;
      box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
      border: 1px solid rgba(255, 255, 255, 0.1);
      backdrop-filter: blur(10px);
      max-width: 800px;
      animation: fadeIn 0.4s ease-out;
    `;

      if (!document.getElementById("demo-narration-styles")) {
        const style = document.createElement("style");
        style.id = "demo-narration-styles";
        style.textContent = `
        @keyframes fadeIn {
          from { opacity: 0; transform: translateX(-50%) translateY(20px); }
          to { opacity: 1; transform: translateX(-50%) translateY(0); }
        }
      `;
        document.head.appendChild(style);
      }

      const titleEl = document.createElement("div");
      titleEl.style.cssText = `
      font-size: 28px;
      font-weight: 700;
      margin-bottom: ${subtitle ? "10px" : "0"};
      letter-spacing: -0.5px;
    `;
      titleEl.textContent = title;
      container.appendChild(titleEl);

      if (subtitle) {
        const subtitleEl = document.createElement("div");
        subtitleEl.style.cssText = `
        font-size: 18px;
        font-weight: 400;
        color: rgba(255, 255, 255, 0.85);
        line-height: 1.4;
      `;
        subtitleEl.textContent = subtitle;
        container.appendChild(subtitleEl);
      }

      document.body.appendChild(container);
    },
    { title, subtitle }
  );
}

async function hideNarration(page: Page): Promise<void> {
  await page.evaluate(() => {
    const existing = document.getElementById("demo-narration");
    if (existing) existing.remove();
    const callout = document.getElementById("demo-callout");
    if (callout) callout.remove();
  });
}

/**
 * Show a callout pointing at a specific element
 */
async function showCallout(
  page: Page,
  selector: string,
  title: string,
  subtitle?: string,
  position: "top" | "bottom" | "left" | "right" = "bottom"
): Promise<void> {
  await page.evaluate(
    ({ selector, title, subtitle, position }) => {
      // Remove existing
      const existing = document.getElementById("demo-callout");
      if (existing) existing.remove();
      const existingNarr = document.getElementById("demo-narration");
      if (existingNarr) existingNarr.remove();

      // Find target element
      const target = document.querySelector(selector);
      if (!target) return;

      const rect = target.getBoundingClientRect();

      // Create callout container
      const container = document.createElement("div");
      container.id = "demo-callout";
      container.style.cssText = `
        position: fixed;
        background: linear-gradient(135deg, rgba(15, 23, 42, 0.95), rgba(30, 41, 59, 0.95));
        color: white;
        padding: 20px 32px;
        border-radius: 12px;
        z-index: 999999;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
        border: 1px solid rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(10px);
        max-width: 400px;
        animation: fadeIn 0.3s ease-out;
      `;

      // Position based on target
      const margin = 16;
      switch (position) {
        case "top":
          container.style.bottom = `${window.innerHeight - rect.top + margin}px`;
          container.style.left = `${rect.left + rect.width / 2}px`;
          container.style.transform = "translateX(-50%)";
          break;
        case "bottom":
          container.style.top = `${rect.bottom + margin}px`;
          container.style.left = `${rect.left + rect.width / 2}px`;
          container.style.transform = "translateX(-50%)";
          break;
        case "left":
          container.style.top = `${rect.top + rect.height / 2}px`;
          container.style.right = `${window.innerWidth - rect.left + margin}px`;
          container.style.transform = "translateY(-50%)";
          break;
        case "right":
          container.style.top = `${rect.top + rect.height / 2}px`;
          container.style.left = `${rect.right + margin}px`;
          container.style.transform = "translateY(-50%)";
          break;
      }

      // Add highlight ring to target
      const highlight = document.createElement("div");
      highlight.id = "demo-highlight";
      highlight.style.cssText = `
        position: fixed;
        top: ${rect.top - 4}px;
        left: ${rect.left - 4}px;
        width: ${rect.width + 8}px;
        height: ${rect.height + 8}px;
        border: 3px solid #3b82f6;
        border-radius: 8px;
        z-index: 999998;
        pointer-events: none;
        animation: pulse 1.5s ease-in-out infinite;
      `;

      // Add pulse animation
      if (!document.getElementById("demo-callout-styles")) {
        const style = document.createElement("style");
        style.id = "demo-callout-styles";
        style.textContent = `
          @keyframes fadeIn {
            from { opacity: 0; transform: translateX(-50%) translateY(10px); }
            to { opacity: 1; transform: translateX(-50%) translateY(0); }
          }
          @keyframes pulse {
            0%, 100% { box-shadow: 0 0 0 0 rgba(59, 130, 246, 0.5); }
            50% { box-shadow: 0 0 0 8px rgba(59, 130, 246, 0); }
          }
        `;
        document.head.appendChild(style);
      }

      // Title
      const titleEl = document.createElement("div");
      titleEl.style.cssText = `
        font-size: 20px;
        font-weight: 700;
        margin-bottom: ${subtitle ? "8px" : "0"};
      `;
      titleEl.textContent = title;
      container.appendChild(titleEl);

      // Subtitle
      if (subtitle) {
        const subtitleEl = document.createElement("div");
        subtitleEl.style.cssText = `
          font-size: 15px;
          font-weight: 400;
          color: rgba(255, 255, 255, 0.85);
          line-height: 1.4;
        `;
        subtitleEl.textContent = subtitle;
        container.appendChild(subtitleEl);
      }

      document.body.appendChild(highlight);
      document.body.appendChild(container);
    },
    { selector, title, subtitle, position }
  );
}

async function hideCallout(page: Page): Promise<void> {
  await page.evaluate(() => {
    const callout = document.getElementById("demo-callout");
    if (callout) callout.remove();
    const highlight = document.getElementById("demo-highlight");
    if (highlight) highlight.remove();
  });
}

// =============================================================================
// COMPREHENSIVE DEMO
// =============================================================================

test.describe("braidMgr Demo Walkthrough", () => {
  test("Complete demo showcasing project management features", async ({
    page,
  }) => {
    // =========================================================================
    // SECTION 1: LOGIN
    // =========================================================================

    await page.goto("/login");
    await page.waitForSelector('button[type="submit"]', { timeout: 30000 });

    await showNarration(page, "BRAID Manager", "Budget & RAID Log Management");
    await page.waitForTimeout(4000);

    await showNarration(
      page,
      "BRAID",
      "Budget • Risks • Actions • Issues • Decisions • Deliverables • Plan Items"
    );
    await page.waitForTimeout(4000);

    await hideNarration(page);

    // Login with demo credentials
    await page.fill('input[type="email"]', "demo@braidmgr.com");
    await page.waitForTimeout(500);
    await page.fill('input[type="password"]', "demo123");
    await page.waitForTimeout(500);

    await showNarration(page, "Secure Login", "Role-based access for your team");
    await page.waitForTimeout(2500);

    await hideNarration(page);
    await page.click('button[type="submit"]');
    await page.waitForURL("**/projects**", { timeout: 15000 });
    await page.waitForTimeout(1500);

    // =========================================================================
    // SECTION 2: PROJECT SELECTION
    // =========================================================================

    await showNarration(
      page,
      "Project Portfolio",
      "All your projects in one place"
    );
    await page.waitForTimeout(3500);

    // Click the project
    await hideNarration(page);
    await page.waitForTimeout(500);

    const projectCard = page.locator('text=Website Modernization').first();
    await projectCard.click();
    await page.waitForURL("**/dashboard**", { timeout: 10000 });
    await page.waitForTimeout(1500);

    // =========================================================================
    // SECTION 3: DASHBOARD - BRAID Overview
    // =========================================================================

    await showNarration(
      page,
      "Project Dashboard",
      "Your BRAID items at a glance"
    );
    await page.waitForTimeout(3500);

    // Point at summary cards
    await hideNarration(page);
    await showCallout(
      page,
      '[data-tour="summary-cards"]',
      "Summary Cards",
      "Budget, Risks, Actions, Issues, Decisions, Deliverables, Plan Items",
      "bottom"
    );
    await page.waitForTimeout(4500);

    // Scroll to show attention items
    await hideCallout(page);
    await page.evaluate(() => window.scrollBy(0, 300));
    await page.waitForTimeout(1000);

    // Show attention needed callout with center narration (since element selection is tricky)
    await showNarration(
      page,
      "Attention Needed",
      "Critical and late items highlighted automatically"
    );
    await page.waitForTimeout(4000);

    // Scroll to status overview
    await hideNarration(page);
    await page.evaluate(() => window.scrollBy(0, 200));
    await page.waitForTimeout(800);

    await showNarration(
      page,
      "Status Overview",
      "See indicator distribution across all items"
    );
    await page.waitForTimeout(3500);

    await hideCallout(page);
    await page.evaluate(() => window.scrollTo(0, 0));
    await page.waitForTimeout(800);

    // =========================================================================
    // SECTION 4: ALL ITEMS - Filtering Demo
    // =========================================================================

    await hideCallout(page);
    await page.click('text="All Items"');
    await page.waitForLoadState("networkidle");
    await page.waitForTimeout(1500);

    // Point at the items table
    await showCallout(
      page,
      '[data-tour="items-table"]',
      "All Items Table",
      "Complete list of every BRAID item in the project",
      "top"
    );
    await page.waitForTimeout(4000);

    // Point at filters
    await hideCallout(page);
    await showCallout(
      page,
      '[data-tour="filter-sidebar"]',
      "Powerful Filters",
      "Filter by type, workstream, indicator, or search text",
      "right"
    );
    await page.waitForTimeout(3500);

    // Demo: Filter by Risk
    await hideCallout(page);
    await page.waitForTimeout(500);

    await showNarration(
      page,
      "Filter by Type",
      "Let's look at just the Risks..."
    );
    await page.waitForTimeout(2500);

    await hideNarration(page);
    // Click the type dropdown and select Risk
    const typeSelect = page.locator('button:has-text("All Types")').first();
    if (await typeSelect.isVisible({ timeout: 2000 }).catch(() => false)) {
      await typeSelect.click();
      await page.waitForTimeout(500);
      const riskOption = page.locator('[role="option"]:has-text("Risk")').first();
      if (await riskOption.isVisible({ timeout: 1000 }).catch(() => false)) {
        await riskOption.click();
      }
      await page.waitForTimeout(1500);
    }

    await showNarration(
      page,
      "Risk Items",
      "Filtered to show only project risks"
    );
    await page.waitForTimeout(3000);

    // Clear filter and filter by Issues
    await hideNarration(page);
    const clearBtn = page.locator('button:has-text("Clear")').first();
    if (await clearBtn.isVisible({ timeout: 1000 }).catch(() => false)) {
      await clearBtn.click();
      await page.waitForTimeout(800);
    }

    await showNarration(
      page,
      "Filter by Indicator",
      "Now let's find items that need attention..."
    );
    await page.waitForTimeout(2500);

    await hideNarration(page);
    // Click indicator dropdown
    const indicatorSelect = page.locator('button:has-text("All Indicators")').first();
    if (await indicatorSelect.isVisible({ timeout: 2000 }).catch(() => false)) {
      await indicatorSelect.click();
      await page.waitForTimeout(500);
      // Select a critical indicator
      const lateOption = page.locator('[role="option"]:has-text("Late Finish")').first();
      if (await lateOption.isVisible({ timeout: 1000 }).catch(() => false)) {
        await lateOption.click();
      }
      await page.waitForTimeout(1500);
    }

    await showNarration(
      page,
      "Late Items Found",
      "Instantly identify items behind schedule"
    );
    await page.waitForTimeout(3500);

    // Clear filters
    await hideNarration(page);
    if (await clearBtn.isVisible({ timeout: 1000 }).catch(() => false)) {
      await clearBtn.click();
      await page.waitForTimeout(800);
    }

    // =========================================================================
    // SECTION 5: CLICK INTO AN ITEM
    // =========================================================================

    await showNarration(
      page,
      "Item Details",
      "Click any row to view and edit details"
    );
    await page.waitForTimeout(3000);

    await hideNarration(page);
    // Click first table row
    const firstRow = page.locator('tbody tr').first();
    if (await firstRow.isVisible({ timeout: 2000 }).catch(() => false)) {
      await firstRow.click();
      await page.waitForTimeout(1500);

      await showNarration(
        page,
        "Edit Item Dialog",
        "Update status, dates, assignments, and more"
      );
      await page.waitForTimeout(4000);

      // Close dialog
      await hideNarration(page);
      await page.keyboard.press("Escape");
      await page.waitForTimeout(800);
    }

    // =========================================================================
    // SECTION 6: ACTIVE ITEMS - Priority View
    // =========================================================================

    await hideNarration(page);
    await page.click('text="Active Items"');
    await page.waitForLoadState("networkidle");
    await page.waitForTimeout(1500);

    await showNarration(
      page,
      "Active Items View",
      "Items grouped by severity for focused action"
    );
    await page.waitForTimeout(4000);

    await showNarration(
      page,
      "Visual Indicators",
      "Red = Critical, Amber = Warning, Blue = In Progress, Green = Done"
    );
    await page.waitForTimeout(4500);

    // Scroll to show more groups
    await hideNarration(page);
    await page.evaluate(() => window.scrollBy(0, 300));
    await page.waitForTimeout(1000);

    await showNarration(
      page,
      "Priority Order",
      "Most critical items always appear first"
    );
    await page.waitForTimeout(3500);

    await page.evaluate(() => window.scrollTo(0, 0));
    await page.waitForTimeout(500);

    // =========================================================================
    // SECTION 7: TIMELINE - Gantt View
    // =========================================================================

    await hideNarration(page);
    await page.click('text="Timeline"');
    await page.waitForLoadState("networkidle");
    await page.waitForTimeout(2000);

    await showNarration(
      page,
      "Timeline View",
      "Gantt-style visualization of your project"
    );
    await page.waitForTimeout(4000);

    // Click Today button if visible
    const todayBtn = page.locator('button:has-text("Today")').first();
    if (await todayBtn.isVisible({ timeout: 1000 }).catch(() => false)) {
      await hideNarration(page);
      await todayBtn.click();
      await page.waitForTimeout(1000);
    }

    await showNarration(
      page,
      "Today Marker",
      "Red line shows current date in context"
    );
    await page.waitForTimeout(3500);

    // Demo zoom
    await hideNarration(page);
    const zoomIn = page.locator('button:has-text("+")').first();
    if (await zoomIn.isVisible({ timeout: 1000 }).catch(() => false)) {
      await zoomIn.click();
      await page.waitForTimeout(500);
      await zoomIn.click();
      await page.waitForTimeout(500);
    }

    await showNarration(
      page,
      "Zoom Controls",
      "Adjust view for the detail level you need"
    );
    await page.waitForTimeout(3500);

    // Show filter by type - use the dropdown menu item selector
    await hideNarration(page);
    const timelineTypeSelect = page.locator('button:has-text("All Types")').first();
    if (await timelineTypeSelect.isVisible({ timeout: 1000 }).catch(() => false)) {
      await timelineTypeSelect.click();
      await page.waitForTimeout(500);
      // Click the dropdown item specifically (inside SelectContent)
      const actionOption = page.locator('[role="option"]:has-text("Action Item")').first();
      if (await actionOption.isVisible({ timeout: 1000 }).catch(() => false)) {
        await actionOption.click();
        await page.waitForTimeout(1500);
      } else {
        // Fallback - close dropdown and continue
        await page.keyboard.press("Escape");
        await page.waitForTimeout(500);
      }
    }

    await showNarration(
      page,
      "Filter Timeline",
      "Focus on specific item types"
    );
    await page.waitForTimeout(3500);

    // =========================================================================
    // SECTION 8: AI CHAT ASSISTANT
    // =========================================================================

    await hideNarration(page);
    await page.click('text="Dashboard"');
    await page.waitForLoadState("networkidle");
    await page.waitForTimeout(1000);

    await showNarration(
      page,
      "AI Chat Assistant",
      "Ask questions about your project in natural language"
    );
    await page.waitForTimeout(3500);

    // Open chat drawer
    const chatButton = page.locator('button[aria-label="Open chat"]');
    if (await chatButton.isVisible({ timeout: 2000 }).catch(() => false)) {
      await chatButton.click();
      await page.waitForTimeout(1500);

      await showNarration(
        page,
        "Query Your Data",
        "Ask Claude about items, risks, deadlines, and more"
      );
      await page.waitForTimeout(3000);

      // Type a question about overdue items
      const chatInput = page.locator('textarea[placeholder*="Ask"], input[placeholder*="Ask"]').first();
      if (await chatInput.isVisible({ timeout: 2000 }).catch(() => false)) {
        await chatInput.fill("What items are currently overdue or at risk?");
        await page.waitForTimeout(2000);

        // Submit the message
        const sendButton = page.locator('button[type="submit"], button:has-text("Send")').first();
        if (await sendButton.isVisible({ timeout: 1000 }).catch(() => false)) {
          await sendButton.click();
        } else {
          await chatInput.press("Enter");
        }

        await showNarration(
          page,
          "Instant Insights",
          "Get AI-powered analysis of your project status"
        );

        // Wait for response (with timeout)
        await page.waitForTimeout(8000);

        await showNarration(
          page,
          "Meeting Notes to Actions",
          "Paste notes and get proposed updates"
        );
        await page.waitForTimeout(3000);

        // Clear and type meeting notes example
        await chatInput.fill("Based on today's meeting: The data migration is delayed by 2 weeks due to schema changes. We need to escalate the contractor cost issue to leadership.");
        await page.waitForTimeout(3000);

        // Submit
        if (await sendButton.isVisible({ timeout: 1000 }).catch(() => false)) {
          await sendButton.click();
        } else {
          await chatInput.press("Enter");
        }

        await showNarration(
          page,
          "Smart Suggestions",
          "Claude proposes item updates based on your notes"
        );
        await page.waitForTimeout(8000);
      }

      // Close chat drawer
      const closeButton = page.locator('button:has-text("×"), button[aria-label="Close"]').first();
      if (await closeButton.isVisible({ timeout: 1000 }).catch(() => false)) {
        await closeButton.click();
      }
      await page.waitForTimeout(1000);
    }

    // =========================================================================
    // SECTION 9: CLOSING
    // =========================================================================

    await hideNarration(page);
    await page.waitForTimeout(1000);

    await showNarration(page, "BRAID Manager", "Budget & RAID Log Management Made Simple");
    await page.waitForTimeout(4000);

    await showNarration(
      page,
      "Key Features",
      "Visual indicators • AI assistant • Multiple views • Powerful filtering"
    );
    await page.waitForTimeout(5000);

    await showNarration(
      page,
      "Keep Your Projects on Track",
      "With braidMgr"
    );
    await page.waitForTimeout(4500);

    await hideNarration(page);
    await page.waitForTimeout(2000);
  });
});
