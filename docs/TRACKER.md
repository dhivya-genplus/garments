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

## Tickets
| Ticket | Module | Title | PRD ref | Status | Owner | Agent | Branch / PR | E2E | Reviewer | Release | AI usage | Notes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| T0-001 | 0 | Workspace, base models, standard JSON envelope | §1 | Merged | Core Team | Architect | main | Yes | Lead | v1.0.0 | High | TimeStamped, SoftDelete, Uppercase |
| T0-002 | 0 | Tenant & Financial Year Middleware | §3 | Merged | Core Team | Builder-API | main | Yes | Lead | v1.0.0 | High | TenantMiddleware, X-Company-ID |
| T1-001 | 1 | Custom User, Role, Privilege, SimpleJWT Auth | §2 | Merged | Auth Team | Builder-API | main | Yes | Lead | v1.0.0 | High | 18 permission modules |
| T1-002 | 1 | Dual-route aliases and CORS header support | §2 | Merged | Auth Team | Builder-API | main | Yes | Lead | v1.0.0 | High | /api/v1/auth/login direct route |
| T2-001 | 2 | Textile Masters (Parties, Yarn, Fabric, Process, Godowns) | §4.1 | Merged | Masters Team | Builder-API | main | Yes | Lead | v1.0.0 | High | UOM, Counts, Colors, Fabrics |
| T2-002 | 2 | Quality Program carton nested sizing | §4.1 | Merged | Masters Team | Builder-API | main | Yes | Lead | v1.0.0 | High | Box ratios, nested serializers |
| T3-001 | 3 | Yarn Purchase Orders with split delivery schedules | §4.2 | Merged | PO Team | Builder-API | main | Yes | Lead | v1.0.0 | High | Draft, auto FY resolution |
| T3-002 | 3 | PO Authorization locking and soft-delete safeguards | §4.2 | Merged | PO Team | Builder-API | main | Yes | Lead | v1.0.0 | High | Prevents delete of active POs |
| T3-003 | 3 | Yarn PO live balance database view scoping | §4.2 | Merged | PO Team | Builder-API | main | Yes | Lead | v1.0.0 | High | Scoped to active company POs |
| T4-001 | 4 | Live Godown Stock Ledger (Bags & Weight tracking) | §4.3 | Merged | Inv Team | Builder-API | main | Yes | Lead | v1.0.0 | High | tm_yarn_stock atomic locks |
| T4-002 | 4 | Inward GRN with child item persistence & PO deduction | §4.3 | Merged | Inv Team | Builder-API | main | Yes | Lead | v1.0.0 | High | child_yarn_inward_table |
| T4-003 | 4 | Delivery Challan Outward with bag non-negative check | §4.3 | Merged | Inv Team | Builder-API | main | Yes | Lead | v1.0.0 | High | Prevents bag underflow |
| T4-004 | 4 | Atomic cancellation and stock rollback | §4.3 | Merged | Inv Team | Builder-API | main | Yes | Lead | v1.0.0 | High | cancel_inward, cancel_outward |
| T5-001 | 5 | Commercial Sales Tax Invoices & Stock Deductions | §4.4 | Merged | Sales Team | Builder-API | main | Yes | Lead | v1.0.0 | High | GST taxes, child_yarn_sales |
| T5-002 | 5 | Customer Sales Returns & Stock Re-crediting | §4.4 | Merged | Sales Team | Builder-API | main | Yes | Lead | v1.0.0 | High | Re-credits physical stock |
| T5-003 | 5 | Sales and Sales Return atomic cancellation workflows | §4.4 | Merged | Sales Team | Builder-API | main | Yes | Lead | v1.0.0 | High | cancel_sales, cancel_sales_return |

## Revisions
| ID | Ticket | Type (bug/polish/change) | Source | Raised | Resolved | PRD version |
|---|---|---|---|---|---|---|
| REV-01 | T1-002 | bug | API Testing | 03/10/2026 | 03/10/2026 | v1.0 |
| REV-02 | T4-002 | bug | Data Audit | 03/10/2026 | 03/10/2026 | v1.0 |
| REV-03 | T4-003 | bug | Invariant Audit | 03/10/2026 | 03/10/2026 | v1.0 |
| REV-04 | T4-004 | bug | QA Testing | 03/10/2026 | 03/10/2026 | v1.0 |
| REV-05 | T2-002 | bug | UI Integration | 03/10/2026 | 03/10/2026 | v1.0 |
