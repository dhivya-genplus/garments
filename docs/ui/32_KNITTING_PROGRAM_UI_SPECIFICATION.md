# Knitting Program Job Card & Production Planning Specification

| Standard Code | Screen ID | Target Platform | API Version | Document Version | Date | Status |
|---|---|---|---|---|---|---|
| **STD-UI-001** | **`SCR-KNIT-001`** | Next.js 14 (App Router) + TypeScript | `v1.2` (Django 5 DRF) | `v1.0.0` | 16/10/2026 | **APPROVED FOR IMPLEMENTATION** |

---

## 1. Document Overview, Version, Scope, and Status

### 1.1 Purpose
This specification defines the complete technical architecture, UI layout, production calculations, yarn feeder breakdown matrix, Zod validation schema, TypeScript interfaces, and backend API integration for the **Knitting Program (Job Card) Production Desk** (`SCR-KNIT-001`).

In the circular and flat knitting manufacturing lifecycle, the Knitting Program serves as the central technical job-order instructing the knitting subcontractor (`KNITTING_UNIT`) or in-house knitting unit:
1. **Target Fabric Technical Specifications**: Target Fabric SKU (`FabricMaster`), Fabric Structure (`FabricTypeMaster`: Single Jersey, Rib, Interlock, Fleece, Pique), Machine Diameter (Dia, e.g. 24", 30", 34"), Machine Gauge (e.g. 24GG, 28GG), Grams per Square Meter (GSM, e.g. 160, 180, 220), and Loop/Stitch Length (e.g. 2.70 mm).
2. **Yarn Feeder & Blend Allocation**: Line-item yarn specifications (`yarn_count`, `color_shade`, `yarn_type`, `blend_ratio_percent`) across circular knitting feeders (e.g., 96-feeder, 108-feeder machines) calculating precise required yarn weights per count.
3. **Loss & Allowance Computation**: Expected process loss percentage ($\text{Loss } \% \approx 2.0\% - 4.5\%$) to calculate total gross yarn requirement from target net fabric weight.
4. **Execution Telemetry**: Tracking issued yarn quantity vs. received fabric weight and knitted roll count, determining knitting efficiency and variance.

### 1.2 Scope
- **Backend Models**: [`parent_knitting_program_table`](file:///d:/Codebase/Garments/backend/apps/knitting/models.py#L23-L146) (`tm_knitting_program`) and [`child_knitting_program_yarn_table`](file:///d:/Codebase/Garments/backend/apps/knitting/models.py#L147-L175) (`tx_knitting_program_yarn`).
- **Country Pack**: India (`IN`) — Indian Rupee (`₹`), Metric units (Kg, Rolls, Dia in inches, GSM in $\text{g/m}^2$, Loop length in mm).
- **Target Route**: `/production/knitting-program` and `/production/knitting-program/[id]` (Next.js route: `app/(app)/production/knitting-program/page.tsx`).

---

## 2. Module Details, Screen ID, Route, Access Privileges, and API Endpoints

### 2.1 Core Metadata

| Parameter | Specification |
|---|---|
| **Module** | `Module 6 — Knitting & Fabric Production` |
| **Screen ID** | `SCR-KNIT-001` |
| **Frontend Route** | `/production/knitting-program` (List/Manage), `/production/knitting-program/new` (Add Job Card) |
| **File Location** | `app/(app)/production/knitting-program/page.tsx` & `new/page.tsx` |
| **Required Privilege** | `knitting_program.can_read` (View programs); `knitting_program.can_create` (Issue Job Card); `knitting_program.can_update` (Edit); `knitting_program.can_release` (Authorize release) |
| **Authorized Roles** | `SUPER_ADMIN`, `ADMIN_USER`, `COMPANY_USER` (Production Manager, Knitting Master, Merchandiser) |
| **Country Pack** | `IN` (India: Currency INR `₹`, Date `DD/MM/YYYY`, Decimal precision: Weight 3 dp `0.000 Kg`, Money 2 dp `₹ 0.00`, Rate 2 dp `₹ 0.00/Kg`) |

### 2.2 Primary API Endpoints

| HTTP Method | API Path | Privilege / Scope | Description |
|---|---|---|---|
| `GET` | `/api/v1/knitting/programs/` | `can_read` | Fetch filtered knitting program register with search, status, and pagination |
| `POST` | `/api/v1/knitting/programs/` | `can_create` | Create a new Knitting Program Job Card with feeder yarn breakdown |
| `GET` | `/api/v1/knitting/programs/{id}/` | `can_read` | Retrieve single program details, yarn lines, and inward reconciliation |
| `PATCH` / `PUT` | `/api/v1/knitting/programs/{id}/` | `can_update` | Modify draft job card parameters, delivery schedules, or rates |
| `POST` | `/api/v1/knitting/programs/{id}/release/` | `can_release` | Release job card from Draft to Released (locks technical specs, enables yarn DC outward) |
| `POST` | `/api/v1/knitting/programs/{id}/complete/` | `can_update` | Mark program completed when fabric inward target is met |
| `POST` | `/api/v1/knitting/programs/{id}/cancel/` | `can_delete` | Cancel job card and release yarn reservations |

---

## 3. UI Layout, Screen Blueprint, and Visual Mockup (1440px+ Wireframe)

```
+-----------------------------------------------------------------------------------------------------------------------------+
| GARMENTS ERP — Knitting Production Management                                Company: ABC Textiles Ltd | FY: 2026-2027      |
+-----------------------------------------------------------------------------------------------------------------------------+
| BREADCRUMB: Production > Knitting Programs > New Job Card                                  [Ctrl+S: Save Draft] [Esc: Back] |
+-----------------------------------------------------------------------------------------------------------------------------+
| SECTION 1: HEADER & JOB-WORK SUBCONTRACTOR DETAILS                                                                          |
| Program No: [ KP-2026-0042        ] (Auto)  Date: [ 16/10/2026 ]  Delivery Due: [ 26/10/2026 ]  Status: [ DRAFT (Badge)   ] |
| Knitter (Party): [ Sri Venkateswara Knitting Mills (Coimbatore) - GSTIN: 33AAAAA0000A1Z5                           | v ] [Search] |
| Receiving Warehouse: [ Main Greige Fabric Godown - Tirupur                                                         | v ]    |
+-----------------------------------------------------------------------------------------------------------------------------+
| SECTION 2: TARGET FABRIC TECHNICAL SPECIFICATIONS                                                                           |
| Fabric Name: [ 100% Combed Cotton Single Jersey             | v ]  Fabric Type: [ Single Jersey (Weft Knitted)         | v ]|
| Machine Dia: [ 30" (Inches)       ]  Gauge: [ 24 GG               ]  Target GSM: [ 160 g/m²   ]  Loop Length: [ 2.70 mm   ] |
| Planned Rolls: [ 120 Rolls        ]  Target Fabric Qty: [ 2,400.000 Kg ]  Expected Loss: [ 2.50 % ] Gross Yarn: [ 2,460.000 Kg ]|
| Knitting Job Rate: [ ₹ 18.50 / Kg ]  Estimated Job Work Total: [ ₹ 44,400.00 (Excl GST) ]                                    |
+-----------------------------------------------------------------------------------------------------------------------------+
| SECTION 3: YARN FEEDER ALLOCATION & COMPOSITION MATRIX                                         [+ Add Yarn Feeder Line]     |
| # | Yarn Count SKU     | Color Shade      | Yarn Category | Blend % | Planned Qty (Kg) | Issued Qty (Kg) | Balance To Issue |
|---|--------------------|------------------|---------------|---------|------------------|-----------------|------------------|
| 1 | 30s Combed Cotton  | Raw White / Grey | GREY          |  95.00% |     2,337.000 Kg |    2,337.000 Kg |         0.000 Kg |
| 2 | 20D Spandex/Lycra  | Semi Dull        | SPANDEX       |   5.00% |       123.000 Kg |      123.000 Kg |         0.000 Kg |
|   | TOTALS             |                  |               | 100.00% |     2,460.000 Kg |    2,460.000 Kg |         0.000 Kg |
+-----------------------------------------------------------------------------------------------------------------------------+
| SECTION 4: PRODUCTION EXECUTION & YIELD RECONCILIATION                                                                       |
| Total Yarn Dispatched: [ 2,460.000 Kg ]  | Fabric Received: [ 2,392.500 Kg ]  | Actual Process Loss: [ 2.74% (67.500 Kg) ]   |
| Total Rolls Received : [ 119 Rolls    ]  | Target Yield   : [ 97.26 %       ]  | Knitter Balance Outstanding: [ 0.000 Kg  ]   |
+-----------------------------------------------------------------------------------------------------------------------------+
| REMARKS: [ Lycra plating required on alternate feeders. Inspect fabric for needle lines and spirality before roll packing. ]|
| ACTION BUTTONS: [ Cancel ]    [ Save Draft (F8) ]    [ Release Program for Yarn DC (F9) ]    [ Print Job Card Sheet (Ctrl+P) ]|
+-----------------------------------------------------------------------------------------------------------------------------+
```

---

## 4. UX Workflow, Step-by-Step Lifecycle, and Edge-Case Handling

### 4.1 Step-by-Step Lifecycle
1. **Creation (Draft)**:
   - Production merchandiser initiates a new Knitting Program (`SCR-KNIT-001`).
   - Selects Knitter (`PartyMaster` filtered by `party_type = 'KNITTING_UNIT'`).
   - Selects Target Fabric (`FabricMaster`) and Fabric Structure (`FabricTypeMaster`).
   - Specifies machine parameters (Diameter, Gauge, GSM, Loop Length).
   - Inputs Planned Net Fabric Quantity ($Q_{\text{fabric}}$ in Kg) and expected loss percentage ($L_{\text{loss}} \approx 2.0\% - 4.5\%$).
   - System automatically calculates the gross yarn required ($Q_{\text{gross}}$).
2. **Feeder Breakdown**:
   - Merchandiser populates feeder yarn lines.
   - For single-blend cotton fabrics: 100% Cotton 30s or 40s.
   - For Lycra single jersey: e.g. 95% 30s Cotton + 5% 20D Spandex/Lycra.
   - System verifies that $\sum \text{blend\_ratio\_percent} = 100.00\%$.
   - System dynamically computes line-item required quantities based on blend proportions.
3. **Authorization & Release**:
   - Authorized Production Head reviews technical specs and clicks **Release Program (F9)**.
   - Program moves from `DRAFT` ($0$) to `RELEASED` ($1$).
   - Releasing unlocks the program in Yarn Outward Delivery Challan (`SCR-INVN-002-ADD`), allowing warehouse staff to allocate and dispatch yarn bags specifically linked to this program ID.
4. **Execution & Real-Time Tracking**:
   - As yarn is dispatched via Delivery Challans, `issued_yarn_quantity` updates.
   - As knitted rolls are received via Grey Fabric Inward (`SCR-INVN-003-ADD`), `received_fabric_quantity` and rolls count update.
   - Once all fabric is received, user marks the program as `COMPLETED` ($3$).

### 4.2 Edge-Case Handling
- **Blend Proportion Mismatch**: If sum of yarn lines does not equal $100.00\%$, form submission is blocked with error: *"Total blend ratio must equal exactly 100.00% (Current: 98.50%)"*.
- **Excessive Process Loss**: If actual received fabric results in a process loss exceeding tolerance by $>1.5\%$ (e.g. $>4.0\%$), a visual warning alert is raised requiring Knitter debit note approval.
- **Yarn Negative Issue**: Yarn Outward DC prevents dispatching more than $110\%$ of planned yarn without explicit supervisor override.

---

## 5. Form Sections, Field Matrix, and Validation Rules

| Section | Field Label | Field Key | Input Type | Required | Default | Validation & Rules |
|---|---|---|---|---|---|---|
| **Header** | Program Number | `program_number` | Text (Readonly) | Yes | Auto `KP-YYYY-XXXX` | Unique document sequence generated by backend |
| **Header** | Program Date | `program_date` | DatePicker | Yes | Current Date | Format `DD/MM/YYYY`, must fall in active FY |
| **Header** | Delivery Due Date | `delivery_date` | DatePicker | No | `program_date + 10d`| Must be $\ge$ `program_date` |
| **Header** | Knitter Unit | `knitter_id` | Searchable Select | Yes | None | Must be active Party with `party_type = 'KNITTING_UNIT'` |
| **Header** | Receiving Warehouse | `warehouse_id` | Select | Yes | Default Godown | Active `WarehouseMaster` |
| **Fabric Spec** | Target Fabric | `fabric_id` | Searchable Select | Yes | None | Active `FabricMaster` |
| **Fabric Spec** | Fabric Structure | `fabric_type_id` | Select | Yes | None | Active `FabricTypeMaster` |
| **Fabric Spec** | Machine Dia | `dia` | Text / Select | Yes | `30"` | Values: 20", 24", 26", 28", 30", 32", 34", 36" |
| **Fabric Spec** | Gauge | `gauge` | Text / Select | Yes | `24 GG` | Values: 20GG, 24GG, 28GG, 32GG |
| **Fabric Spec** | Target GSM | `gsm` | Number (Integer) | Yes | `160` | Range: 80 to 450 $\text{g/m}^2$ |
| **Fabric Spec** | Loop Length | `loop_length` | Text | No | `2.70` | Stitch length in mm (e.g. `2.65 - 2.75`) |
| **Fabric Spec** | Planned Rolls | `planned_rolls` | Number (Integer) | Yes | `1` | $\ge 1$ |
| **Fabric Spec** | Target Net Fabric Qty | `planned_fabric_quantity` | Number (3 dp) | Yes | `0.000` | $\gt 0.000$ Kg |
| **Fabric Spec** | Expected Loss % | `expected_loss_percent` | Number (2 dp) | Yes | `2.00` | Range: $0.00\%$ to $10.00\%$ |
| **Fabric Spec** | Total Gross Yarn Req | `total_yarn_required` | Number (3 dp, Readonly) | Yes | Auto-computed | $Q_{\text{gross}} = Q_{\text{net}} \times (1 + \frac{\text{Loss}}{100})$ |
| **Fabric Spec** | Knitting Rate / Kg | `knitting_rate` | Number (2 dp) | Yes | `0.00` | Subcontract rate per Kg in INR $₹$ |
| **Yarn Line** | Yarn Count SKU | `yarn_count_id` | Searchable Select | Yes | None | Active `YarnCountMaster` |
| **Yarn Line** | Color Shade | `color_shade_id` | Searchable Select | No | `GREY` | Active `ColorShadeMaster` |
| **Yarn Line** | Yarn Category | `yarn_type` | Select | Yes | `GREY` | Enum: `GREY`, `DYED`, `MELANGE`, `SPANDEX` |
| **Yarn Line** | Blend Ratio % | `blend_ratio_percent` | Number (2 dp) | Yes | `100.00` | Sum of all lines must equal $100.00\%$ |
| **Yarn Line** | Planned Quantity | `planned_quantity` | Number (3 dp, Readonly) | Yes | Auto-computed | $Q_{\text{line}} = Q_{\text{gross}} \times \frac{\text{Blend } \%}{100}$ |

---

## 6. Mathematical Formulas and Calculation Specifications (LaTeX)

### 6.1 Total Gross Yarn Requirement
Given target net fabric output $Q_{\text{fabric}}$ in kilograms and expected knitting process loss percentage $L_{\text{loss}}$:

$$\text{Loss Factor} = 1 + \left(\frac{L_{\text{loss}}}{100}\right)$$

$$Q_{\text{gross}} = \operatorname{Round}\left(Q_{\text{fabric}} \times \left(1 + \frac{L_{\text{loss}}}{100}\right), 3\right)$$

### 6.2 Yarn Feeder Line Allocation
For each yarn feeder line $i \in \{1, \dots, n\}$ with blend percentage $B_i$:

$$\sum_{i=1}^{n} B_i = 100.00\%$$

$$Q_{\text{yarn}, i} = \operatorname{Round}\left(Q_{\text{gross}} \times \frac{B_i}{100}, 3\right)$$

### 6.3 Estimated Job Work Amount
Given agreed knitting rate $R_{\text{knit}}$ per kg:

$$\text{Total Knitting Amount} = \operatorname{Round}\left(Q_{\text{fabric}} \times R_{\text{knit}}, 2\right)$$

### 6.4 Actual Process Loss and Yield Variance
Upon receiving finished fabric $Q_{\text{recv}}$ against dispatched yarn $Q_{\text{issued}}$:

$$\text{Actual Loss (Kg)} = Q_{\text{issued}} - Q_{\text{recv}}$$

$$\text{Actual Loss } \% = \operatorname{Round}\left(\frac{Q_{\text{issued}} - Q_{\text{recv}}}{Q_{\text{issued}}} \times 100, 2\right)$$

$$\text{Loss Variance } \% = \text{Actual Loss } \% - L_{\text{loss}}$$

---

## 7. Dynamic Behaviors, Conditional Fields, and Interactivity

1. **Auto Feeder Pro-Rating**:
   - Changing `planned_fabric_quantity` or `expected_loss_percent` instantly triggers recalculation across all existing yarn feeder lines in real time without screen refresh.
2. **Preset Loop Length & Dia Lookup**:
   - Selecting a target fabric and GSM auto-populates standard recommended Dia and Gauge based on company knitting machine standards (e.g. 30" Dia + 24 GG for 160 GSM single jersey).
3. **Status Workflow Progression**:
   - `DRAFT` ($0$): All fields editable; yarn feeder lines can be added/removed.
   - `RELEASED` ($1$): Technical specs locked; Delivery Challans can be created against this Program ID; Rate editable by Accounts.
   - `IN_PROGRESS` ($2$): Yarn dispatched and fabric inward underway.
   - `COMPLETED` ($3$): Fabric inward complete, program closed.

---

## 8. API Request / Response Contracts (DTOs)

### 8.1 Create Knitting Program Request (`POST /api/v1/knitting/programs/`)

```json
{
  "program_date": "16/10/2026",
  "delivery_date": "26/10/2026",
  "knitter": 4,
  "warehouse": 2,
  "fabric": 7,
  "fabric_type": 3,
  "dia": "30\"",
  "gauge": "24 GG",
  "gsm": 160,
  "loop_length": "2.70",
  "planned_rolls": 120,
  "planned_fabric_quantity": "2400.000",
  "expected_loss_percent": "2.50",
  "knitting_rate": "18.50",
  "remarks": "Use high-tenacity Lycra on feeder 4 and 8",
  "yarn_lines": [
    {
      "yarn_count": 12,
      "color_shade": null,
      "yarn_type": "GREY",
      "blend_ratio_percent": "95.00",
      "planned_quantity": "2337.000"
    },
    {
      "yarn_count": 18,
      "color_shade": null,
      "yarn_type": "SPANDEX",
      "blend_ratio_percent": "5.00",
      "planned_quantity": "123.000"
    }
  ]
}
```

### 8.2 Success Response Envelope (`HTTP 201 Created`)

```json
{
  "success": true,
  "message": "Knitting Program KP-2026-0042 created successfully in Draft status.",
  "data": {
    "id": 42,
    "program_number": "KP-2026-0042",
    "program_date": "16/10/2026",
    "delivery_date": "26/10/2026",
    "knitter_id": 4,
    "knitter_name": "Sri Venkateswara Knitting Mills",
    "warehouse_id": 2,
    "warehouse_name": "Main Greige Fabric Godown",
    "fabric_id": 7,
    "fabric_name": "100% Combed Cotton Single Jersey",
    "fabric_type_id": 3,
    "fabric_type_name": "Single Jersey",
    "dia": "30\"",
    "gauge": "24 GG",
    "gsm": 160,
    "loop_length": "2.70",
    "planned_rolls": 120,
    "planned_fabric_quantity": "2400.000",
    "expected_loss_percent": "2.50",
    "total_yarn_required": "2460.000",
    "issued_yarn_quantity": "0.000",
    "received_fabric_quantity": "0.000",
    "knitting_rate": "18.50",
    "total_knitting_amount": "44400.00",
    "status": 0,
    "status_display": "DRAFT",
    "yarn_lines": [
      {
        "id": 108,
        "yarn_count_id": 12,
        "yarn_count_display": "30s Combed Cotton",
        "color_shade_id": null,
        "yarn_type": "GREY",
        "blend_ratio_percent": "95.00",
        "planned_quantity": "2337.000",
        "issued_quantity": "0.000"
      },
      {
        "id": 109,
        "yarn_count_id": 18,
        "yarn_count_display": "20D Spandex/Lycra",
        "color_shade_id": null,
        "yarn_type": "SPANDEX",
        "blend_ratio_percent": "5.00",
        "planned_quantity": "123.000",
        "issued_quantity": "0.000"
      }
    ],
    "created_at": "16/10/2026 17:15",
    "created_by": "arun.kumar"
  }
}
```

---

## 9. Client-Side State Management and Component Architecture

```
app/(app)/production/knitting-program/
├── page.tsx                             # Server-side data fetcher & program list register
├── new/
│   └── page.tsx                         # Client-side new job card entry form
├── [id]/
│   ├── page.tsx                         # Program execution telemetry & tracking desk
│   └── edit/
│       └── page.tsx                     # Program amendment workflow
└── components/
    ├── KnittingHeaderCard.tsx           # Subcontractor, date, and status badges
    ├── FabricTechnicalSpecsCard.tsx     # Dia, Gauge, GSM, Loop length, Loss % inputs
    ├── YarnFeederAllocationTable.tsx    # Feeder yarn breakdown matrix with pro-rating
    ├── ProductionYieldProgressCard.tsx  # Telemetry bar comparing issued yarn vs fabric
    └── KnittingProgramPrintModal.tsx    # Technical job card print preview
```

---

## 10. Zod Validation Schema (Copy-Paste Production Code)

```typescript
import { z } from "zod";

const dateRegex = /^(0[1-9]|[12][0-9]|3[01])\/(0[1-9]|1[0-2])\/\d{4}$/;

export const YarnFeederLineSchema = z.object({
  yarn_count_id: z.number().int().positive({ message: "Yarn count is required." }),
  color_shade_id: z.number().int().positive().nullable().optional(),
  yarn_type: z.enum(["GREY", "DYED", "MELANGE", "SPANDEX"], {
    errorMap: () => ({ message: "Select a valid yarn type." }),
  }),
  blend_ratio_percent: z
    .number()
    .min(0.01, { message: "Blend ratio must be greater than 0%." })
    .max(100.0, { message: "Blend ratio cannot exceed 100%." }),
  planned_quantity: z.number().min(0.001, { message: "Planned quantity must be greater than 0 Kg." }),
});

export const KnittingProgramCreateSchema = z
  .object({
    program_date: z.string().regex(dateRegex, { message: "Date must be DD/MM/YYYY" }),
    delivery_date: z.string().regex(dateRegex, { message: "Due date must be DD/MM/YYYY" }).optional(),
    knitter_id: z.number().int().positive({ message: "Knitting unit subcontractor is required." }),
    warehouse_id: z.number().int().positive({ message: "Receiving warehouse is required." }),
    fabric_id: z.number().int().positive({ message: "Fabric SKU is required." }),
    fabric_type_id: z.number().int().positive({ message: "Fabric structure is required." }),
    dia: z.string().min(1, { message: "Machine diameter (Dia) is required." }),
    gauge: z.string().min(1, { message: "Machine gauge is required." }),
    gsm: z.number().int().min(50, { message: "GSM must be at least 50." }).max(500),
    loop_length: z.string().optional(),
    planned_rolls: z.number().int().min(1, { message: "Planned roll count must be at least 1." }),
    planned_fabric_quantity: z
      .number()
      .min(1.0, { message: "Planned fabric quantity must be at least 1.000 Kg." }),
    expected_loss_percent: z
      .number()
      .min(0.0, { message: "Loss cannot be negative." })
      .max(10.0, { message: "Loss % cannot exceed 10.0%." }),
    knitting_rate: z.number().min(0.0, { message: "Knitting rate cannot be negative." }),
    remarks: z.string().max(255).optional(),
    yarn_lines: z.array(YarnFeederLineSchema).min(1, { message: "At least one yarn feeder line is required." }),
  })
  .refine(
    (data) => {
      const sum = data.yarn_lines.reduce((acc, line) => acc + line.blend_ratio_percent, 0);
      return Math.abs(sum - 100.0) < 0.05;
    },
    {
      message: "The sum of all blend ratios must equal exactly 100.00%.",
      path: ["yarn_lines"],
    }
  );

export type KnittingProgramCreateFormData = z.infer<typeof KnittingProgramCreateSchema>;
```

---

## 11. TypeScript Interfaces & Enums (Complete DTO Declarations)

```typescript
export enum KnittingProgramStatus {
  DRAFT = 0,
  RELEASED = 1,
  IN_PROGRESS = 2,
  COMPLETED = 3,
  CANCELLED = 4,
}

export interface IYarnFeederLineDTO {
  id?: number;
  yarn_count_id: number;
  yarn_count_display?: string;
  color_shade_id?: number | null;
  color_shade_name?: string | null;
  yarn_type: "GREY" | "DYED" | "MELANGE" | "SPANDEX";
  blend_ratio_percent: number;
  planned_quantity: number;
  issued_quantity?: number;
}

export interface IKnittingProgramDTO {
  id: number;
  program_number: string;
  program_date: string;
  delivery_date?: string;
  knitter_id: number;
  knitter_name: string;
  knitter_gstin?: string;
  warehouse_id: number;
  warehouse_name: string;
  fabric_id: number;
  fabric_name: string;
  fabric_type_id: number;
  fabric_type_name: string;
  dia: string;
  gauge: string;
  gsm: number;
  loop_length?: string;
  planned_rolls: number;
  planned_fabric_quantity: number;
  expected_loss_percent: number;
  total_yarn_required: number;
  issued_yarn_quantity: number;
  received_fabric_quantity: number;
  knitting_rate: number;
  total_knitting_amount: number;
  status: KnittingProgramStatus;
  status_display: "DRAFT" | "RELEASED" | "IN_PROGRESS" | "COMPLETED" | "CANCELLED";
  remarks?: string;
  yarn_lines: IYarnFeederLineDTO[];
  created_at: string;
  created_by: string;
  updated_at?: string;
}
```

---

## 12. Keyboard Shortcuts and Rapid Operations

| Key Combination | Action / Trigger | Scope / View |
|---|---|---|
| `Alt + N` | Open New Knitting Program Creator | Program List View |
| `Ctrl + S` | Save Program in `DRAFT` status | Job Card Creator / Editor |
| `F9` | **Release Program** (Locks specs, enables yarn DC) | Job Card Creator / Editor |
| `Alt + A` | Append new Yarn Feeder Row | Feeder Table Section |
| `Ctrl + P` | Open Technical Job Card Print PDF | Program Detail / View |
| `Esc` | Close modal or cancel row edit | Any Active Modal |

---

## 13. Responsive Breakpoints and Mobile Adaptation

| Viewport Width | Screen Category | Layout Behavior |
|---|---|---|
| $\ge 1440\text{px}$ | Desktop Enterprise | 4-column technical specification grid, full width Feeder matrix, inline telemetry |
| $1024\text{px} - 1439\text{px}$ | Laptop / Tablet Landscape | 2-column technical specification cards, horizontal scroll on Feeder matrix |
| $\le 1023\text{px}$ | Tablet Portrait / Mobile | Single column accordion layout, stacked feeder cards with ratio summaries |

---

## 14. Error Handling and User Feedback

| Scenario / Error Trigger | Visual Presentation | Remediation Action |
|---|---|---|
| Blend ratio sum $\neq 100.00\%$ | Red banner alert under feeder table + submit button disabled | Auto-normalize button provided to scale lines to $100.00\%$ |
| Delivery date before Program date | Field validation error on date picker | Highlight input in red, focus on `delivery_date` |
| Attempt to edit released program | Modal warning dialog: *"Program has yarn dispatches. Create amendment?"* | Route to versioned amendment workflow |

---

## 15. Loading, Empty, and Edge States

- **Loading State**: Skeleton card placeholders for Technical Specifications, feeder matrix, and yield gauges.
- **Empty State**: Illustrated vector showing circular knitting machine with text: *"No active knitting programs found. Click [Alt+N] to create a new job card."*
- **Partial Dispatch State**: Amber telemetry pill showing: *"Yarn Dispatch 65% (1,600 / 2,460 Kg) — 1 DC Pending"*.

---

## 16. Accessibility (a11y) Conformance (WCAG 2.1 AA)

- All inputs tagged with explicit `aria-labelledby` and `aria-describedby` referencing error tags.
- Tab sequence strictly ordered: Header $\rightarrow$ Fabric Specs $\rightarrow$ Feeder Table $\rightarrow$ Action Buttons.
- High-contrast badges for program status (`DRAFT`: Slate, `RELEASED`: Blue, `IN_PROGRESS`: Amber, `COMPLETED`: Green).

---

## 17. Security, RBAC, and Audit Logging

- **Role Verification**: Only users holding `knitting_program.can_release` can transition a program from `DRAFT` to `RELEASED`.
- **Company Scoping**: All queries inject active session `company_id` and `cfyear_id`. Cross-tenant leaks strictly blocked.
- **Audit Logging**: Modifications write to `ta_audit_log` capturing previous technical specs (Dia, Gauge, GSM) and modified feeder percentages.

---

## 18. Test Cases and Acceptance Criteria

### 18.1 Acceptance Criteria
1. Given target fabric of $2,400.000\text{ Kg}$ and $2.50\%$ loss, total required yarn must equal $2,460.000\text{ Kg}$.
2. Feeder yarn allocation must sum to exactly $100.00\%$ before releasing.
3. Releasing program allows selecting this program ID in Yarn Delivery Challan (`SCR-INVN-002-ADD`).
4. Incurring greige fabric inward updates received weight and rolls balance in real time.

---

## 19. Performance Budgets and Optimization Targets

- Initial page load time: $< 800\text{ms}$ on 4G connections.
- Feeder line re-calculation latency: $< 15\text{ms}$ client-side execution.
- API response time for program creation: $< 250\text{ms}$ on Django DRF backend.

---

## 20. Future Enhancements and Scalability Roadmap

1. **Barcode / QR Code Generation**: Printing machine-readable QR codes on Knitting Job Cards for scanning at knitting machine terminals.
2. **Yarn Lot Reservation**: Hard-allocating specific yarn lots from godown inventory directly upon program release.
3. **IoT Knitter Machine Telemetry**: Real-time roll completion counter sync from circular knitting machines.

---

## 21. Sign-off and Approval Matrix

| Stakeholder Role | Name / Title | Date | Signature / Status |
|---|---|---|---|
| **Production Head** | Ramanathan S. (VP Manufacturing) | 16/10/2026 | **APPROVED** |
| **Lead Architect** | Enterprise Garments Solutions | 16/10/2026 | **APPROVED** |
| **Quality Manager** | Meenakshi Sundaram | 16/10/2026 | **APPROVED** |
