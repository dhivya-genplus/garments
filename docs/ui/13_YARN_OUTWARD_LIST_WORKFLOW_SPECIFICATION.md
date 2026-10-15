# UI & Frontend Workflow Specification: Yarn Outward Delivery Challan (DC) List & Register Screen

## 1. Document Overview, Version, Scope, and Status

- **Document Title**: Yarn Outward Delivery Challan (DC) Register & List Page UI & Frontend Developer Specification
- **Screen ID**: `SCR-INVN-002-LIST`
- **Document Version**: `v1.0.0`
- **Last Updated**: `15/10/2026`
- **Target Audience**: Frontend Engineers, Full-Stack Developers, QA Engineers, and Technical Product Owners
- **Implementation Status**: `Ready for Review / Implementation`
- **Scope**: Covers the high-density register view, real-time KPI telemetry cards, status tab segmentation (All, To Knitting, To Dyeing, Purchase Returns, Pending at Processor, Completed), multi-parameter search and filtering, batch actions, pagination, API integration (`GET /api/v1/inventory/yarn-outwards/`), keyboard shortcuts, and developer acceptance checklists for the Yarn Outward List page in the Garments ERP & CRM system.

---

## 2. Module Details, Screen ID, Route, Access Privileges, and API Endpoints

### 2.1 Core Metadata

| Parameter | Specification |
|---|---|
| **Module** | `Module 4 — Inventory & Godown Stock Ledger` |
| **Screen ID** | `SCR-INVN-002-LIST` |
| **Frontend Route** | `/inventory/yarn-outward` |
| **File Location** | `app/(app)/inventory/yarn-outward/page.tsx` |
| **Required Privilege** | `inventory_yarn_outward.can_read` (View list and filters); `inventory_yarn_outward.can_export` (Excel/CSV export) |
| **Authorized Roles** | `SUPER_ADMIN`, `ADMIN_USER`, `COMPANY_USER` (Dispatch Officers, Godown Managers, Merchandisers) |
| **Country Pack** | `IN` (India: Currency INR `₹`, Date `DD/MM/YYYY`, Number grouping `12,34,567.89`) |

### 2.2 Primary API Endpoints

| HTTP Method | API Path | Privilege / Scope | Description |
|---|---|---|---|
| `GET` | `/api/v1/inventory/yarn-outwards/` | `can_read` | Fetch paginated outward DC records with filtering (`search`, `outward_type`, `warehouse`, `destination_party`, `yarn_type`, `is_complete`) |
| `POST` | `/api/v1/inventory/yarn-outwards/{id}/authorize/` | `can_approve` | Authorize a draft DC, deducting live godown stock |
| `DELETE` | `/api/v1/inventory/yarn-outwards/{id}/` | `can_delete` | Cancel/Reverse an outward DC and restore godown stock (if zero receipts exist) |
| `GET` | `/api/v1/masters/warehouses/?record_status=A` | `can_read` | Populate filter dropdown for dispatch godowns |
| `GET` | `/api/v1/masters/parties/?party_type=KNITTER,DYER,MILL` | `can_read` | Populate filter dropdown for destination consignees |
| `GET` | `/api/v1/masters/yarn-counts/` | `can_read` | Populate filter dropdown for yarn counts |

---

## 3. UI Layout, Screen Blueprint, and Visual Mockup

### 3.1 Desktop Wireframe Layout (1440px+ Viewport)

```
+--------------------------------------------------------------------------------------------------------------------------+
| TOP BREADCRUMB: Inventory > Yarn Outward                                                                                  |
| Yarn Outward Register (DC)           [🔍 Quick Search (/) ]   [⚡ Filter (F)]   [📥 Export]   [+ New Outward DC (N)]       |
+--------------------------------------------------------------------------------------------------------------------------+
| +------------------------+  +------------------------+  +------------------------+  +--------------------------+ |
| | KPI 1: TOTAL DISPATCHES|  | KPI 2: TOTAL BAGS OUT  |  | KPI 3: TOTAL OUT WEIGHT|  | KPI 4: PENDING AT MILLS  | |
| | 176 DCs                |  | 14,200 Bags            |  | 6,44,112.000 Kg        |  | 1,42,800.000 Kg (22.1%)  | |
| +------------------------+  +------------------------+  +------------------------+  +--------------------------+ |
|                                                                                                                          |
| STATUS TABS: [ All Dispatches (176) ] [ To Knitting (112) ] [ To Dyeing (48) ] [ Returns (16) ] [ Pending at Processor (54) ]|
|                                                                                                                          |
| +----------------------------------------------------------------------------------------------------------------------+ |
| | HIGH-DENSITY ENTERPRISE DATA TABLE                                                                                   | |
| | [ ] | DC No & Date   | Type / Purpose    | Destination Party  | Source Godown | Bags | Dispatched | Processor Balance |...|
| |-----+----------------+-------------------+--------------------+---------------+------+------------+-------------------|---|
| | [ ] | YKNT-202610-31 | [KNITTING]        | Sri Ram Knitter    | Main Factory  | 50   | 2,268.000  | [██████████] 100% |...|
| |     | 15/10/2026     | Job Card #KP-0014 | Tirupur Unit-2     | Bay A-02      | Bags | Kg         | 2,268 Kg Pending  |   |
| |-----+----------------+-------------------+--------------------+---------------+------+------------+-------------------|---|
| | [ ] | YDYE-202610-18 | [DYEING]          | Sri Balaji Dyers   | Main Factory  | 100  | 4,536.000  | [██████░░░░]  40% |...|
| |     | 10/10/2026     | Navy Blue Shade   | Perundurai Unit    | Bay C-01      | Bags | Kg         | 1,814 Kg Pending  |   |
| +----------------------------------------------------------------------------------------------------------------------+ |
|                                                                                                                          |
| PAGINATION & DENSITY:                                                                                                    |
| Showing 1 - 20 of 176 DCs  | Rows per page: [ 20 v ]              [<<] [<]  Page 1 of 9  [>] [>>]                       |
+--------------------------------------------------------------------------------------------------------------------------+
```

---

## 4. Page Initialization, Query Parameters, and Hydration

When accessing `/inventory/yarn-outward`, URL search parameters preserve active view states:

```
/inventory/yarn-outward?status=knitting&warehouse=1&search=30s&page=1&page_size=20&ordering=-outward_date
```

| Query Parameter | Type | Default | Description |
|---|---|---|---|
| `status` | `string` | `'all'` | Tab filter: `'all'`, `'knitting'`, `'dyeing'`, `'return'`, `'pending'`, `'completed'` |
| `search` | `string` | `""` | Search text matching DC No, Destination Party, Vehicle No, Lot No |
| `warehouse` | `number` | `null` | Filter by Dispatch Godown ID (`warehouse_id`) |
| `destination_party`| `number` | `null` | Filter by Consignee Party ID (`destination_party_id`) |
| `yarn_type` | `string` | `null` | Filter by Yarn Category (`GREY`, `DYED`, `MELANGE`, etc.) |
| `page` | `number` | `1` | Pagination page number |
| `page_size` | `number` | `20` | Rows per page: `20`, `50`, `100` |
| `ordering` | `string` | `'-outward_date'` | Sorting column: `-outward_date`, `outward_number`, `-quantity` |

---

## 5. Real-Time KPI Telemetry Cards

Hydrated via aggregate selectors from the backend:

1. **Total Dispatches (`KPI 1`)**:
   - Total number of active outward Delivery Challans within the active financial year.
2. **Total Bags Dispatched (`KPI 2`)**:
   - Aggregate sum of physical yarn bags dispatched across all godowns.
3. **Total Outward Weight (`KPI 3`)**:
   - Total physical net weight in Kilograms (`Kg`), formatted to 3 decimal places.
4. **Active Pending at Processors (`KPI 4`)**:
   - Sum of unreturned yarn weight currently at subcontract knitting mills and dyehouses (`remaining_quantity`).

---

## 6. High-Density Data Table Column Specifications

| Col # | Column Header | Backend Field | Formatting & Visual Behavior |
|---|---|---|---|
| **1** | `[ ]` | `id` | Multi-select checkbox for bulk batch actions. |
| **2** | `DC No & Date` | `outward_number`, `outward_date` | Clickable link to `/inventory/yarn-outward/[id]`. Displays formatted date `DD/MM/YYYY`. |
| **3** | `Purpose / Type` | `outward_type`, `outward_type_display` | Badge: Blue for `[KNITTING]`, Purple for `[DYEING]`, Amber for `[RETURN]`. |
| **4** | `Destination Consignee`| `destination_party_name` | Consignee Name (Knitting Mill / Dyehouse / Spinning Mill). |
| **5** | `Source Godown` | `warehouse_name` | Source dispatch warehouse (e.g. `Main Factory Godown`). |
| **6** | `Yarn Count & Specs`| `yarn_count_name`, `color_shade_name` | Yarn count with color swatch badge if dyed. |
| **7** | `Bags Dispatched` | `bag` | Total number of bags unloaded (e.g. `50 Bags`). |
| **8** | `Dispatched (Kg)` | `quantity` | Bold net weight in Kg (e.g. `2,268.000 Kg`). |
| **9** | `Processor Balance`| `remaining_quantity`, `is_complete` | Progress bar showing pending balance at processor. Green check if `is_complete == 1`. |
| **10**| `Status` | `is_authorized` | Emerald Badge: `● Dispatched`; Amber Badge: `● Draft`. |
| **11**| `Actions` | — | Dropdown menu: `View Details`, `Edit (Draft only)`, `Print DC (PDF)`, `Cancel / Reverse`. |

---

## 7. Row Actions and Batch Operations

### 7.1 Single Row Actions

- **View Details**: Navigates to `/inventory/yarn-outward/[id]`.
- **Edit**: Navigates to `/inventory/yarn-outward/[id]/edit` (Available if `is_authorized == 0`).
- **Print DC Sheet**: Opens printable A4 PDF Delivery Challan at `/inventory/yarn-outward/[id]/print`.
- **Cancel / Reverse**: Triggers atomic stock rollback modal (Enabled only if `received_quantity == 0`).

### 7.2 Batch Operations Bar (Appears when $\ge 1$ row selected)

- **Authorize Selected Drafts**: Batch calls `POST /authorize/` for selected dispatches.
- **Export Selected to CSV / Excel**: Downloads selected DC rows as a spreadsheet.

---

## 8. Keyboard Shortcuts

| Shortcut | Scope | Action |
|---|---|---|
| `/` | Global Page | Focuses the Quick Search input box. |
| `F` | Global Page | Toggles open the Multi-Parameter Filter Drawer. |
| `N` | Global Page | Navigates to `/inventory/yarn-outward/new` to create a new DC. |
| `E` | Global Page | Triggers CSV/Excel export for the current filtered list. |
| `Esc` | Filter Drawer | Closes open drawers or clears search focus. |

---

## 9. Developer Acceptance Checklist

- [ ] **1. High-Density Table**: Table renders responsive rows with proper pagination and sorting.
- [ ] **2. Status Tabs**: Clicking tabs correctly filters `All`, `To Knitting`, `To Dyeing`, `Returns`, and `Pending`.
- [ ] **3. Search Debounce**: Quick search triggers after 300ms debounce without redundant queries.
- [ ] **4. Action Permissions**: "Edit" is only enabled for drafts; "Cancel" requires confirmation.
- [ ] **5. Navigation**: Clicking DC number opens the detail view; clicking Print opens the printable sheet.
- [ ] **6. KPI Telemetry**: Telemetry totals update accurately based on active financial year and company scope.
