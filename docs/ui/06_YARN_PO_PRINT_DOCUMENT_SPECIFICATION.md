# UI & Document Layout Specification: Yarn Purchase Order (PO) Print & PDF Document

## 1. Document Overview, Version, Scope, and Status

- **Document Title**: Yarn Purchase Order (PO) Commercial A4 Print & PDF Document Specification
- **Screen ID**: `SCR-PROC-001-PRINT`
- **Document Version**: `v1.0.0`
- **Last Updated**: `15/10/2026`
- **Target Audience**: Frontend Engineers, Full-Stack Developers, QA Engineers, and Technical Product Owners
- **Implementation Status**: `Ready for Review / Implementation`
- **Scope**: Covers the printable A4 portrait sheet architecture, `@media print` CSS rules, corporate letterhead branding, statutory GST / PAN identification, dual vendor blocks (Spinning Mill vs Commercial Supplier), itemized commercial pricing table, split delivery schedule, legal terms & quality parameters, multi-tier authorized signatory blocks, and PDF export bindings for Yarn Purchase Orders in the Garments ERP & CRM system.

---

## 2. Module Details, Screen ID, Route, Access Privileges, and API Endpoints

### 2.1 Core Metadata

| Parameter | Specification |
|---|---|
| **Module** | `Module 3 — Procurement (Yarn PO)` |
| **Screen ID** | `SCR-PROC-001-PRINT` |
| **Frontend Route** | `/procurement/yarn-po/[id]/print` |
| **File Location** | `app/(app)/procurement/yarn-po/[id]/print/page.tsx` |
| **Required Privilege** | `purchase_yarn_po.can_print` (or `can_read`) |
| **Authorized Roles** | `SUPER_ADMIN`, `ADMIN_USER`, `COMPANY_USER` (All operational roles) |
| **Paper Standard** | `ISO A4 Portrait (210mm x 297mm)` |
| **Country Pack** | `IN` (India: GST 5% on cotton yarn, HSN 5205, Currency INR `₹`, Date `DD/MM/YYYY`) |

### 2.2 Primary API Endpoints

| HTTP Method | API Path | Privilege / Scope | Description |
|---|---|---|---|
| `GET` | `/api/v1/purchase/yarn-pos/{id}/` | `can_read` | Fetch full PO header, line items, deliveries, and authorized signatory metadata |
| `GET` | `/api/v1/administration/companies/{id}/` | `can_read` | Fetch tenant company letterhead, logo, GSTIN, PAN, and registered address |

---

## 3. UI Layout, Screen Blueprint, and Visual Mockup

### 3.1 Visual Mockup Reference

![Garments ERP & CRM Yarn PO Print Sheet Preview](../assets/ui/yarn_po_print_sample.jpg)

### 3.2 A4 Printable Document Structure (210mm x 297mm)

```
+----------------------------------------------------------------------------------------------------+
| [SCREEN ONLY TOOLBAR]  [<- Back]   [🖨 Print (Ctrl+P)]   [📥 Download PDF]   [ Watermark: Original v]|
+----------------------------------------------------------------------------------------------------+
| ================================================================================================== |
| [LOOM LOGO]                      TEXTILE CORP INDIA PVT LTD                                        |
|                                  Registered Office: 124, Mill Road, Angeripalayam, Tirupur - 641604 |
|                                  GSTIN: 33AABCT1234F1Z5 | PAN: AABCT1234F | State: 33 - Tamil Nadu |
|                                  Phone: +91 421 2471000 | Email: purchase@tcipl.in                 |
| ================================================================================================== |
|                                    PURCHASE ORDER — YARN                                           |
|                                                                                                    |
| PO Number : YPO-202610-0042                                  +-----------------------------------+ |
| PO Date   : 15/10/2026                                       |        AUTHORIZED & APPROVED      | |
| Fiscal Yr : FY 2025-2026                                     |        By Ramesh K. on 15/10/2026 | |
| Job Ref   : Summer 2026 Polo T-Shirt Lot                     +-----------------------------------+ |
|                                                                                                    |
| +--------------------------------------------------+-----------------------------------------------+ |
| | SPINNING MILL (MANUFACTURER)                     | BILLING SUPPLIER / TRADER                     | |
| | Name   : Vardhman Textiles Ltd.                  | Name   : Direct Mill Purchase                 | |
| | Address: Spinning Unit-II, Industrial Area,      | Address: Same as Manufacturer                 | |
| |          Ludhiana, Punjab - 141010               |          (Billed directly by Mill)            | |
| | GSTIN  : 03AAACV0123M1Z2 (State: 03 - Punjab)    | GSTIN  : 03AAACV0123M1Z2                      | |
| +--------------------------------------------------+-----------------------------------------------+ |
|                                                                                                    |
| COMMERCIAL YARN LINE ITEMS:                                                                        |
| +---+--------------------+-------+------+--------+---------+-----------+--------+----------+-------+ |
| |#  | Yarn Count & Specs | Shade | HSN  | Bags   | Bag Wt  | Net Qty Kg| Rate/Kg| Disc(₹)  | Amount| |
| +---+--------------------+-------+------+--------+---------+-----------+--------+----------+-------+ |
| | 1 | 30s CVC Dyed Yarn  | Navy  | 5205 | 100    | 45.360  | 4,536.000 | 350.00 | 0.00     |1587600| |
| |   | 60% Cotton/40% Poly| 19-38 |      |        |         |           |        |          |       | |
| +---+--------------------+-------+------+--------+---------+-----------+--------+----------+-------+ |
| | TOTALS:                               | 100    |         | 4,536.000 |        | SUB-TOTAL|1587600| |
| |                                                                    | IGST (5.0%)      |  79380| |
| |                                                                    | ROUND OFF        |   0.00| |
| |                                                                    | GRAND TOTAL (INR)|1666980| |
| +--------------------------------------------------------------------+------------------+-------+ |
| Amount in Words: INR Sixteen Lakh Sixty-Six Thousand Nine Hundred Eighty Only.                      |
|                                                                                                    |
| SPLIT DELIVERY SCHEDULE:                                                                           |
| +--------+---------------+-------------------------------------+----------+----------------------+ |
| | Lot No | Expected Date | Destination Warehouse / Mill        | Bags     | Scheduled Net Weight | |
| +--------+---------------+-------------------------------------+----------+----------------------+ |
| | Lot 1  | 25/10/2026    | Angeripalayam Knitter Godown        | 50 Bags  | 2,268.000 Kg         | |
| | Lot 2  | 05/11/2026    | Main Factory Raw Godown             | 50 Bags  | 2,268.000 Kg         | |
| +--------+---------------+-------------------------------------+----------+----------------------+ |
|                                                                                                    |
| COMMERCIAL & QUALITY TERMS:                                                                        |
| 1. Quality Standard: Yarn CSP must be minimum 2800 for Combed and 2400 for Carded.                 |
| 2. Moisture Regain: Standard 8.5% moisture tolerance. Any excess weight deduction applies.         |
| 3. Packing: New sound HDPE woven bags with plastic cone tare deductions.                           |
| 4. Delivery Tolerance: +/- 2% on quantity acceptable.                                              |
| 5. Payment Terms: Payment within 30 days against LC / verified GRN inward gate pass.               |
|                                                                                                    |
| +-----------------------+-----------------------+--------------------------------------------------+ |
| | Prepared By:          | Verified By:          | For Textile Corp India Pvt Ltd                   | |
| |                       |                       |                                                  | |
| | ____________________  | ____________________  | ________________________________________         | |
| | Merchandiser          | Store / QC Manager    | Authorized Signatory (with Company Seal)         | |
| +-----------------------+-----------------------+--------------------------------------------------+ |
```

---

## 4. Printable Header Block (Letterhead & Statutory Identity)

Occupies the top 45mm of the sheet, styled as a corporate letterhead:

1. **Company Logo**:
   - High-resolution SVG / 300 DPI PNG embedded on the top left or centered (`height: 48px`).
2. **Company Legal Title**:
   - Heading font: `16pt`, bold, uppercase (`Textile Corp India Pvt Ltd`).
3. **Statutory Details & Tax Registrations**:
   - Registered Address Line 1 & 2, City, State, Pincode.
   - **GSTIN**: Formatted 15-character identifier with State prefix (e.g. `GSTIN: 33AABCT1234F1Z5`).
   - **PAN**: 10-character corporate identifier (`PAN: AABCT1234F`).
   - **State Code**: Standard GST state nomenclature (`State: 33 - Tamil Nadu`).
   - **Corporate Identity Number (CIN)**: Optional statutory registration.
   - **Official Communication**: Email (`purchase@tcipl.in`) and Phone (`+91 421 2471000`).
4. **Document Title Banner**:
   - Centered block in high-contrast text: `PURCHASE ORDER — YARN`.
   - Subtle copy indicator on top right: `ORIGINAL FOR RECIPIENT` / `DUPLICATE FOR GODOWN`.

---

## 5. Purchase Order Metadata & Dynamic Approval Seal

Directly below the header, organized in a balanced 2-column format:

### 5.1 Left Column: Document Identifiers
- **PO Number**: `YPO-202610-0042` (Rendered in bold monospace `11pt`).
- **PO Date**: `15/10/2026` (`DD/MM/YYYY`).
- **Financial Year**: `FY 2025-2026`.
- **Buyer Style / Job Reference**: `Summer 2026 Polo T-Shirt Lot` (or *"General Stock"*).

### 5.2 Right Column: Dynamic Status Seal & QR Code
- **Status Stamp**:
  - If **Authorized (`is_authorized == 1`)**:
    - Renders a clean double-bordered green stamp:
      ```
      +-------------------------------+
      |    ★ AUTHORIZED & APPROVED ★  |
      | By Ramesh K. on 15/10/2026    |
      +-------------------------------+
      ```
  - If **Draft (`is_authorized == 0`)**:
    - Renders an amber stamp: `DRAFT — FOR REVIEW ONLY (NOT VALID FOR DISPATCH)`.
    - Translucent diagonal watermark across the page body: `DRAFT`.
- **Verification QR Code**:
  - 40x40mm QR code linking to digital PO verification portal (`https://erp.garments.com/verify/po/YPO-202610-0042`).

---

## 6. Vendor & Supplier Dual-Box Structure

Two equal-width bordered boxes displayed side-by-side:

### Box 1: Spinning Mill (Physical Manufacturer)
- **Header**: `SPINNING MILL (MANUFACTURING MILL)`
- **Mill Name**: `Vardhman Textiles Ltd.` (`font-bold`).
- **Factory Address**: `Spinning Unit-II, Industrial Area, Ludhiana, Punjab - 141010`.
- **GSTIN**: `03AAACV0123M1Z2` (`State: 03 - Punjab`).
- **Contact**: `Mr. S. Sharma (+91 98140 12345)`.

### Box 2: Billing Supplier / Trader (Invoicing Vendor)
- **Header**: `BILLING SUPPLIER / TRADER`
- **Supplier Name**: `Direct Mill Purchase` (or Trader Trading Name).
- **Address**: `Same as Manufacturer (Direct Mill Invoicing)`.
- **GSTIN**: `03AAACV0123M1Z2`.
- **Payment Terms**: `Payment within 30 days against LC / verified GRN`.

---

## 7. Itemized Yarn Schedule & Commercial Pricing Table

High-contrast print table with crisp 1px borders (`#CBD5E1` / `#000000`):

| S.No | Yarn Description & Technical Specs | Color Shade | HSN Code | Bags | Bag Wt (Kg) | Net Weight (Kg) | Rate / Kg (₹) | Disc (₹) | Net Amount (₹) |
|---|---|---|---|---|---|---|---|---|---|
| **1** | **30s CVC Dyed Yarn**<br>Blend: 60% Cotton / 40% Polyester<br>Ply: 1 • Twist: Standard Knitting | Navy Blue<br>(PANTONE 19-3832) | `5205` | 100 | 45.360 | 4,536.000 | 350.00 | 0.00 | 15,87,600.00 |
| **2** | **20s Polyester Spun Yarn**<br>Blend: 100% Virgin Polyester | Optical White | `5509` | 50 | 45.360 | 2,268.000 | 210.00 | 5.00 | 4,64,940.00 |

---

## 8. Commercial Taxes, Deductions, and Amount in Words

Positioned immediately below the line items grid, right-aligned calculation block:

### 8.1 Tax & Financial Summary

| Summary Line | Formula / Calculation | Amount (INR) |
|---|---|---|
| **Sub-Total (Taxable Net Value)** | $\sum \text{Line Amounts}$ | `₹20,52,540.00` |
| **Tax Determination** | Evaluated by Place of Supply: | — |
| — **CGST (2.5%)** *(Intra-state)* | If Mill/Supplier State == Company State | `₹0.00` |
| — **SGST (2.5%)** *(Intra-state)* | If Mill/Supplier State == Company State | `₹0.00` |
| — **IGST (5.0%)** *(Inter-state: Punjab -> TN)*| If Mill/Supplier State $\ne$ Company State | `₹1,02,627.00` |
| **Round Off** | Adjustment to nearest rupee | `+₹0.00` |
| **Grand Total (Net Payable)** | $\text{Sub-Total} + \text{Taxes}$ | **`₹21,55,167.00`** |

### 8.2 Amount in Words
Rendered in bold italic font spanning the full width:
> **Amount in Words (INR)**: *Rupees Twenty-One Lakh Fifty-Five Thousand One Hundred Sixty-Seven Only.*

---

## 9. Split Delivery Schedule Block

Rendered only when `is_delivery == 1` and delivery lots are configured:

```
SPLIT DELIVERY SCHEDULE:
+--------+---------------+-------------------------------------+----------+----------------------+
| Lot No | Expected Date | Destination Warehouse / Mill        | Bags     | Scheduled Net Weight |
+--------+---------------+-------------------------------------+----------+----------------------+
| Lot 1  | 25/10/2026    | Angeripalayam Knitter Godown        | 100 Bags | 4,536.000 Kg         |
| Lot 2  | 05/11/2026    | Main Factory Raw Godown             | 50 Bags  | 2,268.000 Kg         |
+--------+---------------+-------------------------------------+----------+----------------------+
```

---

## 10. Commercial Purchase Terms & Quality Conditions

Standard enterprise textile purchase clauses governing the contract:

1. **Quality & Strength Specifications**:
   - Count Strength Product (CSP) must be minimum 2800 for Combed Hosiery and 2400 for Carded Hosiery.
   - Uster test imperfections (Neps, Thin, Thick places) must not exceed 5% Uster statistics standard.
2. **Moisture Regain & Conditioning**:
   - Standard commercial moisture regain allowance is **8.5%**. Excess moisture over 8.5% will be deducted from gross billing weight upon godown electronic testing.
3. **Packaging & Tare Deductions**:
   - Yarn must be packed in sound, clean, non-reused HDPE woven bags.
   - Actual plastic cone tare and packing bag tare will be deducted at godown gate weighing.
4. **Delivery Tolerance**:
   - Quantity tolerance of $\pm 2\%$ is acceptable for final closing.
5. **Rejection & Debit Notes**:
   - Defective, shade-variation, or substandard yarn rejected during knitting will be held at vendor's risk and cost. Debit notes will include knitting machine downtime charges.
6. **Statutory & Jurisdiction**:
   - Subject to exclusive jurisdiction of Tirupur, Tamil Nadu courts.

---

## 11. Verification & Authorized Signatory Block

Located at the bottom of the printable page, divided into 3 equal execution blocks:

```
+--------------------------+--------------------------+------------------------------------------+
| PREPARED BY              | VERIFIED BY              | FOR TEXTILE CORP INDIA PVT LTD           |
|                          |                          |                                          |
|                          |                          |                                          |
| ________________________ | ________________________ | ________________________________________ |
| Merchandiser / Operator  | Store / Quality Manager  | Authorized Signatory (with Company Seal) |
| Date: 15/10/2026         | Date: 15/10/2026         | Approved On: 15/10/2026 11:30 AM         |
+--------------------------+--------------------------+------------------------------------------+
```

---

## 12. On-Screen Floating Action Toolbar (Screen Only)

A floating toolbar rendered at the top of the browser viewport, automatically hidden during print:

```
+---------------------------------------------------------------------------------------------------+
| [<- Back to PO]        [🖨 Print Document (Ctrl+P)]        [📥 Export PDF]        [ Copy Link ]   |
+---------------------------------------------------------------------------------------------------+
```

- **"Print Document" Button**: Calls `window.print()`.
- **"Export PDF" Button**: Generates vector PDF using browser print engine or server-side headless Chromium.
- **"Back to PO" Button**: Returns to `/procurement/yarn-po/{id}`.

---

## 13. Frontend `@media print` CSS Rules & Multi-Page Break Handling

```css
@media print {
  /* Hide non-printable application chrome */
  nav, sidebar, header, .no-print, .floating-toolbar {
    display: none !important;
  }

  /* Reset body and canvas for A4 dimensions */
  body, html {
    background: #ffffff !important;
    margin: 0 !important;
    padding: 0 !important;
    font-size: 9pt !important;
    color: #000000 !important;
    -webkit-print-color-adjust: exact !important;
    print-color-adjust: exact !important;
  }

  /* A4 Page Margins */
  @page {
    size: A4 portrait;
    margin: 12mm 10mm 12mm 10mm;
  }

  /* Prevent page breaks inside critical elements */
  .po-header-block,
  .vendor-box,
  .line-item-row,
  .totals-block,
  .signatory-block {
    page-break-inside: avoid !important;
    break-inside: avoid !important;
  }

  /* Table styling */
  table {
    width: 100% !important;
    border-collapse: collapse !important;
  }

  th, td {
    border: 1px solid #334155 !important;
    padding: 4px 6px !important;
  }

  th {
    background-color: #f1f5f9 !important;
    font-weight: 700 !important;
  }

  /* Force display of approval seal colors */
  .approval-seal {
    border-color: #16a34a !important;
    color: #16a34a !important;
  }
}
```

---

## 14. API Integration, Hydration, and Number-to-Words Conversion Function

### 14.1 Indian Number to Words Generator (`number-to-words.ts`)

```typescript
export function convertNumberToIndianWords(amount: number): string {
  const units = ["", "One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine", "Ten",
    "Eleven", "Twelve", "Thirteen", "Fourteen", "Fifteen", "Sixteen", "Seventeen", "Eighteen", "Nineteen"];
  const tens = ["", "", "Twenty", "Thirty", "Forty", "Fifty", "Sixty", "Seventy", "Eighty", "Ninety"];

  function convertTwoDigits(num: number): string {
    if (num < 20) return units[num];
    return tens[Math.floor(num / 10)] + (num % 10 !== 0 ? " " + units[num % 10] : "");
  }

  function convertThreeDigits(num: number): string {
    const hundred = Math.floor(num / 100);
    const rest = num % 100;
    let res = "";
    if (hundred > 0) res += units[hundred] + " Hundred";
    if (rest > 0) res += (res ? " " : "") + convertTwoDigits(rest);
    return res;
  }

  if (amount === 0) return "Rupees Zero Only";

  const integerPart = Math.floor(amount);
  const decimalPart = Math.round((amount - integerPart) * 100);

  const crore = Math.floor(integerPart / 10000000);
  let rem = integerPart % 10000000;
  const lakh = Math.floor(rem / 100000);
  rem = rem % 100000;
  const thousand = Math.floor(rem / 1000);
  const hundredAndBelow = rem % 1000;

  let result = "";
  if (crore > 0) result += convertThreeDigits(crore) + " Crore ";
  if (lakh > 0) result += convertTwoDigits(lakh) + " Lakh ";
  if (thousand > 0) result += convertTwoDigits(thousand) + " Thousand ";
  if (hundredAndBelow > 0) result += convertThreeDigits(hundredAndBelow);

  result = "Rupees " + result.trim();
  if (decimalPart > 0) {
    result += " and " + convertTwoDigits(decimalPart) + " Paise";
  }
  return result + " Only.";
}
```

---

## 15. Next.js Folder Structure and Component Hierarchy

```
frontend/app/(app)/procurement/yarn-po/[id]/print/
├── page.tsx                           # Master printable page (Hydrates PO and Company)
├── components/
│   ├── YarnPOPrintToolbar.tsx         # Screen-only toolbar (Print, Export PDF, Back)
│   ├── YarnPOPrintHeader.tsx          # Company letterhead, logo, GSTIN, PAN
│   ├── YarnPOPrintMetadata.tsx        # PO #, Date, QR code, and Approval Seal
│   ├── YarnPOPrintVendorBoxes.tsx     # Mill and Billing Supplier dual boxes
│   ├── YarnPOPrintItemsTable.tsx      # High-density itemized commercial grid
│   ├── YarnPOPrintTaxSummary.tsx      # Sub-total, CGST/SGST/IGST, and Words
│   ├── YarnPOPrintDeliveries.tsx      # Split delivery lots table
│   ├── YarnPOPrintTerms.tsx           # Standard commercial textile purchase terms
│   └── YarnPOPrintSignatures.tsx      # Prepared, Verified, and Authorized signature blocks
└── styles/
    └── print-document.css             # Specialized A4 print stylesheets
```

---

## 16. Developer Implementation Checklist

- [ ] **1. Route Setup**: Dynamic route created at `/procurement/yarn-po/[id]/print/page.tsx`.
- [ ] **2. Letterhead Hydration**: Company Name, Logo, GSTIN, PAN, and address correctly fetched and displayed.
- [ ] **3. Document Status Seal**: Renders green double-line seal if authorized; renders amber warning and diagonal watermark if draft.
- [ ] **4. Vendor Dual-Box**: Accurately differentiates between physical Spinning Mill and commercial Supplier/Trader.
- [ ] **5. Line Items Grid**: Shows Yarn Count, Blend Ratio, Shade, Bags, Bag Tare, Weight Kg, Rate, and Net Amount.
- [ ] **6. GST Calculation**: Computes intra-state (CGST+SGST) vs inter-state (IGST) based on vendor state code vs company state code.
- [ ] **7. Amount in Words**: `convertNumberToIndianWords` converts numerical grand total into Indian currency text accurately.
- [ ] **8. Split Delivery Schedule**: Rendered cleanly only when deliveries exist on the order.
- [ ] **9. Standard Purchase Terms**: Standard 6 quality and commercial clauses rendered without truncation.
- [ ] **10. Signature Blocks**: 3 signature boxes (Prepared, Verified, Authorized) stay grouped and avoid mid-element page breaks.
- [ ] **11. Print CSS (`@media print`)**: Hides top toolbar, removes shadows, enforces 12mm page margins, and triggers browser print dialogue cleanly.

---

## 17. Inconsistencies, Statutory Rules, and Items Requiring Confirmation

| Issue ID | Section | Requirement / Behavior | Identified Inconsistency / Statutory Consideration | Recommended Resolution | Confirmation Required |
|---|---|---|---|---|---|
| **`ISS-P01`** | §8.1 GST Tax Rate on Yarn | Cotton Yarn is taxed at 5% GST (HSN 5205), whereas Synthetic Spun Yarn (Polyester HSN 5509) or Blended Yarn may be taxed at 12% GST in India. | Does the print document calculate tax per line item HSN or apply a flat 5% PO-level tax rate? | Use `TaxEngine.compute()` from `apps/masters/services.py` to calculate exact line-level HSN GST rates. | **Developer Confirmation** |
| **`ISS-P02`** | §5.2 QR Code Verification Target | QR code links to an external verification URL. | Does the tenant require public token-based verification without requiring login for receiving mills? | Implement a public read-only verification route `/verify/po/[hash]`. | **Business Confirmation** |
| **`ISS-P03`** | §11 Signatory Seal Stamp | Physical stamp vs Digital Cryptographic Signature. | Does the business require attaching a stored digital signature image of the approving manager on authorized prints? | Add optional `digital_signature_url` from `User` profile into the Authorized Signatory box. | **Business Confirmation** |
