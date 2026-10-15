# Yarn Sales Tax Invoice Register & List Specification

| Standard Code | Screen ID | Target Platform | API Version | Document Version | Date | Status |
|---|---|---|---|---|---|---|
| **STD-UI-001** | **`SCR-SALE-001-LIST`** | Next.js 14 (App Router) + TypeScript | `v1.2` (Django 5 DRF) | `v1.0.0` | 15/10/2026 | **APPROVED FOR IMPLEMENTATION** |

---

## 1. Document Overview, Version, Scope, and Status

### 1.1 Purpose
This specification details the user experience, real-time KPI metrics, search filtering, column layouts, pagination, and export capabilities for the **Yarn Sales Tax Invoice Register & List Screen** (`SCR-SALE-001-LIST`).

This screen serves as the operational command dashboard for the commercial sales department, accounts receivable team, and management to track daily billing, monitor dispatch volumes (Bags and Kg), analyze revenue, and audit GST output taxes across the enterprise.

### 1.2 Scope
- **Route**: `/sales/yarn-sales`
- **Data Entity**: [`parent_yarn_sales_table`](file:///d:/Codebase/Garments/backend/apps/sales/models.py) (`tm_yarn_sales`) joined with customer and mill master records.
- **Reporting Period**: Defaulting to the current active Financial Year (`01/04/2026 - 31/03/2027`).

---

## 2. Module Details, Screen ID, Route, and Access Privileges

### 2.1 Core Metadata

| Parameter | Specification |
|---|---|
| **Module** | `Module 5 — Commercial Sales & Customer Returns` |
| **Screen ID** | `SCR-SALE-001-LIST` |
| **Frontend Route** | `/sales/yarn-sales` |
| **File Location** | `app/(app)/sales/yarn-sales/page.tsx` |
| **Required Privilege** | `sales_yarn.can_read` |
| **Authorized Roles** | `SUPER_ADMIN`, `ADMIN_USER`, `COMPANY_USER` (Sales, Accounts, Dispatch, Management) |
| **Country Pack** | `IN` (India: Indian Grouping `₹12,34,567.89`, Date `DD/MM/YYYY`) |

### 2.2 Primary API Endpoints

| HTTP Method | API Path | Parameters | Description |
|---|---|---|---|
| `GET` | `/api/v1/sales/yarn-sales/` | `search`, `yarn_type`, `customer`, `warehouse`, `ordering`, `page`, `page_size` | Fetch paginated sales invoice records with filter parameters |
| `GET` | `/api/v1/sales/yarn-sales/export/` | `format=csv` / `format=xlsx` | Export filtered invoice register with line-item and tax breakdown |

---

## 3. UI Layout & Screen Wireframe

```
+-----------------------------------------------------------------------------------------------------------------------------+
| GARMENTS ERP — Commercial Sales Desk                                         Company: ABC Textiles Ltd | FY: 2026-2027      |
+-----------------------------------------------------------------------------------------------------------------------------+
| COMMERCIAL YARN SALES REGISTER                                                  [Export Excel]  [+ NEW SALES INVOICE (F4)]  |
+-----------------------------------------------------------------------------------------------------------------------------+
| TELEMETRY & SALES REVENUE KPIS (Current FY: 2026-2027)                                                                      |
| +-------------------------+ +-------------------------+ +-------------------------+ +-------------------------+            |
| | TOTAL BILLED TURNOVER   | | TOTAL NET WEIGHT SOLD   | | TOTAL BAGS DISPATCHED   | | TOTAL GST COLLECTED     |            |
| | ₹48,25,900.00           | | 14,250.000 Kg           | | 314 Bags                | | ₹2,41,295.00            |            |
| | +18.4% vs last month    | | 42 Active Invoices      | | Standard 45.360 Kg/Bag  | | CGST: ₹1.20L | SGST: ₹1.20L          |
| +-------------------------+ +-------------------------+ +-------------------------+ +-------------------------+            |
+-----------------------------------------------------------------------------------------------------------------------------+
| [ All Invoices (42) ]  [ Grey Yarn (28) ]  [ Dyed Yarn (14) ]  [ Drafts (2) ]  [ Cancelled (1) ]                            |
| Search: [ Search by Invoice No, Customer, Mill, Lot...          ] [ Warehouse: All v ] [ Date Range: This Month v ] [Filters]|
+-----------------------------------------------------------------------------------------------------------------------------+
| INVOICE REGISTER DATA TABLE                                                                                                 |
| [ ] | Invoice #       | Date       | Customer Name            | Godown   | Category | Bags | Weight (Kg) | Subtotal (₹) | Total (₹)   | Status  | Actions |
|-----+-----------------+------------+--------------------------+----------+----------+------+-------------+--------------+-------------+---------+---------|
| [ ] | YSAL-202610-0018| 15/10/2026 | Premier Knittings Ltd    | Central  | GREY     |   35 |   1,587.600 |  5,63,598.00 | 5,91,778.00 | Posted  | [P] [E] |
| [ ] | YSAL-202610-0017| 14/10/2026 | Sree Balaji Fabrics      | Spinning | DYED     |   20 |     907.200 |  3,81,024.00 | 4,00,075.00 | Posted  | [P] [E] |
| [ ] | YSAL-202610-0016| 14/10/2026 | Texspin Exports Pvt Ltd  | Central  | GREY     |   50 |   2,268.000 |  7,71,120.00 | 8,09,676.00 | Posted  | [P] [E] |
| [ ] | YSAL-202610-0015| 12/10/2026 | Maharaja Weaving Mills   | Dyeing   | DYED     |   12 |     544.320 |  2,28,614.00 | 2,40,045.00 | Posted  | [P] [E] |
| [ ] | YSAL-202610-0014| 10/10/2026 | Classic Knits India      | Central  | GREY     |   10 |     453.600 |  1,54,224.00 | 1,61,935.00 | Posted  | [P] [E] |
+-----------------------------------------------------------------------------------------------------------------------------+
| Showing 1 - 5 of 42 Invoices                                 [Rows per page: 20 v]   [<< First] [< Prev] [1] [2] [3] [Next >]|
+-----------------------------------------------------------------------------------------------------------------------------+
```

---

## 4. Telemetry Metric KPI Cards

Calculated dynamically from the current filter criteria:
1. **Total Billed Turnover**: Net invoice value ($\sum \text{total\_amount}$) displayed in Indian currency format (`₹48,25,900.00`).
2. **Total Net Weight Sold**: Sum of physical kilogram weight ($\sum \text{quantity}$) formatted to 3 decimal places (`14,250.000 Kg`).
3. **Total Bags Dispatched**: Total commercial bags delivered ($\sum \text{bag}`).
4. **Total GST Collected**: Combined output tax liability ($\sum \text{tax\_amount}$), with breakdown pill showing Intra-state CGST/SGST vs Inter-state IGST.

---

## 5. Filtering, Search Debounce, and Tab Scopes

### 5.1 Tab Scopes
- **All Invoices**: Returns all active records (`status=1`).
- **Grey Yarn**: Filters `yarn_type=GREY`.
- **Dyed Yarn**: Filters `yarn_type=DYED`.
- **Drafts**: Filters `is_authorized=0` (Unposted commercial billing drafts).
- **Cancelled / Void**: Filters `status=0` (Auditable soft-deleted invoices).

### 5.2 Search Engine
- Search bar executes debounced requests (300ms) across backend fields:
  - `invoice_number` (e.g. `YSAL-202610-0018`)
  - `customer__name` (e.g. `Premier Knittings`)
  - `mill__name` (e.g. `Ramco`)
  - `lot_no` (e.g. `RM-901`)

### 5.3 Filter Drawer
- Accessible via the **[Filters]** button:
  - **Date Range**: Today, This Week, This Month, Current Quarter, Custom Date Range.
  - **Warehouse Godown**: Multi-select dropdown.
  - **Customer Party**: Searchable combobox.
  - **Spinning Mill**: Searchable combobox.
  - **Tax Bracket**: 5% GST, 12% GST, Nil/Exempt.

---

## 6. Table Column Definitions

| Col # | Column Header | Data Key | Alignment | Width | Format |
|---|---|---|---|---|---|
| 1 | `[ ]` | Multi-select Checkbox | Center | 40px | Selection box |
| 2 | **Invoice Number** | `invoice_number` | Left | 160px | Badge link to Edit / View |
| 3 | **Invoice Date** | `invoice_date` | Left | 110px | Date (`DD/MM/YYYY`) |
| 4 | **Customer Name** | `customer_name` | Left | 220px | Truncated text with tooltip |
| 5 | **Godown** | `warehouse_name` | Left | 130px | Pill badge |
| 6 | **Category** | `yarn_type` | Center | 90px | `GREY` (Grey) / `DYED` (Purple) |
| 7 | **Bags** | `bag` | Right | 80px | Integer (`35`) |
| 8 | **Net Weight (Kg)**| `quantity` | Right | 120px | Decimal `1,587.600 Kg` |
| 9 | **Subtotal (₹)** | `subtotal` | Right | 130px | Currency `₹5,63,598.00` |
| 10 | **Net Total (₹)** | `total_amount` | Right | 140px | Currency `₹5,91,778.00` (Bold) |
| 11 | **Status** | `status_badge` | Center | 90px | Green (Posted), Amber (Draft) |
| 12 | **Actions** | Quick Action Menu | Center | 90px | Print Icon, View/Edit Icon |

---

## 7. Row Actions & Batch Operations

### 7.1 Single Row Actions
- **Print Icon `[P]`**: Opens `/sales/yarn-sales/[id]/print` directly in new tab.
- **Edit / View Icon `[E]`**: Navigates to `/sales/yarn-sales/[id]/edit`.

### 7.2 Multi-Select Batch Operations
Selecting multiple rows activates the top floating action bar:
- **[Export Selected to Excel]**: Generates Excel spreadsheet containing itemized line rows.
- **[Bulk Print Invoices]**: Prepares unified printable multi-invoice PDF stream.

---

## 8. Developer Acceptance Criteria

- [ ] Route `/sales/yarn-sales` renders data table with 20 items per page.
- [ ] Telemetry KPI cards compute accurately based on active filters and current financial year.
- [ ] Tab switching immediately triggers scoped API queries.
- [ ] 300ms debounced search filters accurately across invoice number, buyer, and mill.
- [ ] Indian currency (`₹`) and number grouping (`12,34,567.89`) are formatted consistently across all rows.
