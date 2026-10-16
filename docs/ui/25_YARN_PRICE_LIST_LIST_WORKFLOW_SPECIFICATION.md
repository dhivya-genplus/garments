# Yarn Price List Register & Management Screen Specification

| Standard Code | Screen ID | Target Platform | API Version | Document Version | Date | Status |
|---|---|---|---|---|---|---|
| **STD-UI-001** | **`SCR-PRIC-001-LIST`** | Next.js 14 (App Router) + TypeScript | `v1.2` (Django 5 DRF) | `v1.0.0` | 16/10/2026 | **APPROVED FOR IMPLEMENTATION** |

---

## 1. Document Overview, Version, Scope, and Status

### 1.1 Purpose
This specification defines the complete technical architecture, real-time telemetry metrics, status segmentation tabs, multi-parameter filtering, batch operations, and responsive data grid for the **Yarn Price List Register & Management Screen** (`SCR-PRIC-001-LIST`).

In modern garment and textile manufacturing enterprises, managing hundreds of active and historical yarn rate agreements requires a centralized, high-density dashboard. This register serves as the command center for:
1. **Commercial Contract Governance**: Tracking all active raw material agreements across spinning mills and commercial buyer catalogs.
2. **Contract Expiry Watchdog**: Providing early warning alerts for rate cards expiring within 15 days to prevent unmanaged spot rate procurement.
3. **Multi-Dimension Filtering**: Enabling instant searching across list types (`PURCHASE` vs `SALES`), party contracts (specific mills vs buyers), and general company-wide benchmarks.
4. **Operational Efficiency**: Providing direct shortcuts to create, edit, print rate cards, export Excel spreadsheets, and trigger seasonal rollovers.

### 1.2 Scope
- **Entities Handled**: Parent header [`tm_price_list`](file:///d:/Codebase/Garments/backend/apps/pricing/models.py) (`PriceList`) with aggregate item slab counts from [`tm_price_list_item`](file:///d:/Codebase/Garments/backend/apps/pricing/models.py).
- **Country Pack**: India (`IN`) — Indian Rupee (`₹`), Indian numerical grouping (`12,34,567.89`), Date format (`DD/MM/YYYY`), Rates displayed to 4 decimal places (`0.0000`).
- **Target Route**: `/pricing/yarn-price-lists`.

---

## 2. Module Details, Screen ID, Route, Access Privileges, and API Endpoints

### 2.1 Core Metadata

| Parameter | Specification |
|---|---|
| **Module** | `Module 9 — Commercial Pricing Engine` |
| **Screen ID** | `SCR-PRIC-001-LIST` |
| **Frontend Route** | `/pricing/yarn-price-lists` |
| **File Location** | `app/(app)/pricing/yarn-price-lists/page.tsx` |
| **Required Privilege** | `pricing_manage.can_read` (View register); `pricing_manage.can_export` (Excel/PDF export) |
| **Authorized Roles** | `SUPER_ADMIN`, `ADMIN_USER`, `COMPANY_USER` (All procurement, commercial, sales, and costing personnel) |
| **Country Pack** | `IN` (India: Currency INR `₹`, Date `DD/MM/YYYY`, Weights in `Kg`, Rates [4 dp]) |

### 2.2 Primary API Endpoints

| HTTP Method | API Path | Privilege / Scope | Description |
|---|---|---|---|
| `GET` | `/api/v1/pricing/lists/` | `can_read` | Fetch all company price lists with filtering (`list_type`, `scope`, `party_id`) |
| `DELETE` | `/api/v1/pricing/lists/{id}/` | `can_delete` | Soft-delete a selected price list (`record_status = 'D'`) |
| `GET` | `/api/v1/masters/parties/?party_type=MILL,SUPPLIER,CUSTOMER`| `can_read` | Populate filter combobox for spinning mills and buyer parties |
| `GET` | `/api/v1/pricing/resolve/` | `can_read` | Quick rate simulation popover query |

---

## 3. UI Layout, Screen Blueprint, and Visual Mockup (1440px+ Wireframe)

```
+-----------------------------------------------------------------------------------------------------------------------------+
| GARMENTS ERP — Commercial Pricing Engine                                     Company: ABC Textiles Ltd | FY: 2026-2027      |
+-----------------------------------------------------------------------------------------------------------------------------+
| TOP BREADCRUMB: Pricing Engine > Yarn Price Lists                                                                           |
| YARN PRICE LISTS & RATE CARDS            [🔍 Quick Search (/) ]   [⚡ Filter Drawer (F)]   [📥 Export]   [+ Create Price List (N)]|
+-----------------------------------------------------------------------------------------------------------------------------+
| +-------------------------+  +-------------------------+  +-------------------------+  +--------------------------+         |
| | KPI 1: ACTIVE CONTRACTS |  | KPI 2: PURCHASE LISTS   |  | KPI 3: SALES RATE CARDS |  | KPI 4: EXPIRING IN 15 DAYS|        |
| | 28 Active Agreements    |  | 18 Mill Contracts       |  | 10 Buyer Catalogs       |  | 4 Contracts Expiring Soon|        |
| | (3 Base Lists, 25 Party)|  | Avg 30s: ₹341.2000/Kg   |  | Avg Margin: +14.2%      |  | [Review Renewals ->]     |        |
| +-------------------------+  +-------------------------+  +-------------------------+  +--------------------------+         |
+-----------------------------------------------------------------------------------------------------------------------------+
| STATUS TABS:                                                                                                                |
| [ All Lists (34) ]  [★ Purchase / Mills (20) ]  [ Sales / Buyers (14) ]  [ Party-Specific (29) ]  [ General Base (5) ]  [ Expired (6) ] |
+-----------------------------------------------------------------------------------------------------------------------------+
| BULK ACTION BAR (Selected: 0 rows)                   Showing 1-10 of 34 Price Lists               [ Sort: Valid To (Asc) v ]|
+-----------------------------------------------------------------------------------------------------------------------------+
| [ ] | List Code       | Rate Card Title                  | Type      | Scope          | Party / Mill           | Slabs | Validity Period         | Status     | Actions         |
|-----+-----------------+----------------------------------+-----------+----------------+------------------------+-------+-------------------------+------------+-----------------|
| [ ] | YPL-202610-0012 | Ramco Mills Q4 Contract 30s/40s  | PURCHASE  | PARTY_SPECIFIC | Ramco Mills Ltd        |     5 | 16/10/2026 - 31/12/2026 | ● ACTIVE   | [Edit] [Print] v|
| [ ] | YPL-202610-0011 | SVT Spinning Standard Hosiery    | PURCHASE  | PARTY_SPECIFIC | SVT Spinning Mills     |     4 | 01/10/2026 - 31/10/2026 | ▲ 15d LEFT | [Edit] [Print] v|
| [ ] | YPL-202610-0008 | Company Standard Procurement Base| PURCHASE  | GENERAL (DEF)  | -- Company Base --     |     8 | 01/04/2026 - 31/03/2027 | ● ACTIVE   | [Edit] [Print] v|
| [ ] | YPL-202610-0007 | Premier Knittings Buyer Catalog  | SALES     | PARTY_SPECIFIC | Premier Knittings P Ltd|     6 | 15/09/2026 - 15/12/2026 | ● ACTIVE   | [Edit] [Print] v|
| [ ] | YPL-202609-0004 | KPR Mill Q3 Combed Contract      | PURCHASE  | PARTY_SPECIFIC | KPR Mill Limited       |     3 | 01/07/2026 - 30/09/2026 | ✖ EXPIRED  | [Clone] [Print]v|
| [ ] | YPL-202609-0002 | Export Buyer Standard Catalog    | SALES     | GENERAL (DEF)  | -- Standard Export --  |     7 | 01/04/2026 - 31/03/2027 | ● ACTIVE   | [Edit] [Print] v|
+-----------------------------------------------------------------------------------------------------------------------------+
| PAGINATION DOCK:                                                                                                            |
| Displaying 1-10 of 34 Records | Page Size: [ 10 v ]                          [|<] [< Prev]  Page 1 of 4  [Next >] [>|]       |
+-----------------------------------------------------------------------------------------------------------------------------+
```

---

## 4. Telemetry KPI Cards Definition

The register displays four real-time telemetry cards at the top of the viewport:

| KPI Card | Computed Metric | Purpose & Drill-Down Action |
|---|---|---|
| **Active Contracts** | $\text{Count}(record\_status = \text{'A'} \land \text{valid\_to} \ge \text{today})$ | Total enforceable price lists. Clicking filters to active lists. |
| **Purchase Lists** | $\text{Count}(list\_type = \text{'PURCHASE'} \land record\_status = \text{'A'})$ | Raw material procurement agreements with spinning mills. Displays current average 30s count benchmark rate. |
| **Sales Rate Cards** | $\text{Count}(list\_type = \text{'SALES'} \land record\_status = \text{'A'})$ | Active commercial selling catalogs quoted to buyers. |
| **Expiring in 15 Days**| $\text{Count}(\text{valid\_to} \text{ between } \text{today} \text{ and } \text{today}+15\text{d})$ | High-priority contract renewals. Clicking switches directly to Expiring tab. |

---

## 5. Status Segmentation Tabs & Filter System

### 5.1 Tab Definitions

- **`All Lists`**: Comprehensive register without type restriction.
- **`Purchase / Mills`**: Filters `list_type = PURCHASE`.
- **`Sales / Buyers`**: Filters `list_type = SALES`.
- **`Party-Specific`**: Filters `scope = PARTY_SPECIFIC`.
- **`General Base`**: Filters `scope = GENERAL` (company-wide fallbacks).
- **`Expired`**: Filters `valid_to < today`.

### 5.2 Filter Drawer Parameters (`Shift + F` / `F`)

When opened, the slide-over filter drawer allows combining:
- **Search Query**: Matches against `price_list_code`, `price_list_name`, and party name.
- **List Type**: Dropdown (`All`, `Purchase`, `Sales`).
- **Scope**: Dropdown (`All`, `Party-Specific`, `General Base`).
- **Party Selector**: Searchable combobox linking to spinning mills or customer buyers.
- **Validity Window Range**: Date range filter (`Valid From` and `Valid To`).
- **Default Lists Only**: Checkbox to isolate company default lists.

---

## 6. Data Table Columns & Row Actions

| Column Title | Width | Sortable | Display Format & Badges |
|---|---|---|---|
| **Checkbox** | 40px | No | Row selector for batch export. |
| **List Code** | 130px | Yes | Monospace font (e.g. `YPL-202610-0012`). Clicking navigates to Edit. |
| **Rate Card Title** | 220px | Yes | Bold text with subtle description tooltip on hover. |
| **Type** | 100px | Yes | Emerald pill for `PURCHASE`, Indigo pill for `SALES`. |
| **Scope** | 120px | Yes | Blue pill for `PARTY_SPECIFIC`, Purple badge `GENERAL (DEF)` if default. |
| **Party / Mill** | 180px | Yes | Party Name + Vendor Code. Shows *"-- Company Base --"* if General. |
| **Slabs** | 70px | Yes | Count of defined slabs (e.g. `5`). |
| **Validity Period** | 170px | Yes | `DD/MM/YYYY - DD/MM/YYYY`. Displays remaining days badge. |
| **Status** | 110px | Yes | Green `● ACTIVE`, Amber `▲ 15d LEFT`, Gray `✖ EXPIRED`, Yellow `○ DRAFT`. |
| **Actions** | 110px | No | Quick action buttons: `[Edit]`, `[Print]`, overflow menu `[···]`. |

### 6.1 Row Overflow Menu Actions (`[···]`)
- **`Edit Rates`**: Opens `/pricing/yarn-price-lists/[id]/edit`.
- **`Print / PDF Rate Card`**: Opens `/pricing/yarn-price-lists/[id]/print`.
- **`Clone as New Season`**: Pre-populates new creation form with this list's lines.
- **`Test Rate Resolution`**: Opens quick sandbox popover to test an order against this list.
- **`Soft Delete`**: Moves list to deleted status (prompts confirmation modal).

---

## 7. Batch Operations Bar

When one or more rows are selected via checkboxes:
- **`Export Selected (Excel / CSV)`**: Generates an consolidated Excel workbook with count, slab, and rate schedules.
- **`Print Batch Rate Cards`**: Compiles selected rate cards into a sequential PDF print job.
- **`Extend Validity (+30 Days)`**: Bulk updates `valid_to` date across selected active lists.

---

## 8. Fast Search & Keyboard Navigation

| Key Shortcut | Scope | Action |
|---|---|---|
| `/` | Page Level | Focuses the Quick Search input box. |
| `N` | Page Level | Navigates to `/pricing/yarn-price-lists/new` (New Price List). |
| `F` | Page Level | Toggles the slide-over Filter Drawer. |
| `E` | Table Row | Edits the currently focused price list row. |
| `P` | Table Row | Opens Print preview for the focused row. |
| `J / K` | Table | Navigates down/up through table rows. |
| `X` | Table Row | Toggles checkbox selection for the active row. |

---

## 9. Implementation Sequence & Acceptance Checklist

### 9.1 Milestones
- [ ] **Milestone 1**: Scaffold `/pricing/yarn-price-lists` and integrate `GET /api/v1/pricing/lists/`.
- [ ] **Milestone 2**: Build Telemetry KPI cards and status tabs with real-time counts.
- [ ] **Milestone 3**: Implement table sorting, status badges, and validity countdown badges.
- [ ] **Milestone 4**: Build slide-over Filter Drawer with debounce search (300ms).
- [ ] **Milestone 5**: Implement row actions (`Edit`, `Print`, `Clone`, `Delete`).

### 9.2 Acceptance Checklist
- [ ] Register displays all active price lists with accurate slab counts.
- [ ] Filtering by `list_type = PURCHASE` isolates mill procurement contracts.
- [ ] Contracts expiring in $\le 15$ days display amber urgency badges.
- [ ] Clicking `[Clone]` opens `/new` with pre-filled counts and slabs.
- [ ] Soft deletion removes list from active view and sets `record_status = 'D'`.
- [ ] Currency and rates display in INR (`₹`) to 4 decimal places.
