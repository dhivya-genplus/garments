# Yarn Sales Return (Credit Note) Register & List Specification

| Standard Code | Screen ID | Target Platform | API Version | Document Version | Date | Status |
|---|---|---|---|---|---|---|
| **STD-UI-001** | **`SCR-SALE-002-LIST`** | Next.js 14 (App Router) + TypeScript | `v1.2` (Django 5 DRF) | `v1.0.0` | 15/10/2026 | **APPROVED FOR IMPLEMENTATION** |

---

## 1. Document Overview, Version, Scope, and Status

### 1.1 Purpose
This specification details the user experience, real-time KPI metrics, search filtering, column layouts, pagination, and export capabilities for the **Yarn Sales Return Register & List Screen** (`SCR-SALE-002-LIST`).

This screen serves as the operational monitoring desk for tracking customer returns, auditing quality defects (shade mismatches, count variations), managing credit note liabilities, and reconciling returned physical stock back into godown inventory.

### 1.2 Scope
- **Route**: `/sales/yarn-sales-returns`
- **Data Entity**: [`parent_yarn_sales_return_table`](file:///d:/Codebase/Garments/backend/apps/sales/models.py) (`tm_yarn_sales_return`) joined with customer, mill, and linked sales invoice records.
- **Reporting Period**: Defaulting to the current active Financial Year (`01/04/2026 - 31/03/2027`).

---

## 2. Module Details, Screen ID, Route, and Access Privileges

### 2.1 Core Metadata

| Parameter | Specification |
|---|---|
| **Module** | `Module 5 — Commercial Sales & Customer Returns` |
| **Screen ID** | `SCR-SALE-002-LIST` |
| **Frontend Route** | `/sales/yarn-sales-returns` |
| **File Location** | `app/(app)/sales/yarn-sales-returns/page.tsx` |
| **Required Privilege** | `sales_yarn_return.can_read` |
| **Authorized Roles** | `SUPER_ADMIN`, `ADMIN_USER`, `COMPANY_USER` (Sales Coordinator, Quality Head, Commercial Accountant) |
| **Country Pack** | `IN` (India: Currency `₹`, Date `DD/MM/YYYY`, Number Grouping `12,34,567.89`) |

### 2.2 Primary API Endpoints

| HTTP Method | API Path | Parameters | Description |
|---|---|---|---|
| `GET` | `/api/v1/sales/yarn-sales-returns/` | `search`, `customer`, `warehouse`, `sales_invoice`, `ordering`, `page`, `page_size` | Fetch paginated sales return records with search and filter parameters |
| `GET` | `/api/v1/sales/yarn-sales-returns/export/`| `format=csv` / `format=xlsx` | Export filtered credit note and return register |

---

## 3. UI Layout & Screen Wireframe

```
+-----------------------------------------------------------------------------------------------------------------------------+
| GARMENTS ERP — Commercial Sales Desk                                         Company: ABC Textiles Ltd | FY: 2026-2027      |
+-----------------------------------------------------------------------------------------------------------------------------+
| CUSTOMER YARN SALES RETURNS REGISTER (CREDIT NOTES)                             [Export Excel]  [+ NEW SALES RETURN (F4)]   |
+-----------------------------------------------------------------------------------------------------------------------------+
| TELEMETRY & RETURN RATE KPIS (Current FY: 2026-2027)                                                                        |
| +-------------------------+ +-------------------------+ +-------------------------+ +-------------------------+            |
| | TOTAL CREDIT VALUE      | | TOTAL WEIGHT RETURNED   | | TOTAL BAGS RETURNED     | | RETURN RATE %           |            |
| | ₹4,82,900.00            | | 1,420.500 Kg            | | 31 Bags                 | | 2.94% of Gross Sales    |            |
| | 8 Active Credit Notes   | | Re-credited to Godowns  | | Standard 45.360 Kg/Bag  | | Industry Norm: < 3.50%  |            |
| +-------------------------+ +-------------------------+ +-------------------------+ +-------------------------+            |
+-----------------------------------------------------------------------------------------------------------------------------+
| [ All Returns (8) ]  [ Against Invoice (7) ]  [ Direct Returns (1) ]  [ Shade Mismatches (5) ]  [ Cancelled (1) ]           |
| Search: [ Search by Return #, Invoice #, Customer, Mill, Lot... ] [ Warehouse: All v ] [ Date: This Month v ] [Filters]     |
+-----------------------------------------------------------------------------------------------------------------------------+
| SALES RETURN REGISTER DATA TABLE                                                                                            |
| [ ] | Return #        | Date       | Customer Name            | Linked Invoice  | Reason              | Bags | Weight (Kg)| Net Credit (₹) | Status | Actions |
|-----+-----------------+------------+--------------------------+-----------------+---------------------+------+------------+----------------+--------+---------|
| [ ] | YSRET-202610-005| 15/10/2026 | Premier Knittings Ltd    | YSAL-202610-0018| Shade Variation     |    5 |    226.800 |      80,968.00 | Posted | [P] [E] |
| [ ] | YSRET-202610-004| 12/10/2026 | Texspin Exports Pvt Ltd  | YSAL-202610-0016| Uneven Count / Slub |   10 |    453.600 |    1,61,935.00 | Posted | [P] [E] |
| [ ] | YSRET-202610-003| 08/10/2026 | Sree Balaji Fabrics      | YSAL-202610-0012| Excess Dispatch     |    4 |    181.440 |      64,774.00 | Posted | [P] [E] |
| [ ] | YSRET-202610-002| 05/10/2026 | Classic Knits India      | YSAL-202610-0009| Transit Damage      |    6 |    272.160 |      97,161.00 | Posted | [P] [E] |
| [ ] | YSRET-202610-001| 02/10/2026 | Maharaja Weaving Mills   | Direct Return   | Color Bleeding      |    6 |    286.500 |      78,062.00 | Posted | [P] [E] |
+-----------------------------------------------------------------------------------------------------------------------------+
| Showing 1 - 5 of 8 Returns                                   [Rows per page: 20 v]   [<< First] [< Prev] [1] [Next >]       |
+-----------------------------------------------------------------------------------------------------------------------------+
```

---

## 4. Telemetry Metric KPI Cards

1. **Total Credit Value**: Sum of net credit notes ($\sum \text{total\_amount}$) displayed in Indian currency format (`₹4,82,900.00`).
2. **Total Weight Returned**: Kilograms re-credited back to stock ($\sum \text{quantity}$) formatted to 3 decimal places (`1,420.500 Kg`).
3. **Total Bags Returned**: Total physical bags accepted into warehouses ($\sum \text{bag}`).
4. **Return Rate %**: Ratio of returned weight to gross sales weight in the period, benchmarked against quality tolerances:
   $$\text{Return Rate \%} = \frac{\sum \text{Return Quantity}}{\sum \text{Sales Quantity}} \times 100$$

---

## 5. Filtering, Search Debounce, and Tab Scopes

### 5.1 Tab Scopes
- **All Returns**: Returns all active records (`status=1`).
- **Against Invoice**: Filters returns linked to an original invoice (`sales_invoice__isnull=False`).
- **Direct Returns**: Filters standalone trade returns (`sales_invoice__isnull=True`).
- **Shade Mismatches**: Filters returns where `return_reason` contains "Shade".
- **Cancelled / Void**: Filters soft-deleted/reversed returns (`status=0`).

### 5.2 Search Engine
- Search bar executes debounced requests (300ms) across fields:
  - `return_number` (e.g. `YSRET-202610-0005`)
  - `sales_invoice__invoice_number` (e.g. `YSAL-202610-0018`)
  - `customer__name`
  - `mill__name`
  - `lot_no`

---

## 6. Table Column Definitions

| Col # | Column Header | Data Key | Alignment | Width | Format |
|---|---|---|---|---|---|
| 1 | `[ ]` | Multi-select Checkbox | Center | 40px | Selection box |
| 2 | **Return Number** | `return_number` | Left | 160px | Badge link to Edit / View |
| 3 | **Return Date** | `return_date` | Left | 110px | Date (`DD/MM/YYYY`) |
| 4 | **Customer Name** | `customer_name` | Left | 210px | Text with tooltip |
| 5 | **Linked Invoice**| `sales_invoice_number` | Left | 160px | Link to invoice or `Direct Return` badge |
| 6 | **Return Reason** | `return_reason` | Left | 170px | Reason tag |
| 7 | **Bags** | `bag` | Right | 80px | Integer (`5`) |
| 8 | **Weight (Kg)** | `quantity` | Right | 120px | Decimal `226.800 Kg` |
| 9 | **Net Credit (₹)**| `total_amount` | Right | 140px | Currency `₹80,968.00` (Bold) |
| 10 | **Status** | `status_badge` | Center | 90px | Green (Posted), Red (Cancelled) |
| 11 | **Actions** | Quick Action Menu | Center | 90px | Print Credit Note, View/Edit |

---

## 7. Row Actions & Batch Operations

- **Print Icon `[P]`**: Opens Credit Note document preview `/sales/yarn-sales-returns/[id]/print`.
- **Edit Icon `[E]`**: Navigates to `/sales/yarn-sales-returns/[id]/edit`.
- **[Export Selected to Excel]**: Downloads detailed Excel sheet containing itemized return lines and credit note values.

---

## 8. Developer Acceptance Criteria

- [ ] Route `/sales/yarn-sales-returns` renders high-density return table with 20 items per page.
- [ ] Real-time telemetry KPI cards accurately calculate return value and return rate %.
- [ ] 300ms debounced search filters accurately across return number, original invoice, and buyer.
- [ ] All monetary values format with Indian Rupee symbol (`₹`) and standard Indian numbering grouping.
