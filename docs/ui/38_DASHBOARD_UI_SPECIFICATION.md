# Executive & Operations Telemetry Dashboard Specification

| Standard Code | Screen ID | Target Platform | API Version | Document Version | Date | Status |
|---|---|---|---|---|---|---|
| **STD-UI-001** | **`SCR-DASH-001`** | Next.js 14 (App Router) + TypeScript | `v1.2` (Django 5 DRF) | `v1.0.0` | 16/10/2026 | **APPROVED FOR IMPLEMENTATION** |

---

## 1. Document Overview, Version, Scope, and Status

### 1.1 Purpose
This specification defines the complete technical architecture, UI layout, telemetry widgets, KPI metrics, charts, alert feeds, Zod validation schema, TypeScript interfaces, and backend API integration for the **Enterprise Executive & Operations Telemetry Dashboard** (`SCR-DASH-001`).

The Operations Dashboard serves as the primary operational command center upon user login:
1. **Holistic Manufacturing Lifecycle Visibility**: Real-time aggregated metrics across all operational stages:
   - **Procurement & POs**: Active POs, Pending Inward Bags, Unmanaged PO Balances.
   - **Inventory & Godown Stocks**: Total Yarn Stock (Bags & Kg), Total Greige Fabric Stock (Rolls & Kg), Godown Capacity Utilization.
   - **Production & Subcontracting**: Active Knitting Programs, Knitter Fabric Yield %, Dyeing Dispatches.
   - **Commercial Sales & Revenue**: MTD Commercial Sales Invoices, GST Tax Collection, Return Credit Notes.
   - **Financial Health & Cash Flow**: Total Trade Receivables (Sundry Debtors) vs Total Trade Payables (Sundry Creditors), Cash/Bank Balances.
2. **Context-Aware Scoping**: Dynamic KPI filtering driven by the user's active `company_id` and selected `financial_year_id`.
3. **Operational Alert Ticker**: Proactive visual flags highlighting critical textile exceptions:
   - Overdue Yarn PO Deliveries ($> 7\text{ days}$)
   - Subcontractor High Process Loss Alerts ($> 4.5\%$)
   - Negative Stock Preventative Blocks
   - Customer Overdue Credit Windows ($> 60\text{ days}$)
4. **Rapid Action Launchpad**: One-touch keyboard and visual shortcuts to trigger primary transactional flows (`Alt+P` for PO, `Alt+I` for GRN Inward, `Alt+O` for DC Outward, `Alt+S` for Sales Invoice).

### 1.2 Scope
- **Backend Endpoints**: Aggregated telemetry endpoints across `/api/v1/purchase/pos/`, `/api/v1/inventory/stock/`, `/api/v1/knitting/programs/`, `/api/v1/sales/invoices/`, `/api/v1/ledger/`.
- **Country Pack**: India (`IN`) — Indian Rupee (`₹`), Indian numbering system (`12,34,567.89`), Metric weight (`Kg` and `MT`), Date format (`DD/MM/YYYY`).
- **Target Route**: `/dashboard` (Next.js route: `app/(app)/dashboard/page.tsx`).

---

## 2. Module Details, Screen ID, Route, Access Privileges, and API Endpoints

### 2.1 Core Metadata

| Parameter | Specification |
|---|---|
| **Module** | `Module 0 — Foundation & Multi-Tenancy` |
| **Screen ID** | `SCR-DASH-001` |
| **Frontend Route** | `/dashboard` |
| **File Location** | `app/(app)/dashboard/page.tsx` |
| **Required Privilege** | `dashboard.can_view` (Accessible to all authenticated enterprise users with role-gated card visibility) |
| **Authorized Roles** | `SUPER_ADMIN`, `ADMIN_USER`, `COMPANY_USER` (Managing Director, Operations VP, Production Head, Finance Manager, Storekeeper) |
| **Country Pack** | `IN` (India: Currency INR `₹`, Date `DD/MM/YYYY`, Decimal precision: Money 2 dp `₹ 0.00`, Weight 3 dp `0.000 Kg`) |

### 2.2 Primary API Endpoints

| HTTP Method | API Path | Privilege / Scope | Description |
|---|---|---|---|
| `GET` | `/api/v1/dashboard/summary/` | `can_view` | Fetch all aggregated high-level KPIs, inventory balances, and revenue figures |
| `GET` | `/api/v1/dashboard/alerts/` | `can_view` | Retrieve operational exception alerts (overdue POs, yield losses, credit breaches) |
| `GET` | `/api/v1/dashboard/charts/manufacturing-flow/` | `can_view` | Time-series data for monthly Inward vs Outward vs Production dispatches |
| `GET` | `/api/v1/dashboard/charts/financial-exposure/` | `can_view` | Receivables vs Payables aging distribution breakdown |

---

## 3. UI Layout, Screen Blueprint, and Visual Mockup (1440px+ Wireframe)

```
+-----------------------------------------------------------------------------------------------------------------------------+
| GARMENTS ERP — Executive Operations & Manufacturing Telemetry                 Company: ABC Textiles Ltd | FY: 2026-2027      |
+-----------------------------------------------------------------------------------------------------------------------------+
| HEADER BAR: Welcome, Arun Kumar (Operations VP)    Active FY: [ 2026-2027 | v ]    [ Live Sync: 16/10/2026 17:35 ] [F5]     |
| QUICK ACTION LAUNCHPAD:  [+ New PO (Alt+P)]  [+ Inward GRN (Alt+I)]  [+ Outward DC (Alt+O)]  [+ Sales Invoice (Alt+S)]       |
+-----------------------------------------------------------------------------------------------------------------------------+
| ROW 1: PRIMARY KPI SUMMARY CARDS                                                                                            |
| [ YARN STOCK ON HAND ]      [ GREIGE FABRIC STOCK ]      [ MONTHLY REVENUE (MTD) ]    [ NET RECEIVABLES (DR) ]              |
|   1,42,850.500 Kg (142.8 MT)  48,250.600 Kg (48.2 MT)      ₹ 1,84,50,200.00             ₹ 1,04,40,000.00                    |
|   3,571 Bags | 14 Godowns     2,145 Rolls | 4 Warehouses   12.4% vs Last Month [^]      42 Active Accounts                  |
|   Valuation: ₹ 4.28 Cr        Valuation: ₹ 1.15 Cr         GST Paid: ₹ 9,22,510.00      Overdue >45d: ₹ 14.20 L             |
+-----------------------------------------------------------------------------------------------------------------------------+
| ROW 2: CRITICAL OPERATIONAL ALERTS & EXCEPTION TICKER                                                       [Dismiss All]   |
| [!] OVERDUE PO: PO-2026-0038 (Vardhman Mills) 4,800 Kg Yarn overdue by 5 days. Expected: 11/10/2026.       [View PO] [Exp] |
| [!] YIELD EXCEPTION: Knitting Program KP-2026-0042 at Sri Venkateswara Mills reported 4.81% loss (>2.5% max). [Investigate]|
| [!] CREDIT ALERT: Customer "TexTrend Apparel Ltd" reached 94% of ₹ 25.00 Lakh credit limit.                 [View Ledger]   |
+-----------------------------------------------------------------------------------------------------------------------------+
| ROW 3: CHARTS & PRODUCTION TELEMETRY                                                                                        |
| +---------------------------------------------------------+ +-------------------------------------------------------------+ |
| | CHART 1: MONTHLY MATERIAL THROUGHPUT (METRIC TONNES)    | | CHART 2: PRODUCTION YIELD & EFFICIENCY GAUGES               | |
| | 120 |                                                   | | Knitting Yield: [██████████████████░░] 97.4% (Target: 97.5%)| |
| |  90 |          [Inward GRN]                             | | Dyeing Yield  : [█████████████████░░░] 95.2% (Target: 95.5%)| |
| |  60 |                 [Outward DC]                      | | Cutting Yield : [██████████████████░░] 94.8% (Target: 94.0%)| |
| |  30 |                        [Sales Tax Inv]            | | ----------------------------------------------------------- | |
| |   0 +----+-----+-----+-----+-----+-----+-----+-----+--+ | | WAREHOUSE OCCUPANCY:                                        | |
| |      Apr  May   Jun   Jul   Aug   Sep   Oct (MTD)       | | Tirupur Main Godown: 88% | Greige Unit 2: 64% | Central: 45%| |
| +---------------------------------------------------------+ +-------------------------------------------------------------+ |
+-----------------------------------------------------------------------------------------------------------------------------+
| ROW 4: RECENT TRANSACTION FEED & GODOWN LEDGER QUICK LINKS                                                                  |
| Time     | Module     | Document #     | Entity / Subcontractor      | Quantity / Amount       | Status    | Action         |
|----------|------------|----------------|-----------------------------|-------------------------|-----------|----------------|
| 17:15    | Sales      | INV-2026-0089  | Tirupur Garments Export Ltd | 4,200 Kg (₹ 15.12 Lakh) | POSTED    | [View Invoice] |
| 16:40    | Inventory  | DC-2026-0054   | Supreme Dyeing Unit         | 60 Rolls (1,280 Kg)     | DISPATCHED| [View DC]      |
| 15:20    | Knittng    | KP-2026-0042   | Sri Venkateswara Knitting   | 2,400 Kg Target         | RELEASED  | [View Program] |
| 14:05    | Ledger     | PV-2026-0019   | Vardhman Spinning Mills     | ₹ 10,00,000.00 Payment  | CLEARED   | [View Voucher] |
+-----------------------------------------------------------------------------------------------------------------------------+
| FOOTER: Double-Entry Ledger Equilibrium: Verified (Δ = ₹ 0.00) | Multi-Tenancy Scoped to Tenant #1 (ABC Textiles Ltd)         |
| SHORTCUTS: [Alt+P: New PO]  [Alt+I: New Inward]  [Alt+O: New Outward]  [Alt+S: New Sales]  [F5: Refresh Live Dashboard]     |
+-----------------------------------------------------------------------------------------------------------------------------+
```

---

## 4. UX Workflow, Step-by-Step Lifecycle, and Edge-Case Handling

### 4.1 Step-by-Step Lifecycle
1. **Initial Hydration**:
   - User authenticates via `/login` and is redirected to `/dashboard`.
   - Dashboard automatically reads active tenant `company_id` and selected `financial_year_id`.
   - Concurrent API requests populate KPI cards, operational alerts, time-series charts, and recent transaction feeds.
2. **Context Switching**:
   - Switching the Financial Year dropdown dynamically recomputes all MTD and YTD metrics without logging out.
3. **Alert Remediation**:
   - User clicks on an alert action (e.g. **[View PO]** for an overdue delivery).
   - Directly routes the user to the relevant screen with highlighted filters.
4. **Rapid Action Navigation**:
   - Keyboard shortcuts (`Alt+P`, `Alt+I`, etc.) instantly open transaction creation screens with pre-selected company and financial year metadata.

### 4.2 Edge-Case Handling
- **Role-Based Telemetry Scoping**: Storekeepers only see Inventory and Production cards; Financial Figures (Revenue, Bank Balances, Receivables) are automatically hidden for non-accounting roles.
- **Offline / Stale Data Alert**: If background telemetry sync fails, an amber banner appears: *"Telemetry sync paused. Displaying cached data from 10 minutes ago. [Retry (F5)]"*.

---

## 5. Form Sections, Field Matrix, and Validation Rules

| Widget | Parameter | Type | Required | Default | Scope & Description |
|---|---|---|---|---|---|
| **Header** | Financial Year | `fy_id` | Select | Yes | Active FY | Active financial year selector |
| **Header** | Auto-Refresh Interval | `refresh_interval` | Select | Yes | `60s` | Options: 30s, 60s, 5m, Off |
| **Launchpad** | Quick PO Action | Button (`Alt+P`) | N/A | Active | Routes to `/procurement/yarn-po/new` |
| **Launchpad** | Quick Inward GRN | Button (`Alt+I`) | N/A | Active | Routes to `/inventory/yarn-inward/new` |
| **Launchpad** | Quick Outward DC | Button (`Alt+O`) | N/A | Active | Routes to `/inventory/yarn-outward/new` |
| **Launchpad** | Quick Sales Invoice| Button (`Alt+S`) | N/A | Active | Routes to `/sales/yarn-sales/new` |

---

## 6. Mathematical Formulas and Calculation Specifications (LaTeX)

### 6.1 Total Stock Valuation Formula
Given yarn stock $Q_{\text{yarn}, i}$ in kg with valuation rate $R_{\text{yarn}, i}$ and greige fabric stock $Q_{\text{grey}, j}$ with rate $R_{\text{grey}, j}$:

$$V_{\text{inventory}} = \sum_{i=1}^{N_{\text{yarn}}} (Q_{\text{yarn}, i} \times R_{\text{yarn}, i}) + \sum_{j=1}^{M_{\text{grey}}} (Q_{\text{grey}, j} \times R_{\text{grey}, j})$$

### 6.2 Overall Knitting Manufacturing Efficiency Yield %
Given cumulative fabric received $Q_{\text{received}}$ against cumulative dispatched yarn $Q_{\text{issued}}$:

$$\text{Yield Efficiency } \% = \operatorname{Round}\left(\frac{Q_{\text{received}}}{Q_{\text{issued}}} \times 100, 2\right)$$

$$\text{Average Process Loss } \% = 100.00\% - \text{Yield Efficiency } \%$$

### 6.3 Net Working Capital Exposure Indicator
$$\text{Net Working Capital Exposure} = \text{Trade Receivables (Debtors)} - \text{Trade Payables (Creditors)}$$

---

## 7. Dynamic Behaviors, Conditional Fields, and Interactivity

1. **Role-Based Component Visibility**:
   - `SUPER_ADMIN` & `ADMIN_USER`: Unrestricted access to all revenue, margin, and cost cards.
   - `COMPANY_USER` (Inventory/Storekeeper): Only sees Stock on Hand, Godown Utilization, and Inward/Outward registers.
2. **Interactive Hover Tooltips on Charts**:
   - Hovering over chart bars reveals granular breakdowns: Bags vs Weight, CGST vs SGST splits.
3. **Sound / Visual Notification on Critical Alert**:
   - When negative stock attempts or major process loss anomalies occur, the alert banner pulses with high-contrast red styling.

---

## 8. API Request / Response Contracts (DTOs)

### 8.1 Fetch Dashboard Summary (`GET /api/v1/dashboard/summary/`)

```json
{
  "success": true,
  "data": {
    "company_id": 1,
    "company_name": "ABC Textiles Ltd",
    "fy_name": "FY 2026-2027",
    "inventory": {
      "yarn_stock_kg": "142850.500",
      "yarn_stock_bags": 3571,
      "yarn_stock_valuation": "42855150.00",
      "greige_fabric_kg": "48250.600",
      "greige_fabric_rolls": 2145,
      "greige_fabric_valuation": "11580144.00"
    },
    "production": {
      "active_knitting_programs": 12,
      "knitting_yield_percent": "97.40",
      "average_loss_percent": "2.60",
      "pending_fabric_inward_kg": "18400.000"
    },
    "commercial": {
      "mtd_sales_amount": "18450200.00",
      "mtd_sales_count": 89,
      "mtd_gst_collected": "922510.00",
      "mtd_returns_count": 3
    },
    "finance": {
      "total_receivables": "10440000.00",
      "overdue_receivables": "1420000.00",
      "total_payables": "12830000.00",
      "bank_balances": "3780000.00",
      "ledger_difference": "0.00"
    }
  }
}
```

---

## 9. Client-Side State Management and Component Architecture

```
app/(app)/dashboard/
├── page.tsx                             # Server component pre-fetching initial telemetry
└── components/
    ├── DashboardHeaderControls.tsx      # FY switcher and quick action buttons
    ├── KPISummaryGrid.tsx               # 4 primary metric cards
    ├── OperationalAlertBanner.tsx       # Critical exception ticker
    ├── MaterialThroughputChart.tsx      # SVG/Canvas time-series throughput bar chart
    ├── YieldEfficiencyGauge.tsx         # Circular progress bars for knitting/dyeing loss
    └── RecentActivityFeed.tsx           # Live chronological transactional event table
```

---

## 10. Zod Validation Schema (Copy-Paste Production Code)

```typescript
import { z } from "zod";

export const DashboardFilterSchema = z.object({
  fy_id: z.number().int().positive({ message: "Financial year is required." }),
  refresh_interval: z.enum(["30s", "60s", "5m", "off"]).default("60s"),
});

export type DashboardFilterParams = z.infer<typeof DashboardFilterSchema>;
```

---

## 11. TypeScript Interfaces & Enums (Complete DTO Declarations)

```typescript
export interface IDashboardSummaryDTO {
  company_id: number;
  company_name: string;
  fy_name: string;
  inventory: {
    yarn_stock_kg: number;
    yarn_stock_bags: number;
    yarn_stock_valuation: number;
    greige_fabric_kg: number;
    greige_fabric_rolls: number;
    greige_fabric_valuation: number;
  };
  production: {
    active_knitting_programs: number;
    knitting_yield_percent: number;
    average_loss_percent: number;
    pending_fabric_inward_kg: number;
  };
  commercial: {
    mtd_sales_amount: number;
    mtd_sales_count: number;
    mtd_gst_collected: number;
    mtd_returns_count: number;
  };
  finance: {
    total_receivables: number;
    overdue_receivables: number;
    total_payables: number;
    bank_balances: number;
    ledger_difference: number;
  };
}

export interface IOperationalAlertDTO {
  id: string;
  severity: "CRITICAL" | "WARNING" | "INFO";
  title: string;
  message: string;
  document_type: string;
  document_id: number;
  action_route: string;
  timestamp: string;
}
```

---

## 12. Keyboard Shortcuts and Rapid Operations

| Key Combination | Action / Trigger | Scope / View |
|---|---|---|
| `Alt + P` | Route to New Yarn Purchase Order | Dashboard Launchpad |
| `Alt + I` | Route to New Yarn Inward GRN | Dashboard Launchpad |
| `Alt + O` | Route to New Yarn Outward DC | Dashboard Launchpad |
| `Alt + S` | Route to New Commercial Sales Invoice | Dashboard Launchpad |
| `F5` | Refresh Telemetry Data | Dashboard Desk |

---

## 13. Responsive Breakpoints and Mobile Adaptation

| Viewport Width | Screen Category | Layout Behavior |
|---|---|---|
| $\ge 1440\text{px}$ | Desktop Enterprise | 4-column KPI cards, side-by-side throughput charts, full table feed |
| $1024\text{px} - 1439\text{px}$ | Laptop / Tablet Landscape | 2x2 KPI grid, stacked charts, compact event feed |
| $\le 1023\text{px}$ | Tablet Portrait / Mobile | Single column card feed, horizontal swipeable charts |

---

## 14. Error Handling and User Feedback

| Scenario / Error Trigger | Visual Presentation | Remediation Action |
|---|---|---|
| Telemetry API error | Amber toast: *"Failed to refresh real-time metrics"* | Auto-retry after 10s with fallback data |
| Ledger Imbalance detected | Flashing red banner: *"Financial Ledger Variance Detected"* | Link directly to Trial Balance desk |

---

## 15. Loading, Empty, and Edge States

- **Loading State**: Pulse animation over all KPI card numerals and chart areas.
- **Zero Activity State**: Friendly onboarding cards pointing to first PO creation.
- **Balanced Indicator**: Green shield icon confirming zero accounting variance.

---

## 16. Accessibility (a11y) Conformance (WCAG 2.1 AA)

- All chart elements provide text alternatives and accessible data tables.
- Alert announcements use `role="alert"` for immediate screen reader priority.
- Minimum contrast ratio $> 4.5:1$ on all status pills and KPI numerals.

---

## 17. Security, RBAC, and Audit Logging

- **Role Visibility Gates**: Financial KPIs are stripped from API response if user lacks `finance.can_read`.
- **Tenant Scope Enforcement**: `company_id` strictly injected into all telemetry queries.
- **Audit Logging**: Dashboard access and filter changes log to `ta_audit_log`.

---

## 18. Test Cases and Acceptance Criteria

### 18.1 Acceptance Criteria
1. Initial dashboard load completes within 500ms on local development server.
2. Clicking `Alt+P` directly routes to `/procurement/yarn-po/new`.
3. Inventory balances match active sum of `tm_yarn_stock` and `tm_grey_fabric_stock`.

---

## 19. Performance Budgets and Optimization Targets

- Page load First Contentful Paint (FCP): $< 400\text{ms}$.
- Concurrent summary API execution: $< 150\text{ms}$.

---

## 20. Future Enhancements and Scalability Roadmap

1. **Customizable Drag-and-Drop Widgets**: Allowing users to pin preferred cards to the top.
2. **Machine Telemetry Live Feed**: Direct MQTT socket integration showing running circular knitting looms.

---

## 21. Sign-off and Approval Matrix

| Stakeholder Role | Name / Title | Date | Signature / Status |
|---|---|---|---|
| **Managing Director** | K. S. Rajagopalan (MD) | 16/10/2026 | **APPROVED** |
| **Lead Architect** | Enterprise Garments Solutions | 16/10/2026 | **APPROVED** |
| **Operations VP** | Arun Kumar | 16/10/2026 | **APPROVED** |
