# UI & Frontend Workflow Specification: Yarn Purchase Order (PO) List & Register Screen

## 1. Document Overview, Version, Scope, and Status

- **Document Title**: Yarn Purchase Order (PO) Register & List Page UI & Frontend Developer Specification
- **Screen ID**: `SCR-PROC-001-LIST`
- **Document Version**: `v1.0.0`
- **Last Updated**: `15/10/2026`
- **Target Audience**: Frontend Engineers, Full-Stack Developers, QA Engineers, and Technical Product Owners
- **Implementation Status**: `Ready for Review / Implementation`
- **Scope**: Covers the high-density register view, real-time KPI telemetry cards, status tab segmentation, multi-parameter search and filtering, live inward fulfillment progress bars, batch selection actions, pagination, API integration (`GET /api/v1/purchase/yarn-pos/`), keyboard shortcuts, and developer acceptance checklists for the Yarn PO List page in the Garments ERP & CRM system.

---

## 2. Module Details, Screen ID, Route, Access Privileges, and API Endpoints

### 2.1 Core Metadata

| Parameter | Specification |
|---|---|
| **Module** | `Module 3 — Procurement (Yarn PO)` |
| **Screen ID** | `SCR-PROC-001-LIST` |
| **Frontend Route** | `/procurement/yarn-po` |
| **File Location** | `app/(app)/procurement/yarn-po/page.tsx` |
| **Required Privilege** | `purchase_yarn_po.can_read` (View list and filters); `purchase_yarn_po.can_export` (Excel/PDF export) |
| **Authorized Roles** | `SUPER_ADMIN`, `ADMIN_USER`, `COMPANY_USER` (All operational procurement and audit roles) |
| **Country Pack** | `IN` (India: Currency INR `₹`, Date `DD/MM/YYYY`, Number grouping `12,34,567.89`) |

### 2.2 Primary API Endpoints

| HTTP Method | API Path | Privilege / Scope | Description |
|---|---|---|---|
| `GET` | `/api/v1/purchase/yarn-pos/` | `can_read` | Fetch paginated PO records with filtering (`search`, `yarn_type`, `mill`, `party`, `is_authorized`, `is_complete`) |
| `GET` | `/api/v1/purchase/balances/` | `can_read` | Fetch live PO balance register (ordered bags, inward bags, remaining bags) |
| `POST` | `/api/v1/purchase/yarn-pos/{id}/authorize/` | `can_approve` | Authorize a draft order directly from row actions or batch action |
| `POST` | `/api/v1/purchase/yarn-pos/{id}/unauthorize/` | `can_approve` | Re-open an authorized order back to draft status |
| `DELETE` | `/api/v1/purchase/yarn-pos/{id}/` | `can_delete` | Soft delete draft PO (`is_authorized == 0`) |
| `GET` | `/api/v1/masters/parties/?party_type=MILL` | `can_read` | Populate filter dropdown for spinning mills |
| `GET` | `/api/v1/masters/parties/?party_type=TRADER,SUPPLIER` | `can_read` | Populate filter dropdown for billing suppliers |
| `GET` | `/api/v1/masters/yarn-counts/` | `can_read` | Populate filter dropdown for yarn counts |

---

## 3. UI Layout, Screen Blueprint, and Visual Mockup

### 3.1 Visual Mockup Reference

![Garments ERP & CRM Yarn PO List Screen Preview](../assets/ui/yarn_po_list_sample.jpg)

### 3.2 Desktop Wireframe Layout (1440px+ Viewport)

```
+------------------------------------------------------------------------------------------------------------------+
| TOP BREADCRUMB: Procurement > Yarn PO                                                                            |
| Yarn Purchase Orders               [🔍 Quick Search (/) ]   [⚡ Filter (F)]   [📥 Export]   [+ Create Yarn PO (N)]|
+------------------------------------------------------------------------------------------------------------------+
| +------------------------+  +------------------------+  +------------------------+  +--------------------------+ |
| | KPI 1: TOTAL ORDERS    |  | KPI 2: ACTIVE BAGS     |  | KPI 3: OPEN VALUE      |  | KPI 4: INWARD FULFILLMENT| |
| | 142                    |  | 34,100 Bags            |  | ₹11.90 Crore           |  | 68% Fulfilled (23.1k Bags)| |
| +------------------------+  +------------------------+  +------------------------+  +--------------------------+ |
|                                                                                                                  |
| STATUS TABS: [ All Orders (142) ] [ Drafts (12) ] [ Authorized (85) ] [ Partially Received (32) ] [ Fulfilled (13) ]|
|                                                                                                                  |
| +--------------------------------------------------------------------------------------------------------------+ |
| | HIGH-DENSITY ENTERPRISE DATA TABLE                                                                           | |
| | [ ] | PO Number   | Date       | Mill & Supplier        | Yarn Specs       | Bags | Qty (Kg) | Value (₹)  |...| |
| |-----+-------------+------------+------------------------+------------------+------+----------+------------+---| |
| | [ ] | YPO-202610-1| 15/10/2026 | Vardhman Textiles Ltd. | 30s CVC Dyed     | 100  | 4,536.00 | 15,87,600  |...| |
| |     |             |            | Direct Mill Purchase   | Navy Blue (19-38)| [████████░░] 40/100 bags (40%) |...| |
| |-----+-------------+------------+------------------------+------------------+------+----------+------------+---| |
| | [ ] | YPO-202610-2| 14/10/2026 | GTN Textiles Ltd.      | 34s Combed Cotton| 200  | 9,072.00 | 31,75,200  |...| |
| |     |             |            | Sri Balaji Traders     | Grey / Ecru      | [░░░░░░░░░░] 0/200 bags (0%)   |...| |
| +--------------------------------------------------------------------------------------------------------------+ |
|                                                                                                                  |
| PAGINATION & DENSITY:                                                                                            |
| Showing 1 - 20 of 142 orders  | Rows per page: [ 20 v ]           [<<] [<]  Page 1 of 8  [>] [>>]               |
+------------------------------------------------------------------------------------------------------------------+
```

---

## 4. Page Initialization, Query Parameters, and Hydration

When entering `/procurement/yarn-po`, the page hydrates from URL query parameters to support shareable and bookmarkable filter views:

### 4.1 URL Search Parameters Mapping

```
/procurement/yarn-po?status=authorized&mill=3&search=30s&page=1&page_size=20&ordering=-po_date
```

| Query Param | Type | Default | Description |
|---|---|---|---|
| `status` | `string` | `'all'` | Tab filter: `'all'`, `'draft'`, `'authorized'`, `'partial'`, `'completed'` |
| `search` | `string` | `""` | Search text matching PO Number, Mill name, Supplier name, remarks |
| `mill` | `number` | `null` | Filter by Spinning Mill ID (`mill_id`) |
| `party` | `number` | `null` | Filter by Supplier/Trader ID (`party_id`) |
| `yarn_type` | `string` | `null` | Filter by Yarn Category (`GREY`, `DYED`, `MELANGE`, etc.) |
| `yarn_count`| `number` | `null` | Filter by Yarn Count ID |
| `from_date` | `string` | `null` | ISO Start date `YYYY-MM-DD` |
| `to_date` | `string` | `null` | ISO End date `YYYY-MM-DD` |
| `page` | `number` | `1` | Active page index (1-based) |
| `page_size` | `number` | `20` | Items per page (`20`, `50`, `100`) |
| `ordering` | `string` | `'-po_date'` | Sort field (`po_date`, `po_number`, `amount`, `created_on`) |

---

## 5. KPI Telemetry Summary Cards

Displayed directly below the header to provide immediate executive and operational visibility:

```
+--------------------------+--------------------------+--------------------------+--------------------------+
| TOTAL ORDERS             | ACTIVE BAGS              | OPEN ORDER VALUE         | INWARD FULFILLMENT       |
| 142                      | 34,100 Bags              | ₹11,90,50,000.00         | 68%                      |
| +12 orders this month    | 15,46,776.000 Kg         | Committed liability      | 23,188 / 34,100 Bags     |
+--------------------------+--------------------------+--------------------------+--------------------------+
```

1. **Total Orders**: Count of all active purchase orders in the current Financial Year (`status = 1`).
2. **Active Bags**: Total bag count of all non-completed orders ($34,100\text{ Bags}$).
3. **Open Order Value**: Grand financial liability of pending deliveries formatted in Indian currency grouping (`₹11,90,50,000.00`).
4. **Inward Fulfillment %**: Ratio of received inward bags vs total ordered bags:
   $$\text{Fulfillment \%} = \left( \frac{\sum \text{Inward Bags}}{\sum \text{Total PO Bags}} \right) \times 100$$

---

## 6. Status Filter Tabs Architecture

Quick-switch tabs allow merchandisers to filter orders by operational stage with live count badges:

| Tab Name | Query Filter Param | Invariants & Backend Criteria | Badge Style |
|---|---|---|---|
| **All Orders** | `status=all` | All records where `status = 1` | Neutral Gray (`bg-slate-100 text-slate-700`) |
| **Drafts** | `status=draft` | `is_authorized = 0` and `is_complete = 0` | Amber (`bg-amber-100 text-amber-800`) |
| **Authorized** | `status=authorized` | `is_authorized = 1` and `is_complete = 0` | Blue (`bg-blue-100 text-blue-800`) |
| **Partially Received**| `status=partial` | `is_authorized = 1`, `inward_bag > 0`, `is_complete = 0` | Purple (`bg-purple-100 text-purple-800`) |
| **Fulfilled** | `status=completed` | `is_complete = 1` | Emerald (`bg-emerald-100 text-emerald-800`) |

---

## 7. Search Bar, Quick Filters, and Advanced Filter Drawer

### 7.1 Search & Quick Filter Controls

1. **Global Search Input**:
   - Keyboard shortcut: **`/`** (slash focuses search).
   - Debounce delay: `300ms`.
   - Matches: `po_number`, `mill__name`, `party__name`, `name`, `remarks`.
2. **"Filter" Drawer Toggle Button**:
   - Keyboard shortcut: **`F`**.
   - Opens the slide-over filter drawer with multi-select dropdowns for:
     - Date Range (`From Date` to `To Date` with presets: *This Month*, *Last 30 Days*, *Current FY*).
     - Spinning Mill (`mill_id`).
     - Commercial Supplier (`party_id`).
     - Yarn Category (`yarn_type`).
     - Yarn Count (`yarn_count_id`).
   - Action: `[ Reset Filters ]` and `[ Apply Filters ]`.

---

## 8. High-Density Enterprise Data Table Column Specifications

| Col # | Column Header | Data Key | Visual Representation & Alignment | Width |
|---|---|---|---|---|
| **1** | `Checkbox` | `id` | Selection checkbox for batch actions. | `40px` |
| **2** | `PO Number` | `po_number` | **Bold blue link** navigating to `/procurement/yarn-po/{id}`. Includes copy icon on hover. | `150px` |
| **3** | `Date` | `po_date` | Formatted `DD/MM/YYYY` in monospace font. | `110px` |
| **4** | `Spinning Mill & Supplier` | `mill`, `party` | Line 1: **Mill Name** (`font-semibold`). Line 2: Supplier name or `Direct Mill Purchase` pill. | `220px` |
| **5** | `Yarn Details` | `yarn_type`, `yarn_count` | Yarn type pill (`GREY`, `DYED`), Yarn count name, and color swatch preview if dyed. | `180px` |
| **6** | `Bags` | `bag` | Numeric integer right-aligned (`100 Bags`). | `90px` |
| **7** | `Weight (Kg)` | `quantity` | Numeric decimal right-aligned (`4,536.000 Kg`). | `120px` |
| **8** | `Order Value (₹)` | `amount` | Bold currency right-aligned (`₹15,87,600.00`). | `140px` |
| **9** | `Inward Fulfillment`| `inward_progress` | Visual progress bar with label: `40 / 100 bags (40%)`. | `170px` |
| **10**| `Status` | `status_badge` | Contextual status pill: `Draft`, `Authorized`, `Inward Partial`, `Fulfilled`. | `120px` |
| **11**| `Actions` | — | Three-dots dropdown menu (`...`). | `60px` |

---

## 9. Row-Level Actions & Contextual Permissions

Clicking the `...` menu on any row opens contextual actions based on record status and user role:

| Action Item | Required Privilege | Visibility Condition | Behavior |
|---|---|---|---|
| **View Order Details** | `can_read` | Always visible | Navigates to `/procurement/yarn-po/{id}`. |
| **Edit Order** | `can_update` | `is_authorized == 0` (or manager override) | Navigates to `/procurement/yarn-po/{id}/edit`. |
| **Authorize Order** | `can_approve` | `is_authorized == 0` | Triggers prompt: *"Authorize PO #{po_number}?"*. Calls `POST /authorize/`. |
| **Unauthorize / Reopen**| `can_approve` | `is_authorized == 1` and `is_complete == 0` | Triggers confirmation dialog. Calls `POST /unauthorize/`. |
| **Print / Export PDF** | `can_export` | Always visible | Opens printable PO document with company header, GST, and terms. |
| **Delete Draft** | `can_delete` | `is_authorized == 0` and `inward == 0` | Prompts destructive dialog. Calls `DELETE /api/v1/purchase/yarn-pos/{id}/`. |

---

## 10. Floating Batch Selection Action Bar

When 1 or more row checkboxes are selected, a floating bar docks at the bottom center:

```
+---------------------------------------------------------------------------------------------------+
|  [✔ 3 Orders Selected]      [⚡ Bulk Authorize]      [📥 Export Selected (Excel)]      [✖ Clear]  |
+---------------------------------------------------------------------------------------------------+
```

1. **Bulk Authorize**:
   - Visible only if all selected orders are in `DRAFT` status and user holds `purchase_yarn_po.can_approve`.
   - Executes batch authorization in parallel or sequential calls.
2. **Bulk Export Selected**:
   - Generates an `.xlsx` workbook containing PO headers, line items, and delivery schedules.
3. **Clear Selection**:
   - Unchecks all table rows and hides the floating bar.

---

## 11. Inward Progress Bar & Live Balance Calculation

Each table row displays a visual fulfillment indicator sourced from `yarn_po_balance_table`:

$$\text{Received Bags} = \text{ordered\_bag} - \text{remaining\_bag}$$
$$\text{Progress \%} = \left( \frac{\text{Received Bags}}{\text{ordered\_bag}} \right) \times 100$$

- **0% (Unreceived)**: Light gray bar (`bg-slate-200`). Label: `0 / 100 bags (0%)`.
- **1% to 99% (Partial Inward)**: Indigo/Purple bar (`bg-indigo-600`). Label: `40 / 100 bags (40%)`.
- **100% (Fulfilled)**: Emerald green bar (`bg-emerald-500`). Label: `100 / 100 bags (100%)`.

---

## 12. Pagination, Cursor/Offset Controls, and Sort Order

- **Pagination Controls**:
  - `Rows per page`: Select dropdown with options `[20, 50, 100]`. Default: `20`.
  - `Pagination Summary`: *"Showing 1 to 20 of 142 orders"*.
  - `Page Navigation`: First (`<<`), Previous (`<`), Active Page Pill, Next (`>`), Last (`>>`).
- **Column Sorting**:
  - Clickable headers for: `po_number`, `po_date`, `amount`, `created_on`.
  - Clicking toggles ascending (`asc`) / descending (`desc`) and appends `&ordering=-po_date` to URL query.

---

## 13. Empty State, No Search Results, and Skeleton Shimmer States

1. **Loading State**:
   - Renders 8 skeleton shimmer rows mimicking table layout while API fetch is in-flight.
2. **Zero Records State (No POs in System)**:
   - Illustration of textile yarn cones.
   - Title: *"No Yarn Purchase Orders Created Yet"*.
   - Action: `[ + Create First Yarn PO ]` button.
3. **No Filter Results State**:
   - Title: *"No orders match your filter criteria"*.
   - Action: `[ Clear Filters ]` button resetting query parameters to default.

---

## 14. API Integration, Query String Serialization, and Error Handling

### 14.1 Query Fetch Function

```typescript
export async function fetchYarnPOList(params: YarnPOListParams): Promise<YarnPOListResponse> {
  const query = new URLSearchParams();
  
  if (params.search) query.set("search", params.search);
  if (params.yarn_type) query.set("yarn_type", params.yarn_type);
  if (params.mill) query.set("mill", String(params.mill));
  if (params.party) query.set("party", String(params.party));
  if (params.yarn_count) query.set("yarn_count", String(params.yarn_count));
  if (params.from_date) query.set("po_date__gte", params.from_date);
  if (params.to_date) query.set("po_date__lte", params.to_date);
  
  // Status tab mapping
  if (params.status === "draft") query.set("is_authorized", "0");
  if (params.status === "authorized") {
    query.set("is_authorized", "1");
    query.set("is_complete", "0");
  }
  if (params.status === "completed") query.set("is_complete", "1");

  query.set("page", String(params.page || 1));
  query.set("page_size", String(params.page_size || 20));
  query.set("ordering", params.ordering || "-po_date");

  const response = await fetch(`/api/v1/purchase/yarn-pos/?${query.toString()}`, {
    headers: {
      "Authorization": `Bearer ${getAccessToken()}`,
      "X-Company-ID": getActiveCompanyId(),
      "X-Financial-Year-ID": getActiveFinancialYearId(),
    },
  });

  if (!response.ok) {
    throw new Error("Failed to fetch Yarn Purchase Orders register");
  }

  return response.json();
}
```

---

## 15. Next.js Folder Structure and Component Hierarchy

```
frontend/app/(app)/procurement/yarn-po/
├── page.tsx                           # Register page container (URL query sync & SSR state)
├── components/
│   ├── YarnPOKPICards.tsx             # 4 Metric cards (Total, Bags, Open Value, Fulfillment)
│   ├── YarnPOTabs.tsx                 # Status tabs with live counts
│   ├── YarnPOTableToolbar.tsx         # Search bar, Filter drawer toggle, New PO button
│   ├── YarnPOTable.tsx                # Enterprise data grid with sortable headers
│   ├── YarnPOTableRow.tsx             # Single row with progress bar & status pills
│   ├── YarnPORowActionsMenu.tsx       # Contextual action dropdown (...)
│   ├── YarnPOBatchActionBar.tsx       # Floating bar for bulk selection actions
│   ├── YarnPOFilterDrawer.tsx         # Slide-over advanced filter panel
│   └── YarnPOPagination.tsx           # Page numbers & rows-per-page selector
├── hooks/
│   ├── useYarnPOList.ts               # SWR / TanStack Query fetcher with cache invalidation
│   └── useYarnPOBatchSelection.ts     # Row selection checkbox state management
└── types/
    └── yarn-po-list.types.ts          # Table row DTOs & filter query types
```

---

## 16. React Hooks, TypeScript Types, Zod Query Schema, and Filter State

### 16.1 TypeScript Query & List Interfaces

```typescript
export interface YarnPOListItemDTO {
  id: number;
  po_number: string;
  po_date: string;
  yarn_type: string;
  yarn_type_display: string;
  mill: {
    id: number;
    name: string;
    city?: string;
  };
  party: {
    id: number;
    name: string;
  };
  yarn_count?: {
    id: number;
    count: string;
  };
  color_shade?: {
    id: number;
    color_name: string;
    color_code?: string;
  };
  bag: number;
  per_bag: string;
  quantity: string;
  rate: string;
  amount: string;
  is_delivery: number;
  is_complete: number;
  is_authorized: number;
  authorized_by_username?: string;
  inward_bags_received?: number;
  inward_fulfillment_percent?: number;
}

export interface YarnPOListResponse {
  success: boolean;
  data: YarnPOListItemDTO[];
  meta: {
    page: number;
    page_size: number;
    total_count: number;
    total_pages: number;
    has_next: boolean;
    has_previous: boolean;
  };
}
```

---

## 17. Keyboard Shortcuts and Table Ergonomics

| Shortcut Key | Action & Ergonomic Focus Behavior |
|---|---|
| **`/`** (Slash) | Focuses the Quick Search input box. |
| **`N`** | Navigates immediately to `/procurement/yarn-po/new` (New PO). |
| **`F`** | Toggles open the Advanced Filter slide-over drawer. |
| **`J` / `Down Arrow`** | Moves table selection down to the next row. |
| **`K` / `Up Arrow`** | Moves table selection up to the previous row. |
| **`Enter`** (on selected row) | Navigates to `/procurement/yarn-po/{id}` (View PO Detail). |
| **`X`** (on selected row) | Toggles the checkbox for the active row. |
| **`Esc`** | Clears search or closes the active filter drawer. |

---

## 18. Security, Multi-Tenant Scoping, and Role-Based Permissions

1. **Company Scoping Invariant**:
   - Every `GET` query passes the `X-Company-ID` header. The backend strictly isolates records to the authenticated tenant.
2. **Financial Year Visibility**:
   - By default, orders belong to the active Financial Year (`cfyear_id`). Cross-FY historical lookup requires selecting an archived FY in the filter drawer.
3. **Privilege Gating in UI**:
   - The `+ Create Yarn PO` button is rendered only if the user holds `purchase_yarn_po.can_create`.
   - The `Authorize` action is restricted to `purchase_yarn_po.can_approve`.
   - The `Export Excel` button requires `purchase_yarn_po.can_export`.

---

## 19. Implementation Sequence and Developer Acceptance Checklist

- [ ] **1. Route Setup**: Page created at `/procurement/yarn-po/page.tsx` with URL search params syncing.
- [ ] **2. KPI Cards**: Renders Total Orders, Active Bags, Open Value (₹), and Fulfillment % accurately.
- [ ] **3. Status Tabs**: Switching tabs filters by `All`, `Drafts`, `Authorized`, `Partially Received`, and `Fulfilled` with live badge counts.
- [ ] **4. Quick Search**: Typing in search debounces by 300ms and filters by PO Number, Mill, or Trader.
- [ ] **5. Advanced Filter Drawer**: Filter by Date Range, Mill, Supplier, Yarn Type, and Yarn Count updates URL query and refreshes table.
- [ ] **6. Table Data Columns**: Renders all 11 columns cleanly with monospace dates, formatted Indian currency, and copyable PO numbers.
- [ ] **7. Fulfillment Progress Bar**: Progress bar accurately reflects received inward bags vs total ordered bags.
- [ ] **8. Row Actions**: View, Edit, Authorize, Unauthorize, Print, and Delete actions function according to record status and user privileges.
- [ ] **9. Batch Selection Bar**: Selecting multiple checkboxes opens floating bar for Bulk Authorize and Bulk Excel Export.
- [ ] **10. Pagination & Density**: Page sizes 20, 50, 100 and pagination links navigate smoothly.
- [ ] **11. Keyboard Shortcuts**: `/`, `N`, `F`, `J`, `K`, `X`, and `Enter` function across desktop browsers.
- [ ] **12. Responsive Design**: Table scrolls horizontally on mobile/tablet while keeping PO Number and Actions sticky.

---

## 20. Inconsistencies, Performance Considerations, and Items Requiring Confirmation

| Issue ID | Section | Existing Requirement | Identified Inconsistency / Performance Consideration | Recommended Resolution | Confirmation Required |
|---|---|---|---|---|---|
| **`ISS-L01`** | §5 & §11 Balance Join Performance | Live inward fulfillment % requires joining `parent_po_table` with `child_yarn_inward_table` or `yarn_po_balance_table`. | Running balance aggregations on every list request across 10,000+ orders can cause slow query times ($>500\text{ms}$). | Use indexed database view `yarn_po_balance_table` or annotate list queryset with SQL subquery for `inward_bag`. | **Developer Confirmation** |
| **`ISS-L02`** | §6 Status Tab Counts | Each tab displays a live record count: `Drafts (12)`, `Authorized (85)`. | DRF standard pagination only returns total count for the *current* filter query, not all 5 tabs simultaneously. | Add a dedicated summary endpoint `GET /api/v1/purchase/yarn-pos/summary/` returning counts for all tabs in one call. | **Developer Confirmation** |
| **`ISS-L03`** | §10 Bulk Authorization Limit | Bulk authorization allows selecting 50+ POs and approving them in one click. | If 1 order in the batch has invalid delivery schedules, should the entire bulk operation fail or proceed for valid orders? | Partial success reporting: return `{ authorized: [ids], failed: [{ id, error }] }`. | **Business Confirmation** |
| **`ISS-L04`** | §12 Cross-FY Archived Lookup | The default queryset filters by active `company_id` and active `cfyear_id`. | Should merchandisers be able to view previous year POs by toggling an *"Include Archived FYs"* filter? | Add a toggle in the filter drawer to view historical financial year orders in read-only mode. | **Business Confirmation** |
