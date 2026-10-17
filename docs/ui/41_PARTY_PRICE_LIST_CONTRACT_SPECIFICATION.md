# Party Price List Contract Screen & Rate Sandbox Specification

| Standard Code | Screen ID | Target Platform | API Version | Document Version | Date | Status |
|---|---|---|---|---|---|---|
| **STD-UI-001** | **`SCR-PRIC-003`** | Next.js 14 (App Router) + TypeScript | `v1.2` (Django 5 DRF) | `v1.0.0` | 17/10/2026 | **APPROVED FOR IMPLEMENTATION** |

---

## 1. Document Overview, Version, Scope, and Status

### 1.1 Purpose
This specification defines the complete architectural requirements, UI layout, multi-tier pricing resolution matrix, technical parameter matching, TypeScript interfaces, Zod validation schemas, and API bindings for the **Party-Specific Price List Contract Screen & Deterministic Rate Sandbox** (`SCR-PRIC-003`).

In the Garments ERP & CRM ecosystem, commercial transactions with key partners (Spinning Mills, Institutional Fashion Buyers, and Subcontract Job Workers) are governed by formal, legally binding annual or seasonal supply contracts. Rather than relying on generic market catalogs, these partners negotiate dedicated rates with specific volume rebates, machine gauge rules, Lycra plating surcharges, and allowed shrinkage parameters.

Under the system's **Rate Determination Hierarchy**, a Party-Specific Price List holds **Priority 1 (Highest Precedence)**. This screen provides commercial managers, procurement leads, and costing accountants with a unified cockpit to:
1. View, verify, and revise active party contracts across Purchase, Sales, and Job Work.
2. Inspect multi-tier quantity slabs, unit discounts, and technical matrix rules.
3. Test hypothetical orders through an embedded real-time Rate Resolution Sandbox.
4. Review the complete audit log of contract rate amendments and spot overrides (`ta_pricing_audit`).

### 1.2 Scope & Linked Assets
- **Backend Model**: [`PriceList`](file:///d:/Codebase/Garments/backend/apps/pricing/models.py#L8) (`tm_price_list` where `scope = 'PARTY_SPECIFIC'`), [`PriceListItem`](file:///d:/Codebase/Garments/backend/apps/pricing/models.py#L42) (`tm_price_list_item`), [`PriceListJobRule`](file:///d:/Codebase/Garments/backend/apps/pricing/models.py#L105) (`tm_price_list_job_rule`), [`PricingAudit`](file:///d:/Codebase/Garments/backend/apps/pricing/models.py#L198) (`ta_pricing_audit`).
- **Backend Service**: [`PriceListService`](file:///d:/Codebase/Garments/backend/apps/pricing/services.py#L17) & [`PricingResolutionService`](file:///d:/Codebase/Garments/backend/apps/pricing/services.py#L756).
- **Backend API Contract**: [`/api/v1/pricing/lists/{id}/`](file:///d:/Codebase/Garments/docs/api-contract.md#L140-L144), [`/api/v1/pricing/resolve/`](file:///d:/Codebase/Garments/docs/api-contract.md#L145).
- **Interactive Reference Implementation**: [`frontend/party_price_list_sample.html`](file:///d:/Codebase/Garments/frontend/party_price_list_sample.html).
- **Target Next.js Route**: `/pricing/party-price-lists/[id]` (`app/(app)/pricing/party-price-lists/[id]/page.tsx`).

---

## 2. Module Details, Screen ID, Route, Access Privileges, and API Endpoints

### 2.1 Core Metadata

| Parameter | Specification |
|---|---|
| **Module** | `Module 9 — Commercial Pricing Engine` |
| **Screen ID** | `SCR-PRIC-003` |
| **Frontend Route** | `/pricing/party-price-lists/[id]` |
| **File Location** | `app/(app)/pricing/party-price-lists/[id]/page.tsx` |
| **Required Privilege** | `pricing_manage.can_read` (View contract); `pricing_manage.can_create` (Add slab/rule); `pricing_manage.can_update` (Revise rates); `pricing_manage.can_approve` (Lock contract rates) |
| **Authorized Roles** | `SUPER_ADMIN`, `ADMIN_USER`, `COMPANY_USER` (Commercial Director, General Manager Procurement, Merchandising Lead) |
| **Country Pack** | `IN` (India: Currency INR `₹`, Date `DD/MM/YYYY`, Rate precision 4 dp `₹ 0.0000`, Quantity 3 dp `0.000 Kg`) |

### 2.2 Primary API Endpoints

| HTTP Method | API Path | Privilege / Scope | Description |
|---|---|---|---|
| `GET` | `/api/v1/pricing/lists/{id}/` | `can_read` | Fetch price list master header, party profile, validity dates, and status |
| `GET` | `/api/v1/pricing/lists/{id}/items/` | `can_read` | Fetch contracted yarn/fabric line items with quantity slabs and rates |
| `POST` | `/api/v1/pricing/lists/{id}/items/` | `can_create` | Add new tiered quantity slab item to contract |
| `GET` | `/api/v1/pricing/lists/{id}/job-rules/` | `can_read` | Fetch subcontract job work rules (gauge, Lycra surcharge, allowed loss) |
| `POST` | `/api/v1/pricing/lists/{id}/job-rules/` | `can_create` | Add new subcontract job work rule |
| `POST` | `/api/v1/pricing/resolve/` | `can_read` | Real-time simulator payload resolving effective rate against Priority 1 rule |
| `GET` | `/api/v1/pricing/audit/?price_list_id={id}`| `can_read` | Fetch revision history and manual spot override log |

---

## 3. UI Layout, Screen Blueprint, and Visual Mockup (1440px+ Wireframe)

```
+-----------------------------------------------------------------------------------------------------------------------------+
| GARMENTS ERP — Commercial Pricing & Valuation                   Company: Tex Garments Mills Ltd | FY: 2026-2027 (Active)    |
+-----------------------------------------------------------------------------------------------------------------------------+
| Commercial Pricing / Party Price Lists / PL-PUR-LAKSHMI-2026                      [Export PDF]  [+ Revise Contract Rates]   |
+-----------------------------------------------------------------------------------------------------------------------------+
| [ ★ Priority 1 Resolution Hierarchy ]  [ Scope: PARTY_SPECIFIC ]  [ PURCHASE CONTRACT ]  [ (●) ACTIVE ]                     |
| LAKSHMI SPINNING MILLS LTD — ANNUAL YARN PROCUREMENT CONTRACT                                                               |
| Direct spinning mill agreed contract supply rates for high-count combed cotton cone yarn with tiered bulk order rebates.    |
|                                                                                                                             |
| Price List Code: PL-PUR-LAKSHMI-2026    Party: Lakshmi Spinning Mills (#1042)    Role: Spinning Mill / Raw Material Vendor  |
| Validity: 01/04/2026 - 31/03/2027      Terms: INR (₹) • Net 30 Days             GSTIN: 33AAACL1234F1Z8 (Tamil Nadu)         |
+-----------------------------------------------------------------------------------------------------------------------------+
| KPI TELEMETRY BAR:                                                                                                          |
| [ 3 Contract Lines (Active) ]  [ ₹261.50/Kg Avg Base Rate ]  [ 3.6% Savings vs General List ]  [ 4 Active Document Bindings ]|
+---------------------------------------------------------------------------------------------+-------------------------------+
| CONTRACTED ITEMS & MULTI-TIER SLABS:                                                        | RATE RESOLUTION SIMULATOR:    |
| # | Item / Count Description      | Quantity Slab   | Party Rate | Market Rate | Advantage | Select Item:                  |
|---|-------------------------------|-----------------|------------|-------------|-----------| [ 30s Combed Cotton Grey  |v] |
| 1 | 30s Combed Cotton Cone (Grey) | 0 - 2,000 Kg    | ₹ 265.0000 |  ₹ 275.0000 | -₹10.00/Kg| Order Quantity (Kg):          |
| 2 | 30s Combed Cotton Cone (Bulk) | 2,001-10,000 Kg | ₹ 258.0000 |  ₹ 268.0000 | -₹10.00/Kg| [ 3,500.000                 ] |
| 3 | 40s Combed Compact Cone (Grey)| Min 0 Kg        | ₹ 298.0000 |  ₹ 310.0000 | -₹12.00/Kg| [x] Plated Surcharge (+₹3.50) |
|                                                                                             | [ > Simulate Rate Resolution ]|
|                                                                                             |-------------------------------|
|                                                                                             | Effective Rate: ₹ 258.00 / Kg |
|                                                                                             | Matched: 2,001 - 10,000 Kg    |
|                                                                                             | Total Order:   ₹ 9,03,000.00  |
|                                                                                             | Total Savings: ₹ 59,500.00    |
|                                                                                             | Engine: Rule 1 (Party Match)  |
+---------------------------------------------------------------------------------------------+-------------------------------+
| AUDIT TRAIL & CONTRACT AMENDMENT LOG (ta_pricing_audit):                                                                    |
| [✓] 01/04/2026 10:30 AM — Annual Contract Baseline Rate Locked by GM (Purchase) for FY 2026-27 (#LAK-CON-2026-01)          |
| [★] 12/04/2026 04:15 PM — Bulk Spot Concession for YARN_PO #108: ₹275.00 -> ₹268.00 (-₹7.00/Kg). Approved by Superadmin     |
+-----------------------------------------------------------------------------------------------------------------------------+
```

---

## 4. Page Initialization, Query Parameters, and Default Form State

1. **Hydration Route**:
   - `GET /api/v1/pricing/lists/{id}/`: Fetches price list master header.
   - If `scope !== 'PARTY_SPECIFIC'`, display warning banner noting screen is specialized for party contract representations.
2. **Context Resolution**:
   - Checks user company context via header `X-Company-ID`. Cross-company contract access is rejected with `403 Forbidden`.
   - Extracts contracted party profile from `PartyMaster` (`code`, `name`, `gstin`, `credit_days`).
3. **Sub-Item Hydration**:
   - If `list_type == 'JOB_WORK'`, query `/api/v1/pricing/lists/{id}/job-rules/`.
   - If `list_type in ['PURCHASE', 'SALES']`, query `/api/v1/pricing/lists/{id}/items/`.

---

## 5. Master Linkages and Precedence Invariants

```
                                      RATE RESOLUTION ENGINE
                                                │
                                                ▼
                                    ┌───────────────────────┐
                                    │ Priority 1 Check:     │
                                    │ Active Party Contract │
                                    └───────────┬───────────┘
                                                │
                                    ┌───────────┴───────────┐
                                    │                       │
                                 [FOUND]                [NOT FOUND]
                                    │                       │
                                    ▼                       ▼
                        ┌───────────────────────┐ ┌───────────────────────┐
                        │ Apply Party Specific  │ │ Priority 3 Fallback:  │
                        │ Negotiated Rate       │ │ General Base Rate Card│
                        │ (PL-PUR-LAKSHMI-2026) │ │ (PL-PUR-GEN-2026)     │
                        └───────────────────────┘ └───────────────────────┘
```

1. **Party Isolation**: A party price list is strictly bound to `party_id`. When creating transactions, the engine only selects this price list if `tx.party_id == tm_price_list.party_id`.
2. **Date Boundaries**: Rates are valid exclusively within `valid_from <= tx.doc_date <= valid_to`. Any date outside this range automatically cascades to Priority 3 (General Price List) unless overridden.

---

## 6. Interactive Rate Resolution Simulator Engine

The right-hand panel hosts an embedded live sandbox replicating backend rate resolution:
- **Formula for Net Effective Rate**:
  $$\text{Net Rate} = (\text{Base Rate} \times (1 - \frac{\text{Discount \%}}{100})) + \text{Surcharges}$$
- **Formula for Total Savings vs General Benchmark**:
  $$\text{Total Savings} = (\text{General Unit Rate} - \text{Party Effective Unit Rate}) \times \text{Order Quantity}$$
- **Engine Trace Output**: Provides explicit visual feedback detailing which hierarchy rule triggered the price (Rule 1: Party-Specific Contract match).

---

## 7. Form Validation Rules and Invariant Matrix

| Field | Validation Constraint | Error Trigger | Error Message |
|---|---|---|---|
| `price_list_code` | Required, Alphanumeric uppercase, unique per company | Blank or duplicate active code | `Price list code must be unique per company.` |
| `party_id` | Required when `scope == 'PARTY_SPECIFIC'` | Null or invalid ID | `Party selection is mandatory for party contracts.` |
| `valid_from` / `valid_to` | Date range; `valid_from <= valid_to` | Start date after end date | `valid_from cannot be later than valid_to.` |
| `min_quantity` / `max_quantity` | Decimal(18,3); `min_quantity <= max_quantity` | Min > Max | `max_quantity cannot be less than min_quantity.` |
| `base_rate` | Decimal(18,4); non-negative | Rate < 0 | `Base rate cannot be negative.` |
| `discount_percent` | Decimal(5,2); between 0.00 and 100.00% | Discount > 100% | `Discount percentage cannot exceed 100.00%.` |

---

## 8. TypeScript Types and Zod Schema

```typescript
import { z } from 'zod';

export const PartyPriceListItemSchema = z.object({
  id: z.number().optional(),
  item_type: z.enum(['YARN', 'FABRIC', 'GARMENT', 'TRIM']),
  yarn_count_id: z.number().nullable().optional(),
  yarn_type: z.enum(['GREY', 'DYED', 'MELANGE', 'BLENDED', 'WOUND', 'GASSED']).optional(),
  min_quantity: z.number().min(0, "Min quantity must be >= 0"),
  max_quantity: z.number().nullable().optional(),
  base_rate: z.number().positive("Base rate must be positive"),
  discount_percent: z.number().min(0).max(100).default(0),
});

export const PartyPriceListHeaderSchema = z.object({
  id: z.number(),
  price_list_code: z.string().min(3).max(50),
  price_list_name: z.string().min(5).max(255),
  list_type: z.enum(['PURCHASE', 'SALES', 'JOB_WORK']),
  scope: z.literal('PARTY_SPECIFIC'),
  party_id: z.number({ required_error: "Party ID is mandatory" }),
  valid_from: z.string(),
  valid_to: z.string(),
  is_default: z.boolean().default(false),
  description: z.string().optional(),
});

export type PartyPriceListHeader = z.infer<typeof PartyPriceListHeaderSchema>;
export type PartyPriceListItem = z.infer<typeof PartyPriceListItemSchema>;
```

---

## 9. Implementation Reference & Developer Checklist

- [x] Reference standalone implementation delivered in [`frontend/party_price_list_sample.html`](file:///d:/Codebase/Garments/frontend/party_price_list_sample.html).
- [ ] Connect Next.js Page component `app/(app)/pricing/party-price-lists/[id]/page.tsx` with API client.
- [ ] Implement live keystroke simulator debouncing `POST /api/v1/pricing/resolve/`.
- [ ] Add PDF export template matching standard company letterhead with legal validity sign-off blocks.
