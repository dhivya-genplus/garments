# UI & Document Layout Specification: Knitting Program (Job Card) Print & PDF Document

| Standard Code | Screen ID | Target Platform | API Version | Document Version | Date | Status |
|---|---|---|---|---|---|---|
| **STD-UI-001** | **`SCR-KNIT-001-PRINT`** | Next.js 14 (App Router) + TypeScript | `v1.2` (Django 5 DRF) | `v1.0.0` | 16/10/2026 | **APPROVED FOR IMPLEMENTATION** |

---

## 1. Document Overview, Version, Scope, and Status

### 1.1 Purpose
This specification defines the complete technical architecture, `@media print` styling rules, A4 portrait layout blueprint, technical machine settings, yarn feeder allocation matrix, QR code machine-scan bindings, Zod validation schema, TypeScript interfaces, and backend API integration for the **Knitting Program (Job Card) Commercial A4 Print & PDF Document** (`SCR-KNIT-001-PRINT`).

In the circular and flat knitting manufacturing ecosystem, the physical Knitting Job Card serves as the authoritative technical job contract issued to the knitting subcontractor (`KNITTING_UNIT`) or in-house machine floor:
1. **Machine Setup Technical Authority**: Communicating precise machine setup parameters to the knitting machine operator: Machine Diameter (Dia, e.g. 24", 30", 34"), Machine Gauge (e.g. 24GG, 28GG), Grams per Square Meter (GSM, e.g. 160, 180, 220), Loop/Stitch Length (e.g. 2.70 mm), and Needle Cam Timing.
2. **Feeder Breakdown & Yarn Composition**: Itemized yarn feeding instructions indicating exact counts (e.g. 30s Combed Cotton + 20D Spandex/Lycra), blend ratios ($95\% : 5\%$), feeder positioning (e.g. alternate feeders 1, 3, 5), and required gross yarn weights.
3. **Loss & Allowance Governance**: Formalizing the contractual process loss tolerance ($\text{Loss } \% \approx 2.0\% - 4.5\%$) and target greige roll count ($120\text{ Rolls}$).
4. **Commercial Job Work Contract**: Documenting the agreed subcontract knitting rate per Kg (in INR $₹$), GST tax terms, and Delivery Challan reference numbers.
5. **Shop-Floor QR Code Telemetry**: Embedding an ISO/IEC 18004 compliant QR code containing encrypted program metadata (`program_number`, `dia`, `gauge`, `target_kg`, `knitter_id`) for rapid handheld barcode scanning at circular knitting machine terminals and roll weigh scales.

### 1.2 Scope
- **Backend Models**: [`parent_knitting_program_table`](file:///d:/Codebase/Garments/backend/apps/knitting/models.py#L23-L146) (`tm_knitting_program`) and [`child_knitting_program_yarn_table`](file:///d:/Codebase/Garments/backend/apps/knitting/models.py#L147-L175) (`tx_knitting_program_yarn`).
- **Target Route**: `/production/knitting-program/[id]/print` (Next.js route: `app/(app)/production/knitting-program/[id]/print/page.tsx`).
- **Country Pack**: India (`IN`) — Indian Rupee (`₹`), Metric units (Kg, Rolls, Dia in inches, GSM in $\text{g/m}^2$, Loop length in mm), Date format (`DD/MM/YYYY`).
- **Paper Standard**: `ISO A4 Portrait (210mm x 297mm)`.

---

## 2. Module Details, Screen ID, Route, Access Privileges, and API Endpoints

### 2.1 Core Metadata

| Parameter | Specification |
|---|---|
| **Module** | `Module 6 — Knitting & Fabric Production` |
| **Screen ID** | `SCR-KNIT-001-PRINT` |
| **Frontend Route** | `/production/knitting-program/[id]/print` |
| **File Location** | `app/(app)/production/knitting-program/[id]/print/page.tsx` |
| **Required Privilege** | `knitting_program.can_print` (or `can_read`) |
| **Authorized Roles** | `SUPER_ADMIN`, `ADMIN_USER`, `COMPANY_USER` (Production Manager, Knitting Master, Merchandiser, Subcontractor Coordinator) |
| **Paper Standard** | `ISO A4 Portrait (210mm x 297mm)`, Print Margins: `8mm` (Top/Bottom/Left/Right) |
| **Country Pack** | `IN` (India: Currency INR `₹`, Date `DD/MM/YYYY`, Decimal precision: Weight 3 dp `0.000 Kg`, Money 2 dp `₹ 0.00`) |

### 2.2 Primary API Endpoints

| HTTP Method | API Path | Privilege / Scope | Description |
|---|---|---|---|
| `GET` | `/api/v1/knitting/programs/{id}/` | `can_read` | Fetch full program header, technical fabric parameters, feeder yarn lines, and status |
| `GET` | `/api/v1/administration/companies/{id}/` | `can_read` | Fetch tenant company letterhead, factory address, GSTIN, PAN, and corporate logo |
| `GET` | `/api/v1/knitting/programs/{id}/print-telemetry/` | `can_read` | Fetch live dispatched yarn bags and received greige roll weights for execution sheet |

---

## 3. UI Layout, Screen Blueprint, and Visual Mockup (A4 Portrait Wireframe)

```
+----------------------------------------------------------------------------------------------------+
| [SCREEN ONLY FLOATING TOOLBAR]      [<- Back]   [🖨 Print Job Card (Ctrl+P)]   [📥 Download PDF]   |
+----------------------------------------------------------------------------------------------------+
| ================================================================================================== |
| [LOGO: ABC TEXTILES]                 ABC TEXTILES PRIVATE LIMITED                                  |
|                                      Knitting & Processing Division: SF No. 412, Angeripalayam Rd, |
|                                      Tirupur, Tamil Nadu - 641603 | Phone: +91 421 2479000          |
|                                      GSTIN: 33AAAAA1234A1Z5 | PAN: AAAAA1234A | State Code: 33     |
| ================================================================================================== |
|                                KNITTING PROGRAM & TECHNICAL JOB CARD                               |
|                                                                                                    |
| Program No : KP-2026-0042                                  +-------------------------------------+ |
| Program Date: 16/10/2026                                   | QR CODE: [########]  PROGRAM STATUS: | |
| Delivery Due: 26/10/2026                                   | [########]           RELEASED        | |
| Fiscal Year : FY 2026-2027                                 | Scan for Loom Telemetry             | |
|                                                            +-------------------------------------+ |
| +---------------------------------------------------+----------------------------------------------+ |
| | KNITTING SUBCONTRACTOR (JOB WORKER)               | DESTINATION GODOWN / WAREHOUSE               | |
| | Unit Name: Sri Venkateswara Knitting Mills        | Godown : Main Greige Fabric Godown Unit-1    | |
| | Address  : 14/B, Shed-3, SIDCO Industrial Estate, | Address: ABC Textiles Logistics Park, Shed 4,| |
| |            KNP Colony, Coimbatore Rd, Tirupur     |          Angeripalayam, Tirupur - 641603     | |
| | Contact  : K. Palanisamy (+91 98422 12345)        | Contact: Storekeeper (+91 98422 99999)       | |
| | GSTIN    : 33AABCS9876Q1Z2 (State: 33 - TN)       | Inward Route: Via Factory Gate Pass Desk     | |
| +---------------------------------------------------+----------------------------------------------+ |
|                                                                                                    |
| SECTION A: TARGET FABRIC TECHNICAL SPECIFICATIONS                                                  |
| +---------------------------------------+------------------------------------+---------------------+ |
| | Target Fabric Name & Construction     | Fabric Structure / Knit Type       | Loop / Stitch Length| |
| | 100% Combed Cotton Single Jersey      | Single Jersey (Weft Knitted)       | 2.70 mm (Tolerance) | |
| +---------------------------------------+------------------------------------+---------------------+ |
| | Machine Diameter (Dia) : 30" (Inches) | Machine Gauge      : 24 GG         | Target GSM: 160 g/m²| |
| | Planned Roll Count     : 120 Rolls    | Net Fabric Target  : 2,400.000 Kg  | Exp. Loss : 2.50 %  |
| | Subcontract Rate / Kg  : ₹ 18.50 / Kg | Total Job Work Val : ₹ 44,400.00   | Gross Yarn: 2,460 Kg| |
| +---------------------------------------+------------------------------------+---------------------+ |
|                                                                                                    |
| SECTION B: YARN FEEDER BREAKDOWN & COMPOSITION ALLOCATION MATRIX                                   |
| +----+----------------------+-------------------+-----------+---------+------------+---------------+ |
| | #  | Yarn Count & Specs   | Shade / Colorway  | Category  | Blend % | Weight(Kg) | Feeder Alloc. | |
| +----+----------------------+-------------------+-----------+---------+------------+---------------+ |
| | 01 | 30s Combed Cotton    | Raw White / Greige| GREY      |  95.00% |  2,337.000 | Feeders 1..91 | |
| | 02 | 20D Spandex / Lycra  | Semi Dull         | SPANDEX   |   5.00% |    123.000 | Feeders Alt   | |
| +----+----------------------+-------------------+-----------+---------+------------+---------------+ |
| |    | TOTAL REQUIRED GROSS YARN WEIGHT (KG):   | 100.00% |  2,460.000 Kg | 96-Feeder Set |
| +----+------------------------------------------+-----------+---------+------------+---------------+ |
|                                                                                                    |
| SECTION C: TECHNICAL MACHINE SETUP & QUALITY INSTRUCTIONS                                          |
| 1. Machine Needle Timing: Synchronized gating. Cam setting adjusted for 2.70mm loop length.        |
| 2. Tension & Spirality Control: Maximum allowable spirality < 3.5%. Maintain uniform feeder tension.|
| 3. Lycra Attachment: Use positive Lycra feeder attachment. Verify stretch recovery before full run.|
| 4. Greige Roll Packing: Roll weight must target 20.00 Kg (+/- 1.5 Kg). Pack in HDPE tubing.         |
| 5. Process Loss Settlement: Any loss exceeding agreed 2.50% tolerance will be debited to job bill. |
|                                                                                                    |
| SECTION D: MATERIAL TRACKING & DISPATCH RECORD (SHOP FLOOR USE)                                     |
| +--------------------------+-----------------------------+---------------------------------------+ |
| | Yarn DC Outward No & Dt  | Dispatched Yarn Weight (Kg) | Received Fabric Weight & Rolls (Kg)   | |
| | [                        | [                           | [                                     | |
| +--------------------------+-----------------------------+---------------------------------------+ |
|                                                                                                    |
| SIGNATURE & AUTHORIZATION BLOCKS:                                                                  |
|                                                                                                    |
| __________________________      __________________________      __________________________         |
| Prepared By: Merchandiser       Knitting Master / Tech Head     Subcontractor Acceptance & Stamp   |
| (Arun Kumar - 16/10/2026)       (Senthil Nathan - 16/10/2026)   (Sri Venkateswara Knitting Mills)  |
|                                                                                                    |
| FOOTNOTE: Generated by Garments ERP Cloud | Print Ref: KP-2026-0042/P1 | Invariant Verified        |
+----------------------------------------------------------------------------------------------------+
```

---

## 4. UX Workflow, Step-by-Step Lifecycle, and Edge-Case Handling

### 4.1 Step-by-Step Lifecycle
1. **Triggering Print Mode**:
   - User navigates to `/production/knitting-program/[id]` and clicks **[Print Job Card (Ctrl+P)]**, or presses shortcut `Ctrl+P`.
   - The application renders `/production/knitting-program/[id]/print` with print-optimized stylesheets.
2. **Server-Side Hydration**:
   - Fetches target program record, knitter master profile, fabric specifications, feeder yarn allocations, and company letterhead.
   - Generates client-side QR code encoding technical parameters.
3. **Print Execution & PDF Generation**:
   - Browser print dialog opens via `window.print()`.
   - `@media print` rules strip screen toolbars, navigation sidebars, and URL headers.
   - Outputs an exact 1-page A4 sheet (or multi-page if feeder matrix exceeds 8 lines) with page-break controls.

### 4.2 Edge-Case Handling
- **Draft Program Print Warning**: If program is still in `DRAFT` status ($0$), a subtle watermark **`PRELIMINARY DRAFT — NOT FOR PRODUCTION`** is rendered at a $45^\circ$ angle across the sheet to prevent floor execution before release.
- **Multi-Count Blends**: For complex jacquard or stripe knitting programs with $>6$ yarn counts, the feeder table seamlessly paginates across 2 pages without clipping the signature block.
- **Zero Loss Edge Case**: If expected loss is set to $0.00\%$, total gross yarn calculates identically to net fabric quantity without division-by-zero errors.

---

## 5. Form Sections, Field Matrix, and Validation Rules

| Document Section | Field Description | Data Source | Formatting & Rules |
|---|---|---|---|
| **Letterhead** | Company Legal Name | `Company.name` | Uppercase bold, 16pt font |
| **Letterhead** | Factory Address & Phone | `Company.address`, `phone` | 9pt, Tirupur cluster format |
| **Letterhead** | GSTIN & PAN | `Company.tax_number`, `pan` | 15-character GSTIN, 10-char PAN |
| **Header Block** | Program Number | `tm_knitting_program.program_number` | Unique sequence `KP-YYYY-XXXX` |
| **Header Block** | Program Date & Delivery Due | `program_date`, `delivery_date` | `DD/MM/YYYY` Indian format |
| **Header Block** | Status Badge | `status` | `DRAFT`, `RELEASED`, `IN_PROGRESS` |
| **Party Block** | Knitter Unit Details | `knitter` (`PartyMaster`) | Trade Name, Address, Contact, GSTIN |
| **Party Block** | Receiving Godown | `warehouse` (`WarehouseMaster`) | Warehouse name, delivery instructions |
| **Technical Specs** | Fabric SKU & Structure | `FabricMaster`, `FabricTypeMaster` | e.g. "100% Combed Cotton Single Jersey" |
| **Technical Specs** | Machine Dia & Gauge | `dia`, `gauge` | e.g. 30" Dia, 24 GG |
| **Technical Specs** | Target GSM & Loop Length | `gsm`, `loop_length` | e.g. 160 GSM, 2.70 mm |
| **Technical Specs** | Planned Rolls & Weight | `planned_rolls`, `planned_fabric_qty` | Weight in `0.000 Kg`, Rolls Integer |
| **Technical Specs** | Expected Loss % & Gross Yarn | `expected_loss_percent`, `total_yarn_req` | Gross Yarn $= \text{Net} \times (1 + \text{Loss}\% / 100)$ |
| **Technical Specs** | Subcontract Knitting Rate | `knitting_rate` | INR format `₹ 18.50 / Kg` |
| **Feeder Matrix** | Feeder Rows (#1 to #N) | `tx_knitting_program_yarn` | Count SKU, Shade, Category, Blend %, Gross Wt |
| **Instructions** | Quality Parameters | Configurable template | Cam timing, spirality, roll packing |
| **Signatures** | Prepared, Tech, Knitter | Dynamic User & Party names | 3 equal-width signatory columns |

---

## 6. Mathematical Formulas and Calculation Specifications (LaTeX)

### 6.1 Total Gross Required Yarn Weight
Given target net fabric output $Q_{\text{fabric}}$ in kilograms and expected knitting process loss percentage $L_{\text{loss}}$:

$$Q_{\text{gross}} = \operatorname{Round}\left(Q_{\text{fabric}} \times \left(1 + \frac{L_{\text{loss}}}{100}\right), 3\right)$$

### 6.2 Line-Item Feeder Yarn Quantity
For each yarn feeder line $i \in \{1, \dots, n\}$ with blend percentage $B_i$:

$$Q_{\text{line}, i} = \operatorname{Round}\left(Q_{\text{gross}} \times \frac{B_i}{100}, 3\right)$$

$$\sum_{i=1}^{n} B_i \equiv 100.00\% \implies \sum_{i=1}^{n} Q_{\text{line}, i} \equiv Q_{\text{gross}}$$

### 6.3 Estimated Subcontract Job Work Amount
$$A_{\text{job}} = \operatorname{Round}\left(Q_{\text{fabric}} \times R_{\text{knitting}}, 2\right)$$

---

## 7. Dynamic Behaviors, Conditional Fields, and Interactivity

1. **Watermark Automation**:
   - `status === 0 (DRAFT)`: Displays prominent diagonal watermark: `DRAFT - NOT FOR PRODUCTION`.
   - `status === 1 (RELEASED)`: Displays official `RELEASED FOR YARN ISSUE` stamp.
   - `status === 4 (CANCELLED)`: Displays bold red `CANCELLED` banner.
2. **Interactive Print Controls**:
   - **Print Button**: Executes native `window.print()`.
   - **Download PDF**: Streams pre-generated server-side PDF via Weasyprint / Puppeteer.
   - **Barcode / QR Code Generator**: Generates SVG QR code containing JSON payload:
     ```json
     {"kp": "KP-2026-0042", "dia": "30\"", "gg": "24", "gsm": 160, "kg": 2400}
     ```

---

## 8. API Request / Response Contracts (DTOs)

### 8.1 Fetch Printable Knitting Program Payload (`GET /api/v1/knitting/programs/{id}/`)

```json
{
  "success": true,
  "data": {
    "id": 42,
    "program_number": "KP-2026-0042",
    "program_date": "16/10/2026",
    "delivery_date": "26/10/2026",
    "status": 1,
    "status_display": "RELEASED",
    "company": {
      "name": "ABC TEXTILES PRIVATE LIMITED",
      "address": "SF No. 412, Angeripalayam Road, Tirupur - 641603",
      "gstin": "33AAAAA1234A1Z5",
      "pan": "AAAAA1234A",
      "phone": "+91 421 2479000",
      "email": "production@abctextiles.com",
      "logo_url": "/assets/branding/abc_logo.png"
    },
    "knitter": {
      "name": "Sri Venkateswara Knitting Mills",
      "address": "14/B, SIDCO Industrial Estate, Coimbatore Rd, Tirupur",
      "contact_person": "K. Palanisamy",
      "phone": "+91 98422 12345",
      "gstin": "33AABCS9876Q1Z2"
    },
    "warehouse": {
      "name": "Main Greige Fabric Godown Unit-1",
      "address": "ABC Textiles Logistics Park, Shed 4, Tirupur"
    },
    "fabric": {
      "name": "100% Combed Cotton Single Jersey",
      "structure": "Single Jersey (Weft Knitted)",
      "dia": "30\"",
      "gauge": "24 GG",
      "gsm": 160,
      "loop_length": "2.70 mm",
      "planned_rolls": 120,
      "planned_fabric_quantity": "2400.000",
      "expected_loss_percent": "2.50",
      "total_yarn_required": "2460.000",
      "knitting_rate": "18.50",
      "total_knitting_amount": "44400.00"
    },
    "yarn_lines": [
      {
        "yarn_count_display": "30s Combed Cotton",
        "color_shade_name": "Raw White / Greige",
        "yarn_type": "GREY",
        "blend_ratio_percent": "95.00",
        "planned_quantity": "2337.000",
        "feeder_notes": "Feeders 1 to 91 (Positive Feeders)"
      },
      {
        "yarn_count_display": "20D Spandex / Lycra",
        "color_shade_name": "Semi Dull",
        "yarn_type": "SPANDEX",
        "blend_ratio_percent": "5.00",
        "planned_quantity": "123.000",
        "feeder_notes": "Alternate Feeders (Plating Attachment)"
      }
    ],
    "created_by": "arun.kumar",
    "technical_master": "Senthil Nathan P."
  }
}
```

---

## 9. Client-Side State Management and Component Architecture

```
app/(app)/production/knitting-program/[id]/print/
├── page.tsx                             # Server-side print document renderer
└── components/
    ├── PrintToolbar.tsx                 # Screen-only toolbar (Print, Download PDF, Back)
    ├── PrintCorporateHeader.tsx         # Corporate letterhead & mill branding
    ├── JobCardHeaderInfo.tsx            # Program #, Dates, QR Code, Knitter block
    ├── FabricSpecsPrintTable.tsx        # Dia, Gauge, GSM, Loop length, Loss %
    ├── FeederAllocationPrintTable.tsx   # Yarn feeder breakdown matrix
    ├── TechnicalInstructionsCard.tsx    # Needle timing, tension, roll packing rules
    └── PrintSignatoryBlocks.tsx         # Merchandiser, Tech Master, Knitter signature boxes
```

---

## 10. Zod Validation Schema (Copy-Paste Production Code)

```typescript
import { z } from "zod";

export const KnittingPrintParamSchema = z.object({
  id: z.string().regex(/^\d+$/, { message: "Program ID must be a valid numeric integer." }),
});

export type KnittingPrintParam = z.infer<typeof KnittingPrintParamSchema>;
```

---

## 11. TypeScript Interfaces & Enums (Complete DTO Declarations)

```typescript
export interface IKnittingPrintDataDTO {
  id: number;
  program_number: string;
  program_date: string;
  delivery_date?: string;
  status: number;
  status_display: string;
  company: {
    name: string;
    address: string;
    gstin: string;
    pan: string;
    phone: string;
    email: string;
    logo_url?: string;
  };
  knitter: {
    name: string;
    address: string;
    contact_person: string;
    phone: string;
    gstin?: string;
  };
  warehouse: {
    name: string;
    address: string;
  };
  fabric: {
    name: string;
    structure: string;
    dia: string;
    gauge: string;
    gsm: number;
    loop_length?: string;
    planned_rolls: number;
    planned_fabric_quantity: number;
    expected_loss_percent: number;
    total_yarn_required: number;
    knitting_rate: number;
    total_knitting_amount: number;
  };
  yarn_lines: Array<{
    yarn_count_display: string;
    color_shade_name?: string;
    yarn_type: string;
    blend_ratio_percent: number;
    planned_quantity: number;
    feeder_notes?: string;
  }>;
  created_by: string;
  technical_master?: string;
}
```

---

## 12. Keyboard Shortcuts and Rapid Operations

| Key Combination | Action / Trigger | Scope / View |
|---|---|---|
| `Ctrl + P` | Open Browser Native Print Dialog | Print Preview Screen |
| `Alt + D` | Download Generated PDF File | Print Preview Screen |
| `Esc` | Return to Program Details (`/production/knitting-program/[id]`) | Print Preview Screen |

---

## 13. `@media print` CSS Stylesheet Specification (Production Ready)

```css
@media print {
  /* Page Setup */
  @page {
    size: A4 portrait;
    margin: 8mm;
  }

  /* Reset layout */
  body {
    background: #ffffff !important;
    color: #000000 !important;
    font-size: 10pt;
    line-height: 1.3;
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  }

  /* Hide screen-only interactive elements */
  .no-print,
  nav,
  header,
  footer,
  aside,
  .print-toolbar {
    display: none !important;
  }

  /* Container bounds */
  .print-container {
    width: 100% !important;
    max-width: 100% !important;
    margin: 0 !important;
    padding: 0 !important;
    box-shadow: none !important;
    border: none !important;
  }

  /* Table borders */
  table {
    width: 100%;
    border-collapse: collapse !important;
    page-break-inside: auto;
  }

  tr {
    page-break-inside: avoid;
    page-break-after: auto;
  }

  th, td {
    border: 1px solid #475569 !important;
    padding: 4px 6px !important;
    font-size: 9pt !important;
  }

  th {
    background-color: #f1f5f9 !important;
    font-weight: 600;
    color: #0f172a !important;
    -webkit-print-color-adjust: exact;
    print-color-adjust: exact;
  }

  /* Watermark */
  .watermark {
    position: fixed;
    top: 40%;
    left: 20%;
    font-size: 52pt;
    font-weight: 800;
    color: rgba(203, 213, 225, 0.35) !important;
    transform: rotate(-35deg);
    z-index: -1;
    pointer-events: none;
    -webkit-print-color-adjust: exact;
    print-color-adjust: exact;
  }

  /* Signatures page-break defense */
  .signature-block {
    page-break-inside: avoid !important;
    margin-top: 24px;
  }
}
```

---

## 14. Error Handling and User Feedback

| Scenario / Error Trigger | Visual Presentation | Remediation Action |
|---|---|---|
| Program ID not found | Centered 404 card: *"Knitting Program not found"* | Provide back button to `/production/knitting-program` |
| Image/Logo failed to load | Fallback text rendered in letterhead box | Use text corporate title without broken icon |
| Incomplete yarn lines | Alert banner: *"Warning: Feeder yarn lines do not sum to 100%"* | Prompt user to edit program before printing |

---

## 15. Loading, Empty, and Edge States

- **Loading State**: Clean A4 white canvas with light gray shimmering wireframe rectangles for table and header.
- **Watermark States**:
  - `DRAFT`: Gray diagonal watermark *"DRAFT — NOT FOR PRODUCTION"*.
  - `CANCELLED`: Red diagonal watermark *"PROGRAM CANCELLED"*.
  - `RELEASED`: Clean document without watermark; green authorization stamp.

---

## 16. Accessibility (a11y) Conformance (WCAG 2.1 AA)

- Semantic HTML document structure (`<header>`, `<main>`, `<section>`, `<table>`, `<footer>`).
- Screen-only buttons have accessible aria labels (`aria-label="Print Knitting Job Card"`).
- High contrast black-on-white text ensures $100\%$ readability for colorblind operators.

---

## 17. Security, RBAC, and Audit Logging

- **Privilege Gate**: Only users holding `knitting_program.can_print` or `can_read` can view this endpoint.
- **Tenant Isolation**: Injected `company_id` strictly prevents printing another tenant's job cards.
- **Audit Logging**: Each print or PDF generation triggers a background audit event in `ta_audit_log` (`action: "PRINT_JOB_CARD"`, `document_id: id`).

---

## 18. Test Cases and Acceptance Criteria

### 18.1 Acceptance Criteria
1. Accessing `/production/knitting-program/42/print` renders an A4 document without sidebar navigation.
2. Clicking `Ctrl+P` opens the print dialog with document cleanly contained within 1 page for standard 2-feeder programs.
3. The printed QR code decodes to valid JSON containing Program Number and technical Dia/Gauge/GSM.
4. Total Gross Yarn calculates to $2,460.000\text{ Kg}$ for $2,400.000\text{ Kg}$ net fabric and $2.50\%$ loss.

---

## 19. Performance Budgets and Optimization Targets

- Server-side render time: $< 200\text{ms}$.
- Print CSS stylesheet size: $< 4\text{ KB}$.
- QR code rendering latency: $< 15\text{ms}$.

---

## 20. Future Enhancements and Scalability Roadmap

1. **Digital Subcontractor Signatures**: Direct touchscreen signature capture from knitter driver during yarn handover.
2. **Thermal Label Printing**: One-click printing of weather-resistant 4" x 6" roll tags directly from the job card.

---

## 21. Sign-off and Approval Matrix

| Stakeholder Role | Name / Title | Date | Signature / Status |
|---|---|---|---|
| **Production Head** | Ramanathan S. (VP Manufacturing) | 16/10/2026 | **APPROVED** |
| **Lead Architect** | Enterprise Garments Solutions | 16/10/2026 | **APPROVED** |
| **Knitting Master** | Senthil Nathan P. | 16/10/2026 | **APPROVED** |
