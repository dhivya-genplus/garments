# Multi-Party Price List Comparison Matrix & Benchmarking Specification

| Standard Code | Screen ID | Target Platform | API Version | Document Version | Date | Status |
|---|---|---|---|---|---|---|
| **STD-UI-001** | **`SCR-PRIC-004`** | Next.js 14 (App Router) + TypeScript | `v1.2` (Django 5 DRF) | `v1.0.0` | 17/10/2026 | **APPROVED FOR IMPLEMENTATION** |

---

## 1. Document Overview, Version, Scope, and Status

### 1.1 Purpose
This specification establishes the technical blueprint, cross-tabulation data architecture, comparative matrix calculations, UI layout, and API integration for the **Multi-Party Price List Comparison Matrix & Benchmarking Screen** (`SCR-PRIC-004`).

In commercial textile production, procurement officers and merchandisers must continuously benchmark prices across multiple competing spinning mills (for raw yarn), external fabric vendors, and subcontracted process units (knitting, dyeing, printing). Rather than opening separate price list contracts one by one, the Multi-Party Comparison Matrix aggregates and pivots all active party contracts into a unified side-by-side grid. 

This cockpit enables commercial managers to:
1. **Benchmark Vendor Rates**: Compare contractual supply rates from multiple vendors side-by-side for identical items, counts, and volume slabs.
2. **Identify Best Market Opportunities**: Automatically highlight the lowest contracted rate (`BEST RATE` badge) along with percentage variances above the benchmark.
3. **Measure Savings vs General Catalog**: Compute the financial difference between vendor contracts and the company's default benchmark price list (`PL-PUR-GEN-2026` or `PL-SALES-GEN-2026`).
4. **Trigger Downstream Purchasing**: Directly launch a Yarn Purchase Order (`tm_yarn_po`) or Knitting Job Card (`tm_knitting_program`) for the winning vendor with pre-filled negotiated rates.

### 1.2 Scope & Linked Assets
- **Backend Model**: [`PriceList`](file:///d:/Codebase/Garments/backend/apps/pricing/models.py#L8) (`tm_price_list`), [`PriceListItem`](file:///d:/Codebase/Garments/backend/apps/pricing/models.py#L42) (`tm_price_list_item`), [`PriceListJobRule`](file:///d:/Codebase/Garments/backend/apps/pricing/models.py#L105) (`tm_price_list_job_rule`), [`PartyMaster`](file:///d:/Codebase/Garments/backend/apps/masters/models.py) (`tm_party`).
- **Interactive Reference Implementation**: [`frontend/multi_party_price_list_matrix.html`](file:///d:/Codebase/Garments/frontend/multi_party_price_list_matrix.html).
- **Visual Design Mockup**: [`docs/assets/ui/multi_party_pricing_matrix_sample.jpg`](file:///d:/Codebase/Garments/docs/assets/ui/multi_party_pricing_matrix_sample.jpg) and embedded in [`multi_party_pricing_matrix.md`](file:///C:/Users/USER/.gemini/antigravity-ide/brain/65c22b92-643c-4ac6-97cf-be8e7049e2a5/multi_party_pricing_matrix.md).
- **Target Route**: `/pricing/party-comparison-matrix` (`app/(app)/pricing/party-comparison-matrix/page.tsx`).

---

## 2. Module Details, Screen ID, Route, Access Privileges, and API Endpoints

### 2.1 Core Metadata

| Parameter | Specification |
|---|---|
| **Module** | `Module 9 — Commercial Pricing Engine` |
| **Screen ID** | `SCR-PRIC-004` |
| **Frontend Route** | `/pricing/party-comparison-matrix` |
| **File Location** | `app/(app)/pricing/party-comparison-matrix/page.tsx` |
| **Required Privilege** | `pricing_manage.can_read` (View matrix & comparisons); `purchase_order.can_create` (Dispatch PO to winning vendor) |
| **Authorized Roles** | `SUPER_ADMIN`, `ADMIN_USER`, `COMPANY_USER` (General Manager Procurement, Purchase Manager, Costing Analyst) |
| **Country Pack** | `IN` (Currency: INR `₹`, Number grouping: Indian `12,34,567.89`, Rate precision: 4 decimal places) |

### 2.2 Primary API Endpoints

| HTTP Method | API Path | Privilege / Scope | Description |
|---|---|---|---|
| `GET` | `/api/v1/pricing/matrix/?category={category}&fy_id={fy_id}` | `can_read` | Aggregated cross-tabulation endpoint returning items with pivoted party rates |
| `GET` | `/api/v1/pricing/lists/?scope=PARTY_SPECIFIC&list_type={type}` | `can_read` | List all active party price lists participating in comparison |
| `POST` | `/api/v1/purchase/yarn-po/` | `can_create` | Direct procurement dispatch initiating PO with selected party & resolved rate |
| `GET` | `/api/v1/pricing/matrix/export/?format=xlsx` | `can_export` | Export dynamic cross-tabulated Excel matrix |

---

## 3. UI Layout, Screen Blueprint, and Visual Mockup (1440px+ Wireframe)

```
+-----------------------------------------------------------------------------------------------------------------------------+
| GARMENTS ERP — Multi-Party Price List Comparison Matrix (INR ₹)              Company: Tex Garments Mills Ltd | FY: 2026-2027|
+-----------------------------------------------------------------------------------------------------------------------------+
| Multi-Party Price List Comparison Matrix (INR ₹)                                [FY 2026-27 |v] [Category: Yarn Mills |v]   |
| Cross-vendor rate benchmarking across contracted spinning mills, buyers, and job workers.         [🖨️ Export Matrix Report] |
+-----------------------------------------------------------------------------------------------------------------------------+
| KPI TELEMETRY CARDS:                                                                                                        |
| [ 🏭 18 Spinning Mills (Active) ] [ 💎 ₹258.00/Kg Lowest Benchmark (30s) ] [ 📈 6.8% YoY Avg Savings ] [ 🛡️ 100% Conformance]|
+-----------------------------------------------------------------------------------------------------------------------------+
| TABS: [ (●) 1. Yarn Procurement Mills ]   [ 2. Commercial Sales Buyers ]   [ 3. Subcontract Job Workers (Knitting/Dyeing) ] |
+-----------------------------------------------------------------------------------------------------------------------------+
| COMPARATIVE RATE MATRIX TABLE:                                                                                              |
| Item / Yarn Count | Volume Slab | Lakshmi Mills (#1042) | KPR Mill (#1055)   | Ramco Textiles (#1088)| General Benchmark | Action      |
|-------------------|-------------|-----------------------|--------------------|-----------------------|-------------------|-------------|
| 30s Combed Cotton | 10,000+ Kg  | ₹ 258.00 [BEST RATE]  | ₹ 262.50 (+1.7%)   | ₹ 264.00 (+2.3%)      | ₹ 268.00 (PL-GEN) | [Raise PO]  |
| 30s Combed Cotton | 0 - 2,000 Kg| ₹ 265.00 [BEST RATE]  | ₹ 268.00 (+1.1%)   | ₹ 270.00 (+1.9%)      | ₹ 275.00 (PL-GEN) | [Raise PO]  |
| 34s Carded Hosiery| 5,000+ Kg   | ₹ 255.00 (+0.8%)      | ₹ 253.00 [BEST RATE| ₹ 256.50 (+1.4%)      | ₹ 260.00 (PL-GEN) | [Raise PO]  |
| 40s Combed Compact| 5,000+ Kg   | ₹ 298.00 [BEST RATE]  | ₹ 302.00 (+1.3%)   | ₹ 304.50 (+2.1%)      | ₹ 310.00 (PL-GEN) | [Raise PO]  |
| 2/40s Wound Combed| All Qty     | ₹ 325.00 (+1.6%)      | ₹ 320.00 [BEST RATE| ₹ 322.00 (+0.6%)      | ₹ 330.00 (PL-GEN) | [Raise PO]  |
+-----------------------------------------------------------------------------------------------------------------------------+
```

---

## 4. Cross-Tabulation Data Architecture

The matrix transforms normalized database rows into a pivoted columnar representation:

```
Database Rows (Normalized)                              Pivoted Cross-Tabulation View
------------------------------------                    ------------------------------------------------------------
[Item: 30s, Party: Lakshmi, Rate: 258]  ──┐             Row: 30s Combed Cotton (Slab: 10,000+ Kg)
[Item: 30s, Party: KPR,     Rate: 262]  ──┼───► Matrix  ├── Lakshmi Mills: ₹ 258.00  [BEST RATE]
[Item: 30s, Party: Ramco,   Rate: 264]  ──┤   Selector  ├── KPR Mills:     ₹ 262.50  (+1.7% variance)
[Item: 30s, Party: NULL,    Rate: 268]  ──┘             ├── Ramco Mills:   ₹ 264.00  (+2.3% variance)
                                                        └── General List:  ₹ 268.00  (Baseline Reference)
```

### Mathematical Formulas:
1. **Lowest Rate Identification**:
   $$\text{Min Rate} = \min_{p \in \text{Parties}}(\text{Effective Rate}_p)$$
2. **Percentage Variance above Lowest**:
   $$\text{Variance \%} = \frac{\text{Vendor Rate} - \text{Min Rate}}{\text{Min Rate}} \times 100$$
3. **Savings vs General Baseline**:
   $$\text{Contract Savings \%} = \frac{\text{General Catalog Rate} - \text{Min Rate}}{\text{General Catalog Rate}} \times 100$$

---

## 5. Visual Highlighting Rules

- **Winning Rate Badge (`badge-best`)**: Background `rgba(16, 185, 129, 0.16)`, Text `#34d399` (Emerald Green). Applied to the lowest rate for that specific item and volume slab.
- **Variance Badge (`badge-higher`)**: Displays relative premium (e.g. `+1.7%`) above the lowest available vendor contract.
- **General Baseline Column**: Highlighted in subtle amber tint (`rgba(245, 158, 11, 0.08)`) to clearly distinguish standard catalog pricing from contractual pricing.

---

## 6. TypeScript Interfaces & Data Contracts

```typescript
export interface MatrixPartyRate {
  party_id: number;
  party_name: string;
  price_list_code: string;
  rate: number;
  is_best_rate: boolean;
  variance_percent: number;
  payment_terms?: string;
  lead_time_days?: number;
}

export interface MatrixRow {
  item_id: number;
  item_name: string;
  technical_spec: string;
  volume_slab: string;
  min_quantity: number;
  max_quantity: number | null;
  general_benchmark_rate: number;
  lowest_rate: number;
  party_rates: Record<number, MatrixPartyRate>; // Keyed by party_id
}

export interface MultiPartyMatrixResponse {
  financial_year: string;
  category: 'yarn_procurement' | 'commercial_sales' | 'job_work';
  participating_parties: Array<{ id: number; name: string; code: string }>;
  rows: MatrixRow[];
  telemetry: {
    total_vendors: number;
    lowest_benchmark_sample: number;
    average_savings_percent: number;
  };
}
```

---

## 7. Operational Actions & Downstream Dispatch

When clicking the **`[Raise PO]`** or **`[Issue Job Card]`** action button on any matrix row:
1. The system captures the target `item_id`, `volume_slab`, and the `party_id` of the winning vendor.
2. The user is redirected to `/procurement/yarn-po/new?party_id=1042&item_id=5&rate=258.00`.
3. The PO Add Workflow automatically pre-hydrates the supplier, selects the contracted rate, and binds `resolved_price_list_id` to ensure complete audit compliance.

---

## 8. Implementation Reference & Developer Checklist

- [x] Functional HTML reference implementation provided at [`frontend/multi_party_price_list_matrix.html`](file:///d:/Codebase/Garments/frontend/multi_party_price_list_matrix.html).
- [x] Visual UI Mockup generated and documented in [`multi_party_pricing_matrix.md`](file:///C:/Users/USER/.gemini/antigravity-ide/brain/65c22b92-643c-4ac6-97cf-be8e7049e2a5/multi_party_pricing_matrix.md).
- [ ] Implement backend matrix selector in `apps/pricing/selectors.py` performing dynamic cross-tabulation.
- [ ] Create Next.js page at `app/(app)/pricing/party-comparison-matrix/page.tsx`.
- [ ] Connect export button to streaming Excel spreadsheet download (`xlsx`).
