# General Ledger & Multi-Period Trial Balance Specification

| Standard Code | Screen ID | Target Platform | API Version | Document Version | Date | Status |
|---|---|---|---|---|---|---|
| **STD-UI-001** | **`SCR-FINL-002`** | Next.js 14 (App Router) + TypeScript | `v1.2` (Django 5 DRF) | `v1.0.0` | 16/10/2026 | **APPROVED FOR IMPLEMENTATION** |

---

## 1. Document Overview, Version, Scope, and Status

### 1.1 Purpose
This specification defines the complete technical architecture, UI layout, double-entry trial balance ledger logic, account group hierarchies, drill-down voucher views, export formats, Zod validation schema, TypeScript interfaces, and backend API integration for the **General Ledger & Multi-Period Trial Balance Desk** (`SCR-FINL-002`).

The Trial Balance is the foundational financial control instrument in an enterprise ERP:
1. **Double-Entry Equilibrium Verification**: Enforcing that the sum of all debit balances identically equals the sum of all credit balances:
   $$\sum_{i} \text{Debit}_i \equiv \sum_{i} \text{Credit}_i \implies \Delta = \text{₹ 0.00}$$
2. **Hierarchical Chart of Accounts Structure**: Categorizing balances into the 5 primary accounting classes:
   - **Assets** (Cash, Bank, Debtors/Accounts Receivable, Inventory/Stock Valuation, Fixed Assets)
   - **Liabilities** (Creditors/Accounts Payable, GST Payable, Bank Loans, Statutory Dues)
   - **Equity** (Share Capital, Retained Earnings, Partner Capital)
   - **Revenue** (Yarn Sales, Fabric Sales, Scrap Sales, Job Work Service Income)
   - **Expenses** (Yarn Purchases, Dyeing Charges, Knitting Charges, Freight, Electricity, Wages)
3. **Multi-Period Temporal Analysis**: Comparing Opening Balances, Net Period Debits/Credits, and Net Closing Balances across customizable fiscal periods (FY-to-Date, Monthly, Quarterly).
4. **Interactive Audit Drill-Down**: Allowing auditors and finance managers to click any account row to expand its constituent vouchers and double-entry postings.

### 1.2 Scope
- **Backend Models**: `Account` (`tm_account`), `JournalEntry` / `tl_voucher`, `JournalEntryLine` / `tl_voucher_line`.
- **Backend Service**: `AccountingService` / `CurrencyLedgerService`.
- **Country Pack**: India (`IN`) — Indian Rupee (`₹`), Indian numbering system (`12,34,567.89`), Indian Fiscal Year (`01/04` to `31/03`).
- **Target Route**: `/ledgers/trial-balance` (Next.js route: `app/(app)/ledgers/trial-balance/page.tsx`).

---

## 2. Module Details, Screen ID, Route, Access Privileges, and API Endpoints

### 2.1 Core Metadata

| Parameter | Specification |
|---|---|
| **Module** | `Module 8 — Ledgers & Financial Accounting` |
| **Screen ID** | `SCR-FINL-002` |
| **Frontend Route** | `/ledgers/trial-balance` |
| **File Location** | `app/(app)/ledgers/trial-balance/page.tsx` |
| **Required Privilege** | `ledger_financial.can_read` (View trial balance); `ledger_financial.can_export` (Export Excel/PDF) |
| **Authorized Roles** | `SUPER_ADMIN`, `ADMIN_USER`, `COMPANY_USER` (Chief Financial Officer, Head of Accounts, Statutory Auditor) |
| **Country Pack** | `IN` (India: Currency INR `₹`, Date `DD/MM/YYYY`, Decimal precision: Money 2 dp `₹ 0.00`) |

### 2.2 Primary API Endpoints

| HTTP Method | API Path | Privilege / Scope | Description |
|---|---|---|---|
| `GET` | `/api/v1/ledger/trial-balance/` | `can_read` | Fetch hierarchical Trial Balance report with opening, period, and closing totals |
| `GET` | `/api/v1/ledger/accounts/{id}/ledger/` | `can_read` | Drill-down endpoint returning itemized vouchers for a specific account code |
| `GET` | `/api/v1/ledger/trial-balance/export/` | `can_export` | Download official multi-column Trial Balance spreadsheet in XLSX format |

---

## 3. UI Layout, Screen Blueprint, and Visual Mockup (1440px+ Wireframe)

```
+-----------------------------------------------------------------------------------------------------------------------------+
| GARMENTS ERP — Multi-Period General Ledger Trial Balance                     Company: ABC Textiles Ltd | FY: 2026-2027      |
+-----------------------------------------------------------------------------------------------------------------------------+
| CONTROLS & FILTER BAR:                                                                                                      |
| Fiscal Year: [ FY 2026-2027 (01/04/2026 - 31/03/2027) | v ]  Period: [ Custom Date Range | v ]                               |
| From Date: [ 01/04/2026 ]  To Date: [ 16/10/2026 ]  View Mode: [ Detailed Tree View | v ]  [ ] Hide Zero Balances             |
| [ Refresh Ledger (F5) ]                                                       [ Export XLSX (Alt+E) ]  [ Print Audit (Ctrl+P)]|
+-----------------------------------------------------------------------------------------------------------------------------+
| TRIAL BALANCE INTEGRITY STATUS:                                                                                             |
| [ TOTAL OPENING DR ]       [ TOTAL OPENING CR ]       [ PERIOD DR MOVEMENTS ]     [ PERIOD CR MOVEMENTS ]     [ TB STATUS ]  |
|   ₹ 1,48,50,000.00           ₹ 1,48,50,000.00           ₹ 4,28,40,250.00            ₹ 4,28,40,250.00          BALANCED [OK]  |
|   Difference: ₹ 0.00         Difference: ₹ 0.00         Difference: ₹ 0.00          Difference: ₹ 0.00        Variance: ₹ 0.00|
+-----------------------------------------------------------------------------------------------------------------------------+
| HIERARCHICAL CHART OF ACCOUNTS TRIAL BALANCE TABLE:                                                                         |
| Account Code & Title              | Type       | Opening Debit (₹) | Opening Credit(₹) | Period Debit (₹) | Period Credit (₹)| Closing Debit (₹)| Closing Credit(₹)|
|-----------------------------------|------------|-------------------|-------------------|------------------|------------------|------------------|------------------|
| [-] 1000 — ASSETS                 | GROUP      |   1,12,00,000.00  |              0.00 |   2,85,60,000.00 |   1,65,40,000.00 |   2,32,20,000.00 |              0.00|
|   [+] 1100 - Current Assets       | GROUP      |     85,00,000.00  |              0.00 |   2,40,20,000.00 |   1,45,20,000.00 |   1,80,00,000.00 |              0.00|
|       1110 - HDFC Bank Oper A/c   | LEDGER     |     24,50,000.00  |              0.00 |     85,40,000.00 |     72,10,000.00 |     37,80,000.00 |              0.00|
|       1120 - Trade Debtors (Cust) | LEDGER     |     48,20,000.00  |              0.00 |   1,24,60,000.00 |     68,40,000.00 |   1,04,40,000.00 |              0.00|
|       1130 - Yarn Inventory Value | LEDGER     |     12,30,000.00  |              0.00 |     30,20,000.00 |      4,70,000.00 |     37,80,000.00 |              0.00|
| [-] 2000 — LIABILITIES            | GROUP      |              0.00 |     78,50,000.00 |     98,40,000.00 |   1,48,20,000.00 |              0.00 |   1,28,30,000.00|
|   [+] 2100 - Trade Creditors (Mill| LEDGER     |              0.00 |     65,20,000.00 |     82,40,000.00 |   1,22,50,000.00 |              0.00 |   1,05,30,000.00|
|   [+] 2200 - Duties & Taxes (GST) | LEDGER     |              0.00 |     13,30,000.00 |     16,00,000.00 |     25,70,000.00 |              0.00 |     23,00,000.00|
| [-] 3000 — EQUITY & RESERVES      | GROUP      |              0.00 |     70,00,000.00 |             0.00 |             0.00 |              0.00 |     70,00,000.00|
| [-] 4000 — REVENUE (SALES)        | GROUP      |              0.00 |              0.00 |             0.00 |   1,14,80,250.00 |              0.00 |   1,14,80,250.00|
| [-] 5000 — EXPENSES (DIRECT/JOB)  | GROUP      |              0.00 |              0.00 |     44,40,250.00 |             0.00 |     44,40,250.00 |              0.00|
|-----------------------------------|------------|-------------------|-------------------|------------------|------------------|------------------|------------------|
| **GRAND TOTALS (ALL ACCOUNTS)**    |            |**1,48,50,000.00** |**1,48,50,000.00** |**4,28,40,250.00**|**4,28,40,250.00**|**2,76,60,250.00**|**2,76,60,250.00**|
| **DIFFERENCE (DR - CR)**           |            |          **0.00** |                   |          **0.00**|                  |          **0.00** |                  |
+-----------------------------------------------------------------------------------------------------------------------------+
| AUDIT FOOTNOTE: Double-entry ledger integrity mathematically verified. Σ(Closing Dr) = Σ(Closing Cr) = ₹ 2,76,60,250.00      |
| SHORTCUTS: [Alt+E: Export Spreadsheet]  [Ctrl+P: Print Audit Sheet]  [Alt+Z: Toggle Zero Balances]  [Esc: Collapse All]     |
+-----------------------------------------------------------------------------------------------------------------------------+
```

---

## 4. UX Workflow, Step-by-Step Lifecycle, and Edge-Case Handling

### 4.1 Step-by-Step Lifecycle
1. **Period Selection**:
   - User chooses Financial Year (defaults to active FY).
   - Selects evaluation period (e.g., Year to Date, Q1, Q2, or custom date window).
   - System fetches and aggregates account ledger balances via `/api/v1/ledger/trial-balance/`.
2. **Equilibrium Verification**:
   - The UI immediately compares $\sum \text{Debit}$ against $\sum \text{Credit}$.
   - If difference equals zero, a green **BALANCED** seal is displayed.
   - If an imbalance is detected, a prominent red alert is triggered displaying the exact variance amount.
3. **Hierarchy Exploration & Drill-Down**:
   - Users can collapse or expand account groups (Assets, Liabilities, Equity, Revenue, Expense).
   - Clicking any individual ledger account opens a side drawer displaying its itemized constituent journal vouchers.
4. **Audit Export & Print**:
   - One-click export streams a multi-column Excel spreadsheet with embedded summing formulas.
   - Print view formats the report onto standard landscape A4/Letter size with official audit header.

### 4.2 Edge-Case Handling
- **Zero Balance Filtering**: Checkbox **[ ] Hide Zero Balances** filters out dormant accounts having zero opening balance, zero period movements, and zero closing balance.
- **Mid-Year Opening Balance Alignment**: When custom dates are selected mid-year (e.g. from 1st July), opening balances represent cumulative ledger positions up to 30th June.

---

## 5. Form Sections, Field Matrix, and Validation Rules

| Section | Field Label | Field Key | Input Type | Required | Default | Validation & Rules |
|---|---|---|---|---|---|---|
| **Filter** | Financial Year | `fy_id` | Select | Yes | Active FY | Active `tm_financial_year` |
| **Filter** | Period Preset | `period_preset` | Select | Yes | `YTD` | `YTD`, `Q1`, `Q2`, `Q3`, `Q4`, `CUSTOM` |
| **Filter** | From Date | `from_date` | DatePicker | Yes | FY Start Date | `DD/MM/YYYY` |
| **Filter** | To Date | `to_date` | DatePicker | Yes | Current Date | `DD/MM/YYYY`, must be $\ge$ `from_date` |
| **Filter** | View Mode | `view_mode` | Select | Yes | `TREE` | `TREE` (Hierarchical) or `FLAT` (All accounts) |
| **Filter** | Hide Zero Balances| `hide_zero` | Checkbox | No | `true` | Boolean filter |

---

## 6. Mathematical Formulas and Calculation Specifications (LaTeX)

### 6.1 Net Closing Balance by Account Type
For Asset and Expense accounts (Debit normal):

$$\text{Closing Balance} = (\text{Opening Dr} - \text{Opening Cr}) + (\text{Period Dr} - \text{Period Cr})$$

$$\text{If } \text{Closing Balance} \ge 0 \implies \text{Closing Dr} = \text{Closing Balance}, \quad \text{Closing Cr} = 0$$

$$\text{If } \text{Closing Balance} < 0 \implies \text{Closing Dr} = 0, \quad \text{Closing Cr} = |\text{Closing Balance}|$$

For Liability, Equity, and Revenue accounts (Credit normal):

$$\text{Closing Balance} = (\text{Opening Cr} - \text{Opening Dr}) + (\text{Period Cr} - \text{Period Dr})$$

$$\text{If } \text{Closing Balance} \ge 0 \implies \text{Closing Cr} = \text{Closing Balance}, \quad \text{Closing Dr} = 0$$

$$\text{If } \text{Closing Balance} < 0 \implies \text{Closing Cr} = 0, \quad \text{Closing Dr} = |\text{Closing Balance}|$$

### 6.2 Golden Invariant of Trial Balance Equilibrium
$$\sum_{k=1}^{N} \text{Opening Dr}_k \equiv \sum_{k=1}^{N} \text{Opening Cr}_k$$

$$\sum_{k=1}^{N} \text{Period Dr}_k \equiv \sum_{k=1}^{N} \text{Period Cr}_k$$

$$\sum_{k=1}^{N} \text{Closing Dr}_k \equiv \sum_{k=1}^{N} \text{Closing Cr}_k$$

$$\Delta_{\text{variance}} = \left| \sum \text{Closing Dr} - \sum \text{Closing Cr} \right| \equiv 0.00$$

---

## 7. Dynamic Behaviors, Conditional Fields, and Interactivity

1. **Tree Expand / Collapse State**: Expanding parent groups smoothly reveals child subgroups and constituent ledger accounts with indentation.
2. **Instant Search Filter**: Typing in the search input instantly highlights matching account codes (e.g. `1110`) and account titles across the tree.
3. **Drill-Down Drawer**: Clicking any account row slides out an **Account Ledger Vouchers** drawer showing the full date-wise journal line audit.

---

## 8. API Request / Response Contracts (DTOs)

### 8.1 Fetch Trial Balance (`GET /api/v1/ledger/trial-balance/?fy_id=1&from_date=01/04/2026&to_date=16/10/2026`)

```json
{
  "success": true,
  "data": {
    "fy_name": "FY 2026-2027",
    "from_date": "01/04/2026",
    "to_date": "16/10/2026",
    "total_opening_debit": "14850000.00",
    "total_opening_credit": "14850000.00",
    "total_period_debit": "42840250.00",
    "total_period_credit": "42840250.00",
    "total_closing_debit": "27660250.00",
    "total_closing_credit": "27660250.00",
    "difference": "0.00",
    "is_balanced": true,
    "accounts": [
      {
        "code": "1000",
        "name": "ASSETS",
        "account_type": "ASSET",
        "is_group": true,
        "opening_debit": "11200000.00",
        "opening_credit": "0.00",
        "period_debit": "28560000.00",
        "period_credit": "16540000.00",
        "closing_debit": "23220000.00",
        "closing_credit": "0.00",
        "children": [
          {
            "code": "1110",
            "name": "HDFC Bank Operating A/c",
            "account_type": "ASSET",
            "is_group": false,
            "opening_debit": "2450000.00",
            "opening_credit": "0.00",
            "period_debit": "8540000.00",
            "period_credit": "7210000.00",
            "closing_debit": "3780000.00",
            "closing_credit": "0.00"
          }
        ]
      }
    ]
  }
}
```

---

## 9. Client-Side State Management and Component Architecture

```
app/(app)/ledgers/trial-balance/
├── page.tsx                             # Master container managing fiscal period and trial balance
└── components/
    ├── TrialBalanceHeaderMetrics.tsx    # Total Opening, Period, and Closing Dr/Cr KPI tiles
    ├── TrialBalanceFilterControls.tsx   # FY, period preset, date picker, and zero-balance toggle
    ├── TrialBalanceTreeTable.tsx        # Multi-level hierarchical table with collapse controls
    ├── AccountLedgerDrawer.tsx          # Slide-out voucher drill-down drawer
    └── TrialBalanceExportModal.tsx      # Export configuration and print preview
```

---

## 10. Zod Validation Schema (Copy-Paste Production Code)

```typescript
import { z } from "zod";

const dateRegex = /^(0[1-9]|[12][0-9]|3[01])\/(0[1-9]|1[0-2])\/\d{4}$/;

export const TrialBalanceFilterSchema = z.object({
  fy_id: z.number().int().positive({ message: "Financial year is required." }),
  period_preset: z.enum(["YTD", "Q1", "Q2", "Q3", "Q4", "CUSTOM"]),
  from_date: z.string().regex(dateRegex, { message: "From date must be DD/MM/YYYY" }),
  to_date: z.string().regex(dateRegex, { message: "To date must be DD/MM/YYYY" }),
  view_mode: z.enum(["TREE", "FLAT"]),
  hide_zero: z.boolean().default(true),
});

export type TrialBalanceFilterParams = z.infer<typeof TrialBalanceFilterSchema>;
```

---

## 11. TypeScript Interfaces & Enums (Complete DTO Declarations)

```typescript
export interface ITrialBalanceAccountDTO {
  code: string;
  name: string;
  account_type: "ASSET" | "LIABILITY" | "EQUITY" | "REVENUE" | "EXPENSE";
  is_group: boolean;
  opening_debit: number;
  opening_credit: number;
  period_debit: number;
  period_credit: number;
  closing_debit: number;
  closing_credit: number;
  children?: ITrialBalanceAccountDTO[];
}

export interface ITrialBalanceReportDTO {
  fy_name: string;
  from_date: string;
  to_date: string;
  total_opening_debit: number;
  total_opening_credit: number;
  total_period_debit: number;
  total_period_credit: number;
  total_closing_debit: number;
  total_closing_credit: number;
  difference: number;
  is_balanced: boolean;
  accounts: ITrialBalanceAccountDTO[];
}
```

---

## 12. Keyboard Shortcuts and Rapid Operations

| Key Combination | Action / Trigger | Scope / View |
|---|---|---|
| `Alt + E` | Export Trial Balance to Excel XLSX | Trial Balance Desk |
| `Ctrl + P` | Print Official Trial Balance Sheet | Trial Balance Desk |
| `Alt + Z` | Toggle Hide Zero Balances | Trial Balance Desk |
| `F5` | Refresh & Recompute Balances | Trial Balance Desk |
| `Esc` | Close Drill-down Drawer | Drawer View |

---

## 13. Responsive Breakpoints and Mobile Adaptation

| Viewport Width | Screen Category | Layout Behavior |
|---|---|---|
| $\ge 1440\text{px}$ | Desktop Enterprise | 8-column comparative Trial Balance with hierarchical tree view |
| $1024\text{px} - 1439\text{px}$ | Laptop / Tablet Landscape | Condensed columns (Closing Dr/Cr prominent), horizontal scroll on Period Dr/Cr |
| $\le 1023\text{px}$ | Tablet Portrait / Mobile | Collapsible summary cards grouped by Account Class (Assets, Liabilities, etc.) |

---

## 14. Error Handling and User Feedback

| Scenario / Error Trigger | Visual Presentation | Remediation Action |
|---|---|---|
| Ledger Imbalance ($\Delta \neq 0$) | Bright red header banner: *"TRIAL BALANCE IMBALANCE: ₹ 1,500.00"* | Immediate audit trigger link provided |
| From Date $>$ To Date | Red field border on date picker | Adjust dates to chronological order |
| Network Timeout | Shimmer placeholder with retry button | Re-request aggregated summary |

---

## 15. Loading, Empty, and Edge States

- **Loading State**: Full-page skeleton tree reflecting Chart of Accounts structure.
- **Empty State**: Document icon with message: *"No accounting vouchers recorded in selected period."*
- **Balanced State**: Green badge: *"TRIAL BALANCE PERFECTLY BALANCED (DIFFERENCE: ₹ 0.00)"*.

---

## 16. Accessibility (a11y) Conformance (WCAG 2.1 AA)

- Tables use `<table aria-label="General Ledger Trial Balance">` with multi-level row grouping.
- High-contrast text on all financial figures ($\ge 4.5:1$).
- Full keyboard navigation allowing `Space` or `Enter` to expand tree branches.

---

## 17. Security, RBAC, and Audit Logging

- **Privilege Checking**: Only authorized accounts personnel holding `ledger_financial.can_read` can access.
- **Multi-Tenant Isolation**: Enforced strictly by `company_id`.
- **Read-Only Surface**: Trial Balance is a calculated read-model derived from immutable vouchers.

---

## 18. Test Cases and Acceptance Criteria

### 18.1 Acceptance Criteria
1. For any evaluation period, $\sum \text{Opening Dr} \equiv \sum \text{Opening Cr}$ and $\sum \text{Closing Dr} \equiv \sum \text{Closing Cr}$.
2. Expanding group `1000 - ASSETS` displays child accounts with correct subtotal rollups.
3. Exporting to XLSX generates valid Excel file with working sum formulas.

---

## 19. Performance Budgets and Optimization Targets

- Full Chart of Accounts (500+ accounts) aggregation latency: $< 350\text{ms}$.
- Tree expand/collapse DOM update: $< 16\text{ms}$ (60 FPS).

---

## 20. Future Enhancements and Scalability Roadmap

1. **Comparative Prior Year Analysis**: Multi-year column comparison (FY 2026-27 vs FY 2025-26).
2. **Automated Balance Sheet & P&L Generation**: Instant synthesis of statutory Schedule III Balance Sheet and Profit & Loss statement from Trial Balance nodes.

---

## 21. Sign-off and Approval Matrix

| Stakeholder Role | Name / Title | Date | Signature / Status |
|---|---|---|---|
| **Chief Financial Officer** | Krishnan Venkatachalam (CFO) | 16/10/2026 | **APPROVED** |
| **Lead Architect** | Enterprise Garments Solutions | 16/10/2026 | **APPROVED** |
| **Senior Audit Partner** | Sivakumar & Co. (Chartered Accountants)| 16/10/2026 | **APPROVED** |
