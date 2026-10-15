# UI Specification & Frontend Development Guidelines — Garments ERP & CRM

| Standard Code | Target Platform | Architecture Standard | Version | Effective Date | Status |
|---|---|---|---|---|---|
| **STD-UI-001** | Next.js 14 (App Router) + Django REST Monolith | Decoupled UI consuming fixed API contract | `v1.0.0` | 15/10/2026 | **APPROVED & MANDATORY** |

---

## 1. Purpose and Scope

These guidelines establish the **mandatory standards, structural blueprints, architectural patterns, and quality gates** for designing, documenting, and implementing all user interfaces in the Garments ERP & CRM platform.

Every frontend developer, UI/UX architect, and AI agent must adhere to these rules without exception. No screen development may commence until its specification achieves **100% Spec Readiness** under these guidelines.

---

## 2. The 4-Screen Standard Suite Pattern for Transactional Modules

For every operational transaction entity in the system (e.g. Yarn Purchase Order, Yarn Inward GRN, Yarn Outward DC, Sales Tax Invoice, Sales Return, Knitting Program, Grey Fabric GRN), the documentation and implementation must deliver a **complete 4-screen suite**:

```
+--------------------------------------------------------------------------------------------------+
|                            THE 4-SCREEN TRANSACTIONAL SUITE PATTERN                              |
+--------------------------------------------------------------------------------------------------+
|  1. ADD WORKFLOW (/new)        --> High-speed entry form with dynamic specs & live keystroke math|
|  2. EDIT SCREEN (/[id]/edit)   --> State-dependent locking, consumption check & atomic reversals|
|  3. REGISTER LIST (/)          --> KPI telemetry cards, status tabs, search drawer & bulk actions|
|  4. PRINT DOCUMENT (/[id]/print)--> A4 portrait printable sheet, statutory GST & 4-tier signatories|
+--------------------------------------------------------------------------------------------------+
```

### 2.1 Screen Responsibilities Matrix

| # | Screen Role | URL Convention | Core Responsibilities |
|---|---|---|---|
| **1** | **Add Workflow** | `/[module]/[entity]/new` | Data entry, dynamic fields, multi-count matrix, client validation, Save Draft vs Save & Submit. |
| **2** | **Edit Screen** | `/[module]/[entity]/[id]/edit` | Data hydration, draft modification, state-dependent locking, downstream stock consumption checks. |
| **3** | **Register List** | `/[module]/[entity]` | Real-time KPI cards, status tabs (`All`, `Posted`, `Draft`), multi-parameter filters, CSV/Excel export. |
| **4** | **Print Document** | `/[module]/[entity]/[id]/print` | ISO A4 Portrait layout, `@media print` rules, statutory letterhead, GST distribution, multi-tier sign-off. |

---

## 3. The 21-Section Standard Specification Template

All future specification documents (whether for Outward DC, Sales Invoice, or Knitting Program) must follow this exact **21-section sequence** established by the Yarn PO and Yarn Inward specifications:

```
 1. Document Overview, Version, Scope, and Status
 2. Module Details, Screen ID, Route, Access Privileges, and API Endpoints
 3. UI Layout, Screen Blueprint, and Visual Mockup (1440px+ wireframe)
 4. Page Initialization, Query Parameters, and Default Form State
 5. Document Header, Fiscal Context, and Financial Year Configuration
 6. Primary Master Linkages (Vendor, Mill, Godown, Customer, Subcontractor)
 7. Dynamic Technical Specifications (Conditional fields based on Category)
 8. Interactive Spreadsheet Data Grid & Line Items
 9. Mathematical Formulas & Keystroke Calculation Engine
10. Godown / Warehouse Stock Allocation & Storage Location
11. Summary Bar, Remarks, Gate Pass Details, and Total Calculations
12. Form Validation Rules and Error Messages (Field-by-Field Matrix)
13. Lifecycle Workflows (Save as Draft, Save & Post, Authorize, Cancel)
14. API Integration, Request Headers, Payload Serialization, and HTTP Errors
15. Next.js Folder Structure and Component Responsibilities
16. React Hooks, TypeScript Types, Zod Schemas, and Form State
17. Factory Floor & Weighbridge Keyboard Ergonomics (Shortcuts)
18. Loading States, Shimmer Skeletons, Success Feedback, and Failure Handling
19. Security, Tenant Scoping, and Backend Invariant Validation Requirements
20. Implementation Sequence and Developer Acceptance Checklist
21. Existing Inconsistencies, Edge Cases, and Items Requiring Confirmation
```

---


## 4. Enterprise UI Invariants (Non-Negotiable Rules)

### 4.1 Country Pack `IN` (India Standard)
1. **Currency**:
   - Always formatted in Indian Rupees (**₹**) with Indian number grouping:
     $$\text{Example: } ₹12,34,567.89 \quad (\text{Lakhs and Crores grouping, NOT } 1,234,567.89)$$
2. **Date & Time**:
   - Calendar dates: **`DD/MM/YYYY`** (e.g. `15/10/2026`).
   - Timestamps: **`DD/MM/YYYY HH:MM`** (24-hour).
   - ISO formats (`YYYY-MM-DD`) are strictly internal for API JSON payloads and must never be displayed to users.
3. **Weight & Bag Standards**:
   - Textile bag weight defaults to **`45.360 Kg`** (or `50.000 Kg`).
   - Weights displayed to **3 decimal places** (`4,536.000 Kg`).
   - Currency rates displayed to **2 decimal places** (`₹350.00`).
4. **Indian GST Tax Engine**:
   - Intra-state transaction ($\text{Company State} == \text{Party State}$): Split into **CGST (half rate)** and **SGST (half rate)**.
   - Inter-state transaction ($\text{Company State} \ne \text{Party State}$): Single **IGST (full rate)**.

### 4.2 Security & Tenant Invariants
1. **Tenant Isolation**:
   - Never accept or pass `company_id` in request bodies.
   - Injected exclusively via authenticated session and header `X-Company-ID`.
2. **Financial Year Immutability**:
   - All transactions must validate that document dates fall within `active_financial_year.start_date` and `end_date`.
   - Never allow entry into locked or closed financial years unless the user holds the `backdate_entry` privilege.
3. **Double Invariant Enforcement**:
   - Every client calculation (Quantity, Rates, Taxes, Totals) must be verified server-side inside `@transaction.atomic`.

---

## 5. Frontend Technical Architecture Guidelines

### 5.1 Technology Stack Selection
- **Framework**: Next.js 14 App Router (`app/(auth)/`, `app/(app)/[module]/`).
- **Language**: TypeScript 5 with strict null checks (`strict: true`). Zero `any` usage.
- **Form State**: `react-hook-form` with uncontrolled inputs for zero typing latency.
- **Validation**: `zod` schemas with custom `.superRefine()` rules for conditional validation.
- **Server Queries**: TanStack Query v5 (React Query) with 300ms search debounce.

### 5.2 Component Structure Convention

```
app/(app)/[module]/[entity]/[action]/
├── page.tsx                           # Master page orchestrator & query state
├── components/
│   ├── [Entity]HeaderCard.tsx         # Document header & fiscal context
│   ├── [Entity]VendorCard.tsx         # Party, mill & godown allocation
│   ├── [Entity]TechSpecsCard.tsx      # Dynamic category fields
│   ├── [Entity]LineItemsGrid.tsx      # Spreadsheet matrix container
│   ├── [Entity]LineItemRow.tsx        # Individual row with cell keyboard handlers
│   ├── [Entity]TaxSummaryCard.tsx     # Tax breakdown & net payable
│   └── [Entity]StickyFooterBar.tsx    # Bottom aggregate bar & action buttons
├── hooks/
│   ├── use[Entity]Form.ts             # Form state & calculation listeners
│   └── use[Entity]Masters.ts          # Asynchronous master data queries
└── types/
    └── [entity].types.ts              # TypeScript DTOs and Form values
```

---

## 6. Factory Floor & Weighbridge Ergonomics (Keyboard Shortcuts)

Factory gate and warehouse environments prioritize keyboard-only data entry:

| Shortcut | Scope | Behavior |
|---|---|---|
| `Tab` | Form Cells | Advances focus horizontally to the next input cell. |
| `Shift + Tab` | Form Cells | Moves focus backwards to the previous cell. |
| `Enter` | Table Row | Commits cell value, triggers line math, and advances to next column. |
| `Enter` (Last cell) | Table Grid | Commits row, automatically appends a new item row, and focuses first input. |
| `Alt + N` | Global Page | Appends a new item row to the line items grid. |
| `Alt + S` | Global Page | Triggers **Save as Draft** (`is_authorized: 0`). |
| `Alt + Enter` | Global Page | Triggers **Save & Post / Authorize** (`is_authorized: 1`). |
| `/` | List Pages | Focuses the Quick Search input box. |
| `F` | List Pages | Toggles open the Multi-Parameter Filter Drawer. |
| `Esc` | Global Page | Closes open modals/drawers or triggers unsaved change discard prompt. |

---

## 7. Quality Gate: Definition of Ready (DoR) Checklist

Before any screen specification is marked as **`Complete`** in [UI_TRACKER.md](UI_TRACKER.md), it must satisfy this 8-point checklist:

- [ ] **1. 21-Section Compliance**: All 21 standard sections are present and fully fleshed out.
- [ ] **2. Model & API Accuracy**: Field names match backend Django models and DRF serializers exactly.
- [ ] **3. Dynamic Specs Defined**: Conditional visibility matrix defined for every category variant.
- [ ] **4. Keystroke Math Formalized**: LaTeX mathematical formulas provided for all line and header totals.
- [ ] **5. Zod Schema Written**: Complete, copy-paste ready Zod schema with `.superRefine()` provided.
- [ ] **6. Wireframe Blueprint Provided**: Desktop layout ASCII diagram provided with column widths and breakpoints.
- [ ] **7. Downstream Safeguards Addressed**: Edit/Cancel workflows verify live stock and PO balance restitution.
- [ ] **8. Country Pack Compliant**: Verified for INR `₹`, `DD/MM/YYYY`, standard bags, and Indian GST rules.
