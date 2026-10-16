# UI Page-by-Page Specifications — Garments ERP & CRM

This directory contains the authoritative screen-by-screen UI specifications for the Garments ERP & CRM web application. Each document details the layout blueprint, design tokens, component breakdown, interactive states, responsive behavior, mathematical formulas, TypeScript interfaces, Zod validation schemas, and API contract bindings for a specific screen.

> [!TIP]
> For the comprehensive high-level dashboard, development roadmap, and cross-module tracking table, see the master [UI_TRACKER.md](../UI_TRACKER.md). All specifications adhere to the standard 21-section template in [UI_SPECIFICATION_AND_DEVELOPMENT_GUIDELINES.md](../UI_SPECIFICATION_AND_DEVELOPMENT_GUIDELINES.md).

---

## Screen Directory & Status Tracker (40 / 40 Complete — 100% Specification Readiness)

| Screen ID | Page Name | Module | Route | Status | Spec Document |
|---|---|---|---|---|---|
| **`SCR-AUTH-001`** | **User Login & Session Scoping** | `Module 1: Authentication` | `/login` | ✅ Complete | [01_LOGIN_UI_SPECIFICATION.md](01_LOGIN_UI_SPECIFICATION.md) |
| **`SCR-AUTH-002`** | **Password Reset & Credential Recovery** | `Module 1: Authentication` | `/forgot-password` | ✅ Complete | [39_FORGOT_PASSWORD_UI_SPECIFICATION.md](39_FORGOT_PASSWORD_UI_SPECIFICATION.md) |
| **`SCR-COMP-001`** | **Company Profile, Tax & Financial Years** | `Module 0: Foundation` | `/administration/company` | ✅ Complete | [02_COMPANY_UI_SPECIFICATION.md](02_COMPANY_UI_SPECIFICATION.md) |
| **`SCR-DASH-001`** | **Executive Operations & Telemetry Dashboard** | `Module 0: Foundation` | `/dashboard` | ✅ Complete | [38_DASHBOARD_UI_SPECIFICATION.md](38_DASHBOARD_UI_SPECIFICATION.md) |
| **`SCR-MAST-001`** | **Party Master (Mills, Dyers, Knitters, Clients)** | `Module 2: Masters` | `/masters/parties` | ✅ Complete | [29_PARTY_MASTER_UI_SPECIFICATION.md](29_PARTY_MASTER_UI_SPECIFICATION.md) |
| **`SCR-MAST-002`** | **Yarn & Fabric Master Catalog** | `Module 2: Masters` | `/masters/yarn-catalog` | ✅ Complete | [30_YARN_CATALOG_UI_SPECIFICATION.md](30_YARN_CATALOG_UI_SPECIFICATION.md) |
| **`SCR-MAST-003`** | **Godown / Warehouse Locations Master** | `Module 2: Masters` | `/masters/godowns` | ✅ Complete | [31_GODOWNS_MASTER_UI_SPECIFICATION.md](31_GODOWNS_MASTER_UI_SPECIFICATION.md) |
| **`SCR-PROC-001-ADD`** | **Yarn Purchase Order (PO) Add Workflow** | `Module 3: Procurement` | `/procurement/yarn-po/new` | ✅ Complete | [03_YARN_PO_ADD_WORKFLOW_SPECIFICATION.md](03_YARN_PO_ADD_WORKFLOW_SPECIFICATION.md) |
| **`SCR-PROC-001-EDIT`**| **Yarn Purchase Order (PO) Edit Screen** | `Module 3: Procurement` | `/procurement/yarn-po/[id]/edit` | ✅ Complete | [04_YARN_PO_EDIT_WORKFLOW_SPECIFICATION.md](04_YARN_PO_EDIT_WORKFLOW_SPECIFICATION.md) |
| **`SCR-PROC-001-LIST`**| **Yarn Purchase Order (PO) List & Register** | `Module 3: Procurement` | `/procurement/yarn-po` | ✅ Complete | [05_YARN_PO_LIST_WORKFLOW_SPECIFICATION.md](05_YARN_PO_LIST_WORKFLOW_SPECIFICATION.md) |
| **`SCR-PROC-001-PRINT`**|**Yarn Purchase Order (PO) Print / PDF** | `Module 3: Procurement` | `/procurement/yarn-po/[id]/print` | ✅ Complete | [06_YARN_PO_PRINT_DOCUMENT_SPECIFICATION.md](06_YARN_PO_PRINT_DOCUMENT_SPECIFICATION.md) |
| **`SCR-INVN-001-ADD`** | **Yarn Inward (GRN) Add Workflow** | `Module 4: Inventory` | `/inventory/yarn-inward/new` | ✅ Complete | [07_YARN_INWARD_ADD_WORKFLOW_SPECIFICATION.md](07_YARN_INWARD_ADD_WORKFLOW_SPECIFICATION.md) |
| **`SCR-INVN-001-EDIT`**| **Yarn Inward (GRN) Edit Screen** | `Module 4: Inventory` | `/inventory/yarn-inward/[id]/edit` | ✅ Complete | [08_YARN_INWARD_EDIT_WORKFLOW_SPECIFICATION.md](08_YARN_INWARD_EDIT_WORKFLOW_SPECIFICATION.md) |
| **`SCR-INVN-001-LIST`**| **Yarn Inward (GRN) List & Register** | `Module 4: Inventory` | `/inventory/yarn-inward` | ✅ Complete | [09_YARN_INWARD_LIST_WORKFLOW_SPECIFICATION.md](09_YARN_INWARD_LIST_WORKFLOW_SPECIFICATION.md) |
| **`SCR-INVN-001-PRINT`**|**Yarn Inward (GRN) Print / PDF** | `Module 4: Inventory` | `/inventory/yarn-inward/[id]/print` | ✅ Complete | [10_YARN_INWARD_PRINT_DOCUMENT_SPECIFICATION.md](10_YARN_INWARD_PRINT_DOCUMENT_SPECIFICATION.md) |
| **`SCR-INVN-002-ADD`** | **Yarn Outward (DC) Add Workflow** | `Module 4: Inventory` | `/inventory/yarn-outward/new` | ✅ Complete | [11_YARN_OUTWARD_ADD_WORKFLOW_SPECIFICATION.md](11_YARN_OUTWARD_ADD_WORKFLOW_SPECIFICATION.md) |
| **`SCR-INVN-002-EDIT`**| **Yarn Outward (DC) Edit Screen** | `Module 4: Inventory` | `/inventory/yarn-outward/[id]/edit` | ✅ Complete | [12_YARN_OUTWARD_EDIT_WORKFLOW_SPECIFICATION.md](12_YARN_OUTWARD_EDIT_WORKFLOW_SPECIFICATION.md) |
| **`SCR-INVN-002-LIST`**| **Yarn Outward (DC) List & Register** | `Module 4: Inventory` | `/inventory/yarn-outward` | ✅ Complete | [13_YARN_OUTWARD_LIST_WORKFLOW_SPECIFICATION.md](13_YARN_OUTWARD_LIST_WORKFLOW_SPECIFICATION.md) |
| **`SCR-INVN-002-PRINT`**|**Yarn Outward (DC) Print / PDF** | `Module 4: Inventory` | `/inventory/yarn-outward/[id]/print` | ✅ Complete | [14_YARN_OUTWARD_PRINT_DOCUMENT_SPECIFICATION.md](14_YARN_OUTWARD_PRINT_DOCUMENT_SPECIFICATION.md) |
| **`SCR-INVN-003`** | **Live Godown Stock Ledger & Register** | `Module 4: Inventory` | `/inventory/stock-ledger` | ✅ Complete | [27_STOCK_LEDGER_UI_SPECIFICATION.md](27_STOCK_LEDGER_UI_SPECIFICATION.md) |
| **`SCR-INVN-004`** | **Party Stock Ledger & Job Work Reconciliation** | `Module 4: Inventory` | `/inventory/party-stock-ledger` | ✅ Complete | [28_PARTY_STOCK_LEDGER_UI_SPECIFICATION.md](28_PARTY_STOCK_LEDGER_UI_SPECIFICATION.md) |
| **`SCR-SALE-001-ADD`** | **Yarn Sales (Invoice) Add Workflow** | `Module 5: Commercial Sales` | `/sales/yarn-sales/new` | ✅ Complete | [15_YARN_SALES_ADD_WORKFLOW_SPECIFICATION.md](15_YARN_SALES_ADD_WORKFLOW_SPECIFICATION.md) |
| **`SCR-SALE-001-EDIT`**| **Yarn Sales (Invoice) Edit Screen** | `Module 5: Commercial Sales` | `/sales/yarn-sales/[id]/edit` | ✅ Complete | [16_YARN_SALES_EDIT_WORKFLOW_SPECIFICATION.md](16_YARN_SALES_EDIT_WORKFLOW_SPECIFICATION.md) |
| **`SCR-SALE-001-LIST`**| **Yarn Sales (Invoice) List & Register**| `Module 5: Commercial Sales` | `/sales/yarn-sales` | ✅ Complete | [17_YARN_SALES_LIST_WORKFLOW_SPECIFICATION.md](17_YARN_SALES_LIST_WORKFLOW_SPECIFICATION.md) |
| **`SCR-SALE-001-PRINT`**|**Yarn Sales (Invoice) Print / PDF** | `Module 5: Commercial Sales` | `/sales/yarn-sales/[id]/print` | ✅ Complete | [18_YARN_SALES_PRINT_DOCUMENT_SPECIFICATION.md](18_YARN_SALES_PRINT_DOCUMENT_SPECIFICATION.md) |
| **`SCR-SALE-002-ADD`** | **Yarn Sales Return Add Workflow** | `Module 5: Commercial Sales` | `/sales/yarn-sales-returns/new` | ✅ Complete | [19_YARN_SALES_RETURN_ADD_WORKFLOW_SPECIFICATION.md](19_YARN_SALES_RETURN_ADD_WORKFLOW_SPECIFICATION.md) |
| **`SCR-SALE-002-EDIT`**| **Yarn Sales Return Edit Screen** | `Module 5: Commercial Sales` | `/sales/yarn-sales-returns/[id]/edit` | ✅ Complete | [20_YARN_SALES_RETURN_EDIT_WORKFLOW_SPECIFICATION.md](20_YARN_SALES_RETURN_EDIT_WORKFLOW_SPECIFICATION.md) |
| **`SCR-SALE-002-LIST`**| **Yarn Sales Return List & Register**| `Module 5: Commercial Sales` | `/sales/yarn-sales-returns` | ✅ Complete | [21_YARN_SALES_RETURN_LIST_WORKFLOW_SPECIFICATION.md](21_YARN_SALES_RETURN_LIST_WORKFLOW_SPECIFICATION.md) |
| **`SCR-SALE-002-PRINT`**|**Yarn Sales Return (Credit Note) Print**| `Module 5: Commercial Sales` | `/sales/yarn-sales-returns/[id]/print` | ✅ Complete | [22_YARN_SALES_RETURN_PRINT_DOCUMENT_SPECIFICATION.md](22_YARN_SALES_RETURN_PRINT_DOCUMENT_SPECIFICATION.md) |
| **`SCR-KNIT-001`** | **Knitting Program Job Card Planning** | `Module 6: Knitting` | `/production/knitting-program` | ✅ Complete | [32_KNITTING_PROGRAM_UI_SPECIFICATION.md](32_KNITTING_PROGRAM_UI_SPECIFICATION.md) |
| **`SCR-KNIT-001-PRINT`**|**Knitting Program Print / PDF Job Card**| `Module 6: Knitting` | `/production/knitting-program/[id]/print` | ✅ Complete | [40_KNITTING_PROGRAM_PRINT_DOCUMENT_SPECIFICATION.md](40_KNITTING_PROGRAM_PRINT_DOCUMENT_SPECIFICATION.md) |
| **`SCR-KNIT-002`** | **Grey Fabric Inward, Outward & Live Stock** | `Module 6: Knitting` | `/production/grey-fabric` | ✅ Complete | [33_GREY_FABRIC_UI_SPECIFICATION.md](33_GREY_FABRIC_UI_SPECIFICATION.md) |
| **`SCR-PRCS-001`** | **Production Process Routing & Subcontracting** | `Module 7: Process Engine` | `/production/process-routing` | ✅ Complete | [34_PROCESS_ROUTING_UI_SPECIFICATION.md](34_PROCESS_ROUTING_UI_SPECIFICATION.md) |
| **`SCR-FINL-001`** | **Party Financial Ledger & Reconciliation** | `Module 8: Ledgers` | `/ledgers/party-ledger` | ✅ Complete | [35_PARTY_FINANCIAL_LEDGER_UI_SPECIFICATION.md](35_PARTY_FINANCIAL_LEDGER_UI_SPECIFICATION.md) |
| **`SCR-FINL-002`** | **General Ledger & Multi-Period Trial Balance** | `Module 8: Ledgers` | `/ledgers/trial-balance` | ✅ Complete | [36_TRIAL_BALANCE_UI_SPECIFICATION.md](36_TRIAL_BALANCE_UI_SPECIFICATION.md) |
| **`SCR-PRIC-001-ADD`** | **Yarn Price List Add Workflow** | `Module 9: Pricing` | `/pricing/yarn-price-lists/new` | ✅ Complete | [23_YARN_PRICE_LIST_ADD_WORKFLOW_SPECIFICATION.md](23_YARN_PRICE_LIST_ADD_WORKFLOW_SPECIFICATION.md) |
| **`SCR-PRIC-001-EDIT`**| **Yarn Price List Edit & Revision** | `Module 9: Pricing` | `/pricing/yarn-price-lists/[id]/edit` | ✅ Complete | [24_YARN_PRICE_LIST_EDIT_WORKFLOW_SPECIFICATION.md](24_YARN_PRICE_LIST_EDIT_WORKFLOW_SPECIFICATION.md) |
| **`SCR-PRIC-001-LIST`**| **Yarn Price List Register & Management**| `Module 9: Pricing` | `/pricing/yarn-price-lists` | ✅ Complete | [25_YARN_PRICE_LIST_LIST_WORKFLOW_SPECIFICATION.md](25_YARN_PRICE_LIST_LIST_WORKFLOW_SPECIFICATION.md) |
| **`SCR-PRIC-001-PRINT`**|**Yarn Price List (Rate Card) Print**| `Module 9: Pricing` | `/pricing/yarn-price-lists/[id]/print` | ✅ Complete | [26_YARN_PRICE_LIST_PRINT_DOCUMENT_SPECIFICATION.md](26_YARN_PRICE_LIST_PRINT_DOCUMENT_SPECIFICATION.md) |
| **`SCR-PRIC-002`** | **Job Work Subcontract Conversion Matrix** | `Module 9: Pricing` | `/pricing/job-work-rules` | ✅ Complete | [37_JOB_WORK_MATRIX_UI_SPECIFICATION.md](37_JOB_WORK_MATRIX_UI_SPECIFICATION.md) |

---

## Design System Standards

All screen designs adhere to the following unified principles:
1. **Curated Color Tokens**: Midnight slate backdrops (`#0B0F19`), high-contrast card surfaces (`#FFFFFF`), vibrant Indigo/Violet primary gradients (`#4F46E5` -> `#7C3AED`), and functional status indicators (Emerald `#10B981` for active/sync, Rose `#EF4444` for alerts).
2. **Typography Scale**: Clean geometric sans-serif (Inter / Outfit) with strict hierarchy (Heading 24px/32px, Labels 13px Semibold, Body 14px, Captions 12px).
3. **Enterprise Invariants**: All forms display currency in **INR (₹)** with Indian numerical grouping (`12,34,567.89`), dates formatted as **`DD/MM/YYYY`**, and require active company and financial year scoping.
4. **Responsive Breakpoints**: Seamless scaling across Desktop (≥1280px), Laptop (1024px–1279px), Tablet (768px–1023px), and Mobile (<768px).
