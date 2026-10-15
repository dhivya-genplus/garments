# Yarn Sales Return (GST Credit Note) Print Document Specification

| Standard Code | Screen ID | Target Platform | API Version | Document Version | Date | Status |
|---|---|---|---|---|---|---|
| **STD-UI-001** | **`SCR-SALE-002-PRINT`** | Next.js 14 (App Router) + TypeScript | `v1.2` (Django 5 DRF) | `v1.0.0` | 15/10/2026 | **APPROVED FOR IMPLEMENTATION** |

---

## 1. Document Overview, Version, Scope, and Status

### 1.1 Purpose
This specification defines the printable document architecture, CSS `@media print` rules, statutory Indian GST compliance parameters, original invoice references, HSN tax reversal schedules, and signatory authorization requirements for the **Yarn Sales Return GST Credit Note Print Document** (`SCR-SALE-002-PRINT`).

This document fulfills the statutory mandates of **Section 34 of the Central Goods and Services Tax (CGST) Act, 2017** and **Rule 53 of the CGST Rules (Revised Tax Invoice and Credit or Debit Notes)** for sales returns, post-sale discounts, or deficiency in goods supplied.

### 1.2 Scope
- **Route**: `/sales/yarn-sales-returns/[id]/print`
- **Entity**: [`parent_yarn_sales_return_table`](file:///d:/Codebase/Garments/backend/apps/sales/models.py) (`tm_yarn_sales_return`) and child lines [`child_yarn_sales_return_table`](file:///d:/Codebase/Garments/backend/apps/sales/models.py) (`tx_yarn_sales_return`).
- **Standard**: ISO A4 Portrait (`210mm x 297mm`), high-contrast monochrome printing, zero page overflows.
- **Copy Options**: Toggleable for **Original for Recipient**, **Duplicate for Transporter**, and **Triplicate for Supplier**.

---

## 2. Module Details, Screen ID, Route, and Access Privileges

### 2.1 Core Metadata

| Parameter | Specification |
|---|---|
| **Module** | `Module 5 — Commercial Sales & Customer Returns` |
| **Screen ID** | `SCR-SALE-002-PRINT` |
| **Frontend Route** | `/sales/yarn-sales-returns/[id]/print` |
| **File Location** | `app/(app)/sales/yarn-sales-returns/[id]/print/page.tsx` |
| **Required Privilege** | `sales_yarn_return.can_print` |
| **Authorized Roles** | `SUPER_ADMIN`, `ADMIN_USER`, `COMPANY_USER` (Sales, Accounts, Dispatch, Billing Clerk) |
| **Country Pack** | `IN` (India: GST Invariants, Currency `₹`, Date `DD/MM/YYYY`) |

---

## 3. UI Layout & Print Blueprint (ISO A4 Portrait Wireframe)

```
+-------------------------------------------------------------------------------------------------------------------+
| [<- Back to Return]    CREDIT NOTE PRINT PREVIEW        [ Copy: [ Original for Recipient v ] ]   [ PRINT DOCUMENT]|
+===================================================================================================================+
|                                                    CREDIT NOTE                                                    |
|                                    (Issued under Section 34 of the CGST Act, 2017)                                |
|                                             [ ORIGINAL FOR RECIPIENT ]                                            |
|-------------------------------------------------------------------------------------------------------------------|
| ABC TEXTILES PRIVATE LIMITED                                                                                      |
| Regd Office: 120, Avinashi Road, Civil Aerodrome Post, Tirupur - 641 614, Tamil Nadu, India                       |
| Receiving Godown: Central Godown, SF #142, Angeripalayam Main Road, Tirupur - 641 602                             |
| GSTIN: 33AAAAA1234A1Z5 | PAN: AAAAA1234A | CIN: U17111TZ2020PTC012345 | State: Tamil Nadu (Code: 33)              |
| Email: accounts@abctextiles.com | Web: www.abctextiles.com | Tel: +91 421 2233445                                |
|-------------------------------------------------------------------------------------------------------------------|
| CREDIT NOTE DETAILS:                                        | ORIGINAL TAX INVOICE REFERENCE:                     |
| Credit Note No:   YSRET-202610-0005                         | Original Invoice No:   YSAL-202610-0018             |
| Credit Note Date: 15/10/2026                                | Original Invoice Date: 15/10/2026                   |
| Place of Supply:  33 - Tamil Nadu                           | Customer Debit Note:   DN-PK-2026-902 dt. 14/10/2026|
| Nature of Note:   Sales Return / Goods Rejection            | Reason for Return:     Shade Variation              |
|-------------------------------------------------------------+-----------------------------------------------------|
| DETAILS OF RECIPIENT (CREDITED TO):                                                                               |
| Customer Name: PREMIER KNITTINGS PVT LTD                                                                          |
| Address:       45, Shed #3, SIDCO Industrial Estate, Mulanur Road, Tirupur - 641 606, Tamil Nadu, India           |
| GSTIN:         33BBBBB5678B1Z2 | State: Tamil Nadu (State Code: 33)                                               |
|-------------------------------------------------------------------------------------------------------------------|
| PARTICULARS OF RETURNED GOODS:                                                                                    |
| S.# | Description of Goods (Yarn / Count / Mill / Shade / Lot) | HSN    | Bags | Kg/Bag | Net Wt (Kg) | Rate (₹) | Amount (₹)  |
|-----+----------------------------------------------------------+--------+------+--------+------------+----------+-------------|
|  1  | 100% Cotton Grey Yarn - 30s Karded                       | 5205   |    5 | 45.360 |    226.800 |   340.00 |   77,112.00 |
|     | Spinning Mill: Ramco Mills Ltd | Lot #RM-901             |        |      |        |            |          |             |
|     | Defect Note: 5 bags rejected due to uneven dye test      |        |      |        |            |          |             |
|-----+----------------------------------------------------------+--------+------+--------+------------+----------+-------------|
|     | TOTAL GOODS ACCEPTED:                                    |        |    5 |        |    226.800 |          |  ₹77,112.00 |
|-------------------------------------------------------------------------------------------------------------------|
| GST TAX REVERSAL SCHEDULE:                                                                                        |
| HSN/SAC | Taxable Value (₹) | CGST Rate | CGST Amount (₹) | SGST Rate | SGST Amount (₹) | IGST Rate | IGST Amount (₹) | Total Tax (₹) |
|---------+-------------------+-----------+-----------------+-----------+-----------------+-----------+-----------------+---------------|
| 5205    |        77,112.00  |   2.50%   |        1,927.80 |   2.50%   |        1,927.80 |   0.00%   |            0.00 |      3,855.60 |
| Total   |        77,112.00  |           |        1,927.80 |           |        1,927.80 |           |            0.00 |      3,855.60 |
|-------------------------------------------------------------------------------------------------------------------|
| CREDIT SETTLEMENT SUMMARY:                                                                                        |
| Total Taxable Value of Returned Goods:                                                                 ₹77,112.00 |
| Add: Central GST (CGST) Reversal:                                                                       ₹1,927.80 |
| Add: State GST (SGST) Reversal:                                                                         ₹1,927.80 |
| Add: Integrated GST (IGST) Reversal:                                                                        ₹0.00 |
| Round-Off Adjustment:                                                                                      +₹0.40 |
| TOTAL CREDIT VALUE GRANTED:                                                                            ₹80,968.00 |
|-------------------------------------------------------------------------------------------------------------------|
| AMOUNT IN WORDS:                                                                                                  |
| Indian Rupees Eighty Thousand Nine Hundred and Sixty-Eight Only                                                   |
|-------------------------------------------------------------------------------------------------------------------|
| STATUTORY DECLARATION:                                      | SIGNATORIES:                                        |
| We declare that this Credit Note is issued against the      |                                                     |
| original tax invoice referenced above in compliance with    | For ABC TEXTILES PRIVATE LIMITED                    |
| Section 34 of the CGST Act, 2017, and output tax liability  |                                                     |
| has been adjusted accordingly.                              |                                                     |
|                                                             | [Authorized Signatory / Seal]                       |
| Customer Acknowledgement: ________________________________  | Prepared By: M. Kumar       Verified By: S. Nathan  |
+===================================================================================================================+
```

---

## 4. Statutory Rule 53 Compliance Checklist

| Mandatory Rule 53 Field | Implementation Details |
|---|---|
| **Document Type** | Explicitly marked as **"CREDIT NOTE"** with copy markings ("ORIGINAL FOR RECIPIENT"). |
| **Supplier Metadata** | Registered company name, dispatch/receiving godown address, GSTIN, PAN, and State Code. |
| **Consecutive Serial Number**| Consecutive alphanumeric number unique for the FY (`YSRET-YYYYMM-XXXX`). |
| **Credit Note Date** | Calendar date in `DD/MM/YYYY` format (`15/10/2026`). |
| **Recipient Details** | Customer name, registered address, GSTIN, and State Code. |
| **Original Invoice Linkage**| Number (`YSAL-202610-0018`) and Date (`15/10/2026`) of the corresponding Tax Invoice. |
| **Reason for Issuance** | Stated under statutory terms (e.g. `Shade Variation`, `Defective Count`). |
| **Quantitative Measures**| Bags returned, per-bag tare (`45.360 Kg`), and net weight in kilograms (`Kg`). |
| **Tax Breakup** | Explicit schedule detailing Taxable Value, CGST Reversal, SGST Reversal, and IGST Reversal. |
| **Net Amount in Words** | Clean Indian English text ("Rupees ... Only"). |
| **Signatures** | Authorized signatory of supplier and space for customer receipt acknowledgement. |

---

## 5. CSS Print Stylesheet (`@media print`)

```css
@media print {
  @page {
    size: A4 portrait;
    margin: 8mm 10mm 8mm 10mm;
  }

  body {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    color: #000;
    background: #fff;
    -webkit-print-color-adjust: exact;
    print-color-adjust: exact;
    font-size: 9.5pt;
    line-height: 1.25;
  }

  .no-print {
    display: none !important;
  }

  .print-container {
    width: 100%;
    max-width: 190mm;
    margin: 0 auto;
    border: 1.5pt solid #000;
  }

  .table-grid {
    width: 100%;
    border-collapse: collapse;
  }

  .table-grid th, .table-grid td {
    border: 0.5pt solid #000;
    padding: 3pt 5pt;
  }

  .table-grid th {
    background-color: #f1f5f9 !important;
    font-weight: 700;
    text-transform: uppercase;
    font-size: 8pt;
  }

  .page-break-avoid {
    break-inside: avoid;
    page-break-inside: avoid;
  }
}
```

---

## 6. Developer Acceptance Criteria

- [ ] Route `/sales/yarn-sales-returns/[id]/print` fetches complete return header, original invoice reference, and line items.
- [ ] Top bar allows toggling between **Original for Recipient**, **Duplicate for Transporter**, and **Triplicate for Supplier**.
- [ ] Document fits perfectly on a single ISO A4 page for up to 6 return lines.
- [ ] HSN tax schedule accurately calculates and displays tax credit reversals (CGST/SGST/IGST).
- [ ] Number-to-words utility generates accurate Indian currency text (`Rupees Eighty Thousand Nine Hundred and Sixty-Eight Only`).
- [ ] Statutory Section 34 legal declaration and signatory blocks print cleanly.
