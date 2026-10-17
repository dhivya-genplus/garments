# Yarn PO Return (Purchase Return & Debit Note) Add Workflow Specification

| Standard Code | Screen ID | Target Platform | API Version | Document Version | Date | Status |
|---|---|---|---|---|---|---|
| **STD-UI-001** | **`SCR-PROC-002-ADD`** | Next.js 14 (App Router) + TypeScript | `v1.2` (Django 5 DRF) | `v1.0.0` | 17/10/2026 | **APPROVED FOR IMPLEMENTATION** |

---

## 1. Document Overview, Version, Scope, and Status

### 1.1 Purpose
This specification establishes the technical requirements, UI layout, defect categorization, stock deduction safeguards, debit note generation, TypeScript interfaces, Zod validation schemas, and API integration for the **Yarn Purchase Order Return (PO Return / Vendor Return) Add Workflow** (`SCR-PROC-002-ADD`).

In textile production, yarn delivered by spinning mills undergoes rigorous quality inspection at the factory godown (Count testing, CSP strength, Uster hairiness, moisture regain, and cone package condition). If a lot fails quality specifications or is damaged in transit, the factory must issue a **formal Purchase Return Outward Delivery Challan** to dispatch the defective yarn back to the mill, accompanied by a **Statutory Debit Note** to deduct the billing amount from the mill's Accounts Payable ledger.

This screen is strictly separated from Customer Sales Returns (`SCR-SALE-002`) and provides:
1. **Source Document Binding**: Returning goods specifically against an authorized Yarn Purchase Order (`tm_yarn_po`) or Weighbridge Inward GRN (`tx_parent_yarn_inward`).
2. **Defect Reason Codification**: Mill-level rejection categorizations (`COUNT_VARIATION`, `LOW_CSP`, `HIGH_HAIRINESS`, `COLOR_SHADE_DEFECT`, `DAMAGED_CONES`, `EXCESS_MOISTURE`).
3. **Atomic Inventory Reversal**: Deducting exact bags and net weight from `tm_yarn_stock` without allowing negative balance.
4. **Financial Debit Note Integration**: Generating balanced double-entry accounting records (`tl_voucher`) reversing purchase expense and input GST tax credit.

### 1.2 Scope & Target Transactions
- **Operational Master**: `tm_yarn_po_return` (Return Header) & `tx_yarn_po_return_line` (Return Line Items).
- **Source Documents**: Binds to `tm_yarn_po` (`parent_po_table`) and `tm_yarn_inward` (`parent_yarn_inward_table`).
- **Ledger Impact**: Atomic generation of `tl_voucher` (Debit Note: Dr. Supplier AP, Cr. Purchase Returns, Cr. Input GST Reversal).
- **Stock Impact**: Atomic outward movement in `tm_yarn_stock` & `tl_stock_movement` from Godown.
- **Target Route**: `/procurement/yarn-po-returns/new` (`app/(app)/procurement/yarn-po-returns/new/page.tsx`).

---

## 2. Module Details, Screen ID, Route, Access Privileges, and API Endpoints

### 2.1 Core Metadata

| Parameter | Specification |
|---|---|
| **Module** | `Module 3 — Procurement & Vendor Management` |
| **Screen ID** | `SCR-PROC-002-ADD` |
| **Frontend Route** | `/procurement/yarn-po-returns/new` |
| **File Location** | `app/(app)/procurement/yarn-po-returns/new/page.tsx` |
| **Required Privilege** | `purchase_return.can_create` (Create return & debit note); `purchase_return.can_approve` (Authorize outward dispatch) |
| **Authorized Roles** | `SUPER_ADMIN`, `ADMIN_USER`, `COMPANY_USER` (Purchase Head, Quality QC Manager, Godown In-Charge) |
| **Country Pack** | `IN` (Currency: INR `₹`, GST 5% reverse input tax, Bags & Weight in `Kg` to 3 decimal places) |

### 2.2 Primary API Endpoints

| HTTP Method | API Path | Privilege / Scope | Description |
|---|---|---|---|
| `GET` | `/api/v1/purchase/yarn-po/?status=AUTHORIZED&party_id={id}` | `can_read` | Fetch authorized POs for selected spinning mill |
| `GET` | `/api/v1/inventory/yarn-inward/?party_id={id}&has_available_stock=1`| `can_read` | Fetch inward GRNs with unconsumed godown stock available for return |
| `POST` | `/api/v1/purchase/yarn-po-returns/` | `can_create` | Submit Yarn PO Return, deduct stock, and generate Debit Note |
| `GET` | `/api/v1/inventory/stock/yarn-balance/?count_id={id}&godown_id={id}`| `can_read` | Validate live godown balance before permitting return |

---

## 3. UI Layout, Screen Blueprint, and Visual Mockup (1440px+ Wireframe)

```
+-----------------------------------------------------------------------------------------------------------------------------+
| GARMENTS ERP — Yarn Purchase Return & Mill Debit Note                        Company: Tex Garments Mills Ltd | FY: 2026-2027|
+-----------------------------------------------------------------------------------------------------------------------------+
| [<- Back to PO Returns]  CREATE YARN PO RETURN (OUTWARD TO SPINNING MILL)                  [Reset Form]  [Save Draft]       |
+-----------------------------------------------------------------------------------------------------------------------------+
| SECTION 1: RETURN HEADER & SOURCE MILL CONTEXT                                                                              |
| Return Doc No: [ YPR-202610-0018 ] (Auto)       Return Date:  [ 17/10/2026 ]*   Financial Year: [ FY 2026-2027 (Active) ]   |
| Spinning Mill: [ Lakshmi Spinning Mills Ltd (Vendor Code: V-1042)                                                        v ]*|
| Source PO Ref: [ PO-202610-0012 — 30s Combed Cotton Cone Yarn (15,000 Kg)                                                v ]*|
| Inward GRN:    [ YIN-202610-0042 (Lot: L-8802 | Inward Date: 12/10/2026)                                                 v ]*|
| Return Godown: [ Main Central Yarn Godown - Bin A-12 (Available: 42 Bags / 1,905.120 Kg)                                v ]*|
| Defect Reason: [ LOW_CSP — Count Strength Product (CSP: 2450) below contractual minimum of 3000                        v ]*|
+-----------------------------------------------------------------------------------------------------------------------------+
| SECTION 2: DEFECTIVE YARN RETURN LINE ITEMS                                                                                 |
| Source Lot: L-8802 | Count: 30s Combed Cotton | Inward Rate: ₹265.0000/Kg | GST Rate: 5.0% (Input Reversal)                  |
|                                                                                                                             |
| # | Yarn Count*    | Lot No* | Inward Bags | Return Bags* | Net Wt/Bag* | Return Wt (Kg)*| Rate (₹/Kg)*| Taxable Value | GST 5% | Total Debit |
|---|----------------+---------+-------------+--------------+-------------+----------------+-------------+---------------+--------+-------------|
| 1 | 30s Combed     | L-8802  |     40 Bags |      20 Bags |   45.360 Kg |     907.200 Kg |  ₹ 265.0000 |  ₹ 2,40,408.00|₹ 12,020| ₹ 2,52,428  |
| 2 | 30s Combed     | L-8802  |     10 Bags |       5 Bags |   45.360 Kg |     226.800 Kg |  ₹ 265.0000 |  ₹   60,102.00|₹  3,005| ₹   63,107  |
|                                                                                                                             |
| Live Stock Verification: Requested Return 1,134.000 Kg <= Available Godown Stock 1,905.120 Kg [PASSED: SAFE TO RETURN]      |
+-----------------------------------------------------------------------------------------------------------------------------+
| SECTION 3: OUTWARD DISPATCH, TRANSPORTER & DEBIT NOTE SUMMARY                                                               |
| Transporter:    [ VRL Logistics Ltd                 ]   LR / Bilty No:   [ LR-998821034      ]   Vehicle No: [ TN-39-BZ-1290]  |
| Debit Note Ref: [ DN-2026-1042-01 ] (Auto-generated on Post)                                                                |
| Total Bags Ret: [ 25 Bags ]                             Total Net Weight: [ 1,134.000 Kg ]                                  |
| Subtotal Debit: ₹ 3,00,510.00                           CGST (2.5%): ₹ 7,512.75           SGST (2.5%): ₹ 7,512.75           |
| Total Debit Note Value: ₹ 3,15,535.50 (Deducted from Lakshmi Spinning Mills Ledger)                                         |
+-----------------------------------------------------------------------------------------------------------------------------+
| [Cancel (Esc)]                       [Print Defect Test Report]   [Preview Debit Note]   [SAVE & DISPATCH RETURN OUTWARD]   |
+-----------------------------------------------------------------------------------------------------------------------------+
```

---

## 4. Textile Defect Categorization Catalogue

Every Yarn PO Return must classify the underlying quality failure against the industry standard catalogue:

| Defect Code | Defect Description | Laboratory Testing Criteria | Mill Liability Rule |
|---|---|---|---|
| **`COUNT_VARIATION`** | Actual yarn count deviates beyond tolerance | Tested count deviates $>\pm 2.5\%$ from nominal (e.g. 28.5s instead of 30s). | Full lot rejection or rate downgrade debit. |
| **`LOW_CSP`** | Low Count Strength Product | Single yarn strength CSP $< 2800$ for Combed Hosiery. | High risk of needle breakages in knitting; full return. |
| **`HIGH_HAIRINESS`** | Excessive yarn hairiness ($H$-value) | Uster hairiness index $H > 6.2$; causes heavy surface fuzzing and pilling. | Rejection of cones; supplier debit note. |
| **`COLOR_SHADE_DEFECT`** | Shade variation / patchiness in dyed or melange | $\Delta E > 0.8$ against approved master lab dip. | Full lot return to dye house or melange mill. |
| **`DAMAGED_CONES`** | Physical transit or packaging damage | Crushed paper cones, sloughing yarn, grease/oil contamination. | Piece-rate or bag-weight return against transporter/mill. |
| **`EXCESS_MOISTURE`** | Moisture regain exceeds statutory limits | Moisture regain $> 8.5\%$ standard cotton regain (buying water). | Weight correction debit or full return. |

---

## 5. Mathematical Formulas & Keystroke Calculation Engine

1. **Return Weight Calculation**:
   $$\text{Return Weight (Kg)} = \text{Return Bags} \times \text{Nominal Bag Weight (45.360 Kg)}$$
2. **Taxable Debit Value**:
   $$\text{Taxable Value} = \text{Return Weight} \times \text{Inward Unit Rate (₹/Kg)}$$
3. **GST Tax Reversal (5% on Cotton Yarn)**:
   $$\text{CGST} = \text{Taxable Value} \times 2.5\%, \quad \text{SGST} = \text{Taxable Value} \times 2.5\%$$
   $$\text{IGST} = \text{Taxable Value} \times 5.0\% \quad (\text{if Interstate Outward})$$
4. **Total Debit Note Amount**:
   $$\text{Total Debit Note} = \text{Taxable Value} + \text{Tax}$$

---

## 6. Atomic Double-Entry Ledger Posting (`tl_voucher`)

Upon authorization and outward dispatch of the Yarn PO Return, the system creates a balanced voucher:

```
VOUCHER TYPE: DEBIT_NOTE (Reference: tm_yarn_po_return #18)
-------------------------------------------------------------------------------------------
Account                                    Debit (₹)             Credit (₹)
-------------------------------------------------------------------------------------------
Lakshmi Spinning Mills Ltd (Accounts Payable) ₹ 3,15,535.50
    To Yarn Purchase Returns (Expense Reversal)                    ₹ 3,00,510.00
    To Input CGST Reversal Account                                 ₹   7,512.75
    To Input SGST Reversal Account                                 ₹   7,512.75
-------------------------------------------------------------------------------------------
Total:                                      ₹ 3,15,535.50         ₹ 3,15,535.50  (Balanced)
```

---

## 7. TypeScript Types & Zod Schemas

```typescript
import { z } from 'zod';

export const YarnPoReturnLineSchema = z.object({
  id: z.number().optional(),
  yarn_count_id: z.number({ required_error: "Yarn count is required" }),
  lot_number: z.string().min(1, "Lot number is mandatory"),
  return_bags: z.number().int().positive("Return bags must be > 0"),
  weight_per_bag: z.number().positive().default(45.360),
  return_weight: z.number().positive("Return weight must be > 0"),
  return_rate: z.number().positive("Return rate must be > 0"),
  taxable_amount: z.number(),
  tax_rate: z.number().default(5.0),
  tax_amount: z.number(),
  total_debit: z.number(),
});

export const YarnPoReturnHeaderSchema = z.object({
  id: z.number().optional(),
  return_doc_no: z.string().min(3),
  return_date: z.string(),
  company_id: z.number(),
  party_id: z.number({ required_error: "Spinning Mill is mandatory" }),
  source_po_id: z.number({ required_error: "Source PO reference is mandatory" }),
  source_inward_id: z.number({ required_error: "Source Inward GRN is mandatory" }),
  godown_id: z.number({ required_error: "Godown location is mandatory" }),
  defect_reason: z.enum([
    'COUNT_VARIATION',
    'LOW_CSP',
    'HIGH_HAIRINESS',
    'COLOR_SHADE_DEFECT',
    'DAMAGED_CONES',
    'EXCESS_MOISTURE'
  ]),
  defect_notes: z.string().optional(),
  transporter_name: z.string().optional(),
  vehicle_no: z.string().optional(),
  lr_number: z.string().optional(),
  lines: z.array(YarnPoReturnLineSchema).min(1, "At least one return item line is required"),
});
```

---

## 8. Implementation Reference & Developer Checklist

- [x] Functional HTML reference implementation provided at [`frontend/yarn_po_return_sample.html`](file:///d:/Codebase/Garments/frontend/yarn_po_return_sample.html).
- [x] Implement backend models `tm_yarn_po_return` and `tx_yarn_po_return` in [`apps/purchase/models.py`](file:///d:/Codebase/Garments/backend/apps/purchase/models.py).
- [x] Implement `YarnPoReturnService.create_po_return()` with atomic stock decrement and ledger debit note in [`apps/purchase/services.py`](file:///d:/Codebase/Garments/backend/apps/purchase/services.py).
- [x] Enforce all 6 functional, operational, and financial restrictions with 16 automated tests in [`apps/purchase/tests.py`](file:///d:/Codebase/Garments/backend/apps/purchase/tests.py).
- [ ] Connect Next.js Page at `app/(app)/procurement/yarn-po-returns/new/page.tsx`.

---

## 9. Enforced Enterprise Functional, Operational & Financial Restrictions

### 1. Stock & Inventory Safeguards (Zero Negative Stock)
- **Live Balance Verification**: The return quantity cannot exceed the available unconsumed physical stock in that specific godown bin:
  $$\text{Requested Return Weight} \le \text{Available Godown Stock}$$
- **Atomic Lot Deduction**: Returns must be matched against a specific inward lot (`lot_no`). Stock cannot be deducted arbitrarily from a general pool or across different spinning lots.
- **Negative Stock Prohibition**: Atomic row-level locks (`select_for_update()`) prevent stock from dropping below zero under any concurrency circumstance.

### 2. Upstream Source Document Binding
- **Mandatory Reference Links**: Standalone returns are strictly prohibited. A return requires:
  - An authorized Yarn Purchase Order (`tm_yarn_po` / `parent_po_table` where `is_authorized = 1`, `status = 1`).
  - An authorized Inward GRN (`tm_yarn_inward` / `parent_yarn_inward_table` where `is_authorized = 1`, `has_available_stock = 1`).
- **Party Restriction**: The spinning mill vendor selected must match the exact party associated with the source PO and GRN (`party_id == po.party_id == inward.party_id`).
- **Unconsumed Balance Ceiling**: Total active return weight against an Inward GRN cannot exceed its original net receipt weight minus prior returns:
  $$\text{Requested Return Qty} \le \text{Inward GRN Net Wt} - \sum \text{Active Returns}$$

### 3. Role-Based Access Control (RBAC) & Privileges
- **Permission Gating**:
  - Drafting/creating a return requires `purchase_return.can_create`.
  - Outward dispatch and debit note ledger posting require `purchase_return.can_approve`.
- **Authorized Roles Only**: Gated to authorized personnel (`SUPER_ADMIN`, `ADMIN_USER`, `Purchase Head`, `Quality QC Manager`, `Godown In-Charge`). Regular unauthorized users receive an HTTP 403 Forbidden (`PERMISSION_DENIED`) restriction.

### 4. Mandatory Quality Defect Codification
- **Categorized Rejection Only**: Generic or free-text reasons alone are rejected. Returns must be explicitly categorized under a recognized industry defect code:
  - `COUNT_VARIATION` (e.g., count deviation $> \pm 2.5\%$)
  - `LOW_CSP` (e.g., strength CSP $< 2800$)
  - `HIGH_HAIRINESS` (e.g., Uster $H > 6.2$)
  - `COLOR_SHADE_DEFECT` (e.g., $\Delta E > 0.8$)
  - `DAMAGED_CONES` (physical packaging / transit damage)
  - `EXCESS_MOISTURE` (moisture regain $> 8.5\%$)
- **Mandatory Defect Findings**: QC inspection findings or laboratory test metrics (minimum 5 characters) must be documented in `defect_notes`.

### 5. Multi-Tenant & Fiscal Period Constraints
- **Tenant Isolation**: All operations are restricted by `company_id`. Cross-tenant returns or referencing another tenant’s inward GRN/PO is blocked at the database level.
- **Financial Year Lockdown**: Returns can only be posted within an Active / Open Financial Year (`fy.is_closed == False`). Closed or locked fiscal years reject outward movement and voucher creation. Return dates outside the FY period are rejected.

### 6. Double-Entry Accounting Immutability
- **Automated Debit Note Creation**: Outward returns atomically create a balanced `DEBIT_NOTE` voucher (`tl_voucher`):
  - **Debit**: Supplier's Accounts Payable ledger (`2001`, `total_debit_amount`).
  - **Credit**: Yarn Purchase Returns material reversal (`5002`, `subtotal`).
  - **Credit**: Statutory Input GST Reversal (Intrastate: `1006` CGST 2.5% + `1007` SGST 2.5%; Interstate: `1008` IGST 5.0%).
- **Read-Only Ledger Entries**: Direct modification (`PUT` / `PATCH`) and direct deletion (`DELETE`) return HTTP 400 `IMMUTABLE_RECORD`. Adjustments require formal compensatory contra-vouchers via `/cancel/`.

