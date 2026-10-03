# Architecture — Garments ERP & CRM

Stack: Python 3.11+, Django 5.x, Django REST Framework 3.15+, PostgreSQL / SQLite  
Hosting: Gunicorn / Daphne + Nginx on Linux VPS (or Windows Server)  
Background Workers: Celery / Redis  
Client Layer: Next.js Web Frontend & Mobile Terminals via REST APIs  

---

## 1. Architectural Layers & Pattern

All business operations flow through four strict layers:

```
HTTP Request (Client)
    ↓
1. View Layer (APIView / ModelViewSet)
    - Validates request payload via Serializer
    - Extracts tenant context (get_company_id)
    - Calls Domain Service
    ↓
2. Service Layer (Domain Logic)
    - Enforces business rules & invariants
    - Coordinates multiple repositories
    - Wraps operations in @transaction.atomic with row-level locks
    ↓
3. Repository Layer (Data Access)
    - Direct Django ORM queries
    - Scopes by company and filters out soft-deleted records
    ↓
4. Model Layer (Database Entities)
    - Field definitions, audit tracking (TimeStampedModel, SoftDeleteModel)
    - Database constraints and indexes
```

---

## 2. Table Naming Conventions & Data Model

| Domain | Table Prefix | Table Name | Purpose |
|---|---|---|---|
| **System** | `sys_` | `sys_company` | Multi-tenant company account |
| **System** | `sys_` | `sys_financial_year` | Fiscal accounting years |
| **System** | `sys_` | `sys_role` | Roles grouping permissions |
| **System** | `sys_` | `sys_privilege` | Granular CRUD module privileges |
| **System** | `sys_` | `sys_user` | User entities |
| **Masters** | `tm_` | `tm_uom` | Units of measurement |
| **Masters** | `tm_` | `tm_party` | Mills, Traders, Dyers, Knitters, Customers |
| **Masters** | `tm_` | `tm_yarn_count` | Yarn counts (30s, 34s, 40s) |
| **Masters** | `tm_` | `tm_yarn_type` | Compositions |
| **Masters** | `tm_` | `tm_color` | Color shades |
| **Masters** | `tm_` | `tm_yarn` | Yarn SKUs |
| **Masters** | `tm_` | `tm_fabric_type` | Fabric structures |
| **Masters** | `tm_` | `tm_fabric` | Fabric SKUs with GSM, Dia, Gauge |
| **Masters** | `tm_` | `tm_process` | Process stages with loss % and rates |
| **Masters** | `tm_` | `tm_warehouse` | Godowns & warehouses |
| **Masters** | `tm_` | `tm_quality_program` | Garment box quality specifications |
| **Masters** | `tm_` | `tm_sub_quality_program` | Nested size breakdowns per box |
| **Procurement** | `tx_` | `tx_parent_po` | Purchase Order headers |
| **Procurement** | `tx_` | `tx_child_po` | Purchase Order line items |
| **Procurement** | `tx_` | `tx_delivery_schedule` | Split delivery date lots |
| **Procurement** | `vw_` | `view_yarn_po_balance` | Unmanaged live PO vs Inward balance view |
| **Inventory** | `tm_` | `tm_yarn_stock` | Godown Stock Ledger (Bags & Weight) |
| **Inventory** | `tx_` | `tx_parent_yarn_inward` | GRN Inward headers |
| **Inventory** | `tx_` | `tx_child_yarn_inward` | Inward line item breakdown |
| **Inventory** | `tx_` | `tx_parent_yarn_outward`| DC Outward headers |
| **Inventory** | `tx_` | `tx_child_yarn_outward`| Outward line item breakdown |
| **Sales** | `tx_` | `tx_parent_yarn_sales` | Commercial Sales tax invoice headers |
| **Sales** | `tx_` | `tx_child_yarn_sales` | Sales line item breakdown |
| **Sales** | `tx_` | `tx_parent_yarn_sales_return` | Sales Return headers |
| **Sales** | `tx_` | `tx_child_yarn_sales_return` | Return line item breakdown |

---

## 3. Decisions & Architectural Decision Records (ADR)

| # | Decision | Options Considered | Chosen | Why |
|---|---|---|---|---|
| **ADR-01** | Architecture Model | Microservices vs Monolith | Django Monolith | ERP transactions require atomic, multi-table ledger consistency and double-entry guarantees. |
| **ADR-02** | Layered Code Flow | Fat Models vs Viewsets vs Service/Repo | 4-Tier Layered Architecture | Separates HTTP adapters from domain calculations, making the system testable, maintainable, and audit-compliant. |
| **ADR-03** | Stock Invariant Control | Optimistic checks vs Row-level database locks | `select_for_update()` in `@transaction.atomic` | Prevents race conditions during concurrent stock dispatches, ensuring stock bag counts and weights never drop below zero. |
| **ADR-04** | Transaction Deletions | Hard delete vs Logical soft-delete vs Service cancellation | Service Cancellation with Stock Rollback | Hard deletes leave orphan stock records; soft delete alone doesn't reverse balances. Cancellation services atomically reverse ledger adjustments. |
| **ADR-05** | Response Format | Variable shapes vs Standardized JSON envelopes | `StandardJSONRenderer` | Standardizes all client integrations with uniform `{ success, data, meta }` and `{ success, error }` envelopes. |
