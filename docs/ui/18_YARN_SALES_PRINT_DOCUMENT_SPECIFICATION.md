# Yarn Sales Commercial Tax Invoice Print Document Specification

| Standard Code | Screen ID | Target Platform | API Version | Document Version | Date | Status |
|---|---|---|---|---|---|---|
| **STD-UI-001** | **`SCR-SALE-001-PRINT`** | Next.js 14 (App Router) + TypeScript | `v1.2` (Django 5 DRF) | `v1.0.0` | 15/10/2026 | **APPROVED FOR IMPLEMENTATION** |

---

## 1. Document Overview, Version, Scope, and Status

### 1.1 Purpose
This specification defines the exact layout, CSS `@media print` rules, statutory Indian GST compliance parameters, dual-party billing/shipping blocks, HSN tax breakdown tables, and bank remittance details for the **Yarn Sales Commercial Tax Invoice Print Document** (`SCR-SALE-001-PRINT`).

This document fulfills the statutory mandates of **Section 31 of the Central Goods and Services Tax (CGST) Act, 2017** and **Rule 46 of the CGST Rules (Tax Invoice)** for taxable supply of textile yarn products.

### 1.2 Scope
- **Route**: `/sales/yarn-sales/[id]/print`
- **Entity**: [`parent_yarn_sales_table`](file:///d:/Codebase/Garments/backend/apps/sales/models.py) (`tm_yarn_sales`) with lines [`child_yarn_sales_table`](file:///d:/Codebase/Garments/backend/apps/sales/models.py) (`tx_yarn_sales`).
- **Standard**: ISO A4 Portrait (`210mm x 297mm`), high-contrast monochrome printing, zero page overflows.
- **Copy Options**: Toggleable for **Original for Recipient**, **Duplicate for Transporter**, and **Triplicate for Supplier**.

---

## 2. Module Details, Screen ID, Route, and Access Privileges

### 2.1 Core Metadata

| Parameter | Specification |
|---|---|
| **Module** | `Module 5 — Commercial Sales & Customer Returns` |
| **Screen ID** | `SCR-SALE-001-PRINT` |
| **Frontend Route** | `/sales/yarn-sales/[id]/print` |
| **File Location** | `app/(app)/sales/yarn-sales/[id]/print/page.tsx` |
| **Required Privilege** | `sales_yarn.can_print` |
| **Authorized Roles** | `SUPER_ADMIN`, `ADMIN_USER`, `COMPANY_USER` (Sales, Accounts, Dispatch, Billing Clerk) |
| **Country Pack** | `IN` (India: GST Invariants, Currency `₹`, Date `DD/MM/YYYY`) |

---

## 3. UI Layout & Print Blueprint (ISO A4 Portrait Wireframe)

```
+-------------------------------------------------------------------------------------------------------------------+
| [<- Back to Invoice]   TAX INVOICE PRINT PREVIEW        [ Copy: [ Original for Recipient v ] ]  [ PRINT INVOICE ] |
+===================================================================================================================+
|                                                   TAX INVOICE                                                     |
|                                     (Issued under Rule 46 of the CGST Rules, 2017)                                |
|                                             [ ORIGINAL FOR RECIPIENT ]                                            |
|-------------------------------------------------------------------------------------------------------------------|
| ABC TEXTILES PRIVATE LIMITED                                                                                      |
| Regd Office: 120, Avinashi Road, Civil Aerodrome Post, Tirupur - 641 614, Tamil Nadu, India                       |
| Dispatch Godown: Central Godown, SF #142, Angeripalayam Main Road, Tirupur - 641 602                              |
| GSTIN: 33AAAAA1234A1Z5 | PAN: AAAAA1234A | CIN: U17111TZ2020PTC012345 | State: Tamil Nadu (Code: 33)              |
| Email: sales@abctextiles.com | Web: www.abctextiles.com | Tel: +91 421 2233445                                   |
|-------------------------------------------------------------------------------------------------------------------|
| INVOICE DETAILS:                                            | TRANSPORT & LOGISTICS:                              |
| Invoice No:     YSAL-202610-0018                            | Transporter:    VRL Logistics Ltd                   |
| Invoice Date:   15/10/2026                                  | Vehicle No:     TN-38-BZ-4412                       |
| Place of Supply:33 - Tamil Nadu                             | E-Way Bill No:  2410 9812 7654                      |
| Reverse Charge: No                                          | LR / RR No:     LR-990184 dt. 15/10/2026            |
| Payment Terms:  30 Days Credit (Due: 14/11/2026)            | Delivery Terms: Ex-Godown Tirupur                   |
|-------------------------------------------------------------+-----------------------------------------------------|
| DETAILS OF RECEIVER (BILLED TO):                            | DETAILS OF CONSIGNEE (SHIPPED TO):                  |
| Party Name: PREMIER KNITTINGS PVT LTD                       | Party Name: PREMIER KNITTINGS PVT LTD (Unit 2)      |
| Address:    45, Shed #3, SIDCO Industrial Estate,           | Address:    SF #88, Knitting Cluster, Mangalam Road,|
|             Mulanur Road, Tirupur - 641 606, Tamil Nadu     |             Tirupur - 641 687, Tamil Nadu           |
| GSTIN:      33BBBBB5678B1Z2                                 | GSTIN:      33BBBBB5678B1Z2                         |
| State:      Tamil Nadu (State Code: 33)                     | State:      Tamil Nadu (State Code: 33)             |
|-------------------------------------------------------------------------------------------------------------------|
| ITEM PARTICULARS:                                                                                                 |
| S.# | Description of Goods (Yarn / Count / Mill / Shade / Lot) | HSN    | Bags | Kg/Bag | Net Wt (Kg) | Rate (₹) | Amount (₹)  |
|-----+----------------------------------------------------------+--------+------+--------+------------+----------+-------------|
|  1  | 100% Cotton Grey Yarn - 30s Karded                       | 5205   |   20 | 45.360 |    907.200 |   340.00 | 3,08,448.00 |
|     | Spinning Mill: Ramco Mills Ltd | Lot #RM-901             |        |      |        |            |          |             |
|  2  | 100% Cotton Grey Yarn - 40s Combed                       | 5205   |   15 | 45.360 |    680.400 |   375.00 | 2,55,150.00 |
|     | Spinning Mill: Loyal Textile Mills | Lot #LT-440         |        |      |        |            |          |             |
|-----+----------------------------------------------------------+--------+------+--------+------------+----------+-------------|
|     | TOTAL CONSIGNMENT:                                       |        |   35 |        |  1,587.600 |          |₹5,63,598.00 |
|-------------------------------------------------------------------------------------------------------------------|
| HSN/SAC TAX BREAKUP SCHEDULE:                                                                                     |
| HSN/SAC | Taxable Value (₹) | CGST Rate | CGST Amount (₹) | SGST Rate | SGST Amount (₹) | IGST Rate | IGST Amount (₹) | Total Tax (₹) |
|---------+-------------------+-----------+-----------------+-----------+-----------------+-----------+-----------------+---------------|
| 5205    |      5,63,598.00  |   2.50%   |       14,089.95 |   2.50%   |       14,089.95 |   0.00%   |            0.00 |     28,179.90 |
| Total   |      5,63,598.00  |           |       14,089.95 |           |       14,089.95 |           |            0.00 |     28,179.90 |
|-------------------------------------------------------------------------------------------------------------------|
| INVOICE SUMMARY & SETTLEMENT:                               | REMITTANCE BANK DETAILS:                            |
| Taxable Value:                     ₹5,63,598.00             | Bank Name:      HDFC Bank Limited                   |
| Add: Central GST (CGST):             ₹14,089.95             | Branch:         Tirupur Main Branch                 |
| Add: State GST (SGST):               ₹14,089.95             | Account Name:   ABC Textiles Private Limited        |
| Add: Integrated GST (IGST):               ₹0.00             | Current A/c No: 50200012345678                      |
| Round-Off Adjustment:                    +₹0.10             | IFSC Code:      HDFC0000123                         |
| TOTAL PAYABLE AMOUNT:              ₹5,91,778.00             | MICR Code:      641240002                           |
|-------------------------------------------------------------+-----------------------------------------------------|
| AMOUNT IN WORDS:                                                                                                  |
| Indian Rupees Five Lakh Ninety-One Thousand Seven Hundred and Seventy-Eight Only                                  |
|-------------------------------------------------------------------------------------------------------------------|
| TERMS & CONDITIONS:                                         | SIGNATORIES:                                        |
| 1. Interest @ 18% p.a. will be charged if payment is not   |                                                     |
|    settled within the agreed credit period of 30 days.      | For ABC TEXTILES PRIVATE LIMITED                    |
| 2. Goods once sold will not be taken back without prior     |                                                     |
|    written authorization from our quality team.             |                                                     |
| 3. All disputes subject to Tirupur jurisdiction only.       |                                                     |
|                                                             | [Authorized Signatory / Seal]                       |
| Receiver's Signature & Seal: ______________________________ | Prepared By: M. Kumar       Verified By: S. Nathan  |
+===================================================================================================================+
```

---

## 4. Statutory Rule 46 Compliance Checklist

| Mandatory Rule 46 Field | Implementation Details |
|---|---|
| **Invoice Designation** | Clearly stated as **"TAX INVOICE"** with copy marking ("ORIGINAL FOR RECIPIENT"). |
| **Supplier Information** | Registered name, dispatch godown address, GSTIN, PAN, and State Code (`33`). |
| **Serial Number** | Consecutive alphanumeric invoice number unique for the FY (`YSAL-YYYYMM-XXXX`). |
| **Invoice Date** | Calendar date in `DD/MM/YYYY` format (`15/10/2026`). |
| **Recipient Details** | Name, full postal address, GSTIN, and State Code of customer. |
| **Place of Supply** | Statutory state and state code (e.g. `33-Tamil Nadu`). |
| **HSN Code** | 4-digit textile HSN code (`5205` for Cotton Grey, `5206` for Cotton Blended). |
| **Description of Goods**| Comprehensive textile yarn specification (Count, Mill, Color Shade, Lot Number). |
| **Quantitative Measures**| Number of standard bags, per-bag tare (`45.360 Kg`), and net kilogram weight (`Kg`). |
| **Tax Breakup** | Explicit schedule detailing Taxable Value, CGST Rate & Amount, SGST Rate & Amount, IGST Rate & Amount. |
| **Amount in Words** | Auto-translated Indian currency text ("Rupees ... Only"). |
| **Signature** | Signature of authorized signatory or digital signature stamp. |

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

- [ ] Route `/sales/yarn-sales/[id]/print` fetches complete parent and child line-item invoice data.
- [ ] Top bar allows toggling between **Original for Recipient**, **Duplicate for Transporter**, and **Triplicate for Supplier**.
- [ ] Document fits perfectly on a single ISO A4 page for up to 6 line items.
- [ ] HSN tax schedule accurately reflects intra-state (CGST 2.5% + SGST 2.5%) vs inter-state (IGST 5.0%) calculations.
- [ ] Number-to-words utility outputs clean Indian English text (`Rupees Five Lakh Ninety-One Thousand Seven Hundred and Seventy-Eight Only`).
- [ ] Remittance bank details, branch IFSC code, and legal terms print clearly.
