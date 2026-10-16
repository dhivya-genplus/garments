# Grey Fabric Inward, Outward & Live Stock Register Specification

| Standard Code | Screen ID | Target Platform | API Version | Document Version | Date | Status |
|---|---|---|---|---|---|---|
| **STD-UI-001** | **`SCR-KNIT-002`** | Next.js 14 (App Router) + TypeScript | `v1.2` (Django 5 DRF) | `v1.0.0` | 16/10/2026 | **APPROVED FOR IMPLEMENTATION** |

---

## 1. Document Overview, Version, Scope, and Status

### 1.1 Purpose
This specification defines the complete technical architecture, UI layout, roll & weight tracking, batch/lot management, Zod validation schema, TypeScript interfaces, and backend API integration for the **Grey Fabric Inward, Outward & Stock Operations Desk** (`SCR-KNIT-002`).

In garment manufacturing, once yarn is knitted into circular/flat greige fabric rolls, rigorous physical accounting of grey fabric is required prior to wet processing (dyeing/bleaching/compacting):
1. **Dual Inventory Tracking (Rolls & Net Weight)**: Every roll of knitted fabric has individual physical dimensions (Dia, Gauge, GSM) and exact weight in kilograms. Inventory balances must account for both roll counts and cumulative kilogram weights without underflow.
2. **Knitting Inward GRN (Receipt from Subcontractor)**: Receiving knitted rolls against active Knitting Programs (`SCR-KNIT-001`), verifying delivery challans, inspecting roll quality, and recording piece weight breakdowns.
3. **Outward DC (Dispatch to Dyeing / Process Units)**: Issuing Delivery Challans to transfer grey rolls from knitting godowns to wet processing units (`DYEING_UNIT`) with process loss benchmarking.
4. **Live Stock Ledger**: Real-time filtering by godown warehouse, fabric SKU, Dia, GSM, and piece lot number with one-click export to Excel/PDF.

### 1.2 Scope
- **Backend Models**: [`grey_fabric_stock_table`](file:///d:/Codebase/Garments/backend/apps/knitting/models.py#L176-L233) (`tm_grey_fabric_stock`), [`parent_grey_fabric_inward_table`](file:///d:/Codebase/Garments/backend/apps/knitting/models.py#L234-L260) (`tm_grey_fabric_inward`), and `parent_grey_fabric_outward_table` (`tm_grey_fabric_outward`).
- **Country Pack**: India (`IN`) — Indian Rupee (`₹`), Metric weight in Kilograms (`0.000 Kg`), Rolls in Integer, Indian Date format (`DD/MM/YYYY`).
- **Target Route**: `/production/grey-fabric` (Next.js route: `app/(app)/production/grey-fabric/page.tsx`).

---

## 2. Module Details, Screen ID, Route, Access Privileges, and API Endpoints

### 2.1 Core Metadata

| Parameter | Specification |
|---|---|
| **Module** | `Module 6 — Knitting & Fabric Production` |
| **Screen ID** | `SCR-KNIT-002` |
| **Frontend Route** | `/production/grey-fabric` (Register & Live Stock Desk) |
| **File Location** | `app/(app)/production/grey-fabric/page.tsx` |
| **Required Privilege** | `knitting_stock.can_read` (View stock & registers); `knitting_inward.can_create` (Inward GRN); `knitting_outward.can_create` (Outward DC); `knitting_stock.can_export` (Export ledger) |
| **Authorized Roles** | `SUPER_ADMIN`, `ADMIN_USER`, `COMPANY_USER` (Fabric Storekeeper, Production Supervisor, Quality Inspector) |
| **Country Pack** | `IN` (India: Currency INR `₹`, Date `DD/MM/YYYY`, Decimal precision: Weight 3 dp `0.000 Kg`, Rolls Integer) |

### 2.2 Primary API Endpoints

| HTTP Method | API Path | Privilege / Scope | Description |
|---|---|---|---|
| `GET` | `/api/v1/knitting/stock/` | `can_read` | Fetch live grey fabric stock balances filtered by warehouse, fabric, dia, gsm, and lot |
| `GET` | `/api/v1/knitting/inwards/` | `can_read` | Fetch grey fabric inward receipts (GRN) with party, date, and program filters |
| `POST` | `/api/v1/knitting/inwards/` | `can_create` | Post new Grey Fabric Inward GRN (credits stock, updates knitting program balance) |
| `GET` | `/api/v1/knitting/outwards/` | `can_read` | Fetch grey fabric outward dispatches (DC) to dyeing or knitter return |
| `POST` | `/api/v1/knitting/outwards/` | `can_create` | Issue new Grey Fabric Outward DC (validates non-negative stock and debits inventory) |
| `GET` | `/api/v1/knitting/stock/summary/` | `can_read` | Retrieve aggregated totals (Total Rolls, Total Kg, Valuation) for dashboard display |

---

## 3. UI Layout, Screen Blueprint, and Visual Mockup (1440px+ Wireframe)

```
+-----------------------------------------------------------------------------------------------------------------------------+
| GARMENTS ERP — Grey Fabric Inventory & Production Register                   Company: ABC Textiles Ltd | FY: 2026-2027      |
+-----------------------------------------------------------------------------------------------------------------------------+
| TABS: [ 1. Live Godown Stock Desk (Active) ]   [ 2. Inward GRN Register ]   [ 3. Outward DC Register ]                      |
+-----------------------------------------------------------------------------------------------------------------------------+
| KPI SUMMARY CARDS:                                                                                                          |
| [ TOTAL GREY STOCK ]       [ TOTAL ROLLS ON HAND ]      [ KNITTING INWARD (MTD) ]     [ DYEING DISPATCH (MTD) ]             |
|   48,250.600 Kg              2,145 Rolls                  28,400.000 Kg                 22,150.000 Kg                       |
|   ₹ 1,15,80,144.00 Est.      Avg: 22.49 Kg / Roll         1,260 Rolls                   985 Rolls                           |
+-----------------------------------------------------------------------------------------------------------------------------+
| MULTI-DIMENSIONAL FILTERS:                                                                                                  |
| Warehouse: [ All Godowns (Tirupur Main, Greige Unit 2)  | v ]  Fabric: [ 100% Combed Cotton Single Jersey             | v ]|
| Dia: [ 30" (Inches) | v ]  GSM Range: [ 150 ] to [ 180 ]  Lot No: [ LOT-2026-        ]  Search: [ Search by Fabric/Lot... ]|
| [ Reset Filters ]     [ Apply Filter (F3) ]                                         [ Export XLSX ]  [ Print Stock (Ctrl+P) ]|
+-----------------------------------------------------------------------------------------------------------------------------+
| LIVE GREY FABRIC STOCK REGISTER TABLE:                                                                                      |
| # | Warehouse       | Fabric Name & Type            | Dia | GSM | Gauge | Lot / Batch # | In Rolls | In Qty (Kg)| Bal Rolls | Bal Qty (Kg) | Actions      |
|---|-----------------|-------------------------------|-----|-----|-------|---------------|----------|------------|-----------|--------------|--------------|
| 1 | Main Greige God | 100% Cotton Single Jersey (SJ)| 30" | 160 | 24 GG | LOT-2026-K042 |      120 |  2,392.500 |       119 |    2,372.500 | [Issue DC] [P]|
| 2 | Main Greige God | 95/5 Cotton Lycra Jersey (SJ) | 32" | 180 | 28 GG | LOT-2026-K039 |       85 |  1,825.200 |        45 |      965.400 | [Issue DC] [P]|
| 3 | Godown Unit 2   | 100% Cotton 2x2 Rib (RIB)     | 24" | 220 | 18 GG | LOT-2026-K031 |       60 |  1,440.000 |        12 |      288.000 | [Issue DC] [P]|
| 4 | Main Greige God | Cotton French Terry (FLC)     | 34" | 260 | 20 GG | LOT-2026-K028 |       90 |  2,700.000 |        90 |    2,700.000 | [Issue DC] [P]|
|---|-----------------|-------------------------------|-----|-----|-------|---------------|----------|------------|-----------|--------------|--------------|
|   | PAGE TOTALS (4) |                               |     |     |       |               |      355 |  8,357.700 |       266 |    6,325.900 |              |
+-----------------------------------------------------------------------------------------------------------------------------+
| PAGINATION: Showing 1 to 4 of 48 SKU Records    [ < First ]  [ < Prev ]  Page [ 1 ] of 12  [ Next > ]  [ Last > ]           |
| QUICK SHORTCUTS: [Alt+I: New Inward GRN]  [Alt+O: New Outward DC]  [Alt+F: Focus Filter]  [F5: Refresh]                    |
+-----------------------------------------------------------------------------------------------------------------------------+
```

---

## 4. UX Workflow, Step-by-Step Lifecycle, and Edge-Case Handling

### 4.1 Step-by-Step Lifecycle
1. **Live Stock Exploration**:
   - Storekeeper accesses `/production/grey-fabric`.
   - Real-time stock is loaded with pagination, showing available balance in both **Rolls** and **Kilograms**.
   - Filtering allows searching by specific knitting machine Dia (e.g. 30"), GSM tolerance, and Lot Number.
2. **Recording Inward (GRN)**:
   - When knitted rolls arrive at the factory gate with knitter delivery challan:
   - Click **New Inward GRN (Alt+I)** or navigate to Tab 2.
   - User selects Knitter (`PartyMaster`) and links active Knitting Program (`SCR-KNIT-001`).
   - Inputs DC Number, DC Date, Vehicle Number, and itemized roll list (or bulk roll count with gross weight and tare weight).
   - System calculates Net Weight = $\text{Gross Wt} - \text{Tare Wt}$ and auto-credits `tm_grey_fabric_stock`.
3. **Recording Outward (DC to Dyeing)**:
   - When fabric is transferred to dye-house for processing:
   - Click **New Outward DC (Alt+O)** or navigate to Tab 3.
   - User selects Destination Dyeing Unit (`DYEING_UNIT`), source warehouse, and fabric lot.
   - System enforces that dispatched rolls $\le$ available balance rolls and dispatched weight $\le$ balance weight.
   - Upon confirmation, stock balance is decremented and an official Delivery Challan with GST E-Way bill metadata is generated.

### 4.2 Edge-Case Handling
- **Negative Stock Prevention**: Backend atomic transaction (`select_for_update()`) verifies that deducting rolls or weight does not drive stock below zero. If concurrent users attempt to dispatch the same lot, the second transaction is rejected with: *"Insufficient stock balance for Lot LOT-2026-K042 (Available: 12 Rolls, Requested: 15 Rolls)"*.
- **Average Roll Weight Anomaly Detection**: If $\frac{\text{Net Weight}}{\text{Rolls}}$ deviates by $>30\%$ from typical roll sizes ($18\text{ to }26\text{ Kg/Roll}$), a warning modal prompts confirmation.

---

## 5. Form Sections, Field Matrix, and Validation Rules

| Section | Field Label | Field Key | Input Type | Required | Default | Validation & Rules |
|---|---|---|---|---|---|---|
| **Filter** | Warehouse | `warehouse_id` | Select | No | All | Filter by active Godown |
| **Filter** | Fabric SKU | `fabric_id` | Searchable Select | No | All | Filter by `FabricMaster` |
| **Filter** | Diameter | `dia` | Select | No | All | e.g. 20", 24", 26", 28", 30", 32", 34" |
| **Filter** | GSM Min / Max | `gsm_min`, `gsm_max` | Number | No | Empty | Range: 50 to 500 $\text{g/m}^2$ |
| **Filter** | Lot Number | `lot_no` | Text | No | Empty | Case-insensitive prefix search |
| **Inward** | Inward Number | `inward_number` | Text (Readonly) | Yes | Auto `GF-IN-YYYY-XXXX` | Unique document sequence |
| **Inward** | Inward Date | `inward_date` | DatePicker | Yes | Current Date | `DD/MM/YYYY` in active FY |
| **Inward** | Knitter / Supplier | `party_id` | Searchable Select | Yes | None | Active Party |
| **Inward** | Knitting Program | `knitting_program_id` | Searchable Select | No | None | Optional link to `tm_knitting_program` |
| **Inward** | Knitter DC No & Date | `dc_number`, `dc_date` | Text, Date | Yes | None | External Challan validation |
| **Inward** | Received Rolls | `inward_rolls` | Number (Integer) | Yes | `1` | Must be $\ge 1$ |
| **Inward** | Received Net Wt | `inward_quantity` | Number (3 dp) | Yes | `0.000` | Must be $> 0.000$ Kg |
| **Outward** | Outward Number | `outward_number` | Text (Readonly) | Yes | Auto `GF-OUT-YYYY-XXXX`| Unique document sequence |
| **Outward** | Destination Dyeing | `party_id` | Searchable Select | Yes | None | Active `DYEING_UNIT` |
| **Outward** | Dispatched Rolls | `outward_rolls` | Number (Integer) | Yes | `1` | $\le \text{Available Balance Rolls}$ |
| **Outward** | Dispatched Net Wt | `outward_quantity` | Number (3 dp) | Yes | `0.000` | $\le \text{Available Balance Weight}$ |

---

## 6. Mathematical Formulas and Calculation Specifications (LaTeX)

### 6.1 Net Inward Weight Calculation
Given gross roll weight $W_{\text{gross}}$ and tare packaging weight $W_{\text{tare}}$ (paper tubes, plastic wrap):

$$W_{\text{net}} = W_{\text{gross}} - W_{\text{tare}}$$

### 6.2 Live Stock Balance Ledger Invariant
For every distinct tuple $(\text{Company}, \text{Warehouse}, \text{Fabric}, \text{Dia}, \text{GSM}, \text{Gauge}, \text{Lot})$:

$$\text{Balance Rolls} = (\text{Inward Rolls} + \text{Sales Return Rolls}) - (\text{Outward Rolls} + \text{Sales Rolls})$$

$$\text{Balance Weight (Kg)} = (Q_{\text{in}} + Q_{\text{sr}}) - (Q_{\text{out}} + Q_{\text{sales}})$$

$$\text{Invariant Requirement: } \text{Balance Rolls} \ge 0 \quad \land \quad \text{Balance Weight} \ge 0.000\text{ Kg}$$

### 6.3 Average Roll Weight Telemetry
$$\bar{W}_{\text{roll}} = \frac{\text{Balance Weight (Kg)}}{\text{Balance Rolls}}$$

---

## 7. Dynamic Behaviors, Conditional Fields, and Interactivity

1. **Tab Switch State Retention**: Switching between Live Stock Desk, Inward Register, and Outward Register preserves search criteria and filter selections.
2. **Inline Action Menu**: Each stock row features an **[Issue DC]** button that pre-populates an Outward Delivery Challan modal with that specific lot's fabric, dia, gsm, and godown.
3. **Weight vs. Rolls Cross-Check**: Entering a dispatched roll count auto-suggests weight based on that lot's average roll weight:

$$Q_{\text{suggested}} = \text{Dispatched Rolls} \times \bar{W}_{\text{roll}}$$

---

## 8. API Request / Response Contracts (DTOs)

### 8.1 Fetch Live Grey Fabric Stock (`GET /api/v1/knitting/stock/?warehouse_id=2&dia=30"`)

```json
{
  "success": true,
  "data": {
    "results": [
      {
        "id": 14,
        "company_id": 1,
        "warehouse_id": 2,
        "warehouse_name": "Main Greige Godown",
        "fabric_id": 7,
        "fabric_name": "100% Combed Cotton Single Jersey",
        "fabric_type_id": 3,
        "fabric_type_name": "Single Jersey",
        "dia": "30\"",
        "gsm": 160,
        "gauge": "24 GG",
        "lot_no": "LOT-2026-K042",
        "inward_rolls": 120,
        "inward_quantity": "2392.500",
        "outward_rolls": 1,
        "outward_quantity": "20.000",
        "sales_rolls": 0,
        "sales_quantity": "0.000",
        "balance_rolls": 119,
        "balance_quantity": "2372.500",
        "avg_roll_weight": "19.937"
      }
    ],
    "count": 48,
    "next": null,
    "previous": null
  }
}
```

---

## 9. Client-Side State Management and Component Architecture

```
app/(app)/production/grey-fabric/
├── page.tsx                             # Master container managing active tabs & state
└── components/
    ├── GreyStockKPICards.tsx            # KPI tiles (Total Kg, Rolls, Valuation)
    ├── GreyStockFilterBar.tsx           # Multi-criteria filter drawer
    ├── GreyStockLiveTable.tsx           # Live Godown roll & weight register
    ├── GreyInwardRegisterTable.tsx      # Tab 2: Historical GRN receipts
    ├── GreyOutwardRegisterTable.tsx     # Tab 3: Historical DC transfers
    └── GreyOutwardModal.tsx             # Quick dispatch modal directly from stock row
```

---

## 10. Zod Validation Schema (Copy-Paste Production Code)

```typescript
import { z } from "zod";

const dateRegex = /^(0[1-9]|[12][0-9]|3[01])\/(0[1-9]|1[0-2])\/\d{4}$/;

export const GreyFabricInwardSchema = z.object({
  inward_date: z.string().regex(dateRegex, { message: "Date must be DD/MM/YYYY" }),
  dc_number: z.string().min(1, { message: "Delivery Challan number is required." }),
  dc_date: z.string().regex(dateRegex, { message: "DC date must be DD/MM/YYYY" }),
  vehicle_no: z.string().optional(),
  knitter_id: z.number().int().positive({ message: "Knitter is required." }),
  warehouse_id: z.number().int().positive({ message: "Receiving godown is required." }),
  knitting_program_id: z.number().int().positive().optional(),
  fabric_id: z.number().int().positive({ message: "Fabric SKU is required." }),
  fabric_type_id: z.number().int().positive({ message: "Fabric type is required." }),
  dia: z.string().min(1, { message: "Dia is required." }),
  gsm: z.number().int().positive({ message: "GSM is required." }),
  gauge: z.string().optional(),
  lot_no: z.string().min(1, { message: "Lot number is required." }),
  inward_rolls: z.number().int().min(1, { message: "At least 1 roll is required." }),
  inward_quantity: z.number().min(0.001, { message: "Net weight must be positive." }),
});

export const GreyFabricOutwardSchema = z.object({
  outward_date: z.string().regex(dateRegex, { message: "Date must be DD/MM/YYYY" }),
  party_id: z.number().int().positive({ message: "Destination dye-house is required." }),
  warehouse_id: z.number().int().positive({ message: "Dispatch godown is required." }),
  fabric_id: z.number().int().positive({ message: "Fabric SKU is required." }),
  dia: z.string().min(1, { message: "Dia is required." }),
  gsm: z.number().int().positive({ message: "GSM is required." }),
  lot_no: z.string().min(1, { message: "Lot number is required." }),
  outward_rolls: z.number().int().min(1, { message: "At least 1 roll must be dispatched." }),
  outward_quantity: z.number().min(0.001, { message: "Dispatched weight must be positive." }),
  available_balance_rolls: z.number().int(),
  available_balance_quantity: z.number(),
}).refine((data) => data.outward_rolls <= data.available_balance_rolls, {
  message: "Dispatched rolls exceed available balance.",
  path: ["outward_rolls"],
}).refine((data) => data.outward_quantity <= data.available_balance_quantity, {
  message: "Dispatched weight exceeds available balance.",
  path: ["outward_quantity"],
});
```

---

## 11. TypeScript Interfaces & Enums (Complete DTO Declarations)

```typescript
export interface IGreyFabricStockDTO {
  id: number;
  company_id: number;
  warehouse_id: number;
  warehouse_name: string;
  fabric_id: number;
  fabric_name: string;
  fabric_type_id: number;
  fabric_type_name: string;
  dia: string;
  gsm: number;
  gauge?: string;
  lot_no: string;
  inward_rolls: number;
  inward_quantity: number;
  outward_rolls: number;
  outward_quantity: number;
  sales_rolls: number;
  sales_quantity: number;
  balance_rolls: number;
  balance_quantity: number;
  avg_roll_weight: number;
}
```

---

## 12. Keyboard Shortcuts and Rapid Operations

| Key Combination | Action / Trigger | Scope / View |
|---|---|---|
| `Alt + I` | Open New Inward GRN Modal | Register View |
| `Alt + O` | Open New Outward DC Modal | Register View |
| `Alt + F` | Focus Search & Filter Input | Live Stock Desk |
| `F5` | Refresh Stock Balances | Live Stock Desk |
| `Ctrl + P` | Print Stock Ledger Report | Live Stock Desk |

---

## 13. Responsive Breakpoints and Mobile Adaptation

| Viewport Width | Screen Category | Layout Behavior |
|---|---|---|
| $\ge 1440\text{px}$ | Desktop Enterprise | Full 12-column live stock table with inline quick actions |
| $1024\text{px} - 1439\text{px}$ | Laptop / Tablet Landscape | Collapsible filters drawer, horizontal scrolling on roll and kg columns |
| $\le 1023\text{px}$ | Tablet Portrait / Mobile | Tab-based cards with roll badges and one-touch DC dispatch |

---

## 14. Error Handling and User Feedback

| Scenario / Error Trigger | Visual Presentation | Remediation Action |
|---|---|---|
| Dispatched rolls $>$ Balance | Red input border + inline error badge | Enforce value $\le$ available balance |
| Dispatched weight $>$ Balance | Toast notification: *"Cannot exceed available stock weight"* | Reset input to max available weight |
| Knitter DC duplicate | Error alert: *"DC Number already recorded for this knitter"* | Prompt user to check previous GRN |

---

## 15. Loading, Empty, and Edge States

- **Loading State**: Shimmer grid loading 10 tabular rows.
- **Empty State**: Gray fabric roll icon with text: *"No stock records match the selected Dia/GSM criteria."*
- **Zero Balance State**: Dimmed row styling with badge: *"OUT OF STOCK (0 Rolls)"*.

---

## 16. Accessibility (a11y) Conformance (WCAG 2.1 AA)

- Semantic `<table>` tags with proper `<th scope="col">` headers.
- ARIA live region `aria-live="polite"` announcing stock filter results.
- Minimum contrast ratio $> 4.5:1$ on all numeric weight balances.

---

## 17. Security, RBAC, and Audit Logging

- **Data Isolation**: Strictly scoped by user's active tenant `company_id`.
- **Privilege Checking**: Users without `knitting_outward.can_create` have the **[Issue DC]** button disabled.
- **Audit Logging**: Every inward and outward transaction logs user ID, timestamp, and machine IP.

---

## 18. Test Cases and Acceptance Criteria

### 18.1 Acceptance Criteria
1. Given stock of 120 rolls ($2,392.500\text{ Kg}$), issuing DC for 1 roll ($20.000\text{ Kg}$) leaves exactly 119 rolls ($2,372.500\text{ Kg}$).
2. Inward GRN automatically updates the parent Knitting Program's `received_fabric_quantity`.
3. Filter by Dia `30"` displays only fabrics knitted on 30-inch machines.

---

## 19. Performance Budgets and Optimization Targets

- Stock table render time: $< 200\text{ms}$ for 100 rows.
- Filter query execution: $< 50\text{ms}$ on PostgreSQL composite index `(company_id, fabric_id, dia, gsm)`.

---

## 20. Future Enhancements and Scalability Roadmap

1. **Barcode / RFID Roll Tagging**: Scanning individual roll barcodes directly via wireless Bluetooth scanners.
2. **Four-Point Inspection Quality System**: Recording defect points (holes, oil stains, slubs) per roll during inward.

---

## 21. Sign-off and Approval Matrix

| Stakeholder Role | Name / Title | Date | Signature / Status |
|---|---|---|---|
| **Inventory Head** | Natarajan K. (Fabric Warehouse Manager) | 16/10/2026 | **APPROVED** |
| **Lead Architect** | Enterprise Garments Solutions | 16/10/2026 | **APPROVED** |
| **Knitting Head** | Senthil Nathan P. | 16/10/2026 | **APPROVED** |
