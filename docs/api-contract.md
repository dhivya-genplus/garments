# API Contract — Garments ERP & CRM

Fixed contract between Backend (DRF) and Frontend (Web / Mobile / Third-Party).

Base URL: `/api/v1/`  
Auth: Bearer JWT (header `Authorization: Bearer <token>`)  
Company Scope: Header `X-Company-ID: <id>` (or user company context)  
Financial Year Scope: Header `X-Financial-Year-ID: <id>` (or user active FY)  
Date format: `YYYY-MM-DD` (ISO) or `DD/MM/YYYY`  
Number precision: Monetary with 2 decimal places, Quantity/Weight with 2-3 decimal places  
Pagination: Standard page/page_size (`meta: { page: 1, page_size: 20, total_count: n }`)  

## Response Envelopes


### Success
```json
{
  "success": true,
  "data": {},
  "meta": {
    "page": 1,
    "page_size": 20,
    "total_count": 100
  }
}
```

### Error
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Human-readable explanation of error.",
    "details": {}
  }
}
```

---

## Endpoints

### 1. Authentication & System Administration
| Method | Path | Privilege / Role | Description |
|---|---|---|---|
| `POST` | `/api/v1/auth/login/` | `AllowAny` | Obtain JWT tokens & user company context |
| `POST` | `/api/v1/auth/refresh/` | `AllowAny` | Refresh expired access token |
| `GET, PUT` | `/api/v1/auth/me/` | `IsAuthenticated` | User profile & tenant context |
| `POST` | `/api/v1/auth/switch-financial-year/` | `IsCompanyUser` | Change current active working financial year |
| `GET` | `/api/v1/auth/modules/` | `IsAuthenticated` | List all 18 configurable module keys |
| `CRUD` | `/api/v1/administration/companies/` | `IsSuperAdmin` / `IsAdminUser` | Company tenant administration |
| `CRUD` | `/api/v1/administration/financial-years/` | `IsAdminUser` | Fiscal years management |
| `CRUD` | `/api/v1/administration/roles/` | `IsAdminUser` | Custom roles & granular module permissions |
| `CRUD` | `/api/v1/administration/employees/` | `IsAdminUser` | Staff & operator accounts |

### 2. Masters
| Method | Path | Privilege Code | Description |
|---|---|---|---|
| `CRUD` | `/api/v1/masters/uom/` | `masters_uom` | Units of measurement (KGS, MTR, PCS, BAG) |
| `CRUD` | `/api/v1/masters/parties/` | `masters_party` | Mills, Traders, Dyers, Knitters, Customers |
| `CRUD` | `/api/v1/masters/yarn-counts/` | `masters_yarn` | Yarn count specifications (30s, 34s, 40s) |
| `CRUD` | `/api/v1/masters/yarn-types/` | `masters_yarn` | Yarn composition (Combed, Carded, etc.) |
| `CRUD` | `/api/v1/masters/colors/` | `masters_color` | Color shades & references |
| `CRUD` | `/api/v1/masters/yarns/` | `masters_yarn` | Yarn SKUs (Count + Type + Color) |
| `CRUD` | `/api/v1/masters/fabric-types/` | `masters_fabric` | Fabric structures |
| `CRUD` | `/api/v1/masters/fabrics/` | `masters_fabric` | Fabric SKUs with GSM, Dia, Gauge |
| `CRUD` | `/api/v1/masters/processes/` | `masters_process` | Processing stages, loss % and rate |
| `CRUD` | `/api/v1/masters/warehouses/` | `masters_warehouse` | Godowns & warehouse locations |
| `CRUD` | `/api/v1/masters/quality-programs/` | `IsCompanyUser` | Garment box & size breakdowns |
| `CRUD` | `/api/v1/masters/taxes/` | `masters_tax` | GST Tax Master with rates (CGST, SGST, IGST) & HSN codes |
| `POST` | `/api/v1/masters/taxes/seed-defaults/` | `masters_tax` | Seed standard GST tax slabs (0%, 5%, 12%, 18%, 28%) |

### 3. Procurement (Purchase)
| Method | Path | Privilege Code | Description |
|---|---|---|---|
| `GET, POST` | `/api/v1/purchase/yarn-types/` | `purchase_yarn_po` | List / Configure allowed company yarn process types |
| `GET` | `/api/v1/purchase/yarn-types/active/` | `purchase_yarn_po` | List active company yarn types & field requirements for dropdowns |
| `POST` | `/api/v1/purchase/yarn-types/seed-defaults/` | `purchase_yarn_po` | Seed / Reset standard default company yarn types |
| `GET, POST` | `/api/v1/purchase/yarn-pos/` | `purchase_yarn_po` | Create / List POs with auto FY & schedules |
| `GET, PUT` | `/api/v1/purchase/yarn-pos/{id}/` | `purchase_yarn_po` | Retrieve / Update draft PO |
| `DELETE` | `/api/v1/purchase/yarn-pos/{id}/` | `purchase_yarn_po` | Soft delete draft PO (blocked if authorized/inwarded) |
| `POST` | `/api/v1/purchase/yarn-pos/{id}/authorize/` | `purchase_yarn_po` | Lock PO for production |
| `POST` | `/api/v1/purchase/yarn-pos/{id}/unauthorize/` | `purchase_yarn_po` | Re-open PO for changes |
| `GET` | `/api/v1/purchase/balances/` | `purchase_yarn_po` | Live PO unfulfilled balance tracking |

### 4. Inventory Engine
| Method | Path | Privilege Code | Description |
|---|---|---|---|
| `GET` | `/api/v1/inventory/yarn-stock/` | `inventory_yarn_stock` | Live godown inventory ledger (Bags & Kg) |
| `GET, POST` | `/api/v1/inventory/yarn-inwards/` | `inventory_yarn_inward` | Post GRN Inward (credits stock, reduces PO balance) |
| `DELETE` | `/api/v1/inventory/yarn-inwards/{id}/` | `inventory_yarn_inward` | Atomic inward cancellation & stock reversal |
| `GET, POST` | `/api/v1/inventory/yarn-outwards/` | `inventory_yarn_outward` | Issue DC Outward (validates bags/Kg, deducts stock) |
| `DELETE` | `/api/v1/inventory/yarn-outwards/{id}/` | `inventory_yarn_outward` | Atomic outward cancellation & stock re-credit |

### 5. Commercial Sales & Returns
| Method | Path | Privilege Code | Description |
|---|---|---|---|
| `GET, POST` | `/api/v1/sales/yarn-sales/` | `sales_yarn` | Issue commercial sales tax invoice (deducts stock) |
| `DELETE` | `/api/v1/sales/yarn-sales/{id}/` | `sales_yarn` | Cancel sales invoice & restore warehouse stock |
| `GET, POST` | `/api/v1/sales/yarn-sales-returns/` | `sales_yarn_return` | Post customer return (re-credits stock) |
| `DELETE` | `/api/v1/sales/yarn-sales-returns/{id}/` | `sales_yarn_return` | Cancel return & reverse re-credited stock |

### 6. Knitting & Grey Fabric Production
| Method | Path | Privilege Code | Description |
|---|---|---|---|
| `GET, POST` | `/api/v1/knitting/programs/` | `knitting_program` | Create / List Knitting Programs (Job Cards) with loss % & yarn lines |
| `GET, PUT` | `/api/v1/knitting/programs/{id}/` | `knitting_program` | Retrieve / Update Knitting Program |
| `POST` | `/api/v1/knitting/programs/{id}/authorize/` | `knitting_program` | Authorize / Release Program for factory production |
| `POST` | `/api/v1/knitting/programs/{id}/unauthorize/` | `knitting_program` | Re-open Knitting Program to Draft (if not yet in production) |
| `GET` | `/api/v1/knitting/programs/{id}/summary/` | `knitting_program` | Live reconciliation (Planned vs Issued Yarn vs Received Fabric) |
| `GET` | `/api/v1/knitting/stock/` | `knitting_grey_fabric_stock` | Live Godown stock of Grey Fabric (Rolls & Kg) |
| `GET, POST` | `/api/v1/knitting/inwards/` | `knitting_grey_fabric_inward` | Post Grey Fabric Inward GRN (credits stock, updates program) |
| `DELETE` | `/api/v1/knitting/inwards/{id}/` | `knitting_grey_fabric_inward` | Atomic inward cancellation and stock rollback |
| `GET, POST` | `/api/v1/knitting/outwards/` | `knitting_grey_fabric_outward` | Issue Grey Fabric Outward DC (for Dyeing or Return) |
| `DELETE` | `/api/v1/knitting/outwards/{id}/` | `knitting_grey_fabric_outward` | Atomic outward cancellation and stock re-credit |
| `GET, POST` | `/api/v1/knitting/grey-pos/` | `knitting_grey_po` | Create / List Grey Fabric Purchase Orders for Traders |
| `POST` | `/api/v1/knitting/grey-pos/{id}/authorize/` | `knitting_grey_po` | Authorize Grey Fabric PO |
| `GET, POST` | `/api/v1/knitting/sales/` | `knitting_grey_fabric_sales` | Issue Commercial Grey Fabric Tax Invoice (rolls & Kg, deducts stock) |
| `DELETE` | `/api/v1/knitting/sales/{id}/` | `knitting_grey_fabric_sales` | Atomic sales cancellation and godown stock restoration |
| `GET, POST` | `/api/v1/knitting/sales-returns/` | `knitting_grey_fabric_sales_return` | Post Customer Sales Return for Grey Fabric (re-credits godown stock) |
| `DELETE` | `/api/v1/knitting/sales-returns/{id}/` | `knitting_grey_fabric_sales_return` | Atomic return cancellation and stock reversion |

### 7. Production Process Engine (Knitting, Dyeing, Cutting, Printing, Stitching)
| Method | Path | Privilege Code | Description |
|---|---|---|---|
| `GET, POST` | `/api/v1/process/stages/` | `process_stage` | Configure / List Process Stages with routing, loss %, and rate |
| `POST` | `/api/v1/process/stages/seed-defaults/` | `process_stage` | Seed standard stages (Knitting, Dyeing, Compacting, Cutting) |
| `GET, POST` | `/api/v1/process/programs/` | `process_program` | Create / List Production Process Programs (input_from, input_item, output_to, output_item, rates, loss %) |
| `GET, PUT` | `/api/v1/process/programs/{id}/` | `process_program` | Retrieve / Update Process Program |
| `POST` | `/api/v1/process/programs/{id}/authorize/` | `process_program` | Authorize / Release Program for shop floor execution |
| `POST` | `/api/v1/process/programs/{id}/unauthorize/` | `process_program` | Re-open Authorized Program back to Draft |
| `DELETE` | `/api/v1/process/programs/{id}/` | `process_program` | Cancel Process Program (if production has not commenced) |
| `GET` | `/api/v1/process/programs/{id}/summary/` | `process_program` | Live reconciliation (Planned Input vs Expected Output vs Received Output) |


