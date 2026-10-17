# Garments ERP & CRM — Price Lists & Job Work Pricing Engine Architecture Specification

**Document Version:** v1.0  
**Target Release:** Module 9 (Commercial Pricing & Job Work Valuation)  
**Status:** DRAFT / PENDING ARCHITECTURE REVIEW  
**Scope:** Multi-Tenant Garments & Textile ERP (Procurement, Sales, Job Work Subcontracting, Financial Ledgers)  

---

## 1. Executive Summary & Domain Context

In the textile and garment manufacturing industry (e.g., Tirupur, Surat, Coimbatore, Ludhiana clusters), pricing cannot be modeled as a single static number on an item master. Pricing is highly dynamic, multi-dimensional, and governed by:
- **Raw Material Fluctuations**: Cotton yarn prices change weekly based on spinning mill contracts, count (30s, 34s, 40s), and cotton fiber quality.
- **Subcontracted Job Work Operations**: Knitting, dyeing, compacting, printing, embroidery, cutting, and stitching (CMT) are performed by specialized job workers whose rates depend on fabric structure, color depth, machine gauge, and specific styling complexities.
- **Party Relationships**: Tier-1 buyers/brands receive contracted seasonal rates; loyal spinning mills offer contractual volume rebates; preferred job workers hold fixed annual conversion rates.
- **Volume & Slabs**: Order quantities (e.g., 500 Kg vs. 5,000 Kg) dictate tiered unit pricing.
- **Validity Windows**: Price agreements operate under strict validity periods (seasons, quarters, or spot agreements).

This specification establishes a **Unified Pricing Engine** encompassing **Purchase Price Lists**, **Sales Price Lists**, **Job Work Price Lists**, **Party-Specific Price Lists**, and **General Base Price Lists**, underpinned by a deterministic **Rate Determination Hierarchy**.

---

## 2. Price List Classification & Taxonomy

```
                              ┌──────────────────────────────────┐
                              │       UNIFIED PRICE LIST         │
                              │         (tm_price_list)          │
                              └────────────────┬─────────────────┘
                                               │
             ┌─────────────────────────────────┼────────────────────────────────┐
             ▼                                 ▼                                ▼
   ┌───────────────────┐             ┌───────────────────┐            ┌───────────────────┐
   │    PURCHASE       │             │      SALES        │            │     JOB WORK      │
   │   PRICE LISTS     │             │   PRICE LISTS     │            │    PRICE LISTS    │
   └─────────┬─────────┘             └─────────┬─────────┘            └─────────┬─────────┘
             │                                 │                                │
     ┌───────┴───────┐                 ┌───────┴───────┐                ┌───────┴───────┐
     ▼               ▼                 ▼               ▼                ▼               ▼
┌─────────┐    ┌───────────┐     ┌─────────┐    ┌───────────┐    ┌─────────┐    ┌───────────┐
│ General │    │ Party-    │     │ General │    │ Party-    │     │ General │    │ Party-    │
│ (Base)  │    │ Specific  │     │ (Base)  │    │ Specific  │     │ (Base)  │    │ Specific  │
│ List    │    │ (Mill A)  │     │ List    │    │ (Buyer X) │     │ List    │    │ (Knitter) │
└─────────┘    └───────────┘     └─────────┘    └───────────┘     └─────────┘    └───────────┘
```

### 2.1. General Price Lists vs. Party-Specific Price Lists

Every price list belongs to one of two structural scopes:

| Attribute | General Price List (`GENERAL`) | Party-Specific Price List (`PARTY_SPECIFIC`) |
|---|---|---|
| **Party Scope** | Company-wide standard baseline (`party_id = NULL`) | Dedicated contract for a single party (`party_id = 1042`) |
| **Precedence** | Lower priority (Fallback default) | **Highest priority** in rate resolution |
| **Applicability** | Applied when no party-specific contract exists | Applied strictly when matching the transaction's party |
| **Default Flag** | Can be marked as `is_default = TRUE` per list type | Specific to contract reference / agreement number |
| **Use Case** | Standard catalog price, benchmark costing | Negotiated buyer contract, mill annual supply agreement |

---

### 2.2. The Five Functional Price List Types

#### 1. Purchase Price Lists (`list_type = 'PURCHASE'`)
Governs rates paid to suppliers (Spinning Mills, Fabric Traders, Chemical Suppliers, Trims Vendors):
- **Yarn Procurement**: Rate per Kg based on Yarn Count (30s, 34s, 40s), Spinning Mill, Composition (100% Cotton, PC, Melange), and Yarn Form (Cone, Cheese, Hank).
- **Trims & Accessories**: Rate per gross/hundred/piece for sewing thread, zippers, elastic tapes, polybags, buttons, cartons.
- **Fabric Procurement**: Direct procurement of Grey or Finished fabric from external knitters/weavers.
- **Target Transactions**:
  - `tm_yarn_po` / `tx_child_po` (Yarn Purchase Orders)
  - `tm_grey_po` (Grey Fabric Purchase Orders)
  - `tx_parent_yarn_inward` (Inward GRN rate audits)

#### 2. Sales Price Lists (`list_type = 'SALES'`)
Governs selling rates billed to domestic buyers, fashion brands, wholesalers, and export clients:
- **Fabric Sales**: Selling rate per Kg or Meter for Grey Fabric, Dyed Fabric, and Printed Fabric.
- **Garment Sales**: Selling rate per piece/dozen for finished garments (T-Shirts, Hoodies, Polos) based on style code and size group.
- **Yarn Trading**: Selling rate for yarn surplus sales.
- **Currency & Slabs**: Multi-currency support (INR, USD, EUR) with Minimum Order Quantity (MOQ) and tiered volume discounts (e.g., 1–500 pcs @ ₹220, 501–2000 pcs @ ₹200).
- **Target Transactions**:
  - `tm_yarn_sales` / `tx_child_yarn_sales` (Yarn Commercial Tax Invoice)
  - `tm_grey_fabric_sales` (Grey Fabric Commercial Sales)
  - Garment Commercial Sales Invoices & Customer Orders

#### 3. Job Price Lists / Job Work Price Lists (`list_type = 'JOB_WORK'`)
Governs conversion rates paid to external subcontracted process units (Job Workers) who process goods without transferring ownership:
- **Knitting Job Rates**: Rate per Kg conversion charge based on:
  - Fabric Structure (Single Jersey, 1x1 Rib, 2x2 Rib, Interlock, Fleece, Pique, Terry)
  - Yarn Count (e.g., 20s heavy knit vs. 40s fine gauge)
  - Machine Gauge (24GG, 28GG) & Diameter (Dia: 20", 24", 30", 32")
  - Lycra / Spandex Plating (adds +₹/Kg for feeder maintenance and speed reduction)
- **Dyeing & Bleaching Job Rates**: Rate per Kg conversion charge based on:
  - Shade Depth Category (Bleach/White, Light, Medium, Dark, Extra Dark/Jet Black, Fluorescent)
  - Dye Class (Reactive Dyeing, Disperse Dyeing, Cationic, Cotton-Poly double bath)
  - Special Finishes (Bio-polishing, Mercerizing, Silicon wash, Peach finish)
- **Compacting & Heat Setting**: Rate per Kg or Meter for Tubular Compacting, Open Width Compacting, Stenter processing.
- **Printing Job Rates**: Rate per piece or per meter based on:
  - Print Method (Chest Screen Print, Rotary All-Over-Print, Flatbed, Digital DTF)
  - Color Count (1-color, 2-color, up to 12-color setups)
  - Table vs. Machine print
- **Cutting Job Rates**: Rate per piece or per dozen for fabric lay cutting, sorting, and bundle preparation.
- **Stitching / CMT (Cut-Make-Trim) Job Rates**: Rate per piece or per dozen based on:
  - Garment Style Category (Basic Crew Neck Tee, Polo with Placket, Raglan Sleeve, Hoodie with Kangaroo Pocket, Jogger Pant)
  - Seams & Operations (Flatlock, Overlock, Feed-of-the-arm, Bar-tacking)
- **Finishing & Packing Job Rates**: Rate per piece for thread trimming, garment washing, ironing, tagging, and individual polybag boxing.
- **Target Transactions**:
  - `tm_process_program` (Universal Production Process Program)
  - `tm_knitting_program` (Knitting Job Cards)
  - Process Outward Delivery Challans & Inward Process GRNs

#### 4. Party Price Lists (`scope = 'PARTY_SPECIFIC'`)
- Dedicated contract rates negotiated with a specific `PartyMaster` (`party_id`).
- Can be of type `PURCHASE`, `SALES`, or `JOB_WORK`.
- Binds agreed commercial terms for a specific vendor, buyer, or subcontract job worker.

#### 5. General Price Lists (`scope = 'GENERAL'`)
- Standard reference rates for the enterprise across `PURCHASE`, `SALES`, or `JOB_WORK`.
- Acts as the baseline and company-wide benchmark.

---

## 3. Garments & Textile Domain Matrix Specifications

Textile manufacturing requires specialized parameter matching. The tables below specify the exact parameter matrices used in rate evaluation:

### 3.0. Yarn Category, Knitting Process Routing & Production Pipeline Matrix

Every yarn purchase or sales price list links directly to downstream knitting machine setups, resulting fabric stages, and finishing pipelines:

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

### 3.1. Knitting Job Work Rate Matrix
| Fabric Structure | Yarn Count | Machine Gauge | Lycra Plated? | Standard Rate (INR/Kg) | Planned Loss % |
|---|---|---|---|---|---|
| Single Jersey (Plain) | 30s Combed | 24GG / 28GG | No | ₹14.00 | 1.5% |
| Single Jersey + Lycra | 30s + 40D Lycra | 24GG / 28GG | **Yes** | ₹19.50 | 2.5% |
| 1x1 Rib | 30s Combed | 18GG / 20GG | No | ₹18.00 | 2.0% |
| 2x2 Rib + Lycra | 30s + 70D Lycra | 18GG | **Yes** | ₹24.00 | 3.0% |
| Interlock | 40s Combed | 28GG | No | ₹22.00 | 2.0% |
| 2-Thread Fleece | 30s + 10s Waste | 20GG | No | ₹17.50 | 3.5% |
| 3-Thread Fleece | 30s + 20s + 10s | 20GG | No | ₹21.00 | 4.0% |
| Pique / Honeycomb | 30s Combed | 24GG | No | ₹16.50 | 2.0% |

### 3.2. Dyeing Job Work Rate Matrix
| Shade Category | Color Tone Examples | Dye Process Type | Standard Rate (INR/Kg) | Process Loss % | Shrinkage Limit |
|---|---|---|---|---|---|
| Bleach / Optical White | White, Off-White | Peroxide Bleach | ₹32.00 | 2.0% | 3% x 3% |
| Light Shade | Sky Blue, Lemon, Pastel Pink | Reactive Dyeing | ₹48.00 | 2.5% | 4% x 4% |
| Medium Shade | Camel, Royal Blue, Lavender | Reactive Dyeing | ₹62.00 | 3.0% | 4% x 4% |
| Dark Shade | Navy Blue, Maroon, Olive Green | Reactive Dyeing | ₹76.00 | 3.5% | 5% x 5% |
| Extra Dark / Jet Black | Jet Black, Charcoal | High-Fixation Reactive | ₹90.00 | 4.0% | 5% x 5% |
| Melange Wash / Overdye | Grey Heather overdye | Special Disperse/Reactive| ₹68.00 | 3.0% | 4% x 4% |

*Add-on Surcharges:*
- **Bio-Polishing (Enzyme Wash)**: +₹12.00 / Kg
- **Silicon Softener Finish**: +₹6.00 / Kg
- **Antimicrobial / Moisture Wicking Treatment**: +₹18.00 / Kg

### 3.3. Garment Stitching / CMT Job Rate Matrix
| Garment Style Category | Typical Construction Operations | Rate (INR / Piece) | Rate (INR / Dozen) |
|---|---|---|---|
| Basic Round Neck T-Shirt | Neck rib attach, shoulder tape, sleeve hem, bottom hem | ₹16.00 | ₹192.00 |
| Polo T-Shirt (Knitted) | Rib collar, 2-button placket, slit bottom, sleeve cuffs | ₹32.00 | ₹384.00 |
| Henley Neck T-Shirt | Round neck + button placket, double stitch hem | ₹26.00 | ₹312.00 |
| Hooded Sweatshirt (Fleece) | 3-panel hood with cord, kangaroo pocket, ribbed cuffs/waist | ₹58.00 | ₹696.00 |
| Track Pant / Jogger | Elasticated waistband with drawstring, 2 side pockets | ₹42.00 | ₹504.00 |
| Men's Knitted Boxers | Soft concealed waistband, fly front, flatlock seams | ₹14.00 | ₹168.00 |

---

## 4. Rate Determination Engine & Resolution Algorithm

When an operator creates a transaction (e.g., Yarn PO, Sales Invoice, or Process Program), the system automatically triggers the **Rate Determination Engine** to resolve the appropriate price without manual data entry.

### 4.1. Resolution Hierarchy Flowchart

```
                 [ Transaction Triggered (PO / Sales / Process) ]
                                        │
                                        ▼
              [ Collect Context: Company, Party, Doc Date, Item/Process,
                       Technical Specs, Quantity, Currency ]
                                        │
                                        ▼
                   ┌─────────────────────────────────────────┐
                   │ Priority 1: PARTY-SPECIFIC PRICE LIST   │
                   │ (Active, matching party_id, in date)    │
                   └────────────────────┬────────────────────┘
                                        │
                        Found matching Item/Process Line?
                                       / \
                                      /   \
                                  YES/     \NO
                                    /       \
         ┌─────────────────────────┴─┐       ▼
         │ Exact Spec & Slab Match?  │  ┌────────────────────────────────────────┐
         │ (Count, Shade, Slabs)     │  │ Priority 2: GENERAL BASE PRICE LIST    │
         └─────────────┬─────────────┘  │ (Active, party_id is NULL, in date)    │
                       │                └───────────────────┬────────────────────┘
                  YES / \ NO                                │
                     /   \                  Found matching Item/Process Line?
                    /     \                                / \
                   ▼       ▼                           YES/   \NO
             [ APPLY ]   [ Fallback to Base Line ]       /     \
             [ RATE  ]             │                    ▼       ▼
                                   │         ┌───────────────────┐  ┌──────────────────┐
                                   │         │ Exact Spec/Slab?  │  │ Priority 3:      │
                                   │         └─────────┬─────────┘  │ Master Standard  │
                                   │              YES / \ NO        │ Rate (Fallback)  │
                                   │                 /   \          └────────┬─────────┘
                                   │                ▼     ▼                  │
                                   │           [ APPLY ] [ Base Line ]       ▼
                                   │           [ RATE  ]      │        [ Prompt Manual │
                                   │                          │        │ Entry with    │
                                   └──────────────────────────┴───────►│ Warning Flag ]
```

### 4.2. Priority Precedence Rules (Step-by-Step)

The engine executes in order of decreasing specificity:

1. **Rule 1 (Party + Exact Tech Spec + Quantity Slab + Date)**:
   - Matches active party price list (`party_id`), valid for `doc_date`, matching item/process, matching technical parameters (e.g. 30s Combed + Single Jersey + 24GG + Lycra), and where `min_qty <= order_qty <= max_qty`.
2. **Rule 2 (Party + Tech Spec Default + Date)**:
   - Same party, matching technical specs, but falling outside specific slab (applies base party rate).
3. **Rule 3 (Party + General Item Rate)**:
   - Same party, item level base rate without specific variant restrictions.
4. **Rule 4 (General Price List + Exact Tech Spec + Quantity Slab + Date)**:
   - Active default general price list (`party_id IS NULL`), matching exact technical specifications and quantity slab.
5. **Rule 5 (General Price List + Base Item Rate)**:
   - General price list base rate for the item/process.
6. **Rule 6 (Master Table Default Rate)**:
   - Falls back to `standard_rate` on `mx_process_stage` or `standard_rate_per_kg` on `mx_process`.
7. **Rule 7 (Manual Rate Override)**:
   - If no price list matches, or if an authorized user modifies the resolved rate:
     - If the user holds the `special_edit_rate` privilege, the rate is allowed and marked as `is_manual_override = TRUE`.
     - An audit log entry (`ta_pricing_audit`) is recorded with `original_rate`, `override_rate`, `override_reason`, and `user_id`.
     - If rate deviation exceeds company tolerance (e.g., > 10% lower than standard), requires supervisor approval.

### 4.3. Surcharges & Modifiers Computation
Once base rate is resolved, the engine applies conditional surcharges:
$$\text{Final Rate} = (\text{Base Rate} + \sum \text{Fixed Surcharges}) \times (1 + \sum \text{Percentage Surcharges})$$

*Examples in Textiles:*
- Lycra Attachment: $+₹5.50 / \text{Kg}$
- Slub Yarn Pattern: $+₹4.00 / \text{Kg}$
- Bleach / Enzyme Add-on: $+₹12.00 / \text{Kg}$
- Volume Discount (above 5,000 Kg): $-2\%$

---

## 5. Database Schema Design

Strictly adhering to project database rules (`.agents/rules/10-database-and-models.md` and `db-schema-design`):
- Table naming: `tm_<name>` for masters, `tx_<name>` for transactions, `tc_<name>` for control/config, `ta_<name>` for audit.
- **NO database foreign keys and NO Django `ForeignKey` / `OneToOneField`**. References stored as `<entity>_id` BigIntegerField with `db_index=True`.
- Standard audit columns on every table: `id`, `company_id`, `record_status` ('A'/'I'/'D'), `created_by`, `created_at`, `updated_by`, `updated_at`.
- Monetary fields: `DECIMAL(18,2)`. Quantity fields: `DECIMAL(18,3)`. Rates / Percentages: `DECIMAL(18,4)`. Never `FLOAT`.
- Soft delete pattern: `record_status = 'D'`.

```
┌─────────────────────────────────┐
│         tm_price_list           │  (Header: Scope, Type, Party, Validity, Currency)
└───────────────┬─────────────────┘
                │ 1
                │
                ├─────────────────────────────────────────┐
                │ N                                       │ N
┌───────────────▼─────────────────┐       ┌───────────────▼─────────────────┐
│       tm_price_list_item        │       │    tm_price_list_job_rule       │
│ (Standard Items: Yarn, Fabric,  │       │ (Specialized Job Work: Knitting,│
│  Garments, Trims with Slabs)    │       │  Dyeing, Printing, Stitching)   │
└─────────────────────────────────┘       └─────────────────────────────────┘
```

### 5.1. `tm_price_list` (Price List Master Header)
Captures the master header definition for any General, Party, Purchase, Sales, or Job Work price list.

```sql
CREATE TABLE tm_price_list (
    id BIGSERIAL PRIMARY KEY,
    company_id BIGINT NOT NULL,
    price_list_code VARCHAR(50) NOT NULL,
    price_list_name VARCHAR(150) NOT NULL,
    list_type VARCHAR(20) NOT NULL,            -- 'PURCHASE', 'SALES', 'JOB_WORK'
    scope VARCHAR(20) NOT NULL,                -- 'GENERAL', 'PARTY_SPECIFIC'
    party_id BIGINT NULL,                      -- Reference to tm_party.id (NULL if GENERAL)
    currency_id BIGINT NOT NULL DEFAULT 1,     -- Reference to tc_currency (Default INR)
    valid_from DATE NOT NULL,
    valid_to DATE NOT NULL,
    is_default BOOLEAN NOT NULL DEFAULT FALSE, -- Default list for company when no party match
    description TEXT NULL,
    record_status CHAR(1) NOT NULL DEFAULT 'A',-- 'A'=Active, 'I'=Inactive, 'D'=Deleted
    created_by BIGINT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL,
    updated_by BIGINT NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL
);

CREATE UNIQUE INDEX uq_tm_price_list_code ON tm_price_list (company_id, price_list_code) WHERE record_status != 'D';
CREATE INDEX ix_tm_price_list_party ON tm_price_list (company_id, party_id, list_type, record_status);
CREATE INDEX ix_tm_price_list_dates ON tm_price_list (company_id, valid_from, valid_to, record_status);
```

### 5.2. `tm_price_list_item` (Itemized Rate Lines with Slabs)
Captures rates for tangible items: Yarn, Grey Fabric, Finished Fabric, Garment SKUs, and Trims.

```sql
CREATE TABLE tm_price_list_item (
    id BIGSERIAL PRIMARY KEY,
    company_id BIGINT NOT NULL,
    price_list_id BIGINT NOT NULL,             -- Reference to tm_price_list.id
    item_type VARCHAR(30) NOT NULL,            -- 'YARN', 'FABRIC', 'GARMENT', 'TRIM'
    item_id BIGINT NOT NULL,                   -- Ref to mx_yarn, mx_fabric, quality_program, etc.
    uom_id BIGINT NOT NULL,                    -- Reference to mx_uom.id (KGS, MTR, PCS, DOZEN)
    
    -- Specific Technical Variants (Optional filters)
    yarn_count_id BIGINT NULL,                 -- Ref to mx_yarn_count.id
    color_shade_id BIGINT NULL,                -- Ref to mx_color_shade.id
    
    -- Tiered Pricing Slabs
    min_quantity DECIMAL(18,3) NOT NULL DEFAULT 0.000,
    max_quantity DECIMAL(18,3) NULL,           -- NULL indicates infinity / upper bound
    
    base_rate DECIMAL(18,4) NOT NULL,          -- Standard rate per UOM
    discount_percent DECIMAL(5,2) NOT NULL DEFAULT 0.00,
    net_rate DECIMAL(18,4) NOT NULL,           -- Computed: base_rate - (base_rate * discount_percent / 100)
    
    lead_time_days INT NOT NULL DEFAULT 0,
    remarks VARCHAR(255) NULL,
    record_status CHAR(1) NOT NULL DEFAULT 'A',
    created_by BIGINT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL,
    updated_by BIGINT NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL
);

CREATE INDEX ix_tm_price_list_item_lookup ON tm_price_list_item (company_id, price_list_id, item_type, item_id, record_status);
CREATE INDEX ix_tm_price_list_item_slabs ON tm_price_list_item (company_id, item_id, min_quantity, max_quantity, record_status);
```

### 5.3. `tm_price_list_job_rule` (Specialized Job Work Process Matrix)
Captures conversion rates for subcontracted operations: Knitting, Dyeing, Printing, Cutting, Stitching, and Finishing.

```sql
CREATE TABLE tm_price_list_job_rule (
    id BIGSERIAL PRIMARY KEY,
    company_id BIGINT NOT NULL,
    price_list_id BIGINT NOT NULL,             -- Reference to tm_price_list.id
    process_stage_id BIGINT NOT NULL,          -- Ref to mx_process_stage.id (KNITTING, DYEING, etc.)
    uom_id BIGINT NOT NULL,                    -- Ref to mx_uom.id (KG, MTR, PCS, DOZEN)
    
    -- Technical Matching Filters (NULL = Wildcard / Any)
    fabric_type_id BIGINT NULL,                -- Ref to mx_fabric_type.id (Single Jersey, Rib)
    yarn_count_id BIGINT NULL,                 -- Ref to mx_yarn_count.id (30s, 34s)
    machine_gauge VARCHAR(30) NULL,            -- '24GG', '28GG'
    dia_range VARCHAR(50) NULL,                -- e.g. '20-30 inches'
    is_lycra_plated BOOLEAN NULL,              -- True if lycra attachment applies
    shade_category VARCHAR(30) NULL,           -- 'WHITE', 'LIGHT', 'MEDIUM', 'DARK', 'EXTRA_DARK'
    dye_class VARCHAR(50) NULL,                -- 'REACTIVE', 'DISPERSE'
    garment_style_category VARCHAR(100) NULL,  -- 'CREW_NECK_TEE', 'POLO', 'HOODIE'
    print_color_count INT NULL,                -- Number of colors (for screen/rotary print)
    
    -- Commercial Rates & Losses
    job_rate DECIMAL(18,4) NOT NULL,           -- Subcontract conversion charge per UOM
    allowed_loss_percent DECIMAL(5,2) NOT NULL DEFAULT 0.00,
    
    -- Surcharges & Modifiers
    lycra_surcharge DECIMAL(18,4) NOT NULL DEFAULT 0.0000,
    special_finish_surcharge DECIMAL(18,4) NOT NULL DEFAULT 0.0000,
    
    -- Tier Slabs
    min_quantity DECIMAL(18,3) NOT NULL DEFAULT 0.000,
    max_quantity DECIMAL(18,3) NULL,
    
    record_status CHAR(1) NOT NULL DEFAULT 'A',
    created_by BIGINT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL,
    updated_by BIGINT NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL
);

CREATE INDEX ix_tm_job_rule_lookup ON tm_price_list_job_rule (company_id, price_list_id, process_stage_id, record_status);
CREATE INDEX ix_tm_job_rule_knitting ON tm_price_list_job_rule (company_id, process_stage_id, fabric_type_id, yarn_count_id, record_status);
CREATE INDEX ix_tm_job_rule_dyeing ON tm_price_list_job_rule (company_id, process_stage_id, shade_category, record_status);
```

### 5.4. `ta_pricing_audit` (Price Audit & Override History Log)
Maintains an immutable ledger of all price overrides, manual edits, and price list revision history.

```sql
CREATE TABLE ta_pricing_audit (
    id BIGSERIAL PRIMARY KEY,
    company_id BIGINT NOT NULL,
    document_type VARCHAR(50) NOT NULL,        -- 'YARN_PO', 'SALES_INVOICE', 'PROCESS_PROGRAM'
    document_id BIGINT NOT NULL,               -- Reference to transaction PK
    line_item_id BIGINT NOT NULL,              -- Reference to line item PK
    resolved_price_list_id BIGINT NULL,        -- Price list picked by engine (NULL if none)
    resolved_rule_id BIGINT NULL,              -- Rule / Item line PK picked
    system_rate DECIMAL(18,4) NOT NULL,        -- Rate suggested by engine
    actual_rate DECIMAL(18,4) NOT NULL,        -- Rate actually saved/used
    is_override BOOLEAN NOT NULL DEFAULT FALSE,-- True if actual != system
    override_reason VARCHAR(255) NULL,         -- Reason mandatory if override is true
    approved_by BIGINT NULL,                   -- User ID who authorized override
    created_by BIGINT NOT NULL,                -- User who submitted transaction
    created_at TIMESTAMPTZ NOT NULL
);

CREATE INDEX ix_ta_pricing_audit_doc ON ta_pricing_audit (company_id, document_type, document_id);
```

---

## 6. Python / Django Model Architecture

Here is the implementation of the database models following all architecture rules:

```python
# apps/masters/pricing_models.py
from decimal import Decimal
from django.db import models
from django.utils import timezone
from core.base_models import UppercaseModel

class PriceListScope(models.TextChoices):
    GENERAL = "GENERAL", "General / Standard Base"
    PARTY_SPECIFIC = "PARTY_SPECIFIC", "Party Specific Contract"

class PriceListType(models.TextChoices):
    PURCHASE = "PURCHASE", "Purchase Price List"
    SALES = "SALES", "Sales Price List"
    JOB_WORK = "JOB_WORK", "Job Work Price List"

class PriceListItemType(models.TextChoices):
    YARN = "YARN", "Yarn"
    FABRIC = "FABRIC", "Fabric"
    GARMENT = "GARMENT", "Garment / Style"
    TRIM = "TRIM", "Trims / Accessories"
    PROCESS = "PROCESS", "Process Service"


class PriceList(UppercaseModel):
    """
    Price List Master Header: tm_price_list
    """
    company_id = models.BigIntegerField(db_index=True)
    price_list_code = models.CharField(max_length=50, db_index=True)
    price_list_name = models.CharField(max_length=150)
    list_type = models.CharField(max_length=20, choices=PriceListType.choices, db_index=True)
    scope = models.CharField(max_length=20, choices=PriceListScope.choices, default=PriceListScope.GENERAL, db_index=True)
    party_id = models.BigIntegerField(null=True, blank=True, db_index=True, help_text="Reference to tm_party.id")
    currency_id = models.BigIntegerField(default=1, db_index=True, help_text="Reference to tc_currency.id (Default INR)")
    valid_from = models.DateField(db_index=True)
    valid_to = models.DateField(db_index=True)
    is_default = models.BooleanField(default=False, help_text="Default list for company when no party contract exists")
    description = models.TextField(blank=True, null=True)

    record_status = models.CharField(max_length=1, default="A", db_index=True)  # 'A'=Active, 'I'=Inactive, 'D'=Deleted
    created_by = models.BigIntegerField()
    created_at = models.DateTimeField(default=timezone.now)
    updated_by = models.BigIntegerField()
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "tm_price_list"
        verbose_name = "Price List"
        verbose_name_plural = "Price Lists"
        indexes = [
            models.Index(fields=["company_id", "party_id", "list_type", "record_status"]),
            models.Index(fields=["company_id", "valid_from", "valid_to", "record_status"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["company_id", "price_list_code"],
                condition=~models.Q(record_status="D"),
                name="uq_tm_price_list_code"
            )
        ]

    def soft_delete(self, user_id: int):
        self.record_status = "D"
        self.updated_by = user_id
        self.save(update_fields=["record_status", "updated_by", "updated_at"])


class PriceListItem(UppercaseModel):
    """
    Price List Item Line: tm_price_list_item
    Captures pricing lines for physical goods (Yarn, Fabrics, Garments, Trims)
    """
    company_id = models.BigIntegerField(db_index=True)
    price_list_id = models.BigIntegerField(db_index=True, help_text="Reference to tm_price_list.id")
    item_type = models.CharField(max_length=30, choices=PriceListItemType.choices, db_index=True)
    item_id = models.BigIntegerField(db_index=True, help_text="Reference to mx_yarn, mx_fabric, or quality_program")
    uom_id = models.BigIntegerField(db_index=True, help_text="Reference to mx_uom.id")

    yarn_count_id = models.BigIntegerField(null=True, blank=True, db_index=True)
    color_shade_id = models.BigIntegerField(null=True, blank=True, db_index=True)

    min_quantity = models.DecimalField(max_digits=18, decimal_places=3, default=Decimal("0.000"))
    max_quantity = models.DecimalField(max_digits=18, decimal_places=3, null=True, blank=True)

    base_rate = models.DecimalField(max_digits=18, decimal_places=4, default=Decimal("0.0000"))
    discount_percent = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("0.00"))
    net_rate = models.DecimalField(max_digits=18, decimal_places=4, default=Decimal("0.0000"))

    lead_time_days = models.IntegerField(default=0)
    remarks = models.CharField(max_length=255, blank=True, null=True)

    record_status = models.CharField(max_length=1, default="A", db_index=True)
    created_by = models.BigIntegerField()
    created_at = models.DateTimeField(default=timezone.now)
    updated_by = models.BigIntegerField()
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "tm_price_list_item"
        verbose_name = "Price List Item"
        verbose_name_plural = "Price List Items"
        indexes = [
            models.Index(fields=["company_id", "price_list_id", "item_type", "item_id", "record_status"]),
            models.Index(fields=["company_id", "item_id", "min_quantity", "max_quantity", "record_status"]),
        ]

    def save(self, *args, **kwargs):
        if self.base_rate:
            disc = (Decimal(str(self.discount_percent or 0)) / Decimal("100.00"))
            self.net_rate = (self.base_rate * (Decimal("1.0000") - disc)).quantize(Decimal("0.0001"))
        super().save(*args, **kwargs)


class PriceListJobRule(UppercaseModel):
    """
    Job Work Conversion Rates: tm_price_list_job_rule
    Captures subcontract rates for Knitting, Dyeing, Printing, Cutting, Stitching
    """
    company_id = models.BigIntegerField(db_index=True)
    price_list_id = models.BigIntegerField(db_index=True)
    process_stage_id = models.BigIntegerField(db_index=True, help_text="Ref to mx_process_stage.id")
    uom_id = models.BigIntegerField(db_index=True, help_text="Ref to mx_uom.id")

    fabric_type_id = models.BigIntegerField(null=True, blank=True, db_index=True)
    yarn_count_id = models.BigIntegerField(null=True, blank=True, db_index=True)
    machine_gauge = models.CharField(max_length=30, blank=True, null=True)
    dia_range = models.CharField(max_length=50, blank=True, null=True)
    is_lycra_plated = models.BooleanField(null=True, blank=True)
    shade_category = models.CharField(max_length=30, blank=True, null=True)  # WHITE, LIGHT, MEDIUM, DARK, EXTRA_DARK
    dye_class = models.CharField(max_length=50, blank=True, null=True)
    garment_style_category = models.CharField(max_length=100, blank=True, null=True)
    print_color_count = models.IntegerField(null=True, blank=True)

    job_rate = models.DecimalField(max_digits=18, decimal_places=4, default=Decimal("0.0000"))
    allowed_loss_percent = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("0.00"))

    lycra_surcharge = models.DecimalField(max_digits=18, decimal_places=4, default=Decimal("0.0000"))
    special_finish_surcharge = models.DecimalField(max_digits=18, decimal_places=4, default=Decimal("0.0000"))

    min_quantity = models.DecimalField(max_digits=18, decimal_places=3, default=Decimal("0.000"))
    max_quantity = models.DecimalField(max_digits=18, decimal_places=3, null=True, blank=True)

    record_status = models.CharField(max_length=1, default="A", db_index=True)
    created_by = models.BigIntegerField()
    created_at = models.DateTimeField(default=timezone.now)
    updated_by = models.BigIntegerField()
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "tm_price_list_job_rule"
        verbose_name = "Price List Job Rule"
        verbose_name_plural = "Price List Job Rules"
        indexes = [
            models.Index(fields=["company_id", "price_list_id", "process_stage_id", "record_status"]),
            models.Index(fields=["company_id", "process_stage_id", "fabric_type_id", "yarn_count_id", "record_status"]),
            models.Index(fields=["company_id", "process_stage_id", "shade_category", "record_status"]),
        ]
```

---

## 7. REST API Contract & DTOs

Conforming strictly to `docs/api-contract.md`:
- Standard JSON Envelopes (`success`, `data`, `meta` / `error`).
- Bearer JWT authentication.
- Tenant context via `X-Company-ID` or request context.

### 7.1. Endpoints Catalogue
| Method | Path | Privilege Code | Description |
|---|---|---|---|
| `GET, POST` | `/api/v1/pricing/lists/` | `pricing_manage` | List / Create Price Lists (headers) |
| `GET, PUT` | `/api/v1/pricing/lists/{id}/` | `pricing_manage` | Retrieve / Update Price List |
| `DELETE` | `/api/v1/pricing/lists/{id}/` | `pricing_manage` | Soft delete Price List |
| `GET, POST` | `/api/v1/pricing/lists/{id}/items/` | `pricing_manage` | Add / List itemized pricing lines & slabs |
| `GET, POST` | `/api/v1/pricing/lists/{id}/job-rules/` | `pricing_manage` | Add / List Job Work conversion rules |
| `POST` | `/api/v1/pricing/resolve/` | `IsAuthenticated` | **Rate Engine Lookup**: Resolve rate for transaction line |
| `POST` | `/api/v1/pricing/resolve-batch/` | `IsAuthenticated` | Batch lookup for multi-line transactions |
| `GET` | `/api/v1/pricing/audit/` | `pricing_view` | Audit log of rate overrides and manual adjustments |

---

### 7.2. Rate Engine Lookup API: `POST /api/v1/pricing/resolve/`

#### Request Payload: Resolving a Knitting Job Work Rate
```json
{
  "context_type": "JOB_WORK",
  "party_id": 14,
  "doc_date": "2026-10-15",
  "process_stage_code": "KNITTING",
  "fabric_type_id": 3,
  "yarn_count_id": 8,
  "is_lycra_plated": true,
  "machine_gauge": "24GG",
  "quantity": 1250.000,
  "uom": "KG"
}
```

#### Success Response Envelope:
```json
{
  "success": true,
  "data": {
    "resolved_rate": "19.5000",
    "base_rate": "14.0000",
    "surcharges": {
      "lycra_surcharge": "5.5000",
      "special_finish": "0.0000"
    },
    "allowed_loss_percent": "2.50",
    "pricing_source": "PARTY_SPECIFIC",
    "price_list_id": 5,
    "price_list_code": "PL-KNIT-MURUGAN-2026",
    "price_list_name": "Sri Murugan Knits - 2026 Conversion Rates",
    "rule_id": 42,
    "is_slab_applied": true,
    "min_quantity": "500.000",
    "max_quantity": "2000.000",
    "currency_code": "INR",
    "is_manual_override_allowed": true
  },
  "meta": {
    "execution_time_ms": 14
  }
}
```

---

#### Request Payload: Resolving a Yarn Purchase Order Rate
```json
{
  "context_type": "PURCHASE",
  "party_id": 5,
  "doc_date": "2026-10-15",
  "item_type": "YARN",
  "item_id": 22,
  "yarn_count_id": 8,
  "quantity": 3000.000,
  "uom": "KG"
}
```

#### Success Response Envelope:
```json
{
  "success": true,
  "data": {
    "resolved_rate": "258.0000",
    "base_rate": "265.0000",
    "discount_percent": "2.64",
    "net_rate": "258.0000",
    "pricing_source": "PARTY_SPECIFIC",
    "price_list_id": 2,
    "price_list_code": "PL-PUR-SVT-MILLS-Q4",
    "price_list_name": "SVT Spinning Mills Q4 Yarn Contract",
    "rule_id": 108,
    "is_slab_applied": true,
    "min_quantity": "2000.000",
    "max_quantity": "5000.000",
    "currency_code": "INR",
    "is_manual_override_allowed": true
  },
  "meta": {
    "execution_time_ms": 11
  }
}
```

---

#### Error Response: No Active Price List Found & No Default Rate
```json
{
  "success": false,
  "error": {
    "code": "PRICING_RULE_NOT_FOUND",
    "message": "No active price list found for Party #88 or General Base. Please define a price list or enter rate manually with supervisor authorization.",
    "details": {
      "context_type": "SALES",
      "party_id": 88,
      "doc_date": "2026-10-15",
      "item_id": 45
    }
  }
}
```

---

## 8. Business Rules, Invariants & Security Controls

### 8.1. Immutability of Posted Records
1. **Historic Document Integrity**: Once a Purchase Order, Sales Invoice, or Process Program is saved/posted, modifying or deleting a price list **NEVER** retroactively updates existing documents or ledger vouchers.
2. **Version Pinning**: Each transaction line stores `price_list_id` and `price_list_rate` at the moment of creation, guaranteeing 100% audit reproducibility.

### 8.2. Overlapping Date Prevention
For the same `company_id`, `list_type`, `scope`, and `party_id`, price lists must not have conflicting, overlapping `valid_from` and `valid_to` date ranges. The repository validates:
$$\neg (\text{start}_A \le \text{end}_B \land \text{end}_A \ge \text{start}_B)$$

### 8.3. Role-Based Access Control (RBAC) Privileges
| Privilege Code | Name | Description |
|---|---|---|
| `pricing_view` | View Price Lists | View General and Party Price lists and reports |
| `pricing_manage` | Manage Price Lists | Create, edit, and soft-delete price lists & rules |
| `pricing_approve` | Authorize Price Lists | Mark draft price lists as authorized and active |
| `special_edit_rate` | Override Resolved Rate | Allows manual rate changes in POs, Sales, & Job Cards |
| `special_discount_above_limit` | Exceed Discount Limit | Allows entering discounts higher than price list maximum |

### 8.4. Concurrency & Performance
- The resolution engine operates entirely via indexed reads (`Index(company_id, party_id, list_type, record_status)`).
- Queries execute in under 20ms, ensuring responsive auto-complete in Next.js UI grids.
- Multi-item transactions leverage `/api/v1/pricing/resolve-batch/` to resolve up to 50 lines in a single database round-trip.

---

## 9. Next Steps & Implementation Roadmap

1. **Sprint 1 (Architecture & Models)**:
   - Create migrations for `tm_price_list`, `tm_price_list_item`, `tm_price_list_job_rule`, and `ta_pricing_audit`.
   - Implement base serializers and admin registration.
2. **Sprint 2 (Pricing Engine Service Layer)**:
   - Implement `PricingResolutionService` implementing the 7-step priority resolution hierarchy.
   - Implement unit test suite verifying slabs, date validation, and textile spec matches.
3. **Sprint 3 (Module Integration)**:
   - Wire `PricingResolutionService` into `parent_po_table` / Yarn PO creation.
   - Wire into `tm_yarn_sales` and `tm_grey_fabric_sales`.
   - Wire into `tm_process_program` and `tm_knitting_program`.
4. **Sprint 4 (Frontend UI Components)**:
   - Build Price List Master UI (General & Party-Specific management).
   - Integrate auto-fetch badges and rate override modals into PO and Invoicing screens.

---

## 10. Front-End User Interface Specifications & Reference Assets

Comprehensive screen-by-screen specifications following the **STD-UI-001** 21-section standard have been established:

| Screen ID | Screen Name | Route | Specification Document | Reference Implementation |
|---|---|---|---|---|
| **`SCR-PRIC-001`** | **Yarn Price List Suite (Add, Edit, List, Print)** | `/pricing/yarn-price-lists` | [`docs/ui/23_...` to `26_...`](file:///d:/Codebase/Garments/docs/ui/23_YARN_PRICE_LIST_ADD_WORKFLOW_SPECIFICATION.md) | Standard 4-Screen Suite |
| **`SCR-PRIC-002`** | **Job Work Subcontract Conversion Matrix** | `/pricing/job-work-rules` | [`docs/ui/37_JOB_WORK_MATRIX_UI_SPECIFICATION.md`](file:///d:/Codebase/Garments/docs/ui/37_JOB_WORK_MATRIX_UI_SPECIFICATION.md) | Conversion Engine Cockpit |
| **`SCR-PRIC-003`** | **Party Price List Contract & Rate Sandbox** | `/pricing/party-price-lists/[id]` | [`docs/ui/41_PARTY_PRICE_LIST_CONTRACT_SPECIFICATION.md`](file:///d:/Codebase/Garments/docs/ui/41_PARTY_PRICE_LIST_CONTRACT_SPECIFICATION.md) | [`frontend/party_price_list_sample.html`](file:///d:/Codebase/Garments/frontend/party_price_list_sample.html) |
| **`SCR-PRIC-004`** | **Multi-Party Price List Comparison Matrix** | `/pricing/party-comparison-matrix` | [`docs/ui/42_MULTI_PARTY_PRICE_LIST_MATRIX_SPECIFICATION.md`](file:///d:/Codebase/Garments/docs/ui/42_MULTI_PARTY_PRICE_LIST_MATRIX_SPECIFICATION.md) | [`frontend/multi_party_price_list_matrix.html`](file:///d:/Codebase/Garments/frontend/multi_party_price_list_matrix.html) |

