# Master UI & Frontend Workflow Tracking Document — Garments ERP & CRM

| Project | Client | Platform Stack | PRD Reference | Tracker Version | Last Updated |
|---|---|---|---|---|---|
| **Garments ERP & CRM** | Enterprise Garments | Next.js 14 (App Router) + DRF API | v1.2 | `v1.0.0` | 15/10/2026 |

---

## 1. Executive Summary & Telemetry Dashboard

This document serves as the authoritative, centralized tracking register for all **Server-Rendered UI Screens, Frontend Workflows, Component Architectures, API Contract Bindings, and End-to-End Test Statuses** across the Garments ERP & CRM application.

> [!TIP]
> **Excel Workbook Available**: An interactive, formatted multi-tab Excel spreadsheet version of this tracker is available at [GARMENTS_ERP_TRACKER.xlsx](GARMENTS_ERP_TRACKER.xlsx) (and [TRACKER.xlsx](TRACKER.xlsx)).
> 
> **Standard Guidelines**: All screen specifications and development workflows follow the mandatory standards in [UI_SPECIFICATION_AND_DEVELOPMENT_GUIDELINES.md](UI_SPECIFICATION_AND_DEVELOPMENT_GUIDELINES.md).

### 1.1 Progress Metrics at a Glance```
TOTAL IDENTIFIED SCREENS      : 30 Screens across 10 Enterprise Modules
TOTAL IDENTIFIED SCREENS      : 33 Screens across 10 Enterprise Modules
SPECIFICATIONS COMPLETED       : 22 Screens (66.7% Complete) [Yarn Procurement, Inward, Outward & Commercial Sales 100% Defined]
SPECIFICATIONS IN PROGRESS     : 0 Screens (0.0%)
SPECIFICATIONS PLANNED         : 11 Screens (33.3%)
BACKEND REST APIS DEPLOYED     : 100% Deployed & Tested (Django 5 + DRF LTS)
VISUAL MOCKUP BLUEPRINTS       : 7 Generated & Stored in docs/assets/ui/
```

### 1.2 Module-by-Module Specification Progress

```
[Module 0] Foundation & Multi-Tenancy     : [██████████░░░░░░░░░░] 50% (1/2 Screens)
[Module 1] Authentication & RBAC           : [██████████░░░░░░░░░░] 50% (1/2 Screens)
[Module 2] Master Data Governance          : [░░░░░░░░░░░░░░░░░░░░]  0% (0/3 Screens)
[Module 3] Procurement (Yarn PO)           : [████████████████████] 100% (4/4 Screens) - READY FOR DEV
[Module 4] Inventory (Yarn Inward & Outward): [█████████████████░] 88.9% (8/9 Screens) - READY FOR DEV
[Module 5] Commercial Sales & Invoicing    : [████████████████████] 100% (8/8 Screens) - READY FOR DEV
[Module 6] Knitting & Fabric Production    : [░░░░░░░░░░░░░░░░░░░░]  0% (0/2 Screens)
[Module 7] Production Process Engine       : [░░░░░░░░░░░░░░░░░░░░]  0% (0/1 Screens)
[Module 8] Ledgers & Financial Accounting  : [░░░░░░░░░░░░░░░░░░░░]  0% (0/2 Screens)
[Module 9] Commercial Pricing Engine       : [░░░░░░░░░░░░░░░░░░░░]  0% (0/2 Screens)
```

---

## 2. Master Screen Registry & Tracking Table

Status Legend:
- `✅ Complete`: Technical specification fully written, reviewed, and ready for frontend implementation.
- `🔄 In Progress`: Technical specification currently being drafted.
- `⏳ Planned`: Scheduled for specification in upcoming sprints.
- `🎨 Mockup Ready`: High-fidelity visual mockup generated and committed in `docs/assets/ui/`.

| Screen ID | Module | Screen Name | Route Path | Spec Status | UI Mockup | API Status | Specification File | PRD Ref |
|---|---|---|---|---|---|---|---|---|
| **`SCR-AUTH-001`** | Mod 1 | **User Login & Session Scoping** | `/login` | ✅ Complete | 🎨 Mockup Ready | ✅ Deployed | [01_LOGIN_UI_SPECIFICATION.md](ui/01_LOGIN_UI_SPECIFICATION.md) | §2 |
| `SCR-AUTH-002` | Mod 1 | Password Reset & Recovery | `/forgot-password` | ⏳ Planned | ⏳ Pending | ✅ Deployed | `03_FORGOT_PASSWORD_UI_SPECIFICATION.md` | §2 |
| **`SCR-COMP-001`** | Mod 0 | **Company Profile, Tax & FY Setup**| `/administration/company` | ✅ Complete | 🎨 Mockup Ready | ✅ Deployed | [02_COMPANY_UI_SPECIFICATION.md](ui/02_COMPANY_UI_SPECIFICATION.md) | §3 |
| `SCR-DASH-001` | Mod 0 | Executive & Operations Dashboard | `/dashboard` | ⏳ Planned | ⏳ Pending | ✅ Deployed | `04_DASHBOARD_UI_SPECIFICATION.md` | §1 |
| `SCR-MAST-001` | Mod 2 | Party Master (Mills, Dyers, Knitters)| `/masters/parties` | ⏳ Planned | ⏳ Pending | ✅ Deployed | `05_PARTY_MASTER_UI_SPECIFICATION.md` | §4.1 |
| `SCR-MAST-002` | Mod 2 | Yarn & Fabric Master Catalog | `/masters/yarn-catalog` | ⏳ Planned | ⏳ Pending | ✅ Deployed | `06_YARN_CATALOG_UI_SPECIFICATION.md` | §4.1 |
| `SCR-MAST-003` | Mod 2 | Godown / Warehouse Locations | `/masters/godowns` | ⏳ Planned | ⏳ Pending | ✅ Deployed | `07_GODOWNS_MASTER_UI_SPECIFICATION.md` | §4.1 |
| **`SCR-PROC-001-ADD`** | Mod 3 | **Yarn Purchase Order (PO) Add Workflow** | `/procurement/yarn-po/new` | ✅ Complete | 🎨 Mockup Ready | ✅ Deployed | [03_YARN_PO_ADD_WORKFLOW_SPECIFICATION.md](ui/03_YARN_PO_ADD_WORKFLOW_SPECIFICATION.md) | §4.2 |
| **`SCR-PROC-001-EDIT`**| Mod 3 | **Yarn Purchase Order (PO) Edit Screen** | `/procurement/yarn-po/[id]/edit` | ✅ Complete | 🎨 Mockup Ready | ✅ Deployed | [04_YARN_PO_EDIT_WORKFLOW_SPECIFICATION.md](ui/04_YARN_PO_EDIT_WORKFLOW_SPECIFICATION.md) | §4.2 |
| **`SCR-PROC-001-LIST`**| Mod 3 | **Yarn Purchase Order Register & List** | `/procurement/yarn-po` | ✅ Complete | 🎨 Mockup Ready | ✅ Deployed | [05_YARN_PO_LIST_WORKFLOW_SPECIFICATION.md](ui/05_YARN_PO_LIST_WORKFLOW_SPECIFICATION.md) | §4.2 |
| **`SCR-PROC-001-PRINT`**|Mod 3 | **Yarn Purchase Order Print / PDF Sheet**| `/procurement/yarn-po/[id]/print` | ✅ Complete | 🎨 Mockup Ready | ✅ Deployed | [06_YARN_PO_PRINT_DOCUMENT_SPECIFICATION.md](ui/06_YARN_PO_PRINT_DOCUMENT_SPECIFICATION.md) | §4.2 |
| **`SCR-INVN-001-ADD`** | Mod 4 | **Yarn Inward (GRN) Add Workflow** | `/inventory/yarn-inward/new` | ✅ Complete | 🎨 Mockup Ready | ✅ Deployed | [07_YARN_INWARD_ADD_WORKFLOW_SPECIFICATION.md](ui/07_YARN_INWARD_ADD_WORKFLOW_SPECIFICATION.md) | §4.3 |
| **`SCR-INVN-001-EDIT`**| Mod 4 | **Yarn Inward (GRN) Edit Screen** | `/inventory/yarn-inward/[id]/edit` | ✅ Complete | 🎨 Mockup Ready | ✅ Deployed | [08_YARN_INWARD_EDIT_WORKFLOW_SPECIFICATION.md](ui/08_YARN_INWARD_EDIT_WORKFLOW_SPECIFICATION.md) | §4.3 |
| **`SCR-INVN-001-LIST`**| Mod 4 | **Yarn Inward Register & List View** | `/inventory/yarn-inward` | ✅ Complete | 🎨 Mockup Ready | ✅ Deployed | [09_YARN_INWARD_LIST_WORKFLOW_SPECIFICATION.md](ui/09_YARN_INWARD_LIST_WORKFLOW_SPECIFICATION.md) | §4.3 |
| **`SCR-INVN-001-PRINT`**|Mod 4 | **Yarn Inward (GRN) Print / PDF Sheet** | `/inventory/yarn-inward/[id]/print` | ✅ Complete | 🎨 Mockup Ready | ✅ Deployed | [10_YARN_INWARD_PRINT_DOCUMENT_SPECIFICATION.md](ui/10_YARN_INWARD_PRINT_DOCUMENT_SPECIFICATION.md) | §4.3 |
| **`SCR-INVN-002-ADD`** | Mod 4 | **Yarn Outward (DC) Add Workflow** | `/inventory/yarn-outward/new` | ✅ Complete | 🎨 Mockup Ready | ✅ Deployed | [11_YARN_OUTWARD_ADD_WORKFLOW_SPECIFICATION.md](ui/11_YARN_OUTWARD_ADD_WORKFLOW_SPECIFICATION.md) | §4.3 |
| **`SCR-INVN-002-EDIT`**| Mod 4 | **Yarn Outward (DC) Edit Screen** | `/inventory/yarn-outward/[id]/edit` | ✅ Complete | 🎨 Mockup Ready | ✅ Deployed | [12_YARN_OUTWARD_EDIT_WORKFLOW_SPECIFICATION.md](ui/12_YARN_OUTWARD_EDIT_WORKFLOW_SPECIFICATION.md) | §4.3 |
| **`SCR-INVN-002-LIST`**| Mod 4 | **Yarn Outward Register & List View** | `/inventory/yarn-outward` | ✅ Complete | 🎨 Mockup Ready | ✅ Deployed | [13_YARN_OUTWARD_LIST_WORKFLOW_SPECIFICATION.md](ui/13_YARN_OUTWARD_LIST_WORKFLOW_SPECIFICATION.md) | §4.3 |
| **`SCR-INVN-002-PRINT`**|Mod 4 | **Yarn Outward (DC) Print / PDF Sheet** | `/inventory/yarn-outward/[id]/print` | ✅ Complete | 🎨 Mockup Ready | ✅ Deployed | [14_YARN_OUTWARD_PRINT_DOCUMENT_SPECIFICATION.md](ui/14_YARN_OUTWARD_PRINT_DOCUMENT_SPECIFICATION.md) | §4.3 |
| `SCR-INVN-003` | Mod 4 | Live Godown Stock Register (Bags/Kg)| `/inventory/stock-register` | ⏳ Planned | ⏳ Pending | ✅ Deployed | `19_STOCK_REGISTER_UI_SPECIFICATION.md` | §4.3 |
| **`SCR-SALE-001-ADD`** | Mod 5 | **Yarn Sales (Invoice) Add Workflow** | `/sales/yarn-sales/new` | ✅ Complete | 🎨 Mockup Ready | ✅ Deployed | [15_YARN_SALES_ADD_WORKFLOW_SPECIFICATION.md](ui/15_YARN_SALES_ADD_WORKFLOW_SPECIFICATION.md) | §4.4 |
| **`SCR-SALE-001-EDIT`**| Mod 5 | **Yarn Sales (Invoice) Edit Screen** | `/sales/yarn-sales/[id]/edit` | ✅ Complete | 🎨 Mockup Ready | ✅ Deployed | [16_YARN_SALES_EDIT_WORKFLOW_SPECIFICATION.md](ui/16_YARN_SALES_EDIT_WORKFLOW_SPECIFICATION.md) | §4.4 |
| **`SCR-SALE-001-LIST`**| Mod 5 | **Yarn Sales Register & List View** | `/sales/yarn-sales` | ✅ Complete | 🎨 Mockup Ready | ✅ Deployed | [17_YARN_SALES_LIST_WORKFLOW_SPECIFICATION.md](ui/17_YARN_SALES_LIST_WORKFLOW_SPECIFICATION.md) | §4.4 |
| **`SCR-SALE-001-PRINT`**|Mod 5 | **Yarn Sales Tax Invoice Print / PDF** | `/sales/yarn-sales/[id]/print` | ✅ Complete | 🎨 Mockup Ready | ✅ Deployed | [18_YARN_SALES_PRINT_DOCUMENT_SPECIFICATION.md](ui/18_YARN_SALES_PRINT_DOCUMENT_SPECIFICATION.md) | §4.4 |
| **`SCR-SALE-002-ADD`** | Mod 5 | **Yarn Sales Return Add Workflow** | `/sales/yarn-sales-returns/new` | ✅ Complete | 🎨 Mockup Ready | ✅ Deployed | [19_YARN_SALES_RETURN_ADD_WORKFLOW_SPECIFICATION.md](ui/19_YARN_SALES_RETURN_ADD_WORKFLOW_SPECIFICATION.md) | §4.4 |
| **`SCR-SALE-002-EDIT`**| Mod 5 | **Yarn Sales Return Edit Screen** | `/sales/yarn-sales-returns/[id]/edit` | ✅ Complete | 🎨 Mockup Ready | ✅ Deployed | [20_YARN_SALES_RETURN_EDIT_WORKFLOW_SPECIFICATION.md](ui/20_YARN_SALES_RETURN_EDIT_WORKFLOW_SPECIFICATION.md) | §4.4 |
| **`SCR-SALE-002-LIST`**| Mod 5 | **Yarn Sales Return List & Register**| `/sales/yarn-sales-returns` | ✅ Complete | 🎨 Mockup Ready | ✅ Deployed | [21_YARN_SALES_RETURN_LIST_WORKFLOW_SPECIFICATION.md](ui/21_YARN_SALES_RETURN_LIST_WORKFLOW_SPECIFICATION.md) | §4.4 |
| **`SCR-SALE-002-PRINT`**|Mod 5 | **Yarn Sales Return (Credit Note) Print**| `/sales/yarn-sales-returns/[id]/print` | ✅ Complete | 🎨 Mockup Ready | ✅ Deployed | [22_YARN_SALES_RETURN_PRINT_DOCUMENT_SPECIFICATION.md](ui/22_YARN_SALES_RETURN_PRINT_DOCUMENT_SPECIFICATION.md) | §4.4 |
| `SCR-KNIT-001` | Mod 6 | Knitting Program Job Card Planning | `/production/knitting-program`| ⏳ Planned | ⏳ Pending | ✅ Deployed | `23_KNITTING_PROGRAM_UI_SPECIFICATION.md`| §4.3 |
| `SCR-KNIT-002` | Mod 6 | Grey Fabric Inward & Outward Register| `/production/grey-fabric` | ⏳ Planned | ⏳ Pending | ✅ Deployed | `24_GREY_FABRIC_UI_SPECIFICATION.md` | §4.3 |
| `SCR-FINL-001` | Mod 8 | Party Financial Ledger & Reconciliation| `/ledgers/party-ledger` | ⏳ Planned | ⏳ Pending | ✅ Deployed | `25_PARTY_LEDGER_UI_SPECIFICATION.md` | §4.6 |
| `SCR-PRIC-001` | Mod 9 | Multi-Tier Price Lists & Slabs | `/pricing/price-lists` | ⏳ Planned | ⏳ Pending | ✅ Deployed | `26_PRICE_LISTS_UI_SPECIFICATION.md` | §4.5 |
| `SCR-PRIC-002` | Mod 9 | Job Work Subcontract Conversion Matrix| `/pricing/job-work-rules` | ⏳ Planned | ⏳ Pending | ✅ Deployed | `27_JOB_WORK_MATRIX_UI_SPECIFICATION.md` | §4.5 |

---

## 3. Deep-Dive Tracking: Procurement, Inward & Outward Lifecycle

The complete physical yarn lifecycle from Purchase Order through Weighbridge Inward to Processing Outward Dispatch is now **100% specified and production-ready**:

```mermaid
flowchart TD
    subgraph MODULE_3_PROCUREMENT [Module 3: Procurement]
        A["SCR-PROC-001-ADD<br>Yarn PO Creation"] -->|is_authorized=0| B["SCR-PROC-001-LIST<br>PO Register / Drafts"]
        A -->|is_authorized=1| C["SCR-PROC-001-PRINT<br>Authorized PO Print Sheet"]
        B -->|Unlock / Edit| D["SCR-PROC-001-EDIT<br>PO Revision & Schedules"]
    end

    subgraph MODULE_4_INVENTORY [Module 4: Godown Inventory]
        C -->|Physical Goods Arrive| E["SCR-INVN-001-ADD<br>Yarn Inward GRN Creation"]
        E -->|Weighbridge Gross-Tare| F["SCR-INVN-001-LIST<br>Inward Register / Gate Pass"]
        E -->|Print Copy| G["SCR-INVN-001-PRINT<br>4-Tier Signed GRN Sheet"]
        F -->|Reversal Safeguard| H["SCR-INVN-001-EDIT<br>GRN Edit / Cancel Safeguard"]
    end

    subgraph BACKEND_ENGINES [Backend Ledger Invariants]
        E -->|Atomic Row Lock| I["Live Stock Ledger<br>tm_yarn_stock"]
        E -->|Auto-Deduct| J["PO Balance Register<br>child_po_table (remaining_bag)"]
        E -->|Voucher Post| K["Financial Ledger<br>CurrencyLedgerService"]
    end

    classDef complete fill:#ecfdf5,stroke:#10b981,stroke-width:2px;
    classDef engine fill:#eff6ff,stroke:#3b82f6,stroke-width:2px;
    class A,B,C,D,E,F,G,H complete;
    class I,J,K engine;
```

### 3.1 Procurement Suite Verification Status (`Module 3`)

| Component / Feature | Spec Reference | Key Invariants Verified | Frontend Dev Status |
|---|---|---|---|
| **PO Add Screen** | [§8-10 in 03_YARN_PO_ADD](ui/03_YARN_PO_ADD_WORKFLOW_SPECIFICATION.md) | Single/multi-count, split deliveries, bag tare 45.360 Kg, dynamic technical specs for Melange/Dyed | Ready for Component Scaffolding |
| **PO Edit Screen** | [§4-5 in 04_YARN_PO_EDIT](ui/04_YARN_PO_EDIT_WORKFLOW_SPECIFICATION.md) | State-dependent UI locking, inward received floor protection, re-open authorization safeguard | Ready for Component Scaffolding |
| **PO Register List** | [§5-7 in 05_YARN_PO_LIST](ui/05_YARN_PO_LIST_WORKFLOW_SPECIFICATION.md) | Telemetry KPI cards, status tabs, search debounce 300ms, batch actions | Ready for Component Scaffolding |
| **PO Print Sheet** | [§4-7 in 06_YARN_PO_PRINT](ui/06_YARN_PO_PRINT_DOCUMENT_SPECIFICATION.md) | ISO A4 Portrait `@media print`, dual vendor block, legal terms, authorized signature | Ready for Component Scaffolding |

### 3.2 Inventory Inward Suite Verification Status (`Module 4`)

| Component / Feature | Spec Reference | Key Invariants Verified | Frontend Dev Status |
|---|---|---|---|
| **Inward GRN Add** | [§6-9 in 07_YARN_INWARD_ADD](ui/07_YARN_INWARD_ADD_WORKFLOW_SPECIFICATION.md) | Multi-source (PO/Dyeing Return/Direct), dual-mode weighbridge math (Gross-Tare vs Bags*Nominal), GST distribution | Ready for Component Scaffolding |
| **Inward GRN Edit** | [§4-5 in 08_YARN_INWARD_EDIT](ui/08_YARN_INWARD_EDIT_WORKFLOW_SPECIFICATION.md) | Downstream stock consumption check, reversal block if stock issued, PO balance restitution | Ready for Component Scaffolding |
| **Inward Register** | [§5-6 in 09_YARN_INWARD_LIST](ui/09_YARN_INWARD_LIST_WORKFLOW_SPECIFICATION.md) | Total bags & net weight KPIs, stock posted vs draft gate passes, filter drawer | Ready for Component Scaffolding |
| **Inward Print Sheet** | [§4-7 in 10_YARN_INWARD_PRINT](ui/10_YARN_INWARD_PRINT_DOCUMENT_SPECIFICATION.md) | A4 sheet, 4-tier signatories (Gate, Scale, Store, Approver), moisture & package sign-off | Ready for Component Scaffolding |

### 3.3 Inventory Outward Suite Verification Status (`Module 4`)

| Component / Feature | Spec Reference | Key Invariants Verified | Frontend Dev Status |
|---|---|---|---|
| **Outward DC Add** | [§6-9 in 11_YARN_OUTWARD_ADD](ui/11_YARN_OUTWARD_ADD_WORKFLOW_SPECIFICATION.md) | Outward type selection (Knitting, Dyeing, Purchase Return), live stock validation against `tm_yarn_stock`, lot & bag tare math, atomic stock deduction | Ready for Component Scaffolding |
| **Outward DC Edit** | [§4-5 in 12_YARN_OUTWARD_EDIT](ui/12_YARN_OUTWARD_EDIT_WORKFLOW_SPECIFICATION.md) | State-dependent UI locking, incoming receipt safeguard (`received_quantity > 0` blocks cancel), atomic stock reversal on cancellation | Ready for Component Scaffolding |
| **Outward Register** | [§5-6 in 13_YARN_OUTWARD_LIST](ui/13_YARN_OUTWARD_LIST_WORKFLOW_SPECIFICATION.md) | Telemetry KPIs, multi-tab filtering (Knitting, Dyeing, Returns, Pending at Processor), batch print/export | Ready for Component Scaffolding |
| **Outward Print Sheet** | [§4-7 in 14_YARN_OUTWARD_PRINT](ui/14_YARN_OUTWARD_PRINT_DOCUMENT_SPECIFICATION.md) | ISO A4 Portrait Delivery Challan complying with CGST Rule 55 (Job Work, not for sale), transport & E-Way Bill block, 4-tier signatories | Ready for Component Scaffolding |

### 3.4 Commercial Yarn Sales Suite Verification Status (`Module 5`)

| Component / Feature | Spec Reference | Key Invariants Verified | Frontend Dev Status |
|---|---|---|---|
| **Yarn Sales Add** | [§6-9 in 15_YARN_SALES_ADD](ui/15_YARN_SALES_ADD_WORKFLOW_SPECIFICATION.md) | Buyer master linkage, live godown stock validation (`tm_yarn_stock`), intra/inter state GST computation (`TaxEngine`), atomic stock deduction & ledger posting | Ready for Component Scaffolding |
| **Yarn Sales Edit** | [§4-5 in 16_YARN_SALES_EDIT](ui/16_YARN_SALES_EDIT_WORKFLOW_SPECIFICATION.md) | State-dependent UI locking, customer sales return dependency safeguard, atomic stock reversal and voucher reversal on cancellation | Ready for Component Scaffolding |
| **Yarn Sales Register**| [§5-6 in 17_YARN_SALES_LIST](ui/17_YARN_SALES_LIST_WORKFLOW_SPECIFICATION.md) | Revenue & weight KPIs, status tabs (`All`, `Grey`, `Dyed`, `Drafts`, `Cancelled`), 300ms debounced search, batch export | Ready for Component Scaffolding |
| **Tax Invoice Print** | [§4-6 in 18_YARN_SALES_PRINT](ui/18_YARN_SALES_PRINT_DOCUMENT_SPECIFICATION.md) | Statutory CGST Rule 46 Tax Invoice (A4 Portrait), toggleable copies (Recipient, Transporter, Supplier), HSN 5205 tax schedule, bank remittance | Ready for Component Scaffolding |

### 3.5 Customer Yarn Sales Return Suite Verification Status (`Module 5`)

| Component / Feature | Spec Reference | Key Invariants Verified | Frontend Dev Status |
|---|---|---|---|
| **Sales Return Add** | [§6-9 in 19_YARN_SALES_RETURN_ADD](ui/19_YARN_SALES_RETURN_ADD_WORKFLOW_SPECIFICATION.md) | Invoice linkage, return ceiling check ($\le$ billed qty), live stock re-crediting (`tm_yarn_stock`), GST tax credit reversal, credit note ledger voucher | Ready for Component Scaffolding |
| **Sales Return Edit**| [§4-5 in 20_YARN_SALES_RETURN_EDIT](ui/20_YARN_SALES_RETURN_EDIT_WORKFLOW_SPECIFICATION.md) | State-dependent UI locking, downstream stock consumption check (blocks cancellation if stock re-issued), atomic stock/voucher reversal | Ready for Component Scaffolding |
| **Returns Register** | [§5-6 in 21_YARN_SALES_RETURN_LIST](ui/21_YARN_SALES_RETURN_LIST_WORKFLOW_SPECIFICATION.md) | Credit value & return rate KPIs, filter tabs (`Against Invoice`, `Direct`, `Shade Defect`), 300ms debounced search, batch Excel export | Ready for Component Scaffolding |
| **Credit Note Print**| [§4-6 in 22_YARN_SALES_RETURN_PRINT](ui/22_YARN_SALES_RETURN_PRINT_DOCUMENT_SPECIFICATION.md) | Statutory CGST Rule 53 Credit Note (A4 Portrait), toggleable copies, original invoice reference, HSN 5205 credit schedule, legal declaration | Ready for Component Scaffolding |

---

## 4. Frontend Technology Stack & Architecture Standards

All frontend implementations adhere strictly to the following architectural guidelines:

| Technology Layer | Standard | Details |
|---|---|---|
| **Framework** | Next.js 14+ | App Router architecture (`app/(auth)/`, `app/(app)/`) |
| **Language** | TypeScript 5.x | Strict type safety, explicit DTO interfaces, zero `any` usage |
| **Styling** | Vanilla CSS / TailwindCSS | High-contrast enterprise design tokens, responsive breakpoints |
| **Form Handling** | React Hook Form | High-performance uncontrolled inputs with microsecond keystroke math |
| **Schema Validation**| Zod 3.x | Comprehensive client-side schemas matching Django model invariants |
| **Server State** | TanStack Query v5 | Automated cache invalidation, parallel master hydration, optimistic updates |
| **Icons** | Lucide React | Clean, modern iconography |
| **Country Pack** | `IN` (India) | Currency `₹` (INR), Indian grouping (`12,34,567.89`), Date `DD/MM/YYYY` |

---

## 5. Development Sprint Roadmap & Milestone Plan

```
[SPRINT 1: CORE FOUNDATION & PROCUREMENT SUITE] - IN PROGRESS
├── Milestone 1.1: Authentication & Company Settings (SCR-AUTH-001, SCR-COMP-001) - Specs Complete
├── Milestone 1.2: Yarn PO Complete Suite (Add, Edit, List, Print) - Specs Complete
├── Milestone 1.3: Yarn Inward GRN Complete Suite (Add, Edit, List, Print) - Specs Complete
└── Milestone 1.4: Yarn Outward DC Complete Suite (Add, Edit, List, Print) - Specs Complete

[SPRINT 2: MASTER DATA & GODOWN STOCK ENGINE] - SCHEDULED NEXT
├── Milestone 2.1: Party Masters & Yarn/Fabric Catalog (SCR-MAST-001, SCR-MAST-002, SCR-MAST-003)
└── Milestone 2.2: Live Godown Stock Register (Bags & Weight live balances) (SCR-INVN-003)

[SPRINT 3: COMMERCIAL SALES & FABRIC PRODUCTION] - IN PROGRESS
├── Milestone 3.1: Commercial Yarn Sales Tax Invoice Suite (SCR-SALE-001-ADD/EDIT/LIST/PRINT) - Specs Complete
├── Milestone 3.2: Customer Yarn Sales Return Suite (SCR-SALE-002-ADD/EDIT/LIST/PRINT) - Specs Complete
└── Milestone 3.3: Knitting Program & Grey Fabric Inward/Outward (SCR-KNIT-001, SCR-KNIT-002)

[SPRINT 4: PRICING ENGINE & FINANCIAL RECONCILIATION] - PLANNED
├── Milestone 4.1: Unified Multi-Tier Price Lists & Job Work Pricing (SCR-PRIC-001, SCR-PRIC-002)
└── Milestone 4.2: Party Financial Ledger & Trial Balance (SCR-FINL-001, SCR-FINL-002)
```

---

## 6. Review & Audit Sign-Off

| Milestone | Reviewer | Verification Scope | Date | Sign-Off Status |
|---|---|---|---|---|
| **Module 3: Yarn PO Specs** | Tech Lead & QA Architect | 4 Specifications (Add, Edit, List, Print) + Schemas | 15/10/2026 | ✅ APPROVED |
| **Module 4: Yarn Inward Specs**| Tech Lead & Inventory Lead | 4 Specifications (Add, Edit, List, Print) + Schemas | 15/10/2026 | ✅ APPROVED |
| **Module 4: Yarn Outward Specs**| Tech Lead & Inventory Lead | 4 Specifications (Add, Edit, List, Print) + Schemas | 15/10/2026 | ✅ APPROVED |
| **Module 5: Yarn Sales Specs** | Tech Lead & Commercial Head| 4 Specifications (Add, Edit, List, Print) + Schemas | 15/10/2026 | ✅ APPROVED |
| **Module 5: Yarn Returns Specs**| Tech Lead & Commercial Head| 4 Specifications (Add, Edit, List, Print) + Schemas | 15/10/2026 | ✅ APPROVED |
| **API Contract Synchrony** | Backend Lead (Builder-API) | Endpoints, query parameters, payloads & error codes | 15/10/2026 | ✅ SYNCHRONIZED |
| **Country Pack Compliance** | Financial Controller | Indian GST, HSN codes, Indian number grouping, FY | 15/10/2026 | ✅ COMPLIANT |
