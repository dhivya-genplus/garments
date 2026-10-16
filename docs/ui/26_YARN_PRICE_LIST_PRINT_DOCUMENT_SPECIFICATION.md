# Yarn Price List (Rate Card & Contract Schedule) Print Document Specification

| Standard Code | Screen ID | Target Platform | API Version | Document Version | Date | Status |
|---|---|---|---|---|---|---|
| **STD-UI-001** | **`SCR-PRIC-001-PRINT`** | Next.js 14 (App Router) + TypeScript | `v1.2` (Django 5 DRF) | `v1.0.0` | 16/10/2026 | **APPROVED FOR IMPLEMENTATION** |

---

## 1. Document Overview, Version, Scope, and Status

### 1.1 Purpose
This specification defines the printable document architecture, CSS `@media print` rules, ISO A4 Portrait layout, corporate letterhead, itemized count-wise rate schedules, volume slab tiers, commercial terms, and bilateral signatory requirements for the **Yarn Price List Print Document / Official Rate Card** (`SCR-PRIC-001-PRINT`).

In the Indian textile and apparel sector, formal rate cards serve as legally binding commercial annexures for:
1. **Mill Purchase Supply Contracts**: Confirming agreed procurement rates per Kg between spinning mills and the enterprise for specific quarterly delivery windows.
2. **Commercial Buyer Quotations**: Providing domestic brand buyers, knitting subcontractors, and fabric houses with authoritative count-wise selling rates, volume discount tiers, and validity cutoff dates.
3. **Auditing & ERP Verification**: Providing godown receiving desks, accounts payable teams, and external auditors with a hardcopy rate reference to audit invoices against agreed terms.

### 1.2 Scope
- **Entities Handled**: Parent header [`tm_price_list`](file:///d:/Codebase/Garments/backend/apps/pricing/models.py) (`PriceList`), item lines [`tm_price_list_item`](file:///d:/Codebase/Garments/backend/apps/pricing/models.py) (`PriceListItem`), and party master details [`tm_party`](file:///d:/Codebase/Garments/backend/apps/masters/models.py).
- **Physical Document Standard**: ISO A4 Portrait (`210mm x 297mm`), high-contrast monochrome typography, zero page overflows.
- **Country Pack**: India (`IN`) — Indian Rupee (`₹`), Indian numerical grouping (`12,34,567.89`), Date format (`DD/MM/YYYY`), Rates displayed to 4 decimal places (`0.0000`), Bag weight standard `45.360 Kg`.
- **Target Route**: `/pricing/yarn-price-lists/[id]/print`.

---

## 2. Module Details, Screen ID, Route, and Access Privileges

### 2.1 Core Metadata

| Parameter | Specification |
|---|---|
| **Module** | `Module 9 — Commercial Pricing Engine` |
| **Screen ID** | `SCR-PRIC-001-PRINT` |
| **Frontend Route** | `/pricing/yarn-price-lists/[id]/print` |
| **File Location** | `app/(app)/pricing/yarn-price-lists/[id]/print/page.tsx` |
| **Required Privilege** | `pricing_manage.can_print` |
| **Authorized Roles** | `SUPER_ADMIN`, `ADMIN_USER`, `COMPANY_USER` (Commercial Director, Procurement, Sales, Costing, Billing Clerk) |
| **Country Pack** | `IN` (India: Currency INR `₹`, Date `DD/MM/YYYY`, Standard Bag `45.360 Kg`) |

---

## 3. UI Layout & Print Blueprint (ISO A4 Portrait Wireframe)

```
+-------------------------------------------------------------------------------------------------------------------+
| [<- Back to Price Lists]    YARN RATE CARD PRINT PREVIEW               [ Layout: Standard A4 v ]   [ PRINT RATE CARD ]|
+===================================================================================================================+
|                                        ABC TEXTILES PRIVATE LIMITED                                               |
|                    Regd Office: 120, Avinashi Road, Civil Aerodrome Post, Tirupur - 641 614, Tamil Nadu           |
|                    Works / Godown: SF #142, Angeripalayam Main Road, Tirupur - 641 602, Tamil Nadu, India         |
|                    GSTIN: 33AAAAA1234A1Z5 | PAN: AAAAA1234A | CIN: U17111TZ2020PTC012345 | State Code: 33          |
|                    Email: commercial@abctextiles.com | Web: www.abctextiles.com | Tel: +91 421 2233445            |
|-------------------------------------------------------------------------------------------------------------------|
|                                   OFFICIAL YARN RATE CARD & SUPPLY SCHEDULE                                       |
|                                       [ CONTRACT TYPE: PURCHASE AGREEMENT ]                                       |
|-------------------------------------------------------------------------------------------------------------------|
| CONTRACT & RATE CARD DETAILS:                               | CONTRACTED PARTY / MILL DETAILS:                    |
| Price List Code:  YPL-202610-0012                           | Party Name:    RAMCO MILLS LIMITED                  |
| Agreement Title:  Ramco Mills Q4 Contract 30s/40s           | Vendor Code:   V-1042                               |
| Agreement Scope:  PARTY-SPECIFIC CONTRACT                   | Address:       Post Box #1, Railway Station Road,   |
| Issue Date:       16/10/2026                                |                Rajapalayam - 626 117, Tamil Nadu    |
| Valid From Date:  16/10/2026                                | GSTIN:         33CCCC1234C1Z1 | State Code: 33     |
| Valid To Date:    31/12/2026 (77 Days Active)               | Contact Person: K. R. Ramasamy (General Manager)    |
| Operating Currency: INR - Indian Rupee (₹)                  | Contact Tel:   +91 4563 235000 / +91 98421 00000   |
|-------------------------------------------------------------------------------------------------------------------|
| ITEMIZATION: YARN COUNTS, VOLUME BREAK SLABS & NET CONTRACT RATES:                                                |
| S.# | Yarn Description / Technical Specs       | Category | Volume Slab Tier (Kg)    | Base (₹/Kg) | Disc % | Net Rate (₹/Kg)*| MOQ (Kg)| Lead Time|
|-----+------------------------------------------+----------+--------------------------+-------------+--------+-----------------+---------+----------|
|  1  | 100% Cotton 30s Karded Hosiery Yarn      | GREY     |         0.000 -   500.000|    340.0000 |  0.00% |        340.0000 | 100.000 |  3 Days  |
|     | Spinning Mill: Ramco Mills (Auto-Coned)  |          |                          |             |        |                 |         |          |
|  2  | 100% Cotton 30s Karded Hosiery Yarn      | GREY     |       500.001 - 2,000.000|    340.0000 |  2.00% |        333.2000 | 500.000 |  5 Days  |
|     | Spinning Mill: Ramco Mills (Auto-Coned)  |          |                          |             |        |                 |         |          |
|  3  | 100% Cotton 30s Karded Hosiery Yarn      | GREY     |     2,000.001 - [Above]  |    340.0000 |  3.50% |        328.1000 | 2,000.0 |  7 Days  |
|     | Spinning Mill: Ramco Mills (Auto-Coned)  |          |                          |             |        |                 |         |          |
|  4  | 100% Cotton 40s Combed Compact Yarn      | GREY     |         0.000 - 1,000.000|    410.0000 |  0.00% |        410.0000 |  45.360 |  4 Days  |
|     | Spinning Mill: Ramco Mills (Ring Spun)   |          |                          |             |        |                 |         |          |
|  5  | 100% Cotton 34s Combed Hosiery Yarn      | DYED     |         0.000 - [Above]  |    435.0000 |  1.50% |        428.4750 | 200.000 | 10 Days  |
|     | Shade: Navy Blue (Shade Code: SH-102)    |          |                          |             |        |                 |         |          |
|-------------------------------------------------------------------------------------------------------------------|
| COMMERCIAL COVENANTS & DELIVERY TERMS:                                                                            |
| 1. TAXES: All quoted rates are NET EX-MILL / EX-GODOWN and EXCLUSIVE of GST. Statutory CGST (2.5%) + SGST (2.5%)  |
|    or IGST (5.0%) will be charged extra as per applicable tax rules under HSN Chapter 5205 / 5206.                |
| 2. PACKING STANDARD: Standard export packing in woven HDPE bags containing 24 paper cones @ 1.890 Kg each,       |
|    aggregating to 45.360 Kg Net weight per bag. Tare deduction: 0.050 Kg per cone.                                |
| 3. DELIVERY SCHEDULE: As per mutually agreed PO release schedules. Mill shall maintain stated lead times.        |
| 4. PAYMENT TERMS: Net 30 Days from date of Inward GRN receipt against PDC / Irrevocable Bank LC.                  |
| 5. QUALITY TOLERANCE: Count CV% < 1.3, CSP > 2800, Total IPI < 60. Goods subject to testing at SITRA / in-house lab|
| 6. PRICE ESCALATION CLAUSE: Rates remain fixed during the validity window (16/10/2026 - 31/12/2026). In case of   |
|    catastrophic raw cotton market movement (>10% Shankar-6 index fluctuation), renegotiation clause applies.      |
|-------------------------------------------------------------------------------------------------------------------|
| SPECIAL CONTRACT NOTES:                                                                                           |
| Quarterly contract covering hosiery knitting requirements for Season 2026-27 Autumn/Winter production line.      |
| Rates confirmed via Spinning Mill Commercial Letter Ref: RML/COMM/2026-27/Q4-98 dated 15/10/2026.                 |
|-------------------------------------------------------------------------------------------------------------------|
| SIGNATORIES & CONTRACTUAL ACCEPTANCE:                                                                             |
|                                                                                                                   |
| For ABC TEXTILES PRIVATE LIMITED                            For RAMCO MILLS LIMITED                               |
|                                                             (Contracted Mill / Supplier)                          |
|                                                                                                                   |
|                                                                                                                   |
| __________________________________________                  __________________________________________            |
| Authorized Signatory / Commercial Director                  Authorized Signatory / Mill Representative            |
| Name:  S. Muthusamy                                         Name:  K. R. Ramasamy                                 |
| Date:  16/10/2026                                           Date:  16/10/2026                                     |
| Place: Tirupur                                              Place: Rajapalayam                                    |
+===================================================================================================================+
```

---

## 4. CSS `@media print` Rules & Formatting Architecture

To guarantee crisp printing across commercial laser printers and headless PDF generators (Puppeteer / Playwright):

```css
@media print {
  @page {
    size: A4 portrait;
    margin: 10mm 12mm 10mm 12mm;
  }

  body {
    background: #ffffff !important;
    color: #000000 !important;
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    font-size: 11px;
    line-height: 1.35;
    -webkit-print-color-adjust: exact;
    print-color-adjust: exact;
  }

  /* Hide interactive web chrome */
  .no-print,
  nav,
  header,
  footer,
  aside,
  button,
  .print-controls {
    display: none !important;
  }

  /* Table styling */
  table.rate-schedule-table {
    width: 100%;
    border-collapse: collapse;
    page-break-inside: auto;
  }

  table.rate-schedule-table tr {
    page-break-inside: avoid;
    page-break-after: auto;
  }

  table.rate-schedule-table th {
    background-color: #f1f5f9 !important;
    color: #0f172a !important;
    font-weight: 700;
    border: 1px solid #cbd5e1;
    padding: 6px 4px;
    font-size: 10.5px;
    text-transform: uppercase;
  }

  table.rate-schedule-table td {
    border: 1px solid #cbd5e1;
    padding: 5px 4px;
    font-size: 10.5px;
  }

  /* Signatory container avoid break */
  .signatory-block {
    page-break-inside: avoid;
    margin-top: 20px;
  }
}
```

---

## 5. Header Metadata & Letterhead Structure

The top of the document features the official enterprise letterhead with verified corporate identities:
- **Company Name**: ABC Textiles Private Limited (or active tenant name from [`tm_company`](file:///d:/Codebase/Garments/backend/apps/masters/models.py)).
- **Registered & Works Address**: Fetched dynamically from active company profile.
- **Statutory Registration Numbers**:
  - `GSTIN`: 15-character statutory GST identification (e.g. `33AAAAA1234A1Z5`).
  - `PAN`: Permanent Account Number (`AAAAA1234A`).
  - `CIN`: Corporate Identity Number (`U17111TZ2020PTC012345`).
  - `State Code`: State identifier (`33` for Tamil Nadu).

---

## 6. Itemized Rate Schedule Table Formatting

### 6.1 Column Alignment & Formats

| Column | Alignment | Formatting Rule |
|---|---|---|
| **S.#** | Center | Sequential integer (`1, 2, 3...`) |
| **Yarn Description** | Left | Count name + Spinning Mill + Sub-spec notes |
| **Category** | Center | Bold badge (`GREY`, `DYED`, `MELANGE`) |
| **Volume Slab Tier** | Center | Minimum to Maximum Kg formatted with Indian grouping |
| **Base Rate (₹/Kg)** | Right | Currency format to 4 decimal places (`340.0000`) |
| **Discount %** | Right | Percentage with 2 decimal places (`2.00%`) |
| **Net Contract Rate**| Right | Bold black typography with Indian Rupee symbol (`₹333.2000`) |
| **MOQ (Kg)** | Right | In Kg (e.g. `100.000 Kg`) |
| **Lead Time** | Center | Days integer (`3 Days`) |

---

## 7. Commercial Covenants & Legal Terms

The printout incorporates standard textile trade covenants:
1. **GST Terms**: Explicit statement that rates are net ex-mill, exclusive of GST.
2. **Standard Bag Packing**: Explicit declaration of the $45.360\text{ Kg}$ bag tare standard ($24\text{ cones} \times 1.890\text{ Kg}$).
3. **Payment & Credit Terms**: Agreed payment timeframe (e.g. Net 30 Days LC / PDC).
4. **Quality Benchmark**: Reference to SITRA / Uster test standards (Count CV%, CSP, IPI).
5. **Validity & Market Fluctuation**: Clear specification of the contract start and end dates.

---

## 8. Dual Signatory Blocks

To serve as an enforceable commercial instrument, the bottom of the document renders bilateral signature sections:
- **Enterprise Side**:
  - Signatory Line for Commercial Director / Procurement Head.
  - Name, Designation, Date, and Tirupur location.
- **Contracted Party Side**:
  - Counter-signature line for Spinning Mill General Manager / Customer Authorized Buyer.
  - Name, Designation, Date, and Mill location.

---

## 9. Next.js Component Breakdown

```
app/(app)/pricing/yarn-price-lists/[id]/print/
├── page.tsx                           # Print Controller with window.print() triggers
└── components/
    ├── PrintControlsHeader.tsx        # Screen-only toolbar: [<- Back], [Print Button], [Copy Selector]
    ├── CorporateLetterhead.tsx        # Enterprise address, GSTIN, CIN
    ├── RateCardHeaderDetails.tsx      # Dual party and contract metadata block
    ├── RateSchedulePrintTable.tsx     # Clean tabular schedule with volume slabs
    ├── CommercialCovenants.tsx        # Legal terms, packing standards, payment covenants
    └── DualSignatoryBlock.tsx         # Enterprise & Mill sign-off areas
```

---

## 10. Developer Acceptance Checklist

- [ ] Print preview displays cleanly on desktop and matches wireframe layout.
- [ ] Clicking **`[ PRINT RATE CARD ]`** immediately invokes `window.print()`.
- [ ] All interactive web elements (buttons, navigation bars, headers) disappear completely in print mode.
- [ ] Table headers repeat properly if the schedule spans across multiple pages.
- [ ] Number formats adhere strictly to Indian grouping (`12,34,567.89`) and 4 decimal places for rates (`₹340.0000`).
- [ ] Bag packing states the enterprise standard of `45.360 Kg`.
- [ ] Corporate letterhead dynamically renders active tenant details.
