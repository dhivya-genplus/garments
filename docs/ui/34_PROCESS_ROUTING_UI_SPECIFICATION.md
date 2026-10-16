# Production Process Routing & Subcontract Job-Work Tracking Specification

| Standard Code | Screen ID | Target Platform | API Version | Document Version | Date | Status |
|---|---|---|---|---|---|---|
| **STD-UI-001** | **`SCR-PRCS-001`** | Next.js 14 (App Router) + TypeScript | `v1.2` (Django 5 DRF) | `v1.0.0` | 16/10/2026 | **APPROVED FOR IMPLEMENTATION** |

---

## 1. Document Overview, Version, Scope, and Status

### 1.1 Purpose
This specification defines the complete technical architecture, UI layout, multi-stage routing rules, process loss tolerances, Zod validation schema, TypeScript interfaces, and backend API integration for the **Production Process Routing & Subcontract Job-Work Engine** (`SCR-PRCS-001`).

Textile and garment manufacturing requires transforming raw fiber through multiple specialized sequential processes:
$$\text{Yarn} \xrightarrow{\text{Knitting}} \text{Grey Fabric} \xrightarrow{\text{Dyeing}} \text{Dyed Fabric} \xrightarrow{\text{Compacting}} \text{Finished Fabric} \xrightarrow{\text{Cutting}} \text{Panels} \xrightarrow{\text{Stitching}} \text{Garments}$$

The Universal Production Process Engine governs:
1. **Configurable Process Stages**: Defining stage masters (`mx_process_stage`) with sequence order, input material type, output material type, standard loss tolerances ($1.5\% - 6.0\%$), and recipe/shrinkage requirements.
2. **Universal Process Job Card (Program)**: Generating execution programs (`tm_process_program`) for any production stage (e.g., Dyeing program dispatching grey fabric rolls to a commission dye-house, or Cutting program converting dyed fabric into cut garment panels).
3. **Multi-Unit Input/Output Tracking**: Flexible unit conversion across stages (e.g. Input: Rolls/Kg $\rightarrow$ Output: Rolls/Kg for Dyeing; or Input: Rolls/Kg $\rightarrow$ Output: Cut Garment Pieces for Cutting).
4. **Subcontractor Yield & Loss Governance**: Real-time comparison of actual received yield against standard process loss limits, flagging deviations that exceed agreed contract allowances.

### 1.2 Scope
- **Backend Models**: [`parent_process_stage_table`](file:///d:/Codebase/Garments/backend/apps/process/models.py#L10-L56) (`mx_process_stage`) and [`parent_process_program_table`](file:///d:/Codebase/Garments/backend/apps/process/models.py#L58-L130) (`tm_process_program`).
- **Country Pack**: India (`IN`) — Indian Rupee (`₹`), Metric units (Kg, Pieces, Rolls, Meters), Indian Date format (`DD/MM/YYYY`).
- **Target Route**: `/production/process-routing` (Next.js route: `app/(app)/production/process-routing/page.tsx`).

---

## 2. Module Details, Screen ID, Route, Access Privileges, and API Endpoints

### 2.1 Core Metadata

| Parameter | Specification |
|---|---|
| **Module** | `Module 7 — Production Process Engine` |
| **Screen ID** | `SCR-PRCS-001` |
| **Frontend Route** | `/production/process-routing` |
| **File Location** | `app/(app)/production/process-routing/page.tsx` |
| **Required Privilege** | `process_program.can_read` (View routing & programs); `process_program.can_create` (Issue Job Card); `process_program.can_update` (Update); `process_stage.can_manage` (Configure stages) |
| **Authorized Roles** | `SUPER_ADMIN`, `ADMIN_USER`, `COMPANY_USER` (Production Head, Dyeing Manager, Merchandiser) |
| **Country Pack** | `IN` (India: Currency INR `₹`, Date `DD/MM/YYYY`, Decimal precision: Weight 3 dp `0.000 Kg`, Pieces Integer) |

### 2.2 Primary API Endpoints

| HTTP Method | API Path | Privilege / Scope | Description |
|---|---|---|---|
| `GET` | `/api/v1/process/stages/` | `can_read` | Fetch all configured production stages with routing sequences |
| `POST` | `/api/v1/process/stages/` | `can_manage` | Create or configure a new process stage (e.g. Embroidery, Bio-Wash) |
| `GET` | `/api/v1/process/programs/` | `can_read` | List process job card programs filtered by stage, party, status, and date |
| `POST` | `/api/v1/process/programs/` | `can_create` | Issue a new Process Job Card program |
| `GET` | `/api/v1/process/programs/{id}/` | `can_read` | Retrieve single process program with input/output progress |
| `POST` | `/api/v1/process/programs/{id}/release/` | `can_create` | Release process program for raw material outward transfer |
| `POST` | `/api/v1/process/programs/{id}/complete/`| `can_update` | Mark process program as completed and calculate yield loss |

---

## 3. UI Layout, Screen Blueprint, and Visual Mockup (1440px+ Wireframe)

```
+-----------------------------------------------------------------------------------------------------------------------------+
| GARMENTS ERP — Universal Production Process & Subcontract Routing            Company: ABC Textiles Ltd | FY: 2026-2027      |
+-----------------------------------------------------------------------------------------------------------------------------+
| TABS: [ 1. Active Process Programs (Job Cards) ]   [ 2. Process Stage Configuration ]   [ 3. Yield Loss Analytics ]        |
+-----------------------------------------------------------------------------------------------------------------------------+
| FILTER DRAWER:                                                                                                              |
| Stage: [ All Stages (Knitting, Dyeing, Compacting, Cutting) | v ]  Status: [ IN_PROGRESS (Badge) | v ]                     |
| Subcontractor: [ Supreme Processing Mills (Dyeing Unit)     | v ]  Date Range: [ 01/10/2026 ] to [ 31/10/2026 ]             |
| [ Reset Filters ]     [ Apply Filters (F3) ]                        [+ New Process Job Card (Alt+N)]  [Export XLSX]         |
+-----------------------------------------------------------------------------------------------------------------------------+
| PROCESS PIPELINE STATUS OVERVIEW:                                                                                           |
|  [ KNITTING (12 Active) ]  ==>  [ DYEING (8 Active) ]  ==>  [ COMPACTING (5 Active) ]  ==>  [ CUTTING (6 Active) ]          |
|    Total Qty: 28,400 Kg           Total Qty: 19,250 Kg        Total Qty: 12,100 Kg            Total Qty: 18,500 Pcs         |
|    Avg Loss: 2.45%                Avg Loss: 4.80%             Avg Loss: 1.10%                 Avg Yield: 94.20%             |
+-----------------------------------------------------------------------------------------------------------------------------+
| ACTIVE PROCESS PROGRAMS TABLE:                                                                                              |
| Program #     | Stage     | Subcontractor / Unit        | Input Material -> Output   | Issued Qty | Received Qty | Loss % | Status     | Actions      |
|---------------|-----------|-----------------------------|----------------------------|------------|--------------|--------|------------|--------------|
| PR-2026-D0014 | DYEING    | Supreme Processing Mills    | Greige SJ -> Navy Blue SJ  | 2,400.00 Kg|  2,284.50 Kg | 4.81%  | IN_PROGRESS| [View] [Recv]|
| PR-2026-D0015 | DYEING    | Rainbow Textile Dyers       | Greige Rib -> Black Rib    | 1,200.00 Kg|  1,142.00 Kg | 4.83%  | IN_PROGRESS| [View] [Recv]|
| PR-2026-C0008 | CUTTING   | In-House Cutting Floor Unit1| Navy Dyed SJ -> Front Panel| 1,500.00 Kg|    6,200 Pcs | --     | IN_PROGRESS| [View] [Recv]|
| PR-2026-K0042 | KNITTING  | Sri Venkateswara Knitting   | 30s Cotton -> Greige SJ    | 2,460.00 Kg|  2,392.50 Kg | 2.74%  | COMPLETED  | [View] [Rep] |
+-----------------------------------------------------------------------------------------------------------------------------+
| PAGINATION: Showing 1 to 4 of 31 Active Programs   [ < Prev ] Page [ 1 ] of 8 [ Next > ]                                    |
| SHORTCUTS: [Alt+N: New Program]  [Alt+S: Config Stages]  [Alt+F: Focus Filter]  [Esc: Reset]                               |
+-----------------------------------------------------------------------------------------------------------------------------+
```

---

## 4. UX Workflow, Step-by-Step Lifecycle, and Edge-Case Handling

### 4.1 Step-by-Step Lifecycle
1. **Stage Definition**:
   - Company Admin configures process stages (`mx_process_stage`), setting standard sequence order, standard rate per kg/piece, standard loss percentage ($L_{\text{std}}$), and specific requirements (recipe tracking, shrinkage test).
2. **Job Card Program Creation**:
   - Production controller creates a new Process Program (`SCR-PRCS-001`).
   - Selects Stage (`DYEING`, `COMPACTING`, `CUTTING`, etc.) and designated Job Worker (`PartyMaster`).
   - Specifies input material, source warehouse, input quantity, and target output item.
   - System auto-calculates expected output quantity based on the stage's standard loss allowance:
     $$Q_{\text{expected}} = Q_{\text{input}} \times \left(1 - \frac{L_{\text{std}}}{100}\right)$$
3. **Execution & Material Dispatch**:
   - Releasing the program authorizes raw material transfer from source godown to the subcontractor.
4. **Receipt & Reconciliation**:
   - Subcontractor completes processing and dispatches finished goods.
   - Quality inspector records received output units and net weight.
   - System calculates actual loss percentage and flags variance against standard contract loss limits.

### 4.2 Edge-Case Handling
- **Excessive Loss Tolerance Breach**: If actual loss exceeds standard tolerance by $>1.0\%$ (e.g. Dyeing loss of $6.2\%$ vs standard $4.5\%$), the program raises a warning and triggers a deduction workflow against the subcontractor's job-work invoice.
- **Cross-Unit Transformation**: For cutting processes converting kilograms of fabric into counted garment pieces (e.g. $1,500\text{ Kg} \rightarrow 6,200\text{ Pieces}$), the system enforces input validation in kilograms and output in integer pieces.

---

## 5. Form Sections, Field Matrix, and Validation Rules

| Section | Field Label | Field Key | Input Type | Required | Default | Validation & Rules |
|---|---|---|---|---|---|---|
| **Header** | Program Number | `program_number` | Text (Readonly) | Yes | Auto `PR-YYYY-XXXX` | Unique document sequence |
| **Header** | Program Date | `program_date` | DatePicker | Yes | Current Date | Format `DD/MM/YYYY` in active FY |
| **Header** | Process Stage | `process_stage_id` | Select | Yes | None | Active `parent_process_stage_table` |
| **Header** | Job Worker (Party) | `job_worker_id` | Searchable Select | Yes | None | Active `PartyMaster` with appropriate type |
| **Warehouse** | Source Godown | `source_warehouse_id` | Select | Yes | None | Warehouse holding raw materials |
| **Warehouse** | Destination Godown| `dest_warehouse_id` | Select | Yes | None | Warehouse receiving finished goods |
| **Input Spec** | Input Stage Name | `input_from` | Text (Auto) | Yes | Auto | Derived from stage master |
| **Input Spec** | Input Item Desc | `input_item` | Text | Yes | None | e.g. "30s Combed Greige Single Jersey" |
| **Input Spec** | Input Unit Type | `input_type` | Select | Yes | `KG` | `KG`, `ROLL_WT_KG`, `PIECES`, `METERS` |
| **Input Spec** | Input Units Count| `input_units` | Number (Integer) | Yes | `0` | e.g. 100 Rolls or 50 Bags |
| **Input Spec** | Input Total Qty | `input_quantity` | Number (3 dp) | Yes | `0.000` | Total weight in Kg or Pieces |
| **Output Spec**| Output Stage Name| `output_to` | Text (Auto) | Yes | Auto | Derived from stage master |
| **Output Spec**| Output Item Desc | `output_item` | Text | Yes | None | e.g. "Navy Blue Dyed Single Jersey" |
| **Output Spec**| Output Unit Type | `output_type` | Select | Yes | `KG` | `KG`, `ROLL_WT_KG`, `PIECES` |
| **Output Spec**| Expected Out Qty | `expected_output_qty` | Number (3 dp, Readonly) | Yes | Auto-computed | $Q_{\text{input}} \times (1 - \frac{\text{Loss}}{100})$ |

---

## 6. Mathematical Formulas and Calculation Specifications (LaTeX)

### 6.1 Expected Output Output Formula
Given input material quantity $Q_{\text{input}}$ and standard stage process loss percentage $L_{\text{std}}$:

$$Q_{\text{expected}} = \operatorname{Round}\left(Q_{\text{input}} \times \left(1 - \frac{L_{\text{std}}}{100}\right), 3\right)$$

### 6.2 Actual Process Loss Percentage
Upon cumulative delivery of finished material $Q_{\text{received}}$:

$$\Delta Q_{\text{loss}} = Q_{\text{input}} - Q_{\text{received}}$$

$$\text{Actual Loss } \% = \operatorname{Round}\left(\frac{Q_{\text{input}} - Q_{\text{received}}}{Q_{\text{input}}} \times 100, 2\right)$$

### 6.3 Tolerance Variance and Subcontractor Debit Note Formula
If $\text{Actual Loss } \% > L_{\text{std}} + T_{\text{allowance}}$, the excess shortage in kg is debited:

$$\text{Shortage Qty (Kg)} = \left(\frac{\text{Actual Loss } \% - L_{\text{std}}}{100}\right) \times Q_{\text{input}}$$

$$\text{Subcontractor Penalty (INR)} = \text{Shortage Qty} \times \text{Yarn/Fabric Valuation Rate}$$

---

## 7. Dynamic Behaviors, Conditional Fields, and Interactivity

1. **Stage-Driven Dynamic Labels**: Selecting stage `CUTTING` dynamically reconfigures the output units from `Kg` to `Pieces / Garment Units`, updating form validation constraints accordingly.
2. **Recipe & Chemical Card Reveal**: If the selected process stage has `has_recipe = True` (e.g. Dyeing), an additional collapsible panel appears allowing entry of Dyeing Recipe Code, Shade Target, Liquor Ratio, and Bath Temperature.
3. **Automated Status Advancement**: Tracking cumulative received quantity automatically moves program status from `IN_PROGRESS` to `COMPLETED` when received quantity reaches $\ge 98\%$ of expected output.

---

## 8. API Request / Response Contracts (DTOs)

### 8.1 Create Process Program Request (`POST /api/v1/process/programs/`)

```json
{
  "program_date": "16/10/2026",
  "process_stage": 2,
  "job_worker": 9,
  "source_warehouse": 2,
  "dest_warehouse": 4,
  "input_from": "GREY_FABRIC",
  "input_item": "100% Cotton Greige Single Jersey 30\" Dia 160 GSM",
  "input_type": "ROLL_WT_KG",
  "input_units": 120,
  "input_quantity": "2400.000",
  "output_to": "DYED_FABRIC",
  "output_item": "Navy Blue Dyed Single Jersey 30\" Dia 160 GSM",
  "output_type": "ROLL_WT_KG",
  "expected_output_units": 120,
  "expected_output_qty": "2292.000",
  "remarks": "Reactive Dyeing - Fastness grade 4 minimum required"
}
```

### 8.2 Success Response Envelope (`HTTP 201 Created`)

```json
{
  "success": true,
  "message": "Process Program PR-2026-D0014 created successfully.",
  "data": {
    "id": 14,
    "program_number": "PR-2026-D0014",
    "program_date": "16/10/2026",
    "process_stage_id": 2,
    "process_stage_name": "Dyeing",
    "job_worker_id": 9,
    "job_worker_name": "Supreme Processing Mills",
    "source_warehouse_id": 2,
    "source_warehouse_name": "Main Greige Godown",
    "dest_warehouse_id": 4,
    "dest_warehouse_name": "Finished Dyed Fabric Godown",
    "input_quantity": "2400.000",
    "expected_output_qty": "2292.000",
    "received_output_qty": "0.000",
    "status": 1,
    "status_display": "RELEASED",
    "created_at": "16/10/2026 17:25",
    "created_by": "arun.kumar"
  }
}
```

---

## 9. Client-Side State Management and Component Architecture

```
app/(app)/production/process-routing/
├── page.tsx                             # Master container with stage pipeline overview
└── components/
    ├── ProcessPipelineSummary.tsx       # Flow diagram with live KPI badges per stage
    ├── ProcessProgramTable.tsx          # Program register with real-time loss tracking
    ├── ProcessProgramCreateModal.tsx    # Universal job card issuance modal
    ├── ProcessStageConfigDrawer.tsx     # Configuration panel for stage loss tolerances
    └── ProcessYieldAnalyticsCard.tsx    # Yield loss charts comparing actual vs standard
```

---

## 10. Zod Validation Schema (Copy-Paste Production Code)

```typescript
import { z } from "zod";

const dateRegex = /^(0[1-9]|[12][0-9]|3[01])\/(0[1-9]|1[0-2])\/\d{4}$/;

export const ProcessProgramCreateSchema = z.object({
  program_date: z.string().regex(dateRegex, { message: "Date must be DD/MM/YYYY" }),
  process_stage_id: z.number().int().positive({ message: "Process stage is required." }),
  job_worker_id: z.number().int().positive({ message: "Job worker / processor is required." }),
  source_warehouse_id: z.number().int().positive({ message: "Source godown is required." }),
  dest_warehouse_id: z.number().int().positive({ message: "Destination godown is required." }),
  input_from: z.string().min(1, { message: "Input source stage is required." }),
  input_item: z.string().min(1, { message: "Input item description is required." }),
  input_type: z.string().min(1, { message: "Input unit type is required." }),
  input_units: z.number().int().min(0),
  input_quantity: z.number().min(0.001, { message: "Input quantity must be positive." }),
  output_to: z.string().min(1, { message: "Output target stage is required." }),
  output_item: z.string().min(1, { message: "Output item description is required." }),
  output_type: z.string().min(1, { message: "Output unit type is required." }),
  expected_output_units: z.number().int().min(0),
  expected_output_qty: z.number().min(0.001, { message: "Expected output quantity must be positive." }),
  remarks: z.string().max(255).optional(),
});

export type ProcessProgramCreateFormData = z.infer<typeof ProcessProgramCreateSchema>;
```

---

## 11. TypeScript Interfaces & Enums (Complete DTO Declarations)

```typescript
export interface IProcessStageDTO {
  id: number;
  name: string;
  code: string;
  sequence_order: number;
  input_from_stage: string;
  input_item_category: string;
  input_unit_type: string;
  output_to_stage: string;
  output_item_category: string;
  output_unit_type: string;
  standard_loss_percent: number;
  standard_rate: number;
  has_recipe: boolean;
  has_shrinkage: boolean;
  has_sizes: boolean;
  is_active: boolean;
}

export interface IProcessProgramDTO {
  id: number;
  program_number: string;
  program_date: string;
  process_stage_id: number;
  process_stage_name: string;
  job_worker_id: number;
  job_worker_name: string;
  source_warehouse_id: number;
  source_warehouse_name: string;
  dest_warehouse_id: number;
  dest_warehouse_name: string;
  input_from: string;
  input_item: string;
  input_type: string;
  input_units: number;
  input_quantity: number;
  output_to: string;
  output_item: string;
  output_type: string;
  expected_output_units: number;
  expected_output_qty: number;
  received_output_units: number;
  received_output_qty: number;
  status: number;
  status_display: string;
  remarks?: string;
  created_at: string;
  created_by: string;
}
```

---

## 12. Keyboard Shortcuts and Rapid Operations

| Key Combination | Action / Trigger | Scope / View |
|---|---|---|
| `Alt + N` | Open New Process Job Card Modal | Process Routing Desk |
| `Alt + S` | Open Stage Configuration Drawer | Process Routing Desk |
| `Alt + F` | Focus Filter Input Bar | Process Routing Desk |
| `F5` | Refresh Pipeline Telemetry | Process Routing Desk |
| `Esc` | Close Active Modal or Drawer | Active Dialog |

---

## 13. Responsive Breakpoints and Mobile Adaptation

| Viewport Width | Screen Category | Layout Behavior |
|---|---|---|
| $\ge 1440\text{px}$ | Desktop Enterprise | Horizontal pipeline stage diagram with full tabular job card register |
| $1024\text{px} - 1439\text{px}$ | Laptop / Tablet Landscape | 2-row pipeline cards with scrollable process table |
| $\le 1023\text{px}$ | Tablet Portrait / Mobile | Vertical pipeline timeline with compact job card summaries |

---

## 14. Error Handling and User Feedback

| Scenario / Error Trigger | Visual Presentation | Remediation Action |
|---|---|---|
| Process Loss $> L_{\text{std}} + 1.0\%$ | Red alert pill in table + badge: *"EXCESS LOSS"* | Prompt for debit note generation |
| Input warehouse empty | Validation error: *"Source godown has insufficient inventory"* | Select alternate godown with stock |
| Invalid FY date | Red field border on `program_date` | Date must be in active FY |

---

## 15. Loading, Empty, and Edge States

- **Loading State**: Animated pipeline pulse diagram with table skeletons.
- **Empty State**: Factory diagram with text: *"No active process programs found for the selected stage."*
- **Completed State**: Green checkmark badge with actual loss percentage displayed.

---

## 16. Accessibility (a11y) Conformance (WCAG 2.1 AA)

- ARIA role `region` for the process pipeline visualization with descriptive text labels.
- Keyboard accessible tab order across all interactive pipeline stage buttons.
- Contrast ratio $\ge 4.5:1$ across all status indicators.

---

## 17. Security, RBAC, and Audit Logging

- **Role Scoping**: Only users with `process_stage.can_manage` can edit stage loss parameters.
- **Tenant Isolation**: Strictly filtered by authenticated `company_id`.
- **Audit Logging**: Modifications write to `ta_audit_log` capturing changes in expected vs actual quantities.

---

## 18. Test Cases and Acceptance Criteria

### 18.1 Acceptance Criteria
1. Given Dyeing stage with $4.5\%$ standard loss and $2,400\text{ Kg}$ input, expected output must calculate to $2,292.000\text{ Kg}$.
2. Cutting stage transforms input in Kilograms into output in integer Pieces.
3. Submitting program validates that source and destination godowns are distinct.

---

## 19. Performance Budgets and Optimization Targets

- Pipeline diagram render: $< 150\text{ms}$.
- Table pagination: $< 200\text{ms}$ for 50 records.

---

## 20. Future Enhancements and Scalability Roadmap

1. **Chemical Recipe Inventory Depletion**: Automatically deducting dyes and auxiliary chemicals from chemical godown upon Dyeing program release.
2. **Barcode Tracking on Subcontract Bags**: Generating water-resistant barcode tags for dye-lot identification.

---

## 21. Sign-off and Approval Matrix

| Stakeholder Role | Name / Title | Date | Signature / Status |
|---|---|---|---|
| **Production Head** | Ramanathan S. (VP Manufacturing) | 16/10/2026 | **APPROVED** |
| **Lead Architect** | Enterprise Garments Solutions | 16/10/2026 | **APPROVED** |
| **Processing Head** | Muruganandam K. (Dyeing GM) | 16/10/2026 | **APPROVED** |
