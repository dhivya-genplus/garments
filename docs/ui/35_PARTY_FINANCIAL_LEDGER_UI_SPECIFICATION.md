# Party Financial Ledger, Statements & Payment Reconciliation Specification

| Standard Code | Screen ID | Target Platform | API Version | Document Version | Date | Status |
|---|---|---|---|---|---|---|
| **STD-UI-001** | **`SCR-FINL-001`** | Next.js 14 (App Router) + TypeScript | `v1.2` (Django 5 DRF) | `v1.0.0` | 16/10/2026 | **APPROVED FOR IMPLEMENTATION** |

---

## 1. Document Overview, Version, Scope, and Status

### 1.1 Purpose
This specification defines the complete technical architecture, UI layout, double-entry financial statement logic, running balance computation, payment/receipt recording modals, Zod validation schema, TypeScript interfaces, and backend API integration for the **Party Financial Ledger & Reconciliation Desk** (`SCR-FINL-001`).

While the physical stock ledger (`SCR-INVN-004`) tracks kilograms and bag counts, the Party Financial Ledger is the authoritative double-entry currency ledger for all commercial partners (Spinning Mills, Dye Houses, Knitters, Commercial Customers, and Raw Material Vendors):
1. **Running Balance & Accounting Invariants**: Dynamic calculation of Debit (Dr) vs. Credit (Cr) transactions, starting from Master Opening Balance plus prior movements, arriving at mathematically verified period closing balances.
2. **Transaction Against Tracing**: Full lineage mapping every voucher line back to its source operational document:
   - Commercial Sales Tax Invoice (`INV-YYYY-XXXX`) $\rightarrow$ Debit Customer
   - Customer Sales Return Credit Note (`CRN-YYYY-XXXX`) $\rightarrow$ Credit Customer
   - Yarn Inward Purchase GRN (`GRN-YYYY-XXXX`) $\rightarrow$ Credit Mill / Trader
   - Bank Payment / NEFT / RTGS Voucher $\rightarrow$ Debit Supplier, Credit Bank
   - Bank Receipt / Customer Cheque $\rightarrow$ Debit Bank, Credit Customer
3. **One-Touch Payment & Receipt Recording**: Modal dialogs for recording bank transfers, cheques, RTGS/NEFT, and cash settlements with reference document allocation.
4. **Audit Trail & Immutable Reversals**: Posted vouchers cannot be edited or hard-deleted; corrections create explicit reversal vouchers (`is_reversed = True`, `reversed_by = ReversalVoucher`).

### 1.2 Scope
- **Backend Models**: [`tl_voucher`](file:///d:/Codebase/Garments/backend/apps/ledger/models.py) and [`tl_voucher_line`](file:///d:/Codebase/Garments/backend/apps/ledger/models.py).
- **Backend Service**: [`CurrencyLedgerService`](file:///d:/Codebase/Garments/backend/apps/ledger/services.py#L215-L450).
- **Country Pack**: India (`IN`) — Indian Rupee (`₹`), Indian numbering system (`12,34,567.89`), Date format (`DD/MM/YYYY`).
- **Target Route**: `/ledgers/party-ledger` (Next.js route: `app/(app)/ledgers/party-ledger/page.tsx`).

---

## 2. Module Details, Screen ID, Route, Access Privileges, and API Endpoints

### 2.1 Core Metadata

| Parameter | Specification |
|---|---|
| **Module** | `Module 8 — Ledgers & Financial Accounting` |
| **Screen ID** | `SCR-FINL-001` |
| **Frontend Route** | `/ledgers/party-ledger` |
| **File Location** | `app/(app)/ledgers/party-ledger/page.tsx` |
| **Required Privilege** | `ledger_financial.can_read` (View statements); `ledger_voucher.can_create` (Record payment/receipt); `ledger_voucher.can_reverse` (Reverse voucher); `ledger_financial.can_export` (Export PDF/Excel) |
| **Authorized Roles** | `SUPER_ADMIN`, `ADMIN_USER`, `COMPANY_USER` (Chief Accountant, Finance Manager, Accounts Executive) |
| **Country Pack** | `IN` (India: Currency INR `₹`, Date `DD/MM/YYYY`, Decimal precision: Money 2 dp `₹ 0.00`) |

### 2.2 Primary API Endpoints

| HTTP Method | API Path | Privilege / Scope | Description |
|---|---|---|---|
| `GET` | `/api/v1/ledger/vouchers/party-statement/` | `can_read` | Fetch full running financial ledger statement for a selected party with date range |
| `POST` | `/api/v1/ledger/vouchers/record-payment/` | `can_create` | Record an outgoing bank payment to a supplier / subcontractor |
| `POST` | `/api/v1/ledger/vouchers/record-receipt/` | `can_create` | Record an incoming customer payment receipt with bank allocation |
| `POST` | `/api/v1/ledger/vouchers/{id}/reverse/` | `can_reverse` | Execute an immutable double-entry reversal voucher |
| `GET` | `/api/v1/ledger/vouchers/{id}/` | `can_read` | Retrieve full multi-line double-entry voucher details |

---

## 3. UI Layout, Screen Blueprint, and Visual Mockup (1440px+ Wireframe)

```
+-----------------------------------------------------------------------------------------------------------------------------+
| GARMENTS ERP — Party Financial Statement & Reconciliation Desk               Company: ABC Textiles Ltd | FY: 2026-2027      |
+-----------------------------------------------------------------------------------------------------------------------------+
| TOP CONTROLS & PARTY SELECTION:                                                                                             |
| Party (Account): [ Vardhman Spinning Mills Ltd (MILL) - GSTIN: 03AAAAA1234A1Z5                                      | v ] |
| Date From: [ 01/04/2026 ]  Date To: [ 16/10/2026 ]  Voucher Type: [ All Types (INV, GRN, PAY, REC, JV) | v ]  Ref #: [     ]|
| [ Apply Filters (F3) ]  [ Clear ]       [+ Record Payment (Alt+P)]  [+ Record Receipt (Alt+R)]  [Export XLSX] [Print Statement] |
+-----------------------------------------------------------------------------------------------------------------------------+
| FINANCIAL SUMMARY BANNER:                                                                                                   |
| [ OPENING BALANCE ]         [ TOTAL DEBIT (DR) ]        [ TOTAL CREDIT (CR) ]        [ CLOSING BALANCE (NET) ]              |
|   ₹ 4,50,000.00 Cr            ₹ 12,40,000.00              ₹ 18,25,000.00               ₹ 10,35,000.00 Cr (Payable)           |
|   As on 01/04/2026            (Payments & Returns)        (Invoices & Inwards)         Credit Limit: ₹ 25,00,000.00 (Safe)   |
+-----------------------------------------------------------------------------------------------------------------------------+
| STATEMENT OF ACCOUNTS LEDGER TABLE:                                                                                         |
| # | Date       | Voucher #     | Type | Transaction Against       | Narration                     | Debit (₹)   | Credit (₹)  | Balance (₹)    | Action|
|---|------------|---------------|------|---------------------------|-------------------------------|-------------|-------------|----------------|-------|
| 1 | 01/04/2026 | --            | OB   | Master Opening Balance    | Opening Balance FY 2026-27    |        0.00 |        0.00 | 4,50,000.00 Cr |       |
| 2 | 14/04/2026 | GRN-2026-0012 | GRN  | Yarn Inward #GRN-0012     | 30s Combed Cotton 4,800 Kg    |        0.00 |15,36,000.00 |19,86,000.00 Cr | [View]|
| 3 | 28/04/2026 | PV-2026-0004  | PAY  | Against GRN #GRN-0012     | HDFC Bank NEFT #N1029384      |10,000.00.00 |        0.00 | 9,86,000.00 Cr | [Rev] |
| 4 | 15/05/2026 | GRN-2026-0045 | GRN  | Yarn Inward #GRN-0045     | 40s Combed Cotton 1,000 Kg    |        0.00 | 2,89,000.00 |12,75,000.00 Cr | [View]|
| 5 | 10/06/2026 | PV-2026-0019  | PAY  | Against GRN #GRN-0045     | ICICI Bank Cheque #492019     | 2,40,000.00 |        0.00 |10,35,000.00 Cr | [Rev] |
|---|------------|---------------|------|---------------------------|-------------------------------|-------------|-------------|----------------|-------|
|   | PERIOD TOTALS              |      | 4 Transactions recorded   |                               |12,40,000.00 |18,25,000.00 |10,35,000.00 Cr |       |
+-----------------------------------------------------------------------------------------------------------------------------+
| AUDIT FOOTER: Statement generated on 16/10/2026 17:30 by arun.kumar | Invariant Verified: Σ(Dr) - Σ(Cr) = Net Balance Change  |
| SHORTCUTS: [Alt+P: Record Payment]  [Alt+R: Record Receipt]  [Alt+F: Focus Party]  [Ctrl+P: Print Statement] [Esc: Back]   |
+-----------------------------------------------------------------------------------------------------------------------------+
```

---

## 4. UX Workflow, Step-by-Step Lifecycle, and Edge-Case Handling

### 4.1 Step-by-Step Lifecycle
1. **Party Statement Inquiries**:
   - Accountant selects Party from searchable autocomplete.
   - Sets date range (defaults to current Financial Year: `01/04/YYYY` to Current Date).
   - System fetches statement via `/api/v1/ledger/vouchers/party-statement/`.
   - Computes Opening Balance, line-by-line running balances, and Closing Balance.
2. **Recording Payment (Outgoing to Supplier/Knitter)**:
   - Click **Record Payment (Alt+P)**.
   - Populates Party, Payment Date, Amount ($₹$), Payment Mode (Bank NEFT, RTGS, Cheque, Cash).
   - Selects specific against-document (e.g. against Inward GRN or Knitting Bill).
   - Selects Bank Account from Chart of Accounts.
   - Upon submission, backend creates a balanced two-line voucher:
     $$\text{Debit Party Account} \quad \text{and} \quad \text{Credit Bank/Cash Account}$$
3. **Recording Receipt (Incoming from Customer)**:
   - Click **Record Receipt (Alt+R)**.
   - Populates Customer, Receipt Date, Amount ($₹$), Cheque/UTR reference.
   - Upon submission, backend creates:
     $$\text{Debit Bank Account} \quad \text{and} \quad \text{Credit Customer Account}$$
4. **Double-Entry Reversal**:
   - If an incorrect payment entry was posted, authorized user clicks **[Reverse]**.
   - System prompts for Reversal Date and Narration.
   - An exact contra voucher is generated atomically, and original voucher is marked `is_reversed = True`.

### 4.2 Edge-Case Handling
- **Opening Balance Temporal Alignment**: If user changes `from_date` from `01/04/2026` to `01/06/2026`, backend automatically computes all transactions between `01/04/2026` and `31/05/2026` and rolls them into the dynamic Opening Balance.
- **Double-Entry Ledger Imbalance Prevention**: Vouchers that do not satisfy $\sum \text{Debit} = \sum \text{Credit}$ are rejected at the database level with `LedgerImbalanceError`.

---

## 5. Form Sections, Field Matrix, and Validation Rules

| Section | Field Label | Field Key | Input Type | Required | Default | Validation & Rules |
|---|---|---|---|---|---|---|
| **Filter** | Select Party | `party_id` | Searchable Select | Yes | None | Active `PartyMaster` |
| **Filter** | From Date | `from_date` | DatePicker | No | FY Start Date | `DD/MM/YYYY` |
| **Filter** | To Date | `to_date` | DatePicker | No | Current Date | `DD/MM/YYYY`, must be $\ge$ `from_date` |
| **Filter** | Voucher Type | `voucher_type` | Select | No | All | `SALES`, `PURCHASE`, `PAYMENT`, `RECEIPT`, `JOURNAL` |
| **Payment** | Payment Date | `payment_date` | DatePicker | Yes | Current Date | `DD/MM/YYYY` in active FY |
| **Payment** | Amount (INR) | `amount` | Number (2 dp) | Yes | `0.00` | Must be $> 0.00$ |
| **Payment** | Payment Mode | `payment_mode` | Select | Yes | `BANK_NEFT` | `BANK_NEFT`, `RTGS`, `CHEQUE`, `CASH` |
| **Payment** | Reference / UTR # | `reference_no` | Text | Yes | None | e.g. UTR or Cheque number |
| **Payment** | Against Doc Type | `against_doc_type` | Select | No | None | `INWARD_GRN`, `KNITTING_BILL`, `ON_ACCOUNT` |
| **Payment** | Against Doc # | `against_doc_number` | Text | No | None | Document reference |
| **Payment** | Bank Account | `bank_account_name` | Select | Yes | Main Bank | Active Chart of Accounts asset |
| **Payment** | Narration | `narration` | Text | No | None | Max 255 chars |

---

## 6. Mathematical Formulas and Calculation Specifications (LaTeX)

### 6.1 Dynamic Opening Balance Formula
Given base master opening balance $B_{\text{master}}$ and user filter start date $D_{\text{from}}$:

$$B_{\text{open}}(D_{\text{from}}) = B_{\text{master}} + \sum_{t < D_{\text{from}}} (\text{Debit}_t - \text{Credit}_t)$$

### 6.2 Running Balance & Closing Balance
For each transaction line $k \in \{1, \dots, m\}$:

$$\text{Running Balance}_k = B_{\text{open}} + \sum_{j=1}^{k} (\text{Debit}_j - \text{Credit}_j)$$

$$\text{Closing Balance} = \text{Running Balance}_m = B_{\text{open}} + \sum_{j=1}^{m} \text{Debit}_j - \sum_{j=1}^{m} \text{Credit}_j$$

### 6.3 Accounting Balance Direction Indicator
$$\text{Balance Display} = \begin{cases} 
|\text{Closing Balance}| \text{ Dr (Receivable)}, & \text{if } \text{Closing Balance} > 0 \\ 
|\text{Closing Balance}| \text{ Cr (Payable)}, & \text{if } \text{Closing Balance} < 0 \\ 
\text{₹ 0.00 (Settled)}, & \text{if } \text{Closing Balance} = 0 
\end{cases}$$

---

## 7. Dynamic Behaviors, Conditional Fields, and Interactivity

1. **Party Type Aware Balance Color**:
   - For Customers (`CUSTOMER`): Debit balance is colored **Neutral/Blue** (Asset / Receivable); Credit balance is colored **Amber** (Advance Received).
   - For Suppliers/Mills (`MILL`, `TRADER`): Credit balance is colored **Neutral/Blue** (Liability / Payable); Debit balance is colored **Amber** (Advance Paid).
2. **One-Click Contra Reversal**:
   - Clicking **[Reverse]** on any posted payment opens a confirmation modal displaying the contra debit/credit legs before execution.
3. **Instant PDF Statement Export**:
   - Clicking **[Print Statement (Ctrl+P)]** renders a formal, auditor-ready Statement of Accounts with company header, GSTIN, PAN, and bank reconciliation columns.

---

## 8. API Request / Response Contracts (DTOs)

### 8.1 Fetch Party Ledger Statement (`GET /api/v1/ledger/vouchers/party-statement/?party_id=1&from_date=01/04/2026`)

```json
{
  "success": true,
  "data": {
    "party": {
      "id": 1,
      "code": "P-0001",
      "name": "Vardhman Spinning Mills Ltd",
      "party_type": "MILL",
      "party_type_display": "Spinning Mill",
      "gstin": "03AAAAA1234A1Z5",
      "pan_number": "AAAAA1234A"
    },
    "date_range": {
      "from_date": "01/04/2026",
      "to_date": "16/10/2026"
    },
    "opening_balance": "-450000.00",
    "opening_balance_display": "₹ 4,50,000.00 Cr",
    "total_debit": "1240000.00",
    "total_credit": "1825000.00",
    "closing_balance": "-1035000.00",
    "closing_balance_display": "₹ 10,35,000.00 Cr",
    "statement_lines": [
      {
        "id": 101,
        "date": "14/04/2026",
        "voucher_number": "GRN-2026-0012",
        "voucher_type": "GRN",
        "reference_no": "INV-VM-8841",
        "transaction_against": "Yarn Inward #GRN-0012",
        "narration": "30s Combed Cotton 4,800 Kg",
        "debit": "0.00",
        "credit": "1536000.00",
        "running_balance": "-1986000.00",
        "running_balance_display": "₹ 19,86,000.00 Cr"
      },
      {
        "id": 102,
        "date": "28/04/2026",
        "voucher_number": "PV-2026-0004",
        "voucher_type": "PAYMENT",
        "reference_no": "NEFT-N1029384",
        "transaction_against": "Against GRN #GRN-0012",
        "narration": "HDFC Bank NEFT #N1029384",
        "debit": "1000000.00",
        "credit": "0.00",
        "running_balance": "-986000.00",
        "running_balance_display": "₹ 9,86,000.00 Cr"
      }
    ]
  }
}
```

---

## 9. Client-Side State Management and Component Architecture

```
app/(app)/ledgers/party-ledger/
├── page.tsx                             # Master container managing party selection and statement
└── components/
    ├── PartyStatementHeaderCards.tsx    # Opening, Dr, Cr, and Closing balance KPI cards
    ├── PartyStatementFilterBar.tsx      # Date range and voucher type filter controls
    ├── PartyStatementTable.tsx          # Running double-entry ledger table
    ├── RecordPaymentModal.tsx           # Outgoing payment dialog
    ├── RecordReceiptModal.tsx           # Incoming receipt dialog
    └── VoucherReversalModal.tsx         # Double-entry contra reversal confirmation
```

---

## 10. Zod Validation Schema (Copy-Paste Production Code)

```typescript
import { z } from "zod";

const dateRegex = /^(0[1-9]|[12][0-9]|3[01])\/(0[1-9]|1[0-2])\/\d{4}$/;

export const RecordPaymentSchema = z.object({
  party_id: z.number().int().positive({ message: "Party is required." }),
  payment_date: z.string().regex(dateRegex, { message: "Date must be DD/MM/YYYY" }),
  amount: z.number().min(0.01, { message: "Payment amount must be greater than zero." }),
  payment_mode: z.enum(["BANK_NEFT", "RTGS", "CHEQUE", "CASH"], {
    errorMap: () => ({ message: "Select a valid payment mode." }),
  }),
  reference_no: z.string().min(1, { message: "Cheque / UTR reference number is required." }),
  against_doc_type: z.string().optional(),
  against_doc_number: z.string().optional(),
  bank_account_name: z.string().min(1, { message: "Bank account is required." }),
  narration: z.string().max(255).optional(),
});

export const RecordReceiptSchema = z.object({
  party_id: z.number().int().positive({ message: "Customer is required." }),
  receipt_date: z.string().regex(dateRegex, { message: "Date must be DD/MM/YYYY" }),
  amount: z.number().min(0.01, { message: "Receipt amount must be greater than zero." }),
  payment_mode: z.enum(["BANK_NEFT", "RTGS", "CHEQUE", "CASH"], {
    errorMap: () => ({ message: "Select a valid payment mode." }),
  }),
  reference_no: z.string().min(1, { message: "Cheque / UTR reference is required." }),
  against_doc_type: z.string().optional(),
  against_doc_number: z.string().optional(),
  bank_account_name: z.string().min(1, { message: "Deposit bank account is required." }),
  narration: z.string().max(255).optional(),
});

export type RecordPaymentFormData = z.infer<typeof RecordPaymentSchema>;
export type RecordReceiptFormData = z.infer<typeof RecordReceiptSchema>;
```

---

## 11. TypeScript Interfaces & Enums (Complete DTO Declarations)

```typescript
export interface IPartyStatementLineDTO {
  id: number;
  date: string;
  voucher_number: string;
  voucher_type: string;
  reference_no?: string;
  transaction_against?: string;
  narration?: string;
  debit: number;
  credit: number;
  running_balance: number;
  running_balance_display: string;
}

export interface IPartyStatementDTO {
  party: {
    id: number;
    code: string;
    name: string;
    party_type: string;
    party_type_display: string;
    gstin?: string;
    pan_number?: string;
  };
  date_range: {
    from_date: string;
    to_date: string;
  };
  opening_balance: number;
  opening_balance_display: string;
  total_debit: number;
  total_credit: number;
  closing_balance: number;
  closing_balance_display: string;
  statement_lines: IPartyStatementLineDTO[];
}
```

---

## 12. Keyboard Shortcuts and Rapid Operations

| Key Combination | Action / Trigger | Scope / View |
|---|---|---|
| `Alt + P` | Open Record Payment Modal | Party Statement View |
| `Alt + R` | Open Record Receipt Modal | Party Statement View |
| `Alt + F` | Focus Party Autocomplete Field | Party Statement View |
| `Ctrl + P` | Print Statement of Accounts PDF | Party Statement View |
| `Esc` | Close Active Modal / Reset Search | Any Modal |

---

## 13. Responsive Breakpoints and Mobile Adaptation

| Viewport Width | Screen Category | Layout Behavior |
|---|---|---|
| $\ge 1440\text{px}$ | Desktop Enterprise | 4 KPI summary cards, full width Statement table with inline audit links |
| $1024\text{px} - 1439\text{px}$ | Laptop / Tablet Landscape | 2x2 grid KPI cards, horizontal scroll on Dr/Cr columns |
| $\le 1023\text{px}$ | Tablet Portrait / Mobile | Collapsible card statement entries with Dr/Cr badges |

---

## 14. Error Handling and User Feedback

| Scenario / Error Trigger | Visual Presentation | Remediation Action |
|---|---|---|
| Unbalanced voucher attempt | Modal error: *"Ledger Imbalance: Total Debits must equal Total Credits"* | Check bank and party allocations |
| Negative amount input | Red field border on `amount` input | Amount must be positive |
| Date outside active FY | Validation error under date input | Date must fall within active FY |

---

## 15. Loading, Empty, and Edge States

- **Loading State**: Table shimmer placeholders with pulse effect on KPI summary cards.
- **Empty State**: Document icon with message: *"Select a party above to view their financial ledger statement."*
- **Nil Balance State**: Green badge: *"ACCOUNT FULLY RECONCILED (₹ 0.00 BALANCE)"*.

---

## 16. Accessibility (a11y) Conformance (WCAG 2.1 AA)

- Tables use `<caption className="sr-only">Party Statement of Accounts</caption>`.
- Distinct color coding supported by text suffixes: "Dr (Receivable)" and "Cr (Payable)".
- Full keyboard trap management within Record Payment / Receipt modals.

---

## 17. Security, RBAC, and Audit Logging

- **Role Gate**: Only users with `ledger_voucher.can_create` can record payments.
- **Multi-Tenancy**: Enforced at database and service layer via `company_id`.
- **Immutable Vouchers**: Hard deletions are forbidden; all adjustments require contra reversal vouchers.

---

## 18. Test Cases and Acceptance Criteria

### 18.1 Acceptance Criteria
1. Given Opening Balance ₹ 4,50,000.00 Cr, Credit entry of ₹ 15,36,000.00, and Debit payment of ₹ 10,000.00.00, running closing balance must equal ₹ 9,86,000.00 Cr.
2. Posting a payment creates a balanced voucher with equal debit and credit legs.
3. Reversing a voucher creates contra legs and marks original voucher as reversed.

---

## 19. Performance Budgets and Optimization Targets

- Statement generation time: $< 250\text{ms}$ for parties with up to 2,000 historical vouchers.
- Autocomplete search response: $< 100\text{ms}$.

---

## 20. Future Enhancements and Scalability Roadmap

1. **Automated Bank Statement (MT940/CSV) Reconciliation**: Matching bank debits/credits automatically against ERP vouchers.
2. **Automated WhatsApp Statement Dispatch**: Sending PDF statements directly to party accounts contact.

---

## 21. Sign-off and Approval Matrix

| Stakeholder Role | Name / Title | Date | Signature / Status |
|---|---|---|---|
| **Chief Financial Officer** | Krishnan Venkatachalam (CFO) | 16/10/2026 | **APPROVED** |
| **Lead Architect** | Enterprise Garments Solutions | 16/10/2026 | **APPROVED** |
| **Audit Lead** | Sivakumar & Co. (Chartered Accountants)| 16/10/2026 | **APPROVED** |
