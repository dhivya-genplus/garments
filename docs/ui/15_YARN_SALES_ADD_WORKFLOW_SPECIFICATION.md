# Yarn Sales Commercial Tax Invoice Add Workflow Specification

| Standard Code | Screen ID | Target Platform | API Version | Document Version | Date | Status |
|---|---|---|---|---|---|---|
| **STD-UI-001** | **`SCR-SALE-001-ADD`** | Next.js 14 (App Router) + TypeScript | `v1.2` (Django 5 DRF) | `v1.0.0` | 15/10/2026 | **APPROVED FOR IMPLEMENTATION** |

---

## 1. Document Overview, Version, Scope, and Status

### 1.1 Purpose
This specification defines the complete end-to-end frontend architecture, user interaction model, data grid operations, real-time keystroke math, statutory Indian GST calculations, and backend API integration for the **Yarn Sales Commercial Tax Invoice Add Workflow** (`SCR-SALE-001-ADD`).

This screen enables the commercial sales desk and godown billing team to generate statutory GST Tax Invoices for selling spinning yarn (Grey Yarn and Dyed Yarn) directly to domestic fabric manufacturers, export buyers, and merchant converters. Creating this invoice:
1. Atomically decrements stock from [`tm_yarn_stock`](file:///d:/Codebase/Garments/backend/apps/inventory/models.py) via [`YarnStockService.deduct_sales_stock`](file:///d:/Codebase/Garments/backend/apps/sales/services.py).
2. Computes Indian GST (Intra-state CGST 2.5% + SGST 2.5% or Inter-state IGST 5.0%) using the [`TaxEngine`](file:///d:/Codebase/Garments/backend/core/utils/tax_engine.py).
3. Automatically posts commercial receivables to the double-entry accounting ledger via [`CurrencyLedgerService.post_sales_invoice_voucher`](file:///d:/Codebase/Garments/backend/apps/sales/services.py).
4. Records itemized physical stock movements under [`tl_stock_movement`](file:///d:/Codebase/Garments/backend/apps/ledger/models.py).

### 1.2 Scope
- **Entities Handled**: Parent header [`parent_yarn_sales_table`](file:///d:/Codebase/Garments/backend/apps/sales/models.py) (`tm_yarn_sales`) and itemized line items [`child_yarn_sales_table`](file:///d:/Codebase/Garments/backend/apps/sales/models.py) (`tx_yarn_sales`).
- **Yarn Categories**: Grey Yarn (`GREY`) and Dyed Yarn (`DYED`).
- **Country Pack**: India (`IN`) — Indian Rupee (`₹`), Indian numbering formatting (`12,34,567.89`), Date format (`DD/MM/YYYY`), HSN codes `5205` / `5206`, standard bag tare calculations (`45.360 Kg`), and GST rules.

---


## 2. Module Details, Screen ID, Route, Access Privileges, and API Endpoints

### 2.1 Core Metadata

| Parameter | Specification |
|---|---|
| **Module** | `Module 5 — Commercial Sales & Customer Returns` |
| **Screen ID** | `SCR-SALE-001-ADD` |
| **Frontend Route** | `/sales/yarn-sales/new` |
| **File Location** | `app/(app)/sales/yarn-sales/new/page.tsx` |
| **Required Privilege** | `sales_yarn.can_create` |
| **Authorized Roles** | `SUPER_ADMIN`, `ADMIN_USER`, `COMPANY_USER` (Sales Executive, Commercial Accountant, Godown In-Charge) |
| **Country Pack** | `IN` (India: Currency INR `₹`, Date `DD/MM/YYYY`, Bags standard `45.360 Kg`, GST CGST/SGST/IGST) |

### 2.2 Primary API Endpoints

| HTTP Method | API Path | Privilege / Scope | Description |
|---|---|---|---|
| `POST` | `/api/v1/sales/yarn-sales/` | `can_create` | Create a new Yarn Sales Tax Invoice header and line items, deduct live stock atomically, and post financial vouchers |
| `GET` | `/api/v1/masters/parties/?party_type=CUSTOMER&is_active=1` | `can_read` | Fetch registered buyers and commercial customers |
| `GET` | `/api/v1/masters/warehouses/?is_active=1` | `can_read` | Fetch authorized storage godowns |
| `GET` | `/api/v1/masters/yarn-counts/?is_active=1` | `can_read` | Fetch standard textile yarn counts (e.g. 30s Karded, 40s Combed) |
| `GET` | `/api/v1/masters/parties/?party_type=MILL&is_active=1` | `can_read` | Fetch source spinning mills |
| `GET` | `/api/v1/masters/color-shades/?is_active=1` | `can_read` | Fetch master color shades (mandatory for Dyed yarn sales) |
| `GET` | `/api/v1/masters/taxes/?is_active=1` | `can_read` | Fetch GST tax rates (GST 5%, GST 12%, etc.) |
| `GET` | `/api/v1/inventory/yarn-stocks/?warehouse={id}&yarn_type={type}` | `can_read` | Query live physical godown stock balances before billing |
| `POST` | `/api/v1/pricing/resolve/` | `can_read` | Resolve contract / price-list selling rates based on customer, count, and category |

---

## 3. UI Layout, Screen Blueprint, and Visual Mockup (1440px+ Wireframe)

```
+-----------------------------------------------------------------------------------------------------------------------------+
| GARMENTS ERP — Commercial Sales Desk                                         Company: ABC Textiles Ltd | FY: 2026-2027      |
+-----------------------------------------------------------------------------------------------------------------------------+
| [<- Back to Invoices]  NEW YARN SALES TAX INVOICE (GST)                                      [Reset Form]  [Save Draft]    |
+-----------------------------------------------------------------------------------------------------------------------------+
| SECTION 1: INVOICE HEADER & BUYER CONTEXT                                                                                   |
| Invoice No: [ YSAL-202610-0018 ] (Auto)   Invoice Date: [ 15/10/2026 ]*   Payment Terms: [ 30 Days Credit      v ]         |
| Warehouse:  [ Central Godown       v ]*   Yarn Category: [ (o) Grey Yarn   ( ) Dyed Yarn ]   Place of Supply: [ 33-Tamil Nadu v ]*|
| Customer:   [ Premier Knittings Pvt Ltd - GSTIN: 33AAAAA1234A1Z5 - Tirupur                                                v ]*|
+-----------------------------------------------------------------------------------------------------------------------------+
| SECTION 2: LIVE STOCK LOOKUP & ITEM BILLING GRID                                                                            |
| Live Godown Stock Available: 30s Combed (Ramco Mills) - Lot #RM-901:  142 Bags | 6,441.120 Kg | Cost: ₹325.00/Kg           |
|                                                                                                                             |
| # | Yarn Count*    | Mill*        | Color Shade   | Lot No*  | Bags* | Kg/Bag* | Net Weight (Kg)* | Rate (₹/Kg)* | Subtotal (₹) |
|---+----------------+--------------+---------------+----------+-------+---------+------------------+--------------+--------------|
| 1 | 30s Karded     | Ramco Mills  | -- N/A --     | RM-901   |    20 |  45.360 |          907.200 |       340.00 |  3,08,448.00 |
| 2 | 40s Combed     | Loyal Textile| -- N/A --     | LT-440   |    15 |  45.360 |          680.400 |       375.00 |  2,55,150.00 |
|   |                |              |               |          |       |         |                  |              |              |
| [+ Add Line Item (F4)]                                                                                                      |
+-----------------------------------------------------------------------------------------------------------------------------+
| SECTION 3: GST TAXATION, LOGISTICS & SUMMARY DOCK                                                                           |
| Transport & E-Way Bill Details:                               | Commercial Tax & Settlement Summary:                        |
| Vehicle No:     [ TN-38-BZ-4412   ]                           | Total Bags:                    35 Bags                      |
| Transporter:    [ VRL Logistics    ]                           | Total Net Weight:        1,587.600 Kg                       |
| E-Way Bill No:  [ 2410 9812 7654  ]                           | Subtotal (Taxable):      ₹5,63,598.00                       |
| Driver / Mobile:[ K. Palanisamy - 9842100000 ]                | Tax Structure:           [ GST 5% (Yarn)             v ]    |
| Delivery Note:  [ Urgent dispatch for knitting unit ]         | CGST (2.50%):              ₹14,089.95                       |
| Remarks:        [ Against Contract #CON-2026-88 ]             | SGST (2.50%):              ₹14,089.95                       |
|                                                               | IGST (0.00%):                   ₹0.00 (Intra-State)         |
|                                                               | Round-Off Adjustment:           +₹0.10                      |
|                                                               | NET INVOICE PAYABLE:     ₹5,91,778.00                       |
|                                                               | (Rupees Five Lakh Ninety-One Thousand Seven Hundred         |
|                                                               |  and Seventy-Eight Only)                                    |
+-----------------------------------------------------------------------------------------------------------------------------+
| [Cancel (Esc)]                                    [View Stock Balance (F2)]     [Save & Print]  [POST TAX INVOICE (Ctrl+S)] |
+-----------------------------------------------------------------------------------------------------------------------------+
```

---

## 4. Page Initialization, Query Parameters, and Default Form State

### 4.1 Page Hydration Lifecycle
1. **Parallel Master Data Hydration** (`TanStack Query`):
   - Active warehouses for the tenant (`tm_warehouse`).
   - Active customers (`tm_party` where `party_type='CUSTOMER'`).
   - Active spinning mills (`tm_party` where `party_type='MILL'`).
   - Active yarn counts (`tm_yarn_count`).
   - Active color shades (`tm_color_shade`).
   - Master taxes (`mx_tax`).
2. **Current Financial Year Context**:
   - Evaluates tenant company state code (e.g. `33` for Tamil Nadu).
   - Validates that current date falls within `active_fy.start_date` and `active_fy.end_date`.
3. **Query Parameter Handling**:
   - `?customer_id=12`: Pre-selects buyer and automatically resolves billing/shipping state and payment terms.
   - `?warehouse_id=2`: Locks storage godown and scopes stock queries.
   - `?yarn_type=DYED`: Switches form mode to Dyed Yarn and enforces color shade selection.

---

## 5. Document Header, Fiscal Context, and Financial Year Configuration

| Field Name | Type | UI Control | Validation & Invariants | Default Value |
|---|---|---|---|---|
| `invoice_number` | String | Read-only Input | Auto-generated by backend (`YSAL-YYYYMM-XXXX`). Read-only. | System generated |
| `invoice_date` | Date | Date Picker (`DD/MM/YYYY`) | Must fall within active FY (`01/04/2026 - 31/03/2027`). Cannot be future date. | Current local date |
| `warehouse` | Integer | Searchable Select | Required. Master warehouse location. Stock deducted from this godown. | Default Company Warehouse |
| `customer` | Integer | Searchable Select | Required. Buyer party. Auto-fetches GSTIN, billing address, and default state. | None (Prompt to select) |
| `yarn_type` | String | Radio Group (`GREY`/`DYED`) | Required. If `DYED`, unlocks color shade columns and validation. | `GREY` |
| `place_of_supply`| String | Searchable Select | Required for GST engine. State code (e.g., `33-Tamil Nadu`, `29-Karnataka`). | Customer State |
| `payment_terms` | String | Select / Input | Commercial credit term (e.g., `Advance`, `Immediate`, `15 Days Credit`, `30 Days Credit`). | `30 Days Credit` |

---

## 6. Primary Master Linkages

### 6.1 Customer Master Linkage
- Fetching a customer triggers auto-population of:
  1. **GSTIN**: 15-character statutory alphanumeric code (e.g., `33AAAAA0000A1Z5`).
  2. **Billing / Shipping Address**: Full postal address including pincode.
  3. **State Code**: First 2 digits of GSTIN (e.g., `33` for Tamil Nadu, `27` for Maharashtra).
  4. **Tax Applicability**: If customer is registered in the same state as the company warehouse, the system applies **Intra-state GST (CGST 2.5% + SGST 2.5%)**; otherwise, it applies **Inter-state GST (IGST 5.0%)**.

### 6.2 Price List Resolution Engine
- When selecting `customer` + `yarn_count` + `yarn_type`, the UI queries `/api/v1/pricing/resolve/`:
  - Returns agreed price-list contract rate (₹/Kg).
  - Populates the `rate` field with visual indicator: `[Contract Rate Applied: ₹340.00]`.
  - Can be manually overridden if user holds the `pricing.edit_rate` privilege.

---

## 7. Dynamic Technical Specifications

When `yarn_type == 'DYED'`:
1. **Color Shade Master Linkage** becomes strictly mandatory (`color_shade_id`).
2. **Dyeing Lot / Batch Number** is validated against dyed yarn stock layers.
3. Grid unlocks `Color Shade` dropdown with color preview swatch and shade code.

---

## 8. Interactive Spreadsheet Data Grid & Line Items

| Col # | Column Header | Data Key | UI Control | Formatting | Required | Behavior |
|---|---|---|---|---|---|---|
| 1 | **#** | `line_number` | Text Badge | Integer | Yes | Auto-incremented row index |
| 2 | **Yarn Count** | `yarn_count_id` | Select | Text (30s K, 40s C) | Yes | Triggers live stock query |
| 3 | **Spinning Mill** | `mill_id` | Select | Text (Ramco, Loyal) | Yes | Filters stock by mill |
| 4 | **Color Shade** | `color_shade_id` | Select | Text (Navy Blue #04) | Conditional | Required if `yarn_type == 'DYED'` |
| 5 | **Lot Number** | `lot_no` | Combobox | Alphanumeric | Yes | Auto-fills from stock lots |
| 6 | **Stock On Hand** | `stock_available` | Read-only Pill | `1,234.000 Kg` (Bags) | No | Displays live balance in warehouse |
| 7 | **Bags Sold** | `bag` | Number Input | Integer (`20`) | Yes | Keystroke calculates weight |
| 8 | **Weight/Bag** | `per_bag` | Number Input | Decimal (`45.360`) | Yes | Defaults to 45.360 Kg |
| 9 | **Net Weight (Kg)**| `quantity` | Number Input | Decimal (`907.200`) | Yes | `bag * per_bag` (or direct input) |
| 10 | **Rate (₹/Kg)** | `rate` | Currency Input | `₹340.00` | Yes | Selling price per net Kg |
| 11 | **Subtotal (₹)** | `amount` | Read-only | `₹3,08,448.00` | Yes | `quantity * rate` |
| 12 | **Actions** | `actions` | Button | Icon (Trash) | No | Deletes row (Min 1 row required) |

---

## 9. Mathematical Formulas & Keystroke Calculation Engine

Every calculation executes synchronously in memory on keystroke:

### 9.1 Net Billed Weight
$$\text{Line Quantity (Kg)} = \text{Line Bags} \times \text{Line Per-Bag Tare Weight (45.360)}$$

### 9.2 Taxable Line Amount
$$\text{Line Subtotal (₹)} = \text{Line Quantity (Kg)} \times \text{Selling Rate (₹/Kg)}$$

### 9.3 Invoice Subtotal
$$\text{Invoice Subtotal} = \sum_{i=1}^{n} \text{Line Subtotal}_i$$

### 9.4 GST Tax Breakdown
Using [`TaxEngine`](file:///d:/Codebase/Garments/backend/core/utils/tax_engine.py):
- **Intra-State Sale** ($\text{Company State} == \text{Place of Supply}$):
  $$\text{CGST Amount} = \text{Round}\left(\text{Invoice Subtotal} \times \frac{2.50}{100}, 2\right)$$
  $$\text{SGST Amount} = \text{Round}\left(\text{Invoice Subtotal} \times \frac{2.50}{100}, 2\right)$$
  $$\text{IGST Amount} = ₹0.00$$
- **Inter-State Sale** ($\text{Company State} \ne \text{Place of Supply}$):
  $$\text{CGST Amount} = ₹0.00, \quad \text{SGST Amount} = ₹0.00$$
  $$\text{IGST Amount} = \text{Round}\left(\text{Invoice Subtotal} \times \frac{5.00}{100}, 2\right)$$

### 9.5 Total Payable & Indian Round-Off
$$\text{Gross Total} = \text{Invoice Subtotal} + \text{CGST Amount} + \text{SGST Amount} + \text{IGST Amount}$$
$$\text{Net Invoice Payable} = \text{Round}(\text{Gross Total}, 0)$$
$$\text{Round-Off Adjustment} = \text{Net Invoice Payable} - \text{Gross Total}$$

---

## 10. Godown / Warehouse Stock Allocation & Storage Location

1. When a user selects `(Warehouse, Yarn Count, Mill, Lot No)`:
   - Client sends asynchronous check to `/api/v1/inventory/yarn-stocks/`.
   - Displays real-time badge: `Available in Godown: 142 Bags (6,441.120 Kg)`.
2. **Hard Validation**:
   - If `entered_bags > available_bags` OR `entered_quantity > available_quantity`:
     - Input flashes red with warning tooltip: *"Insufficient stock! Maximum available is 142 bags."*
     - Disables form submission button until quantity is adjusted or stock override privilege is held.

---

## 11. Summary Bar, Remarks, Gate Pass Details, and Total Calculations

Located in the bottom sticky dock:
- **Total Bags**: $\sum \text{Bags}$ formatted as integer badge.
- **Total Net Weight**: $\sum \text{Quantity}$ formatted as `1,587.600 Kg`.
- **Taxable Subtotal**: Formatted in Indian Rupees `₹5,63,598.00`.
- **Total GST Amount**: Formatted as `₹28,179.90`.
- **Net Amount Payable**: Formatted as `₹5,91,778.00`.
- **Amount in Words**: Auto-generated in Indian English (e.g. *"Rupees Five Lakh Ninety-One Thousand Seven Hundred and Seventy-Eight Only"*).
- **Logistics Inputs**: Vehicle No, Transporter Name, E-Way Bill No.

---

## 12. Form Validation Rules and Error Messages

| Field | Validation Condition | Error Message |
|---|---|---|
| `customer` | Must not be empty | "Please select a registered customer/buyer." |
| `warehouse` | Must not be empty | "Please select the dispatch warehouse godown." |
| `invoice_date` | Must fall within active FY | "Invoice date must fall within current FY (01/04/2026 - 31/03/2027)." |
| `yarn_type` | Must be `GREY` or `DYED` | "Invalid yarn type selected." |
| `color_shade` | Required if `yarn_type == 'DYED'` | "Color shade is required for Dyed Yarn Sales." |
| `line_items` | Minimum 1 valid line item | "Invoice must contain at least one line item." |
| `bag` | Integer > 0 | "Bag count must be greater than zero." |
| `quantity` | Decimal > 0.000 | "Sold quantity must be greater than zero." |
| `rate` | Decimal > 0.00 | "Sale rate per Kg must be greater than zero." |
| `stock_check` | `quantity <= available_stock` | "Dispatch exceeds current godown balance! Available: {x} Kg." |

---

## 13. Lifecycle Workflows

```mermaid
flowchart TD
    A[Start: Open /sales/yarn-sales/new] --> B[Select Warehouse, Customer & Yarn Type]
    B --> C[Add Line Items & Select Mill/Count/Lot]
    C --> D[Live Stock Availability Query]
    D -->|Insufficient Stock| E[Block Submission / Show Red Alert]
    D -->|Stock Available| F[Keystroke Net Weight & Tax Calculation]
    F --> G[Enter Vehicle No & E-Way Bill]
    G --> H{Action Chosen}
    H -->|Save Draft| I[POST /api/v1/sales/yarn-sales/ with is_authorized=0]
    H -->|Post Tax Invoice| J[POST /api/v1/sales/yarn-sales/ with is_authorized=1]
    J --> K[Atomic Stock Decrement in tm_yarn_stock]
    K --> L[Post Voucher in Currency Ledger]
    L --> M[Record Movement in Stock Ledger]
    M --> N[Redirect to Print View /sales/yarn-sales/[id]/print]
```

---

## 14. API Integration, Request Headers, Payload Serialization, and HTTP Errors

### 14.1 Request Headers
```http
POST /api/v1/sales/yarn-sales/ HTTP/1.1
Host: api.garmentserp.local
Authorization: Bearer <jwt_access_token>
X-Company-ID: 1
Content-Type: application/json
```

### 14.2 Request Payload
```json
{
  "invoice_date": "15/10/2026",
  "yarn_type": "GREY",
  "warehouse_id": 1,
  "customer_id": 5,
  "place_of_supply": "33-Tamil Nadu",
  "payment_terms": "30 Days Credit",
  "remarks": "Against Contract #CON-2026-88",
  "tax_id": 1,
  "bag": 35,
  "per_bag": "45.360",
  "quantity": "1587.600",
  "rate": "355.00",
  "line_items": [
    {
      "yarn_count_id": 1,
      "mill_id": 3,
      "color_shade_id": null,
      "lot_no": "RM-901",
      "bag": 20,
      "per_bag": "45.360",
      "quantity": "907.200",
      "rate": "340.00",
      "amount": "308448.000"
    },
    {
      "yarn_count_id": 2,
      "mill_id": 4,
      "color_shade_id": null,
      "lot_no": "LT-440",
      "bag": 15,
      "per_bag": "45.360",
      "quantity": "680.400",
      "rate": "375.00",
      "amount": "255150.000"
    }
  ]
}
```

### 14.3 Success Response (`201 Created`)
```json
{
  "success": true,
  "data": {
    "id": 18,
    "invoice_number": "YSAL-202610-0018",
    "invoice_date": "15/10/2026",
    "yarn_type": "GREY",
    "customer_name": "Premier Knittings Pvt Ltd",
    "warehouse_name": "Central Godown",
    "subtotal": "563598.000",
    "tax_percent": "5.00",
    "tax_amount": "28179.900",
    "cgst_percent": "2.50",
    "cgst_amount": "14089.950",
    "sgst_percent": "2.50",
    "sgst_amount": "14089.950",
    "igst_percent": "0.00",
    "igst_amount": "0.000",
    "total_amount": "591777.900",
    "is_authorized": 1,
    "status": 1
  }
}
```

---

## 15. Next.js Folder Structure and Component Responsibilities

```
frontend/src/app/(app)/sales/yarn-sales/
├── page.tsx                           # SCR-SALE-001-LIST (Sales Register)
├── new/
│   ├── page.tsx                       # SCR-SALE-001-ADD (Invoice Add Workflow)
│   ├── components/
│   │   ├── InvoiceHeaderCard.tsx      # Customer, warehouse, date, place of supply
│   │   ├── YarnSalesDataGrid.tsx      # Interactive line items table with live math
│   │   ├── LiveStockIndicator.tsx     # Real-time stock badge & warning
│   │   ├── GSTSummaryDock.tsx         # Tax calculation, round-off, amount in words
│   │   └── TransportDetailsModal.tsx  # Vehicle, E-Way Bill & Transporter details
│   ├── hooks/
│   │   ├── useYarnSalesForm.ts        # React Hook Form + Zod controller
│   │   ├── useStockAvailability.ts    # Debounced godown stock querying hook
│   │   └── useGstCalculator.ts        # Intra/Inter state GST computation engine
│   └── types/
│       └── yarn-sales.types.ts        # TypeScript DTOs and Zod schemas
└── [id]/
    ├── edit/
    │   └── page.tsx                   # SCR-SALE-001-EDIT (Edit & Cancellation)
    └── print/
        └── page.tsx                   # SCR-SALE-001-PRINT (A4 Tax Invoice Print)
```

---

## 16. React Hooks, TypeScript Types, Zod Schemas, and Form State

### 16.1 Zod Validation Schema
```typescript
import { z } from "zod";

export const YarnSalesLineItemSchema = z.object({
  yarn_count_id: z.number({ required_error: "Select yarn count" }).min(1),
  mill_id: z.number({ required_error: "Select spinning mill" }).min(1),
  color_shade_id: z.number().nullable().optional(),
  lot_no: z.string().min(1, "Enter lot number"),
  bag: z.number().int().min(1, "Minimum 1 bag"),
  per_bag: z.number().positive().default(45.360),
  quantity: z.number().positive("Quantity must be positive"),
  rate: z.number().positive("Rate must be positive"),
  amount: z.number().nonnegative(),
});

export const YarnSalesFormSchema = z.object({
  invoice_date: z.string().regex(/^\d{2}\/\d{2}\/\d{4}$/, "Format: DD/MM/YYYY"),
  yarn_type: z.enum(["GREY", "DYED"]),
  warehouse_id: z.number({ required_error: "Select warehouse" }).min(1),
  customer_id: z.number({ required_error: "Select customer" }).min(1),
  place_of_supply: z.string().min(1, "Select place of supply"),
  payment_terms: z.string().default("30 Days Credit"),
  remarks: z.string().max(200).optional(),
  vehicle_no: z.string().max(30).optional(),
  transporter_name: z.string().max(100).optional(),
  eway_bill_no: z.string().max(50).optional(),
  tax_id: z.number().optional(),
  line_items: z.array(YarnSalesLineItemSchema).min(1, "At least one line item required"),
}).superRefine((data, ctx) => {
  if (data.yarn_type === "DYED") {
    data.line_items.forEach((item, idx) => {
      if (!item.color_shade_id) {
        ctx.addIssue({
          code: z.ZodIssueCode.custom,
          message: "Color shade required for dyed yarn",
          path: ["line_items", idx, "color_shade_id"],
        });
      }
    });
  }
});

export type YarnSalesFormData = z.infer<typeof YarnSalesFormSchema>;
```

---

## 17. Factory Floor & Billing Desk Keyboard Ergonomics

| Key Combination | Action Scope | Function |
|---|---|---|
| `Ctrl + S` | Global Form | Post & Submit Sales Tax Invoice |
| `F4` | Data Grid | Insert new line item row |
| `F2` | Selected Row | Trigger live godown stock balance inspector |
| `Delete` / `Backspace` | Data Grid Row | Remove highlighted line item (with confirm) |
| `Tab` / `Enter` | Data Inputs | Advance focus horizontally across line item fields |
| `Escape` | Global Form | Open discard changes confirmation modal |

---

## 18. Loading States, Shimmer Skeletons, and User Feedback

- **Form Loading**: Shimmer skeleton placeholder for header cards and 4 mock table rows while master data hydrates.
- **Stock Checking Indicator**: Inline spinning micro-loader inside the `Stock On Hand` cell during debounced API check.
- **Submission Feedback**:
  - Button switches to spinning icon with text *"Deducting Stock & Posting Invoice..."*.
  - On success: Toast notification: *"Invoice YSAL-202610-0018 posted successfully! Redirecting to print..."*.
- **Error Banner**: Toast message displaying exact backend error (e.g. *"Insufficient Stock: Only 50.000 Kg available in Central Godown"*).

---

## 19. Security, Tenant Scoping, and Backend Invariant Validation Requirements

1. **Strict Tenant Isolation**: `company_id` is never accepted in request payloads; extracted exclusively from authenticated JWT session on the server.
2. **Double-Entry Financial Accounting**: Creating an invoice automatically dispatches `CurrencyLedgerService.post_sales_invoice_voucher()` to post balanced Dr/Cr ledger entries (Dr Customer Account, Cr Yarn Sales Account, Cr CGST/SGST/IGST Output Accounts).
3. **Physical Stock Invariant**: No sales transaction may reduce `balance_quantity` or `balance_bag` below zero in `tm_yarn_stock`.

---

## 20. Implementation Sequence and Developer Acceptance Checklist

- [ ] Scaffold `app/(app)/sales/yarn-sales/new/page.tsx` with layout dock.
- [ ] Implement `InvoiceHeaderCard` with customer selection, GSTIN display, and Place of Supply resolution.
- [ ] Build `YarnSalesDataGrid` with auto-calculated weight, rate, and subtotal.
- [ ] Connect debounced stock lookup to warn when billed quantity exceeds physical godown stock.
- [ ] Implement `useGstCalculator` with intra-state (CGST+SGST) vs inter-state (IGST) logic and Indian round-off.
- [ ] Connect `POST /api/v1/sales/yarn-sales/` and verify atomic stock deduction.
- [ ] Verify automatic redirection to `/sales/yarn-sales/[id]/print` upon invoice posting.

---

## 21. Existing Inconsistencies, Edge Cases, and Items Requiring Confirmation

1. **Credit Limit Blocking**: Currently, if a customer exceeds their sanctioned credit limit, the invoice saves with a warning. A future enhancement will introduce a strict `credit_limit_override` privilege lock.
2. **Split Tax Rates**: Standard spinning yarn attracts 5% GST (HSN 5205/5206). Multi-tax invoices (e.g. 12% polyester blended yarn on the same bill) are supported via line-item tax overrides.
