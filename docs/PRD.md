# PRD — Garments ERP & CRM (v1.0, status: ACTIVE)

## 1. Goals / Non-Goals
### Goals
- Enterprise-grade, multi-tenant ERP system for textile and garment manufacturers.
- Support complete manufacturing lifecycle: Procurement (Yarn PO), Godown Stock Ledger, Inwards (GRN), Outwards (DC for Knitting & Dyeing), Sales Invoicing (GST compliant), and Customer Sales Returns.
- Maintain double-entry ledger invariants, row-level concurrency locks (`select_for_update()`), and atomic rollback capabilities.
- Multi-company data isolation with granular role-based access control (RBAC) and active financial year scoping.

### Non-Goals
- Microservices architecture (this is strictly a single, cohesive monolith).
- Direct ORM queries or business logic inside controllers/views.

## 2. Users and Roles
- **SuperAdmin (`SUPER_ADMIN`)**: Platform operator; oversees all tenant companies, master settings, and company admins.
- **Company Admin (`ADMIN_USER`)**: Manages own company settings, branches, financial years, roles, employees, and privileges.
- **Company User (`COMPANY_USER`)**: Operational staff (procurement officers, storekeepers, sales representatives) restricted by role privileges.

## 3. Company Setup
- **Country Pack**: IN (India)
- **Currency**: INR (₹)
- **Taxation**: Indian GST (CGST, SGST, IGST)
- **Date Format**: DD/MM/YYYY
- **Financial Year Cycle**: April 1 to March 31 (e.g. `2025-2026`)

## 4. Modules & User Stories

### 4.1 Master Data Governance
- **Parties**: Mills, Traders, Dyers, Knitters, and Customers with GST/PAN validation.
- **Yarn & Fabric Catalog**: Yarn count, yarn composition, colors/shades, fabric structures, GSM, Dia, and Gauge.
- **Godowns / Warehouses**: Multi-location inventory storage management.
- **Quality Sizing Programs**: Box and carton breakdown configurations with nested multi-size ratios.

### 4.2 Procurement & Purchase Orders
- **US-4.2.1 (PO Creation)**: Given an active company and financial year, when a user issues a yarn PO with line items and split delivery schedules, then the system records the PO in Draft status with auto-computed line totals.
- **US-4.2.2 (PO Authorization)**: Given a draft PO, when an authorized officer approves the PO, then the PO is locked against direct edits.
- **US-4.2.3 (Unmanaged Balance Reporting)**: Given approved POs and inward receipts, the system maintains real-time balance tracking via `yarn_po_balance_table`.

### 4.3 Inventory Engine & Godown Stock Ledger
- **US-4.3.1 (GRN Inward)**: Given an authorized PO, when yarn bags arrive at the godown, the user posts a GRN Inward, crediting the godown ledger (`tm_yarn_stock`) and reducing PO balance.
- **US-4.3.2 (Delivery Challan Outward)**: Given available godown stock, when yarn is dispatched for knitting, dyeing, or sales, the system validates both bag count and weight (preventing negative stock) and decrements the balance.
- **US-4.3.3 (Atomic Cancellation & Rollback)**: When an Inward or Outward entry is cancelled, the system atomically rolls back stock adjustments and restores PO balances using row-level database locks.

### 4.4 Commercial Sales & Customer Returns
- **US-4.4.1 (Sales Tax Invoice)**: Given customer orders, the sales team issues commercial invoices calculating CGST, SGST, or IGST, deducting stock from the designated godown.
- **US-4.4.2 (Customer Sales Return)**: When goods are returned by a client, the return is accepted, re-crediting physical bags and weight back into active godown stock.

## 5. Reports
- PO Status and Balance Ledger.
- Godown Stock Register (Gross, Tare, Net Weight, and Bag counts).
- Inward GRN vs Outward DC Reconciliation.
- Sales and GST Tax Register.

## 6. Integrations
- REST API integration for web application, mobile warehouse terminals, and external accounting systems.

## 7. Non-Functional Requirements
- **Response Time**: < 200ms for read endpoints; < 500ms for multi-item atomic transactions.
- **Concurrency**: Safe multi-user stock deductions via `select_for_update()`.
- **Auditability**: Complete audit logs (`created_by`, `updated_by`, `deleted_by`) on all transactional and master records.

## 8. Version History
| Version | Date | Change | Approved by |
|---|---|---|---|
| v1.0 | 03/10/2026 | Initial PRD baseline and module definitions | Product Owner |
