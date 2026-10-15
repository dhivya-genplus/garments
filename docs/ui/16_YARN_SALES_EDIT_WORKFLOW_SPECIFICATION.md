# Yarn Sales Tax Invoice Edit & Cancellation Specification

| Standard Code | Screen ID | Target Platform | API Version | Document Version | Date | Status |
|---|---|---|---|---|---|---|
| **STD-UI-001** | **`SCR-SALE-001-EDIT`** | Next.js 14 (App Router) + TypeScript | `v1.2` (Django 5 DRF) | `v1.0.0` | 15/10/2026 | **APPROVED FOR IMPLEMENTATION** |

---

## 1. Document Overview, Version, Scope, and Status

### 1.1 Purpose
This specification governs the frontend behavior, state-dependent UI field locking, customer sales return dependencies, and atomic inventory/accounting reversal procedures for the **Yarn Sales Tax Invoice Edit & Cancellation Screen** (`SCR-SALE-001-EDIT`).

Because a posted Yarn Sales Tax Invoice has already:
1. Deducted stock physically from [`tm_yarn_stock`](file:///d:/Codebase/Garments/backend/apps/inventory/models.py),
2. Created double-entry financial debtor vouchers in [`tl_voucher`](file:///d:/Codebase/Garments/backend/apps/ledger/models.py), and
3. Reported statutory GST liability under GSTR-1,

modifying or cancelling an invoice requires rigorous verification of downstream customer returns and strict role-based authorization.

### 1.2 Scope
- **Entities Handled**: Parent invoice [`parent_yarn_sales_table`](file:///d:/Codebase/Garments/backend/apps/sales/models.py) (`tm_yarn_sales`) and lines [`child_yarn_sales_table`](file:///d:/Codebase/Garments/backend/apps/sales/models.py) (`tx_yarn_sales`).
- **Dependencies Checked**: [`parent_yarn_sales_return_table`](file:///d:/Codebase/Garments/backend/apps/sales/models.py) (`tm_yarn_sales_return`).
- **Invariants**: Cancellation reverses live godown stock and posts a contra reversal voucher in the financial ledger.

---

## 2. Module Details, Screen ID, Route, and Access Privileges

### 2.1 Core Metadata

| Parameter | Specification |
|---|---|
| **Module** | `Module 5 — Commercial Sales & Customer Returns` |
| **Screen ID** | `SCR-SALE-001-EDIT` |
| **Frontend Route** | `/sales/yarn-sales/[id]/edit` |
| **File Location** | `app/(app)/sales/yarn-sales/[id]/edit/page.tsx` |
| **Required Privileges** | `sales_yarn.can_edit` (for drafts/logistics), `sales_yarn.can_cancel` (for cancellation) |
| **Authorized Roles** | `SUPER_ADMIN`, `ADMIN_USER`, `COMPANY_USER` (Commercial Manager, Accounts Head) |
| **Country Pack** | `IN` (India: GST Invariants, Currency `₹`, Date `DD/MM/YYYY`) |

### 2.2 Primary API Endpoints

| HTTP Method | API Path | Privilege / Scope | Description |
|---|---|---|---|
| `GET` | `/api/v1/sales/yarn-sales/{id}/` | `can_read` | Fetch full invoice details, line items, buyer metadata, and return references |
| `PATCH` | `/api/v1/sales/yarn-sales/{id}/` | `can_edit` | Update editable fields (logistics, remarks, delivery notes) on posted invoices |
| `DELETE` | `/api/v1/sales/yarn-sales/{id}/` | `can_cancel` | Atomically cancel invoice, reverse godown stock, and create ledger reversal voucher |
| `GET` | `/api/v1/sales/yarn-sales-returns/?sales_invoice={id}&status=1` | `can_read` | Query any active customer sales returns referencing this invoice |

---

## 3. UI Layout & State-Dependent Wireframe

```
+-----------------------------------------------------------------------------------------------------------------------------+
| GARMENTS ERP — Commercial Sales Desk                                         Company: ABC Textiles Ltd | FY: 2026-2027      |
+-----------------------------------------------------------------------------------------------------------------------------+
| [<- Back to Invoices]  EDIT YARN SALES INVOICE #YSAL-202610-0018              [STATUS: POSTED / AUTHORIZED] [Print (Ctrl+P)]|
+-----------------------------------------------------------------------------------------------------------------------------+
| [!] POSTED COMMERCIAL INVOICE NOTICE                                                                                        |
| This invoice has been posted to accounting ledgers and live godown stock has been deducted. Commercial items, counts,       |
| and tax figures are locked. To make adjustments to billed goods, issue a Customer Sales Return or Cancel & Re-bill.         |
+-----------------------------------------------------------------------------------------------------------------------------+
| INVOICE HEADER & BUYER CONTEXT                                                                                              |
| Invoice No:   [ YSAL-202610-0018 ] (Locked)      Invoice Date: [ 15/10/2026 ] (Locked)    Payment Terms: [ 30 Days Credit ] |
| Warehouse:    [ Central Godown   ] (Locked)      Category:     [ Grey Yarn  ] (Locked)    Place of Supply: [ 33-Tamil Nadu ]|
| Customer:     [ Premier Knittings Pvt Ltd - GSTIN: 33AAAAA1234A1Z5 - Tirupur                                       ] (Locked)|
+-----------------------------------------------------------------------------------------------------------------------------+
| BILLED ITEMS & GST SUMMARY (LOCKED)                                                                                         |
| # | Yarn Count    | Mill         | Color Shade | Lot No | Bags | Kg/Bag | Net Weight (Kg) | Rate (₹/Kg) | Subtotal (₹)      |
|---+---------------+--------------+-------------+--------+------+--------+-----------------+-------------+-------------------|
| 1 | 30s Karded    | Ramco Mills  | -- N/A --   | RM-901 |   20 | 45.360 |         907.200 |      340.00 |       3,08,448.00 |
| 2 | 40s Combed    | Loyal Textile| -- N/A --   | LT-440 |   15 | 45.360 |         680.400 |      375.00 |       2,55,150.00 |
| Total Net Billed Weight: 1,587.600 Kg  | Subtotal: ₹5,63,598.00 | GST (5%): ₹28,179.90 | Total Payable: ₹5,91,778.00        |
+-----------------------------------------------------------------------------------------------------------------------------+
| EDITABLE LOGISTICS & DISPATCH METADATA                                                                                      |
| Vehicle No:      [ TN-38-BZ-4412            ]    Transporter:     [ VRL Logistics Ltd                 ]                         |
| E-Way Bill No:   [ 2410 9812 7654           ]    LR / RR No:      [ LR-990184                         ]                         |
| Driver Name/Tel: [ K. Palanisamy - 98421000 ]    Remarks:         [ Customer requested delivery before 5 PM ]               |
+-----------------------------------------------------------------------------------------------------------------------------+
| [!] SALES RETURN DEPENDENCY CHECK:                                                                                          |
| [✓] No active Customer Sales Returns exist against this invoice. Safe to cancel if unfulfilled.                             |
|                                                                                                                             |
| [CANCEL / REVERSE INVOICE]                       [Discard Changes]                 [SAVE LOGISTICS UPDATES]                 |
+-----------------------------------------------------------------------------------------------------------------------------+
```

---

## 4. State-Dependent Locking Matrix

| Invoice State | Commercial Line Items | Warehouse & Buyer | Logistics & E-Way Bill | Cancellation Button | Permitted Actions |
|---|---|---|---|---|---|
| **Draft (`status=1, is_authorized=0`)** | Fully Editable (Add, Delete, Edit) | Fully Editable | Fully Editable | Enabled (Direct Delete) | Full modification, line item additions, save draft or post. |
| **Posted (`status=1, is_authorized=1`)** | **LOCKED** (Read-only) | **LOCKED** (Read-only) | **EDITABLE** | **CONDITIONAL** (Checks Returns) | Update transport details, print invoice, cancel with stock reversal. |
| **With Sales Returns** | **LOCKED** (Read-only) | **LOCKED** (Read-only) | **EDITABLE** | **DISABLED** (Strict Block) | View only. Cannot cancel because credit notes / stock returns exist. |
| **Cancelled (`status=0`)** | **LOCKED** (Read-only) | **LOCKED** (Read-only) | **LOCKED** (Read-only) | **DISABLED** | Void document. Displays red cancellation watermark. |

---

## 5. Downstream Sales Return Protection (Critical Invariant)

When the user clicks the **`[CANCEL / REVERSE INVOICE]`** button:
1. The client executes an API check:
   ```http
   GET /api/v1/sales/yarn-sales-returns/?sales_invoice={id}&status=1
   ```
2. **If Returns Exist (`returns.length > 0`)**:
   - The action is aborted immediately on the client.
   - A modal dialog appears:
     ```
     +-------------------------------------------------------------------------+
     | [!] CANNOT CANCEL INVOICE                                              |
     | Active Customer Sales Return records exist against this invoice:        |
     | • Return #YSRET-202610-0004 (Dated 16/10/2026 - 200.000 Kg)            |
     |                                                                         |
     | You must first cancel all linked sales returns before this sales        |
     | invoice can be reversed.                                                |
     |                                                               [Close]   |
     +-------------------------------------------------------------------------+
     ```
3. **If No Returns Exist**:
   - The system displays a confirmation dialog requiring explicit typed confirmation:
     *"Type 'CANCEL' to reverse this invoice, restore 1,587.600 Kg to Central Godown, and reverse financial ledger vouchers."*

---

## 6. Atomic Reversal & Stock Restitution

When confirmed, calling `DELETE /api/v1/sales/yarn-sales/{id}/` executes [`YarnSalesService.cancel_sales`](file:///d:/Codebase/Garments/backend/apps/sales/services.py) inside `@transaction.atomic`:
1. **Verifies Invariant**: Asserts `sales.returns.filter(status=1).exists() == False`.
2. **Reverses Financial Voucher**: Locates voucher with `reference_type="SALES_INVOICE"` and `reference_no=invoice_number`. Calls [`CurrencyLedgerService.reverse_voucher`](file:///d:/Codebase/Garments/backend/apps/sales/services.py) to swap Debits and Credits atomically.
3. **Restores Godown Stock**: Calls [`YarnStockService.reverse_sales_stock`](file:///d:/Codebase/Garments/backend/apps/sales/services.py):
   $$\text{balance\_bag} \leftarrow \text{balance\_bag} + \text{sales.bag}$$
   $$\text{balance\_quantity} \leftarrow \text{balance\_quantity} + \text{sales.quantity}$$
4. **Soft Deletes Invoice**: Sets `status = 0`, updates `updated_by`, and soft-deletes child line items.

---

## 7. TypeScript Interfaces & Mutation Hook

```typescript
export interface CancelYarnSalesParams {
  id: number;
  reason: string;
}

export function useCancelYarnSales() {
  const queryClient = useQueryClient();
  const router = useRouter();

  return useMutation({
    mutationFn: async ({ id, reason }: CancelYarnSalesParams) => {
      const response = await apiClient.delete(`/api/v1/sales/yarn-sales/${id}/`, {
        data: { reason },
      });
      return response.data;
    },
    onSuccess: (_, { id }) => {
      toast.success(`Invoice YSAL-${id} has been cancelled and stock re-credited.`);
      queryClient.invalidateQueries({ queryKey: ["yarn-sales"] });
      queryClient.invalidateQueries({ queryKey: ["yarn-stock"] });
      router.push("/sales/yarn-sales");
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.error?.message || "Failed to cancel invoice.");
    },
  });
}
```

---

## 8. Developer Acceptance Criteria

- [ ] Route `/sales/yarn-sales/[id]/edit` accurately fetches and hydrates invoice data.
- [ ] Commercial line items, yarn counts, rates, and tax calculations are strictly read-only for posted invoices.
- [ ] Logistics metadata (Vehicle No, Transporter, E-Way Bill, Remarks) can be updated via `PATCH`.
- [ ] The `[CANCEL / REVERSE INVOICE]` button is disabled with tooltip if customer returns exist against the invoice.
- [ ] Invoice cancellation restores `balance_bag` and `balance_quantity` in `tm_yarn_stock` atomically.
- [ ] Invoice cancellation reverses the financial debtor voucher in `tl_voucher`.
