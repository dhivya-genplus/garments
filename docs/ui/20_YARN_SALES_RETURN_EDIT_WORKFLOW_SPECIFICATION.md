# Yarn Sales Return Edit & Cancellation Safeguard Specification

| Standard Code | Screen ID | Target Platform | API Version | Document Version | Date | Status |
|---|---|---|---|---|---|---|
| **STD-UI-001** | **`SCR-SALE-002-EDIT`** | Next.js 14 (App Router) + TypeScript | `v1.2` (Django 5 DRF) | `v1.0.0` | 15/10/2026 | **APPROVED FOR IMPLEMENTATION** |

---

## 1. Document Overview, Version, Scope, and Status

### 1.1 Purpose
This specification defines the user interface, state-dependent locking, stock consumption safeguards, and atomic financial/inventory reversal workflows for the **Yarn Sales Return Edit & Cancellation Screen** (`SCR-SALE-002-EDIT`).

Because a posted sales return has already:
1. Re-credited physical bags and weight into live godown stock in [`tm_yarn_stock`](file:///d:/Codebase/Garments/backend/apps/inventory/models.py),
2. Issued a financial Credit Note reducing customer receivables in [`tl_voucher`](file:///d:/Codebase/Garments/backend/apps/ledger/models.py), and
3. Impacted GST return reporting under GSTR-1 (Table 9B),

modifying or cancelling a sales return requires strict verification that the re-credited yarn has not already been consumed or re-dispatched into downstream knitting or dyeing programs.

### 1.2 Scope
- **Route**: `/sales/yarn-sales-returns/[id]/edit`
- **Entity**: [`parent_yarn_sales_return_table`](file:///d:/Codebase/Garments/backend/apps/sales/models.py) (`tm_yarn_sales_return`) and child lines [`child_yarn_sales_return_table`](file:///d:/Codebase/Garments/backend/apps/sales/models.py) (`tx_yarn_sales_return`).
- **Dependencies**: Verified against [`tm_yarn_stock`](file:///d:/Codebase/Garments/backend/apps/inventory/models.py) balances and linked sales invoices.

---

## 2. Module Details, Screen ID, Route, and Access Privileges

### 2.1 Core Metadata

| Parameter | Specification |
|---|---|
| **Module** | `Module 5 — Commercial Sales & Customer Returns` |
| **Screen ID** | `SCR-SALE-002-EDIT` |
| **Frontend Route** | `/sales/yarn-sales-returns/[id]/edit` |
| **File Location** | `app/(app)/sales/yarn-sales-returns/[id]/edit/page.tsx` |
| **Required Privileges** | `sales_yarn_return.can_edit`, `sales_yarn_return.can_cancel` |
| **Authorized Roles** | `SUPER_ADMIN`, `ADMIN_USER`, `COMPANY_USER` (Commercial Head, Senior Accountant, Store Manager) |
| **Country Pack** | `IN` (India: Currency `₹`, Date `DD/MM/YYYY`) |

### 2.2 Primary API Endpoints

| HTTP Method | API Path | Privilege / Scope | Description |
|---|---|---|---|
| `GET` | `/api/v1/sales/yarn-sales-returns/{id}/` | `can_read` | Fetch return details, original invoice reference, and line items |
| `PATCH` | `/api/v1/sales/yarn-sales-returns/{id}/` | `can_edit` | Update editable fields (inspection remarks, customer debit note reference) |
| `DELETE` | `/api/v1/sales/yarn-sales-returns/{id}/` | `can_cancel` | Atomically cancel return, reverse re-credited stock, and reverse credit note voucher |

---

## 3. UI Layout & State-Dependent Wireframe

```
+-----------------------------------------------------------------------------------------------------------------------------+
| GARMENTS ERP — Commercial Sales Desk                                         Company: ABC Textiles Ltd | FY: 2026-2027      |
+-----------------------------------------------------------------------------------------------------------------------------+
| [<- Back to Returns]  EDIT YARN SALES RETURN #YSRET-202610-0005                 [STATUS: POSTED / CREDIT NOTE ISSUED]       |
+-----------------------------------------------------------------------------------------------------------------------------+
| [!] POSTED CREDIT NOTE NOTICE                                                                                               |
| This customer return has been posted to accounting ledgers and live godown stock has been re-credited. Commercial weights,  |
| counts, and credit note figures are locked. Only inspection notes and cross-reference remarks may be updated.               |
+-----------------------------------------------------------------------------------------------------------------------------+
| RETURN HEADER & BUYER CONTEXT                                                                                               |
| Return Number:  [ YSRET-202610-0005 ] (Locked)    Return Date:   [ 15/10/2026 ] (Locked)    Warehouse: [ Central Godown   ] |
| Linked Invoice: [ YSAL-202610-0018  ] (Locked)    Category:      [ Grey Yarn  ] (Locked)    Place:     [ 33-Tamil Nadu    ] |
| Customer:       [ Premier Knittings Pvt Ltd - GSTIN: 33AAAAA1234A1Z5 - Tirupur                                     ] (Locked)|
| Return Reason:  [ Shade Variation / Uneven Color                                                                   ] (Locked)|
+-----------------------------------------------------------------------------------------------------------------------------+
| RETURNED ITEMS & CREDIT VALUE (LOCKED)                                                                                      |
| # | Yarn Count    | Mill         | Color Shade | Lot No | Ret Bags | Kg/Bag | Net Weight (Kg) | Rate (₹/Kg) | Credit Amt (₹)    |
|---+---------------+--------------+-------------+--------+----------+--------+-----------------+-------------+-------------------|
| 1 | 30s Karded    | Ramco Mills  | -- N/A --   | RM-901 |        5 | 45.360 |         226.800 |      340.00 |         77,112.00 |
| Total Returned Weight: 226.800 Kg  | Taxable Credit: ₹77,112.00 | GST Reversal (5%): ₹3,855.60 | Net Credit: ₹80,968.00     |
+-----------------------------------------------------------------------------------------------------------------------------+
| EDITABLE INSPECTION & INTERNAL NOTES                                                                                        |
| Quality Inspector:   [ S. Muthusamy - QC Lead     ]    Inspection Date: [ 15/10/2026                      ]                 |
| Customer Debit Note: [ DN-PK-2026-902             ]    Godown Rack Loc: [ Bin #B-14 (Quarantine / Hold)   ]                 |
| Inspection Remarks:  [ 5 bags confirmed with shade variation. Moved to quarantine rack for supplier return.             ]   |
+-----------------------------------------------------------------------------------------------------------------------------+
| [!] DOWNSTREAM STOCK CONSUMPTION CHECK:                                                                                     |
| Current Available Godown Stock for 30s Karded (Ramco - Lot #RM-901): 162 Bags | 7,348.320 Kg                                |
| [✓] Sufficient stock available in Central Godown to permit cancellation rollback.                                           |
|                                                                                                                             |
| [CANCEL / REVERSE SALES RETURN]                    [Discard Changes]                 [SAVE INSPECTION UPDATES]              |
+-----------------------------------------------------------------------------------------------------------------------------+
```

---

## 4. State-Dependent Locking Matrix

| Return State | Returned Items & Weights | Buyer & Warehouse | Quality & Internal Notes | Cancellation Button | Permitted Actions |
|---|---|---|---|---|---|
| **Draft (`status=1, is_authorized=0`)** | Fully Editable | Fully Editable | Fully Editable | Enabled | Modify lines, delete draft, or authorize. |
| **Posted (`status=1, is_authorized=1`)** | **LOCKED** (Read-only) | **LOCKED** (Read-only) | **EDITABLE** | **CONDITIONAL** (Checks Stock) | Update inspection notes, print credit note, cancel return. |
| **Stock Consumed / Deficit** | **LOCKED** (Read-only) | **LOCKED** (Read-only) | **EDITABLE** | **DISABLED** (Strict Block) | View and print only. Cannot cancel because stock has been re-dispatched. |
| **Cancelled (`status=0`)** | **LOCKED** (Read-only) | **LOCKED** (Read-only) | **LOCKED** (Read-only) | **DISABLED** | Void document with cancellation watermark. |

---

## 5. Downstream Stock Re-Dispatch Safeguard (Critical Invariant)

When a sales return is cancelled, the ERP must **deduct the returned stock back out** of [`tm_yarn_stock`](file:///d:/Codebase/Garments/backend/apps/inventory/models.py).

### The Invariant Check:
Before permitting cancellation, the system executes an atomic check:
$$\text{Current Godown Balance Quantity} \ge \text{Sales Return Quantity}$$
$$\text{Current Godown Balance Bags} \ge \text{Sales Return Bags}$$

1. **If Stock Has Been Issued/Consumed (`balance < return_quantity`)**:
   - The **`[CANCEL / REVERSE SALES RETURN]`** button is strictly disabled.
   - An alert dialog explains:
     ```
     +-------------------------------------------------------------------------+
     | [!] CANNOT CANCEL SALES RETURN                                         |
     | The yarn returned under this document (226.800 Kg) has already been     |
     | re-dispatched to production or sold.                                    |
     |                                                                         |
     | Current available balance in Central Godown is insufficient to allow    |
     | stock rollback without causing a negative stock violation.              |
     |                                                               [Close]   |
     +-------------------------------------------------------------------------+
     ```
2. **If Sufficient Stock Exists**:
   - The user is prompted with a confirmation modal requiring authorization PIN or explicit confirmation to proceed with the cancellation.

---

## 6. Atomic Reversal Workflow

Calling `DELETE /api/v1/sales/yarn-sales-returns/{id}/` executes [`YarnSalesReturnService.cancel_sales_return`](file:///d:/Codebase/Garments/backend/apps/sales/services.py) inside `@transaction.atomic`:
1. **Deducts Returned Stock**: Calls [`YarnStockService.reverse_sales_return_stock`](file:///d:/Codebase/Garments/backend/apps/sales/services.py):
   $$\text{balance\_bag} \leftarrow \text{balance\_bag} - \text{return.bag}$$
   $$\text{balance\_quantity} \leftarrow \text{balance\_quantity} - \text{return.quantity}$$
2. **Reverses Financial Voucher**: Locates voucher with `reference_type="SALES_RETURN"` and calls [`CurrencyLedgerService.reverse_voucher`](file:///d:/Codebase/Garments/backend/apps/sales/services.py) to swap Debits and Credits, reinstating the customer's original receivable balance.
3. **Soft Deletes Return**: Sets `status = 0` and records `updated_by`.

---

## 7. Developer Acceptance Criteria

- [ ] Route `/sales/yarn-sales-returns/[id]/edit` hydrates return data and displays locked commercial items.
- [ ] Internal notes and customer debit note numbers can be updated via `PATCH`.
- [ ] System dynamically checks `tm_yarn_stock` and blocks cancellation if current stock balance is lower than return weight.
- [ ] Cancellation successfully decrements stock and reverses the financial credit note voucher.
