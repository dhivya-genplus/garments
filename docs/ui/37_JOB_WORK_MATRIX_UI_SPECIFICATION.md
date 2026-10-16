# Job Work Subcontract Conversion Rate Matrix & Pricing Engine Specification

| Standard Code | Screen ID | Target Platform | API Version | Document Version | Date | Status |
|---|---|---|---|---|---|---|
| **STD-UI-001** | **`SCR-PRIC-002`** | Next.js 14 (App Router) + TypeScript | `v1.2` (Django 5 DRF) | `v1.0.0` | 16/10/2026 | **APPROVED FOR IMPLEMENTATION** |

---

## 1. Document Overview, Version, Scope, and Status

### 1.1 Purpose
This specification defines the complete technical architecture, UI layout, multi-tier pricing resolution matrix, technical parameter matching (Fabric structure, Gauge, Dia, Lycra plating, Shade depth, Print colors), Zod validation schema, TypeScript interfaces, and backend API integration for the **Textile Job Work Subcontract Conversion Pricing Engine** (`SCR-PRIC-002`).

In textile manufacturing, converting yarn into finished garments relies heavily on specialized external job workers (Knitting units, Dye houses, Rotary/Chest printing mills, Compacting units, Cutting floors, and Stitching assemblies). Subcontract conversion charges are not fixed commodity prices; they vary deterministically based on complex technical dimensions:
1. **Knitting Conversion Matrix**:
   - Fabric Structure (`Single Jersey`, `Rib 1x1`, `Interlock`, `Fleece`, `Pique`)
   - Machine Gauge (e.g. 24GG, 28GG) & Diameter range (20"-34")
   - Lycra / Spandex plating surcharge ($+\text{₹ 4.00 - ₹ 8.00 / Kg}$)
2. **Dyeing & Bleaching Conversion Matrix**:
   - Shade Category Depth: `BLEACH` / `WHITE` ($+\text{₹ 0}$), `LIGHT` ($+\text{₹ 12/Kg}$), `MEDIUM` ($+\text{₹ 24/Kg}$), `DARK` ($+\text{₹ 38/Kg}$), `EXTRA_DARK` / `BLACK` ($+\text{₹ 55/Kg}$)
   - Dye Class: `REACTIVE`, `DISPERSE`, `VAT`
   - Special chemical finishes (Bio-polishing, Silicon softener, Anti-microbial)
3. **Printing & Garment Assembly Matrix**:
   - Chest / Rotary screen count (1-color up to 12-color setups)
   - Garment Style Category (`Crew Neck Tee`, `Polo with Collar`, `Hooded Jacket`)
4. **Commercial Safeguards**:
   - Minimum Order Quantity (MOQ) thresholds and Small Lot Surcharges (e.g. $+\text{₹ 1,500}$ if order $< 250\text{ Kg}$)
   - Process turnaround lead times (`procurement_days` + `process_days`)
   - Contractual allowed process loss allowances ($1.5\% - 5.0\%$)

### 1.2 Scope
- **Backend Model**: [`PriceListJobRule`](file:///d:/Codebase/Garments/backend/apps/pricing/models.py#L139-L208) (`tm_price_list_job_rule`).
- **Backend Resolution API**: [`/api/v1/pricing/resolve/`](file:///d:/Codebase/Garments/backend/apps/pricing/views.py) (7-tier deterministic pricing resolution engine).
- **Country Pack**: India (`IN`) — Indian Rupee (`₹`), Rate precision to 4 decimal places (`₹ 0.0000 / Kg`).
- **Target Route**: `/pricing/job-work-rules` (Next.js route: `app/(app)/pricing/job-work-rules/page.tsx`).

---

## 2. Module Details, Screen ID, Route, Access Privileges, and API Endpoints

### 2.1 Core Metadata

| Parameter | Specification |
|---|---|
| **Module** | `Module 9 — Commercial Pricing Engine` |
| **Screen ID** | `SCR-PRIC-002` |
| **Frontend Route** | `/pricing/job-work-rules` |
| **File Location** | `app/(app)/pricing/job-work-rules/page.tsx` |
| **Required Privilege** | `pricing_rule.can_read` (View rate matrix); `pricing_rule.can_create` (Add rate rule); `pricing_rule.can_update` (Edit rates); `pricing_rule.can_override` (Manual price override) |
| **Authorized Roles** | `SUPER_ADMIN`, `ADMIN_USER`, `COMPANY_USER` (Merchandising Head, Costing Accountant, Production VP) |
| **Country Pack** | `IN` (India: Currency INR `₹`, Date `DD/MM/YYYY`, Rate 4 dp `₹ 0.0000`, Quantity 3 dp `0.000 Kg`) |

### 2.2 Primary API Endpoints

| HTTP Method | API Path | Privilege / Scope | Description |
|---|---|---|---|
| `GET` | `/api/v1/pricing/job-rules/` | `can_read` | Fetch filtered job work rate rules with search and pagination |
| `POST` | `/api/v1/pricing/lists/{list_id}/job-rules/` | `can_create` | Add a new job work conversion rule to a specific price list |
| `GET` | `/api/v1/pricing/job-rules/{id}/` | `can_read` | Retrieve single job work rule details with technical specifications |
| `PATCH` / `PUT` | `/api/v1/pricing/job-rules/{id}/` | `can_update` | Modify conversion rate, allowed loss, surcharges, or MOQ |
| `DELETE` | `/api/v1/pricing/job-rules/{id}/` | `can_update` | Soft delete rule (`record_status = 'D'`) |
| `POST` | `/api/v1/pricing/resolve/` | `can_read` | Test simulator resolving exact job rate based on technical parameters |

---

## 3. UI Layout, Screen Blueprint, and Visual Mockup (1440px+ Wireframe)

```
+-----------------------------------------------------------------------------------------------------------------------------+
| GARMENTS ERP — Job Work Subcontract Conversion Rate Matrix                   Company: ABC Textiles Ltd | FY: 2026-2027      |
+-----------------------------------------------------------------------------------------------------------------------------+
| PRICE LIST CONTEXT & STAGE SELECTION:                                                                                       |
| Price List: [ PL-2026-JW-01 — General Subcontract Processing Master Rate Card (Effective: 01/04/2026 - 31/03/2027) | v ]    |
| Process Stage: [ All Stages (Knitting, Dyeing, Printing, Compacting, Cutting, Stitching)                           | v ]    |
| Search Parameters: [ Search by Fabric / Shade / Surcharge... ]       [+ Add New Conversion Rule (Alt+N)]  [Rate Simulator]  |
+-----------------------------------------------------------------------------------------------------------------------------+
| RATE MATRIX TABS:                                                                                                           |
| [ 1. Knitting Rates (14) ]  [ 2. Dyeing Rates (22) ]  [ 3. Printing (8) ]  [ 4. Compacting (4) ]  [ 5. Cutting/Stitching (12) ]|
+-----------------------------------------------------------------------------------------------------------------------------+
| KNITTING CONVERSION RATE MATRIX TABLE:                                                                                      |
| # | Fabric Structure | Count Ref | Gauge | Dia Range | Lycra Plated | Base Rate / Kg | Allowed Loss | MOQ (Kg) | Small Lot Surch| Action |
|---|------------------|-----------|-------|-----------|--------------|----------------|--------------|----------|----------------|--------|
| 1 | Single Jersey    | 30s-40s   | 24 GG | 24"-30"   | NO           |   ₹ 18.5000    |    2.00%     |  500.000 |   ₹ 1,500.00   | [Edit] |
| 2 | Single Jersey    | 30s-40s   | 24 GG | 24"-30"   | YES (+Lycra) |   ₹ 23.0000    |    2.50%     |  500.000 |   ₹ 1,500.00   | [Edit] |
| 3 | 1x1 / 2x2 Rib    | 24s-30s   | 18 GG | 20"-24"   | NO           |   ₹ 22.0000    |    2.50%     |  300.000 |   ₹ 1,200.00   | [Edit] |
| 4 | Cotton Fleece    | 20s/10s   | 20 GG | 30"-34"   | NO           |   ₹ 26.5000    |    3.50%     |  600.000 |   ₹ 2,000.00   | [Edit] |
| 5 | Interlock        | 40s       | 28 GG | 28"-32"   | NO           |   ₹ 28.0000    |    2.20%     |  500.000 |   ₹ 1,800.00   | [Edit] |
+-----------------------------------------------------------------------------------------------------------------------------+
| DYEING CONVERSION RATE MATRIX (PREVIEW):                                                                                    |
| # | Shade Category   | Dye Class | Finish Type         | Base Rate / Kg | Surcharges / Kg | Total Rate / Kg| Allowed Loss % | Action |
|---|------------------|-----------|---------------------|----------------|-----------------|----------------|----------------|--------|
| 1 | WHITE / BLEACH   | REACTIVE  | Normal Softener     |   ₹ 42.0000    |     ₹ 0.0000    |   ₹ 42.0000    |    4.00%       | [Edit] |
| 2 | LIGHT SHADE      | REACTIVE  | Normal Softener     |   ₹ 54.0000    |     ₹ 0.0000    |   ₹ 54.0000    |    4.20%       | [Edit] |
| 3 | MEDIUM SHADE     | REACTIVE  | Bio-Polish Silicone |   ₹ 68.0000    |     ₹ 8.5000    |   ₹ 76.5000    |    4.50%       | [Edit] |
| 4 | DARK SHADE       | REACTIVE  | Bio-Polish Silicone |   ₹ 82.0000    |     ₹ 8.5000    |   ₹ 90.5000    |    4.80%       | [Edit] |
| 5 | EXTRA DARK/BLACK | REACTIVE  | Bio-Polish Silicone |   ₹ 98.0000    |     ₹ 8.5000    |  ₹ 106.5000    |    5.00%       | [Edit] |
+-----------------------------------------------------------------------------------------------------------------------------+
| SIMULATOR DRAWER: Enter (Stage: Dyeing, Shade: Dark, Finish: Bio-Polish, Qty: 400 Kg) => Resolved Rate: ₹ 90.5000 / Kg [OK]  |
| SHORTCUTS: [Alt+N: Add Rule]  [Alt+S: Open Simulator]  [Alt+E: Export Matrix]  [Esc: Close Drawer]                          |
+-----------------------------------------------------------------------------------------------------------------------------+
```

---

## 4. UX Workflow, Step-by-Step Lifecycle, and Edge-Case Handling

### 4.1 Step-by-Step Lifecycle
1. **Rule Definition**:
   - Costing accountant opens `/pricing/job-work-rules`.
   - Selects target Price List (e.g. Master Subcontract List or Party-Specific Knitter Agreement).
   - Selects Process Stage (`KNITTING`, `DYEING`, `PRINTING`, `CUTTING`, `STITCHING`).
   - Fills in matching criteria: Fabric structure, Gauge, Dia, Lycra attachment, Shade depth.
   - Enters base rate, loss tolerance percentage, lead time days, MOQ, and small lot surcharge.
2. **Deterministic Resolution**:
   - When a production order or Job Card (`SCR-KNIT-001` or `SCR-PRCS-001`) is issued, the backend calls `/api/v1/pricing/resolve/`.
   - The engine searches for matching rules:
     - Exact party-specific rule $\rightarrow$ General price list rule $\rightarrow$ Master fallback.
   - Returns resolved rate, calculated loss %, and audit log identifier.
3. **Interactive Rate Simulator**:
   - Costing merchandisers can click **[Rate Simulator (Alt+S)]** to test hypothetical orders (e.g. 180 Kg Dark Shade Single Jersey with Lycra) and verify whether small lot surcharges trigger.

### 4.2 Edge-Case Handling
- **Below-MOQ Orders**: If order quantity is below specified MOQ (e.g. $180\text{ Kg} < 500\text{ Kg}$ MOQ), the engine automatically appends the `small_lot_surcharge` ($+\text{₹ 1,500}$) to the total job-work bill.
- **Wildcard Matching**: If a rule leaves `yarn_count_id` or `machine_gauge` blank/null, it acts as a universal wildcard matching all counts for that fabric structure.

---

## 5. Form Sections, Field Matrix, and Validation Rules

| Section | Field Label | Field Key | Input Type | Required | Default | Validation & Rules |
|---|---|---|---|---|---|---|
| **Header** | Price List | `price_list_id` | Select | Yes | Master PL | Active `tm_price_list` |
| **Header** | Process Stage | `process_stage_id` | Select | Yes | None | Active `mx_process_stage` |
| **Technical**| Fabric Structure | `fabric_type_id` | Select | No | All (Wildcard) | Active `FabricTypeMaster` |
| **Technical**| Yarn Count SKU | `yarn_count_id` | Select | No | All (Wildcard) | Active `YarnCountMaster` |
| **Technical**| Machine Gauge | `machine_gauge` | Text | No | All | e.g. `24GG`, `28GG` |
| **Technical**| Machine Dia Range | `dia_range` | Text | No | All | e.g. `24-30 inches` |
| **Technical**| Lycra Plating | `is_lycra_plated` | Checkbox | No | `false` | Lycra attachment |
| **Technical**| Shade Category | `shade_category` | Select | No | All | `WHITE`, `LIGHT`, `MEDIUM`, `DARK`, `EXTRA_DARK` |
| **Commercial**| Job Work Rate / UOM | `job_rate` | Number (4 dp) | Yes | `0.0000` | Rate per Kg/Pcs in INR $₹$ |
| **Commercial**| Allowed Loss % | `allowed_loss_percent` | Number (2 dp) | Yes | `2.00` | Process loss tolerance ($0-10\%$) |
| **Commercial**| Lycra Surcharge | `lycra_surcharge` | Number (4 dp) | No | `0.0000` | Additional rate if Lycra plated |
| **Commercial**| Special Finish Surch| `special_finish_surcharge`| Number (4 dp) | No | `0.0000` | Bio-polish, silicone, etc. |
| **Commercial**| Minimum Order Qty | `moq` | Number (3 dp) | Yes | `0.000` | MOQ in Kg or Pcs |
| **Commercial**| Small Lot Surcharge| `small_lot_surcharge` | Number (2 dp) | No | `0.00` | Lump sum or per unit penalty |
| **Lead Time** | Transit Lead Days | `procurement_days` | Number (Int) | No | `2` | Transit/dispatch days |
| **Lead Time** | Process Turnaround | `process_days` | Number (Int) | Yes | `5` | Subcontract TAT in days |

---

## 6. Mathematical Formulas and Calculation Specifications (LaTeX)

### 6.1 Total Effective Job Work Unit Rate
Given Base Job Rate $R_{\text{base}}$, Lycra Surcharge $S_{\text{lycra}}$, and Finish Surcharge $S_{\text{finish}}$:

$$R_{\text{effective}} = R_{\text{base}} + (\mathbb{I}_{\text{lycra}} \times S_{\text{lycra}}) + S_{\text{finish}}$$

where $\mathbb{I}_{\text{lycra}} \in \{0, 1\}$ indicates whether the order requires Lycra/Spandex plating.

### 6.2 Total Commercial Job Work Charge with MOQ Surcharge
Given order quantity $Q_{\text{order}}$ and Minimum Order Quantity $\text{MOQ}$:

$$\text{Small Lot Charge} = \begin{cases} 
S_{\text{small\_lot}}, & \text{if } Q_{\text{order}} < \text{MOQ} \\ 
0.00, & \text{if } Q_{\text{order}} \ge \text{MOQ} 
\end{cases}$$

$$\text{Total Job Work Amount (INR)} = \operatorname{Round}\left(Q_{\text{order}} \times R_{\text{effective}} + \text{Small Lot Charge}, 2\right)$$

### 6.3 Contractual Process Loss Allowance
$$\text{Allowed Loss (Kg)} = \operatorname{Round}\left(Q_{\text{order}} \times \frac{\text{Allowed Loss } \%}{100}, 3\right)$$

---

## 7. Dynamic Behaviors, Conditional Fields, and Interactivity

1. **Stage-Specific Field Visibility**:
   - When stage is `KNITTING`: Gauge, Dia, and Lycra Plating controls are enabled; Shade Category is hidden.
   - When stage is `DYEING`: Shade Category, Dye Class, and Special Finish inputs are enabled; Gauge and Dia are hidden.
   - When stage is `PRINTING`: Screen color count and print placement controls appear.
2. **Interactive Rate Simulator**:
   - Typing sample input criteria instantly evaluates and highlights the exact matching database rule in green, showing the step-by-step resolution path.

---

## 8. API Request / Response Contracts (DTOs)

### 8.1 Create Job Work Rule Request (`POST /api/v1/pricing/lists/1/job-rules/`)

```json
{
  "process_stage_id": 1,
  "fabric_type_id": 3,
  "yarn_count_id": 12,
  "machine_gauge": "24 GG",
  "dia_range": "24-30 inches",
  "is_lycra_plated": true,
  "job_rate": "23.0000",
  "allowed_loss_percent": "2.50",
  "lycra_surcharge": "4.5000",
  "moq": "500.000",
  "small_lot_surcharge": "1500.00",
  "process_days": 4,
  "procurement_days": 1
}
```

### 8.2 Resolve Job Work Rate Request (`POST /api/v1/pricing/resolve/`)

```json
{
  "item_type": "JOB_WORK",
  "process_stage_id": 1,
  "party_id": 4,
  "fabric_type_id": 3,
  "is_lycra_plated": true,
  "quantity": "650.000"
}
```

```json
{
  "success": true,
  "data": {
    "resolved_rate": "23.0000",
    "effective_total_rate": "23.0000",
    "allowed_loss_percent": "2.50",
    "small_lot_surcharge": "0.00",
    "total_estimated_amount": "14950.00",
    "matched_rule_id": 18,
    "price_list_id": 1,
    "resolution_tier": "PARTY_JOB_RULE"
  }
}
```

---

## 9. Client-Side State Management and Component Architecture

```
app/(app)/pricing/job-work-rules/
├── page.tsx                             # Master container managing active stages and rule matrices
└── components/
    ├── JobRuleStageTabs.tsx             # Stage navigation tabs (Knitting, Dyeing, Printing)
    ├── KnittingRateMatrixTable.tsx      # Specialized gauge/dia/lycra rule table
    ├── DyeingRateMatrixTable.tsx        # Specialized shade depth/finish rule table
    ├── JobRuleCreateDrawer.tsx          # Dynamic rule creation drawer
    └── RateSimulatorModal.tsx           # Real-time pricing testing sandbox
```

---

## 10. Zod Validation Schema (Copy-Paste Production Code)

```typescript
import { z } from "zod";

export const JobWorkRuleCreateSchema = z.object({
  price_list_id: z.number().int().positive({ message: "Price list is required." }),
  process_stage_id: z.number().int().positive({ message: "Process stage is required." }),
  fabric_type_id: z.number().int().positive().nullable().optional(),
  yarn_count_id: z.number().int().positive().nullable().optional(),
  machine_gauge: z.string().optional(),
  dia_range: z.string().optional(),
  is_lycra_plated: z.boolean().default(false),
  shade_category: z.enum(["WHITE", "LIGHT", "MEDIUM", "DARK", "EXTRA_DARK"]).nullable().optional(),
  job_rate: z.number().min(0.0001, { message: "Job work rate must be greater than zero." }),
  allowed_loss_percent: z.number().min(0.0).max(15.0, { message: "Allowed loss % cannot exceed 15%." }),
  lycra_surcharge: z.number().min(0.0).default(0.0),
  special_finish_surcharge: z.number().min(0.0).default(0.0),
  moq: z.number().min(0.0).default(0.0),
  small_lot_surcharge: z.number().min(0.0).default(0.0),
  process_days: z.number().int().min(0).default(3),
  procurement_days: z.number().int().min(0).default(1),
});

export type JobWorkRuleFormData = z.infer<typeof JobWorkRuleCreateSchema>;
```

---

## 11. TypeScript Interfaces & Enums (Complete DTO Declarations)

```typescript
export interface IJobWorkRuleDTO {
  id: number;
  company_id: number;
  price_list_id: number;
  process_stage_id: number;
  process_stage_name?: string;
  fabric_type_id?: number | null;
  fabric_type_name?: string | null;
  yarn_count_id?: number | null;
  yarn_count_display?: string | null;
  machine_gauge?: string;
  dia_range?: string;
  is_lycra_plated?: boolean;
  shade_category?: "WHITE" | "LIGHT" | "MEDIUM" | "DARK" | "EXTRA_DARK" | null;
  job_rate: number;
  allowed_loss_percent: number;
  lycra_surcharge: number;
  special_finish_surcharge: number;
  moq: number;
  small_lot_surcharge: number;
  process_days: number;
  procurement_days: number;
  record_status: "A" | "I" | "D";
}
```

---

## 12. Keyboard Shortcuts and Rapid Operations

| Key Combination | Action / Trigger | Scope / View |
|---|---|---|
| `Alt + N` | Open New Job Rule Drawer | Rule Matrix View |
| `Alt + S` | Open Rate Simulator Modal | Rule Matrix View |
| `Alt + E` | Export Rate Matrix to Excel | Rule Matrix View |
| `F5` | Refresh Rate Cache | Rule Matrix View |
| `Esc` | Close Active Drawer / Modal | Any Modal |

---

## 13. Responsive Breakpoints and Mobile Adaptation

| Viewport Width | Screen Category | Layout Behavior |
|---|---|---|
| $\ge 1440\text{px}$ | Desktop Enterprise | Full matrix table with inline surcharges and simulator drawer |
| $1024\text{px} - 1439\text{px}$ | Laptop / Tablet Landscape | Horizontal scrolling matrix with sticky Rate and Actions columns |
| $\le 1023\text{px}$ | Tablet Portrait / Mobile | Collapsible rate cards with quick badge indicators for Lycra and MOQ |

---

## 14. Error Handling and User Feedback

| Scenario / Error Trigger | Visual Presentation | Remediation Action |
|---|---|---|
| Duplicate rule conflict | Red toast alert: *"Rule with identical technical specs already exists in this price list"* | Edit existing rule or add quantity tier |
| Loss % $> 10.0\%$ | Yellow warning banner under input | Prompt user for high-loss confirmation |
| Missing required stage | Red border on process stage dropdown | Select active process stage |

---

## 15. Loading, Empty, and Edge States

- **Loading State**: Shimmer table grid with 8 placeholder rows.
- **Empty State**: Calculator icon with text: *"No subcontract conversion rules defined for this stage."*
- **Wildcard Indicator**: Subtle badge *"ANY (WILDCARD)"* on unconstrained parameter fields.

---

## 16. Accessibility (a11y) Conformance (WCAG 2.1 AA)

- Tables use proper ARIA labels and rowgroup semantics.
- Interactive simulator provides live screen reader announcement of resolved rates via `aria-live="polite"`.
- Contrast ratio $\ge 4.5:1$ across all rate badges.

---

## 17. Security, RBAC, and Audit Logging

- **Privilege Scoping**: Rate modifications strictly gated by `pricing_rule.can_update`.
- **Pricing Audit Log**: Every price resolution logs into `ta_pricing_audit` recording exact input parameters and matched rule ID.
- **Tenant Isolation**: Injected `company_id` prevents cross-tenant price visibility.

---

## 18. Test Cases and Acceptance Criteria

### 18.1 Acceptance Criteria
1. Given 30s Cotton Single Jersey with Lycra, resolved knitting rate must equal $\text{Base Rate} + \text{Lycra Surcharge} = \text{₹ } 18.50 + \text{₹ } 4.50 = \text{₹ } 23.0000$.
2. Given order of $180\text{ Kg}$ against $500\text{ Kg}$ MOQ, small lot surcharge of $\text{₹ } 1,500.00$ is added to total.
3. Dark Shade dyeing reactive rule resolves to base rate plus silicone finish surcharge.

---

## 19. Performance Budgets and Optimization Targets

- Resolution API execution latency: $< 20\text{ms}$ on backend.
- Rate table filter DOM update: $< 20\text{ms}$.

---

## 20. Future Enhancements and Scalability Roadmap

1. **Volume Slab Discounts**: Automatically scaling conversion rates based on monthly cumulative tonnage committed to a subcontractor.
2. **Dynamic Yarn Feeder Matrix Sync**: Directly auto-populating job-work rates during Knitting Program creation (`SCR-KNIT-001`).

---

## 21. Sign-off and Approval Matrix

| Stakeholder Role | Name / Title | Date | Signature / Status |
|---|---|---|---|
| **Commercial Head** | Balamurugan M. (VP Commercial) | 16/10/2026 | **APPROVED** |
| **Lead Architect** | Enterprise Garments Solutions | 16/10/2026 | **APPROVED** |
| **Costing Manager** | Anandha Krishnan | 16/10/2026 | **APPROVED** |
