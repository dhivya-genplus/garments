# Tracker — Garments ERP & CRM

| Product | Client | PRD version | Workflow setup version | Current release | Next release |
|---|---|---|---|---|---|
| Garments ERP | Enterprise Garments | v1.0 | kit-1.0 | v1.0.0 | v1.1.0 |

Status values: Not started • Ready • In progress • In review • Testing • Revision • Blocked • Merged • Deployed

## Modules
| # | Module | Status | Gate passed on | UAT sign-off |
|---|---|---|---|---|
| 0 | Foundation & Multi-Tenancy | Deployed | 03/10/2026 | Yes |
| 1 | Authentication & RBAC | Deployed | 03/10/2026 | Yes |
| 2 | Master Data Governance | Deployed | 03/10/2026 | Yes |
| 3 | Procurement (Yarn PO) | Deployed | 03/10/2026 | Yes |
| 4 | Inventory & Godown Stock Ledger | Deployed | 03/10/2026 | Yes |
| 5 | Commercial Sales & Customer Returns | Deployed | 03/10/2026 | Yes |
| 6 | Knitting & Grey Fabric Production | Deployed | 05/10/2026 | Yes |
| 7 | Production Process Engine (Knitting, Dyeing, Cutting) | Deployed | 05/10/2026 | Yes |
| 8 | Dual Stock & Currency Ledger Engine | Deployed | 05/10/2026 | Yes |
| 9 | Commercial Pricing & Job Work Valuation Engine | Ready | 14/10/2026 | Pending |

## Tickets
| Ticket | Module | Title | PRD ref | Status | Owner | Agent | Branch / PR | E2E | Reviewer | Release | AI usage | Notes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| T9-001 | 9 | Unified Price Lists (Purchase, Sales, Job Work, Party & General) | §4.5 | Merged | Pricing Team | Builder-API | main | Yes | Lead | v1.2.0 | High | tm_price_list, tm_price_list_item, tm_price_list_job_rule, ta_pricing_audit, seed_defaults |
| T9-002 | 9 | Job Work Subcontract Conversion Rate Engine & Multi-Tier Resolution API | §4.5 | In review | Pricing Team | Builder-API | feature/T9-002-engine | Yes | Lead | v1.2.0 | High | /api/v1/pricing/resolve/ (Yarn & Job Work), job-rules CRUD, 13 automated tests passed |
| T0-001 | 0 | Workspace, base models, standard JSON envelope | §1 | Merged | Core Team | Architect | main | Yes | Lead | v1.0.0 | High | TimeStamped, SoftDelete, Uppercase |
| T0-002 | 0 | Tenant & Financial Year Middleware | §3 | Merged | Core Team | Builder-API | main | Yes | Lead | v1.0.0 | High | TenantMiddleware, X-Company-ID |
| T1-001 | 1 | Custom User, Role, Privilege, SimpleJWT Auth | §2 | Merged | Auth Team | Builder-API | main | Yes | Lead | v1.0.0 | High | 18 permission modules |
| T1-002 | 1 | Dual-route aliases and CORS header support | §2 | Merged | Auth Team | Builder-API | main | Yes | Lead | v1.0.0 | High | /api/v1/auth/login direct route |
| T2-001 | 2 | Textile Masters (Parties, Yarn, Fabric, Process, Godowns) | §4.1 | Merged | Masters Team | Builder-API | main | Yes | Lead | v1.0.0 | High | UOM, Counts, Colors, Fabrics |
| T2-002 | 2 | Quality Program carton nested sizing | §4.1 | Merged | Masters Team | Builder-API | main | Yes | Lead | v1.0.0 | High | Box ratios, nested serializers |
| T2-003 | 2 | Tax Master & GST Engine (0%, 5%, 12%, 18%, 28%, HSN/SAC) | §4.1 | Merged | Masters Team | Builder-API | main | Yes | Lead | v1.1.0 | High | mx_tax, TaxEngine, seed_defaults |
| T3-001 | 3 | Yarn Purchase Orders with split delivery schedules | §4.2 | Merged | PO Team | Builder-API | main | Yes | Lead | v1.0.0 | High | Draft, auto FY resolution |
| T3-002 | 3 | PO Authorization locking and soft-delete safeguards | §4.2 | Merged | PO Team | Builder-API | main | Yes | Lead | v1.0.0 | High | Prevents delete of active POs |
| T3-003 | 3 | Yarn PO live balance database view scoping | §4.2 | Merged | PO Team | Builder-API | main | Yes | Lead | v1.0.0 | High | Scoped to active company POs |
| T3-004 | 3 | Company-Configurable Multi-Type Yarn POs (Melange, Blended, Wound, etc.) | §4.2 | Merged | PO Team | Builder-API | main | Yes | Lead | v1.1.0 | High | tc_company_yarn_type, dynamic conditional validation |
| T4-001 | 4 | Live Godown Stock Ledger (Bags & Weight tracking) | §4.3 | Merged | Inv Team | Builder-API | main | Yes | Lead | v1.0.0 | High | tm_yarn_stock atomic locks |
| T4-002 | 4 | Inward GRN with Multi-Type Yarn Specs, GST Tax & PO deduction | §4.3 | Merged | Inv Team | Builder-API | main | Yes | Lead | v1.1.0 | High | child_yarn_inward_table, technical specs, TaxEngine |
| T4-003 | 4 | Delivery Challan Outward with bag non-negative check | §4.3 | Merged | Inv Team | Builder-API | main | Yes | Lead | v1.0.0 | High | Prevents bag underflow |
| T4-004 | 4 | Atomic cancellation and stock rollback | §4.3 | Merged | Inv Team | Builder-API | main | Yes | Lead | v1.0.0 | High | cancel_inward, cancel_outward |
| T5-001 | 5 | Commercial Sales Tax Invoices & Stock Deductions | §4.4 | Merged | Sales Team | Builder-API | main | Yes | Lead | v1.1.0 | High | GST taxes (CGST/SGST/IGST), child_yarn_sales |
| T5-002 | 5 | Customer Sales Returns with GST Tax & Stock Re-crediting | §4.4 | Merged | Sales Team | Builder-API | main | Yes | Lead | v1.1.0 | High | Re-credits physical stock, GST TaxEngine |
| T5-003 | 5 | Sales and Sales Return atomic cancellation workflows | §4.4 | Merged | Sales Team | Builder-API | main | Yes | Lead | v1.0.0 | High | cancel_sales, cancel_sales_return |
| T6-001 | 6 | Knitting Program (Job Card) planning & requirement engine | §4.3 | Merged | Knitting Team | Builder-API | main | Yes | Lead | v1.1.0 | High | tm_knitting_program, loss % |
| T6-002 | 6 | Live Grey Fabric Stock Ledger (Rolls & Kg tracking) | §4.3 | Merged | Knitting Team | Builder-API | main | Yes | Lead | v1.1.0 | High | tm_grey_fabric_stock locks |
| T6-003 | 6 | Grey Fabric Inward GRN with process loss & job charges | §4.3 | Merged | Knitting Team | Builder-API | main | Yes | Lead | v1.1.0 | High | tm_grey_fabric_inward |
| T6-004 | 6 | Grey Fabric Outward DC for Dyeing & Knitter Return | §4.3 | Merged | Knitting Team | Builder-API | main | Yes | Lead | v1.1.0 | High | tm_grey_fabric_outward |
| T6-005 | 6 | Grey Fabric PO for direct trader procurement | §4.3 | Merged | Knitting Team | Builder-API | main | Yes | Lead | v1.1.0 | High | tm_grey_po |
| T6-006 | 6 | Grey Fabric Commercial Sales & Customer Sales Returns | §4.3 | Merged | Knitting Team | Builder-API | main | Yes | Lead | v1.1.0 | High | tm_grey_fabric_sales, returns, live stock deduction |
| T7-001 | 7 | Unified Production Process Engine (Stages, Programs, Routing) | §4.5 | Merged | Process Team | Builder-API | main | Yes | Lead | v1.1.0 | High | mx_process_stage, tm_process_program, dynamic routing |
| T8-001 | 8 | Dual Stock & Currency Ledger Engine (In/Out, Dr/Cr) | §4.6 | Merged | Ledger Team | Builder-API | main | Yes | Lead | v1.1.0 | High | tl_stock_movement, tm_stage_stock, tl_voucher, tl_voucher_line |
| T8-002 | 8 | Party Financial Ledger Maintenance & Payment Workflows | §4.6 | Merged | Ledger Team | Builder-API | main | Yes | Lead | v1.1.0 | High | Opening balance, date range filter, payment/receipt recording, auto-posting from Sales & GRN |
| T8-003 | 8 | Transaction Against in Party Ledger & Party Filtering in Stock Ledger | §4.6 | Merged | Ledger Team | Builder-API | main | Yes | Lead | v1.1.0 | High | StockMovementFilterSet (party, party_id, date), party-summary endpoint, transaction_against tracking |


## Revisions
| ID | Ticket | Type (bug/polish/change) | Source | Raised | Resolved | PRD version |
|---|---|---|---|---|---|---|
| REV-01 | T1-002 | bug | API Testing | 03/10/2026 | 03/10/2026 | v1.0 |
| REV-02 | T4-002 | bug | Data Audit | 03/10/2026 | 03/10/2026 | v1.0 |
| REV-03 | T4-003 | bug | Invariant Audit | 03/10/2026 | 03/10/2026 | v1.0 |
| REV-04 | T4-004 | bug | QA Testing | 03/10/2026 | 03/10/2026 | v1.0 |
| REV-05 | T2-002 | bug | UI Integration | 03/10/2026 | 03/10/2026 | v1.0 |
