# UI & Document Layout Specification: Yarn Inward (GRN) Print & PDF Document

## 1. Document Overview, Version, Scope, and Status

- **Document Title**: Yarn Inward Goods Receipt Note (GRN) Commercial A4 Print & PDF Document Specification
- **Screen ID**: `SCR-INVN-001-PRINT`
- **Document Version**: `v1.0.0`
- **Last Updated**: `15/10/2026`
- **Target Audience**: Frontend Engineers, Full-Stack Developers, QA Engineers, and Technical Product Owners
- **Implementation Status**: `Ready for Review / Implementation`
- **Scope**: Covers the printable A4 portrait sheet architecture, `@media print` CSS rules, corporate letterhead branding, statutory GST / PAN identification, dual vendor blocks (Spinning Mill vs Invoicing Supplier), itemized weighbridge physical weighing table, gross-to-tare deduction records, statutory GST tax distribution, quality/moisture inspection block, 4-tier authorized signatory blocks, and PDF export bindings for Yarn Inward GRNs in the Garments ERP & CRM system.

---

## 2. Module Details, Screen ID, Route, Access Privileges, and API Endpoints

### 2.1 Core Metadata

| Parameter | Specification |
|---|---|
| **Module** | `Module 4 — Inventory & Godown Stock Ledger` |
| **Screen ID** | `SCR-INVN-001-PRINT` |
| **Frontend Route** | `/inventory/yarn-inward/[id]/print` |
| **File Location** | `app/(app)/inventory/yarn-inward/[id]/print/page.tsx` |
| **Required Privilege** | `inventory_yarn_inward.can_print` (or `inventory_yarn_inward.can_read`) |
| **Authorized Roles** | `SUPER_ADMIN`, `ADMIN_USER`, `COMPANY_USER` (All operational and audit roles) |
| **Paper Standard** | `ISO A4 Portrait (210mm x 297mm)` |
| **Country Pack** | `IN` (India: GST 5% on cotton yarn, HSN 5205, Currency INR `₹`, Date `DD/MM/YYYY`) |


### 2.2 Primary API Endpoints

| HTTP Method | API Path | Privilege / Scope | Description |
|---|---|---|---|
| `GET` | `/api/v1/inventory/yarn-inwards/{id}/` | `can_read` | Fetch complete inward header, weighbridge line items, tax breakdown, vehicle, and gate pass metadata |
| `GET` | `/api/v1/administration/companies/{id}/` | `can_read` | Fetch tenant company letterhead, logo, GSTIN, PAN, and registered factory address |

---

## 3. UI Layout, Screen Blueprint, and Visual Mockup

### 3.1 Visual Mockup Reference

![Garments ERP & CRM Yarn Inward Print Sheet Preview](../assets/ui/yarn_po_print_sample.jpg)

### 3.2 A4 Printable Document Structure (210mm x 297mm)

```
+----------------------------------------------------------------------------------------------------+
| [SCREEN ONLY TOOLBAR]  [<- Back]   [🖨 Print (Ctrl+P)]   [📥 Download PDF]   [ Copy: Original (Store) v]|
+----------------------------------------------------------------------------------------------------+
| ================================================================================================== |
| [FACTORY LOGO]                   TEXTILE CORP INDIA PVT LTD                                        |
|                                  Spinning & Knitting Division, Mill Road, Tirupur - 641604         |
|                                  GSTIN: 33AABCT1234F1Z5 | PAN: AABCT1234F | State: 33 - Tamil Nadu |
|                                  Phone: +91 421 2471000 | Email: inventory@tcipl.in                |
| ================================================================================================== |
|                               GOODS RECEIPT NOTE (GRN) — YARN INWARD                                |
|                                                                                                    |
| GRN Number : YIN-202610-0084                                 +-----------------------------------+ |
| GRN Date   : 15/10/2026                                      |         STOCK POSTED TO LEDGER    | |
| Supplier DC: DC-94821 (Dated 14/10/2026)                     |         Verified by K. Velu (Store| |
| PO Ref #   : YPO-202610-0042                                 +-----------------------------------+ |
| Vehicle No : TN-38-BZ-4921                                   | Gate Pass #: GE-2026-10-094        | |
| Destination: Main Raw Material Godown (Bay A-02)             | Fiscal Year: FY 2025-2026         | |
|                                                                                                    |
| +--------------------------------------------------+-----------------------------------------------+ |
| | SPINNING MILL (MANUFACTURER)                     | BILLING SUPPLIER / TRADER                     | |
| | Name   : Vardhman Textiles Ltd.                  | Name   : Direct Mill Purchase                 | |
| | Address: Spinning Unit-II, Ludhiana, Punjab      | Address: Same as Manufacturer                 | |
| | GSTIN  : 03AAACV0123M1Z2 (State: 03 - Punjab)    | GSTIN  : 03AAACV0123M1Z2                      | |
| +--------------------------------------------------+-----------------------------------------------+ |
|                                                                                                    |
| PHYSICAL WEIGHBRIDGE & ITEMIZATION TABLE:                                                          |
| +---+--------------------+----------+------+--------+------------+-----------+-----------+---------+ |
| |#  | Yarn Count & Specs | Lot No   | Bags | Kg/Bag | Gross (Kg) | Tare (Kg) | Net Wt(Kg)| Rate(₹) | |
| +---+--------------------+----------+------+--------+------------+-----------+-----------+---------+ |
| | 1 | 30s Combed Cotton  | VTM-7842 | 100  | 45.360 | 4,590.000  | 54.000    | 4,536.000 | 350.00  | |
| |   | Grey Yarn / HSN5205|          |      |        |            |           |           |         | |
| +---+--------------------+----------+------+--------+------------+-----------+-----------+---------+ |
| | TOTALS:                           | 100  |        | 4,590.000  | 54.000    | 4,536.000 | SUB-TOT |₹15,87,600
| |                                                                | CGST (2.5%)           |  ₹39,690| |
| |                                                                | SGST (2.5%)           |  ₹39,690| |
| |                                                                | IGST (0.0%)           |    ₹0.00| |
| |                                                                | GRAND TOTAL VALUE     |₹16,66,980
| +----------------------------------------------------------------+-----------------------+---------+ |
| Net Weight in Words: Four Thousand Five Hundred Thirty-Six Kilograms Only.                          |
| Total Value in Words: INR Sixteen Lakh Sixty-Six Thousand Nine Hundred Eighty Only.                 |
|                                                                                                    |
| QUALITY INSPECTION & PACKAGE VERIFICATION:                                                         |
| [✔] Sound Packing Condition   [✔] Cones Tare Verified (54.00 Kg)   [✔] Moisture Tested: 8.4% (Pass)  |
|                                                                                                    |
| FOUR-TIER AUTHORIZED SIGNATORIES:                                                                  |
| +--------------------+--------------------+-----------------------+--------------------------------+ |
| | 1. Gate Guard      | 2. Weighbridge     | 3. Godown In-Charge   | 4. Commercial / Factory Head   | |
| | Vehicle In: 09:40AM| Gross Wt Checked   | Stacked: Bay A-02     | Passed for Payment & Accounts  | |
| | Sign: _____________| Sign: _____________| Sign: ________________| Sign: _________________________| |
| +--------------------+--------------------+-----------------------+--------------------------------+ |
+----------------------------------------------------------------------------------------------------+
```

---

## 4. Header, Letterhead, and Statutory Metadata

1. **Company Branding & Letterhead**:
   - High-resolution SVG / PNG company logo with 300 DPI print fidelity.
   - Company Legal Name, Registered Godown Address, GSTIN, PAN, CIN, State Code.
2. **Document Title & Identification**:
   - Heading: `GOODS RECEIPT NOTE (GRN) — YARN INWARD`.
   - Distinctive copy watermark in top right:
     - `ORIGINAL FOR GODOWN RECORD`
     - `DUPLICATE FOR ACCOUNTS PAYABLE`
     - `TRIPLICATE FOR SECURITY GATE ENTRY`
3. **Tracking References**:
   - `GRN Number`: High-contrast bold barcode/text (`YIN-YYYYMM-XXXX`).
   - `GRN Date`: Formatted `DD/MM/YYYY`.
   - `Supplier DC & Date`: Delivery challan reference.
   - `Vehicle Number`: Commercial vehicle registration.

---

## 5. Dual Vendor Entity Block (Spinning Mill vs Commercial Supplier)

In textile accounting, the physical manufacturing spinning mill often differs from the commercial invoice billing party:

- **Left Block (Spinning Mill / Manufacturer)**:
  - Name, Manufacturing Unit Address, State, and GSTIN.
  - Used for technical lot tracking, twist quality, and CSP laboratory testing.
- **Right Block (Invoicing Supplier / Trader)**:
  - Name, Registered Commercial Address, GSTIN.
  - Used for commercial purchase accounts payable and input tax credit (ITC) ledger posting.

---

## 6. Weighbridge Data Table and GST Breakdown

- **Exact Weight Metrics**:
  - Itemized rows displaying Count, Mill Lot Number, Bags, Bag Nominal Tare, Gross Weight, Tare Weight, and Net Weight in Kilograms.
  - Clear aggregate row totaling Bags, Gross Weight, Tare Deductions, and Net Kilograms.
- **Statutory GST Breakdown**:
  - Intra-state dispatches print explicit lines for **CGST (2.5%)** and **SGST (2.5%)**.
  - Inter-state dispatches print a unified line for **IGST (5.0%)**.
- **Amount & Weight in Words**:
  - Formatted dynamically in Indian numbering format via `FormatService.amount_to_words()` and `FormatService.weight_to_words()`.

---

## 7. Quality Inspection & Four-Tier Signatory Block

A valid textile factory GRN requires 4 sequential operational handoffs:

1. **Security Gate Guard**:
   - Verifies vehicle number, physical seal integrity, gate entry number, and vehicle arrival time.
2. **Weighbridge Operator**:
   - Certifies that lorry gross weight and tare weight were measured on a calibrated weighbridge scale.
3. **Godown Storekeeper / In-Charge**:
   - Certifies that the bags were unloaded, counted, checked for damage, and stacked in the assigned godown bay.
4. **Commercial / Plant Manager**:
   - Authorizes the commercial valuation and passes the GRN for three-way invoice matching and supplier payment release.

---

## 8. Print Styling Rules (`@media print`)

```css
@media print {
  body {
    background: #ffffff !important;
    color: #000000 !important;
    font-size: 11pt;
    line-height: 1.3;
  }

  .screen-only-toolbar {
    display: none !important;
  }

  .print-page-container {
    width: 210mm;
    min-height: 297mm;
    padding: 12mm 15mm;
    margin: 0 auto;
    page-break-after: always;
  }

  table {
    border-collapse: collapse !important;
    width: 100% !important;
  }

  table, th, td {
    border: 1px solid #1e293b !important;
  }

  th {
    background-color: #f1f5f9 !important;
    font-weight: 700 !important;
  }

  .signatory-block {
    page-break-inside: avoid !important;
    margin-top: 25px;
  }
}
```

---

## 9. Developer Acceptance Checklist

- [ ] **1. Clean A4 Fit**: Entire GRN document prints seamlessly on a single A4 portrait page for standard orders ($\le 5$ lines).
- [ ] **2. Hide Web Chrome**: Browser headers, footers, and screen toolbar disappear during `Ctrl+P` print previews.
- [ ] **3. Accurate Math**: Gross minus Tare equals Net Weight exactly to 3 decimal places across all rows.
- [ ] **4. Dual Vendor Blocks**: Spinning Mill and Invoicing Trader render distinctly with correct GSTINs.
- [ ] **5. Amount & Weight in Words**: Accurately renders Indian English words for both Net Weight (Kg) and Grand Total (₹).
- [ ] **6. Copy Selector**: Toolbar dropdown allows switching between "Original (Godown)", "Duplicate (Accounts)", and "Triplicate (Gate)".
