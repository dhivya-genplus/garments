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
| **System** | `sys_` | `company` | Multi-tenant company account |
| **System** | `sys_` | `financial_year` | Fiscal accounting years |
| **System** | `sys_` | `user_role` | Roles grouping permissions |
| **System** | `sys_` | `user_privilege` | Granular CRUD module privileges |
| **System** | `sys_` | `employee` | User / Employee entities |
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
| **Procurement** | `tm_` | `tm_yarn_po_return` | Yarn PO Return & Debit Note to Spinning Mill |
| **Procurement** | `tx_` | `tx_yarn_po_return` | Itemized Yarn PO Return line items |
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
| **ADR-06** | Yarn PO Returns Separation | Embedded in Sales Return vs Outward DC vs Dedicated Module | Dedicated Service & Workflow (`tm_yarn_po_return`) | Returning yarn to spinning mills involves QC laboratory defect categorization, supplier AP debit notes, and input tax credit reversals. Coupling it with customer sales returns creates accounting and privilege violations. |

---

## 4. Authoritative Textile Domain Mapping: Yarn Category &rarr; Knitting Setup &rarr; Output Fabric &rarr; Downstream Pipeline

The manufacturing pipeline engine enforces technical validation based on input yarn categories:

| Input Yarn Category | Intended Knitting Usage / End Fabric Output | Knitting Process / Machine Setup | Inward Stage Received (Output from Knitting) | Next Production Stage / Pipeline |
|---|---|---|---|---|
| **Grey Yarn** *(Raw / Ecru Cotton, Blends)* | Solid-color T-shirts, tops, and basic apparel | Circular single jersey machines (plain knit) | **Grey Fabric (`GREY_FABRIC`)** *(Greige rolls / thans)* | Sent to dye house for scouring, bleaching, and batch/piece dyeing (soft-flow) |
| **Grey Yarn** *(Raw / Ecru)* | Stretch T-shirts, leggings, activewear | Single jersey machines with elastane attachment (e.g., 20D/40D Lycra) | **Grey Fabric (`GREY_FABRIC`)** *(Greige Lycra single jersey)* | Sent for heat-setting (stenter), scouring, and piece dyeing |
| **Grey Yarn** *(Raw / Ecru)* | Polo shirt bodies, tennis tees | Pique / honeycomb / Lacoste circular machines | **Grey Fabric (`GREY_FABRIC`)** *(Greige pique rolls)* | Batch dyeing, bio-polishing, compacting |
| **Grey Yarn** *(Raw / Ecru)* | Winter hoodies, sweatshirts, joggers | 2-thread or 3-thread fleece machines (face, tie, and loop yarn) | **Grey Fabric (`GREY_FABRIC`)** *(Greige fleece rolls)* | Scouring, dyeing, loop raising/brushing (fleece nap) |
| **Grey Yarn** *(Raw / Ecru)* | Premium tees, babywear, double-sided knitwear | Interlock circular knitting machines | **Grey Fabric (`GREY_FABRIC`)** *(Greige interlock rolls)* | Batch dyeing, softening, compacting |
| **Dyed Yarn** *(Package/Cone-Dyed)* | Horizontal striped T-shirts, rugby shirts | Circular machines with multiple feeders alternating colored yarn cones (feeder stripe) | **Yarn-Dyed Fabric (`DYED_FABRIC`)** *(Striped rolls ready without batch dyeing)* | Direct scouring, tentering/stenter finishing, and compacting (no piece dyeing required) |
| **Dyed Yarn** *(Package/Cone-Dyed)* | Branded polo bodies with custom chest bands | Auto-striper circular knitting machines with programmable finger selectors (engineered stripes) | **Yarn-Dyed Fabric (`DYED_FABRIC`)** *(Engineered stripe rolls)* | Slitting, finishing, stenter, compacting |
| **Dyed Yarn** *(Package/Cone-Dyed)* | Polo neck collars and sleeve cuffs with tipping lines | Flatbed knitting machines (e.g., Shima Seiki, Stoll) | **Flat Knit Trims / Collars (`TRIM` / `FABRIC`)** *(Pieces or collar strips)* | Ironing, cutting, inspection, directly attached during garment stitching |
| **Dyed Yarn** *(Package/Cone-Dyed)* | Multi-color textured patterns, knit cardigans, sweaters | Electronic jacquard circular or flat knitting machines | **Jacquard Knit Fabric (`DYED_FABRIC`)** *(Patterned rolls / panels)* | Steam relaxing, washing/softening, compacting |
| **Melange Yarn** *(Fibre-dyed blend)* | Heather grey athletic T-shirts, joggers, gym wear | Circular single jersey, fleece, or French terry machines | **Melange Fabric (`DYED_FABRIC`)** *(Grey/color heather rolls)* | Scouring, softening, compacting (no piece-dye bath needed) |

