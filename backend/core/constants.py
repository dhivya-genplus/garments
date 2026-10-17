class UserRoles:
    SUPER_ADMIN = "SUPER_ADMIN"
    ADMIN_USER = "ADMIN_USER"        # Company Administrator
    COMPANY_USER = "COMPANY_USER"    # Company Employee / Staff / Operator

    CHOICES = [
        (SUPER_ADMIN, "Super Admin"),
        (ADMIN_USER, "Admin User (Company Admin)"),
        (COMPANY_USER, "Company User (Employee)"),
    ]


class ModulePermissions:
    # System & Administration
    COMPANY_MANAGEMENT = "company_management"
    FINANCIAL_YEAR_MANAGEMENT = "financial_year_management"
    USER_MANAGEMENT = "user_management"
    EMPLOYEE_MANAGEMENT = "employee_management"
    ROLE_MANAGEMENT = "role_management"

    # Masters
    MASTERS_PARTY = "masters_party"
    MASTERS_YARN = "masters_yarn"
    MASTERS_FABRIC = "masters_fabric"
    MASTERS_PROCESS = "masters_process"
    MASTERS_UOM = "masters_uom"
    MASTERS_COLOR = "masters_color"
    MASTERS_WAREHOUSE = "masters_warehouse"

    # Purchase
    PURCHASE_YARN_PO = "purchase_yarn_po"
    PURCHASE_YARN_PO_RETURN = "purchase_yarn_po_return"

    # Inventory
    INVENTORY_YARN_INWARD = "inventory_yarn_inward"
    INVENTORY_YARN_OUTWARD = "inventory_yarn_outward"
    INVENTORY_YARN_STOCK = "inventory_yarn_stock"

    # Sales
    SALES_YARN = "sales_yarn"
    SALES_YARN_RETURN = "sales_yarn_return"

    # Knitting & Grey Fabric Production
    KNITTING_PROGRAM = "knitting_program"
    KNITTING_GREY_FABRIC_STOCK = "knitting_grey_fabric_stock"
    KNITTING_GREY_FABRIC_INWARD = "knitting_grey_fabric_inward"
    KNITTING_GREY_FABRIC_OUTWARD = "knitting_grey_fabric_outward"
    KNITTING_GREY_PO = "knitting_grey_po"
    KNITTING_GREY_FABRIC_SALES = "knitting_grey_fabric_sales"
    KNITTING_GREY_FABRIC_SALES_RETURN = "knitting_grey_fabric_sales_return"

    # Production Process Engine (Knitting, Dyeing, Cutting, Printing, Stitching, etc.)
    PROCESS_STAGE = "process_stage"
    PROCESS_PROGRAM = "process_program"

    # Dual Stock & Currency Ledgers
    LEDGER_STOCK = "ledger_stock"
    LEDGER_CURRENCY = "ledger_currency"

    # Commercial Pricing & Price Lists
    PRICING_MANAGE = "pricing_manage"
    PRICING_VIEW = "pricing_view"

    # All Modules List
    ALL_MODULES = [
        (COMPANY_MANAGEMENT, "Company Management"),
        (FINANCIAL_YEAR_MANAGEMENT, "Financial Year Management"),
        (USER_MANAGEMENT, "Admin User Management"),
        (EMPLOYEE_MANAGEMENT, "Employee / Company User Management"),
        (ROLE_MANAGEMENT, "Role & Privilege Management"),
        (MASTERS_PARTY, "Party Master (Mills, Traders, Customers, Suppliers)"),
        (MASTERS_YARN, "Yarn Master"),
        (MASTERS_FABRIC, "Fabric Master"),
        (MASTERS_PROCESS, "Process Master"),
        (MASTERS_UOM, "Unit of Measurement"),
        (MASTERS_COLOR, "Color / Shade Master"),
        (MASTERS_WAREHOUSE, "Warehouse / Location Master"),
        (PURCHASE_YARN_PO, "Yarn Purchase Order"),
        (PURCHASE_YARN_PO_RETURN, "Yarn Purchase Order Return (Debit Note)"),
        (INVENTORY_YARN_INWARD, "Yarn Inward (GRN)"),
        (INVENTORY_YARN_OUTWARD, "Yarn Outward (Knitting/Dyeing/Return)"),
        (INVENTORY_YARN_STOCK, "Yarn Stock Ledger"),
        (SALES_YARN, "Yarn Sales"),
        (SALES_YARN_RETURN, "Yarn Sales Return"),
        (KNITTING_PROGRAM, "Knitting Program (Job Order)"),
        (KNITTING_GREY_FABRIC_STOCK, "Grey Fabric Stock Ledger"),
        (KNITTING_GREY_FABRIC_INWARD, "Grey Fabric Inward (GRN)"),
        (KNITTING_GREY_FABRIC_OUTWARD, "Grey Fabric Outward (Dyeing / Return)"),
        (KNITTING_GREY_PO, "Grey Fabric Purchase Order"),
        (KNITTING_GREY_FABRIC_SALES, "Grey Fabric Commercial Sales"),
        (KNITTING_GREY_FABRIC_SALES_RETURN, "Grey Fabric Customer Sales Return"),
        (PROCESS_STAGE, "Process Stage Master (Routing & Stages)"),
        (PROCESS_PROGRAM, "Production Process Program (Job Orders)"),
        (LEDGER_STOCK, "Stage Stock Ledger (Physical In/Out)"),
        (LEDGER_CURRENCY, "Currency General Ledger (Double-Entry Dr/Cr)"),
        (PRICING_MANAGE, "Commercial Pricing & Price Lists Management"),
        (PRICING_VIEW, "Price Lists View & Rate Audit"),
    ]


class StockMovementTypes:
    INWARD = "INWARD"
    OUTWARD = "OUTWARD"
    SALES = "SALES"
    SALES_RETURN = "SALES_RETURN"
    SUPPLIER_RETURN = "SUPPLIER_RETURN"
    ADJUSTMENT = "ADJUSTMENT"

    CHOICES = [
        (INWARD, "Stock Inward (+)"),
        (OUTWARD, "Stock Outward (-)"),
        (SALES, "Commercial Sales (-)"),
        (SALES_RETURN, "Customer Sales Return (+)"),
        (SUPPLIER_RETURN, "Supplier Rejection Return (-)"),
        (ADJUSTMENT, "Stock Adjustment"),
    ]


class VoucherTypes:
    PURCHASE = "PURCHASE"
    SALES = "SALES"
    JOB_WORK_EXPENSE = "JOB_WORK_EXPENSE"
    PAYMENT = "PAYMENT"
    RECEIPT = "RECEIPT"
    DEBIT_NOTE = "DEBIT_NOTE"
    CREDIT_NOTE = "CREDIT_NOTE"
    JOURNAL = "JOURNAL"

    CHOICES = [
        (PURCHASE, "Purchase Invoice"),
        (SALES, "Sales Invoice"),
        (JOB_WORK_EXPENSE, "Job Work Expense"),
        (PAYMENT, "Payment Voucher"),
        (RECEIPT, "Receipt Voucher"),
        (DEBIT_NOTE, "Debit Note"),
        (CREDIT_NOTE, "Credit Note"),
        (JOURNAL, "Journal Voucher"),
    ]



class ProcessProgramStatus:
    DRAFT = 0
    AUTHORIZED = 1
    IN_PROGRESS = 2
    COMPLETED = 3
    CANCELLED = 4

    CHOICES = [
        (DRAFT, "Draft"),
        (AUTHORIZED, "Authorized / Released"),
        (IN_PROGRESS, "In Progress"),
        (COMPLETED, "Completed"),
        (CANCELLED, "Cancelled"),
    ]



class YarnOutwardTypes:
    KNITTING = "KNITTING"
    DYEING = "DYEING"
    PURCHASE_RETURN = "PURCHASE_RETURN"

    CHOICES = [
        (KNITTING, "Yarn Outward for Knitting"),
        (DYEING, "Yarn Outward for Dyeing"),
        (PURCHASE_RETURN, "Yarn Return (Purchase Return)"),
    ]


class PartyTypes:
    MILL = "MILL"
    TRADER = "TRADER"
    BROKER = "BROKER"
    SUPPLIER = "SUPPLIER"
    CUSTOMER = "CUSTOMER"
    KNITTING_UNIT = "KNITTING_UNIT"
    DYEING_UNIT = "DYEING_UNIT"
    JOB_WORKER = "JOB_WORKER"
    SUBCONTRACTOR = "SUBCONTRACTOR"
    TRANSPORTER = "TRANSPORTER"

    CHOICES = [
        (MILL, "Yarn / Fabric Mill"),
        (TRADER, "Trader"),
        (BROKER, "Broker / Agent"),
        (SUPPLIER, "Supplier / Vendor"),
        (CUSTOMER, "Customer / Buyer"),
        (KNITTING_UNIT, "Knitting Unit"),
        (DYEING_UNIT, "Dyeing / Processing Unit"),
        (JOB_WORKER, "Job Worker"),
        (SUBCONTRACTOR, "Subcontractor"),
        (TRANSPORTER, "Transporter"),
    ]


class PartyCategory:
    MANUFACTURER = "MANUFACTURER"
    TRADER = "TRADER"
    BROKER = "BROKER"
    WHOLESALER = "WHOLESALER"
    RETAILER = "RETAILER"
    JOB_WORKER = "JOB_WORKER"
    OTHER = "OTHER"

    CHOICES = [
        (MANUFACTURER, "Manufacturer"),
        (TRADER, "Trader"),
        (BROKER, "Broker"),
        (WHOLESALER, "Wholesaler"),
        (RETAILER, "Retailer"),
        (JOB_WORKER, "Job Worker"),
        (OTHER, "Other"),
    ]


class AddressTypes:
    REGISTERED = "REGISTERED"
    BILLING = "BILLING"
    DELIVERY = "DELIVERY"
    BRANCH = "BRANCH"

    CHOICES = [
        (REGISTERED, "Registered Office"),
        (BILLING, "Billing Address"),
        (DELIVERY, "Delivery / Shipping Address"),
        (BRANCH, "Branch / Unit Location"),
    ]


class GstRegistrationType:
    REGULAR = "REGULAR"
    COMPOSITION = "COMPOSITION"
    UNREGISTERED = "UNREGISTERED"
    CONSUMER = "CONSUMER"
    OVERSEAS = "OVERSEAS"
    SPECIAL_ECONOMIC_ZONE = "SEZ"

    CHOICES = [
        (REGULAR, "Regular Registered Business"),
        (COMPOSITION, "Composition Scheme"),
        (UNREGISTERED, "Unregistered Entity"),
        (CONSUMER, "Consumer"),
        (OVERSEAS, "Overseas / Import-Export"),
        (SPECIAL_ECONOMIC_ZONE, "Special Economic Zone (SEZ)"),
    ]


class GstTreatment:
    TAXABLE = "TAXABLE"
    EXEMPT = "EXEMPT"
    NIL_RATED = "NIL_RATED"
    NON_GST = "NON_GST"

    CHOICES = [
        (TAXABLE, "Taxable Goods / Services"),
        (EXEMPT, "Exempt from GST"),
        (NIL_RATED, "Nil Rated (0%)"),
        (NON_GST, "Non-GST Supply"),
    ]


class PaymentModes:
    NEFT_RTGS = "NEFT_RTGS"
    CHEQUE = "CHEQUE"
    LC = "LC"
    UPI = "UPI"
    CASH = "CASH"

    CHOICES = [
        (NEFT_RTGS, "NEFT / RTGS / Net Banking"),
        (CHEQUE, "Cheque / Demand Draft"),
        (LC, "Letter of Credit (LC)"),
        (UPI, "UPI / Digital Payment"),
        (CASH, "Cash"),
    ]


class VerificationStatus:
    UNVERIFIED = "UNVERIFIED"
    VERIFIED = "VERIFIED"
    FAILED = "FAILED"

    CHOICES = [
        (UNVERIFIED, "Unverified / Pending"),
        (VERIFIED, "Verified"),
        (FAILED, "Verification Failed / Rejected"),
    ]


class PartyDocumentTypes:
    GST_CERT = "GST_CERT"
    PAN_CARD = "PAN_CARD"
    MSME_CERT = "MSME_CERT"
    BANK_PROOF = "BANK_PROOF"
    QUALITY_CERT = "QUALITY_CERT"
    RATE_CONTRACT = "RATE_CONTRACT"
    OTHER = "OTHER"

    CHOICES = [
        (GST_CERT, "GST Registration Certificate"),
        (PAN_CARD, "PAN Card Copy"),
        (MSME_CERT, "MSME / Udyam Certificate"),
        (BANK_PROOF, "Cancelled Cheque / Bank Statement"),
        (QUALITY_CERT, "Quality / Compliance Certificate"),
        (RATE_CONTRACT, "Rate Contract / Agreement"),
        (OTHER, "Other Supporting Document"),
    ]


class YarnCategory:
    GREY = "GREY"
    DYED = "DYED"
    MELANGE = "MELANGE"
    BLENDED = "BLENDED"
    WOUND = "WOUND"
    SLUB = "SLUB"
    CORE_SPUN = "CORE_SPUN"
    RECYCLED = "RECYCLED"

    CHOICES = [
        (GREY, "Grey Yarn"),
        (DYED, "Dyed Yarn"),
        (MELANGE, "Melange Yarn"),
        (BLENDED, "Blended Yarn"),
        (WOUND, "Wound / Doubled & Twisted Yarn"),
        (SLUB, "Slub / Fancy Yarn"),
        (CORE_SPUN, "Lycra / Core-Spun Yarn"),
        (RECYCLED, "Recycled / Sustainable Yarn"),
    ]


class FabricCategory:
    GREY = "GREY"
    DYED = "DYED"

    CHOICES = [
        (GREY, "Grey Fabric"),
        (DYED, "Dyed Fabric"),
    ]


class ProcessTypes:
    KNITTING = "KNITTING"
    DYEING = "DYEING"
    COMPACTING = "COMPACTING"
    PRINTING = "PRINTING"
    WASHING = "WASHING"
    SPINNING = "SPINNING"
    STENTERING = "STENTERING"
    FINISHING = "FINISHING"

    CHOICES = [
        (KNITTING, "Knitting"),
        (DYEING, "Dyeing"),
        (COMPACTING, "Compacting"),
        (PRINTING, "Printing"),
        (WASHING, "Washing"),
        (SPINNING, "Spinning"),
        (STENTERING, "Stentering"),
        (FINISHING, "Finishing"),
    ]


class WarehouseTypes:
    YARN_GODOWN = "YARN_GODOWN"
    GREY_FABRIC_GODOWN = "GREY_FABRIC_GODOWN"
    DYED_FABRIC_GODOWN = "DYED_FABRIC_GODOWN"
    ACCESSORIES_GODOWN = "ACCESSORIES_GODOWN"
    FINISHED_GOODS_GODOWN = "FINISHED_GOODS_GODOWN"

    CHOICES = [
        (YARN_GODOWN, "Yarn Godown / Warehouse"),
        (GREY_FABRIC_GODOWN, "Grey Fabric Godown"),
        (DYED_FABRIC_GODOWN, "Dyed Fabric Godown"),
        (ACCESSORIES_GODOWN, "Accessories Godown"),
        (FINISHED_GOODS_GODOWN, "Finished Goods Godown"),
    ]


class KnittingProgramStatus:
    DRAFT = 0
    AUTHORIZED = 1
    IN_PROGRESS = 2
    COMPLETED = 3
    CANCELLED = 4

    CHOICES = [
        (DRAFT, "Draft"),
        (AUTHORIZED, "Authorized / Released"),
        (IN_PROGRESS, "In Progress"),
        (COMPLETED, "Completed"),
        (CANCELLED, "Cancelled"),
    ]


class GreyFabricInwardSources:
    KNITTING = "KNITTING"
    PURCHASE_PO = "PURCHASE_PO"

    CHOICES = [
        (KNITTING, "Knitting Job Work"),
        (PURCHASE_PO, "Direct Grey Fabric Purchase PO"),
    ]


class GreyFabricOutwardTypes:
    DYEING = "DYEING"
    RETURN = "RETURN"

    CHOICES = [
        (DYEING, "Grey Fabric Outward for Dyeing"),
        (RETURN, "Grey Fabric Return (to Knitter/Trader)"),
    ]


class PriceListType:
    PURCHASE = "PURCHASE"
    SALES = "SALES"
    JOB_WORK = "JOB_WORK"

    CHOICES = [
        (PURCHASE, "Purchase Price List"),
        (SALES, "Sales Price List"),
        (JOB_WORK, "Job Work Price List"),
    ]


class PriceListScope:
    GENERAL = "GENERAL"
    PARTY_SPECIFIC = "PARTY_SPECIFIC"

    CHOICES = [
        (GENERAL, "General Base Price List"),
        (PARTY_SPECIFIC, "Party-Specific Price List"),
    ]


class PriceListItemType:
    YARN = "YARN"
    FABRIC = "FABRIC"
    GARMENT = "GARMENT"
    TRIM = "TRIM"
    PROCESS = "PROCESS"

    CHOICES = [
        (YARN, "Yarn"),
        (FABRIC, "Fabric"),
        (GARMENT, "Garment / Style"),
        (TRIM, "Trims / Accessories"),
        (PROCESS, "Process Service"),
    ]


class YarnDefectReasons:
    COUNT_VARIATION = "COUNT_VARIATION"
    LOW_CSP = "LOW_CSP"
    HIGH_HAIRINESS = "HIGH_HAIRINESS"
    COLOR_SHADE_DEFECT = "COLOR_SHADE_DEFECT"
    DAMAGED_CONES = "DAMAGED_CONES"
    EXCESS_MOISTURE = "EXCESS_MOISTURE"

    CHOICES = [
        (COUNT_VARIATION, "Count Variation (> ±2.5%)"),
        (LOW_CSP, "Low CSP (Strength below standard)"),
        (HIGH_HAIRINESS, "High Hairiness (H-value > 6.2)"),
        (COLOR_SHADE_DEFECT, "Color / Shade Variation (Delta E > 0.8)"),
        (DAMAGED_CONES, "Damaged / Crushed Cones / Transit Defect"),
        (EXCESS_MOISTURE, "Excess Moisture Regain (> 8.5%)"),
    ]


YARN_KNITTING_PIPELINE_ROUTING = [
    {
        "yarn_category": YarnCategory.GREY,
        "yarn_description": "Raw / Ecru Cotton, Blends",
        "intended_end_fabric": "Solid-color T-shirts, tops, and basic apparel",
        "knitting_process_setup": "Circular single jersey machines (plain knit)",
        "inward_output_stage": FabricCategory.GREY,
        "inward_output_description": "Grey Fabric (GREY_FABRIC) - Greige rolls / thans",
        "next_production_pipeline": "Sent to dye house for scouring, bleaching, and batch/piece dyeing (soft-flow)",
    },
    {
        "yarn_category": YarnCategory.GREY,
        "yarn_description": "Raw / Ecru with Elastane attachment",
        "intended_end_fabric": "Stretch T-shirts, leggings, activewear",
        "knitting_process_setup": "Single jersey machines with elastane attachment (e.g., 20D/40D Lycra)",
        "inward_output_stage": FabricCategory.GREY,
        "inward_output_description": "Grey Fabric (GREY_FABRIC) - Greige Lycra single jersey",
        "next_production_pipeline": "Sent for heat-setting (stenter), scouring, and piece dyeing",
    },
    {
        "yarn_category": YarnCategory.GREY,
        "yarn_description": "Raw / Ecru",
        "intended_end_fabric": "Polo shirt bodies, tennis tees",
        "knitting_process_setup": "Pique / honeycomb / Lacoste circular machines",
        "inward_output_stage": FabricCategory.GREY,
        "inward_output_description": "Grey Fabric (GREY_FABRIC) - Greige pique rolls",
        "next_production_pipeline": "Batch dyeing, bio-polishing, compacting",
    },
    {
        "yarn_category": YarnCategory.GREY,
        "yarn_description": "Raw / Ecru Cotton / Blends",
        "intended_end_fabric": "Winter hoodies, sweatshirts, joggers",
        "knitting_process_setup": "2-thread or 3-thread fleece machines (face, tie, and loop yarn)",
        "inward_output_stage": FabricCategory.GREY,
        "inward_output_description": "Grey Fabric (GREY_FABRIC) - Greige fleece rolls",
        "next_production_pipeline": "Scouring, dyeing, loop raising/brushing (fleece nap)",
    },
    {
        "yarn_category": YarnCategory.GREY,
        "yarn_description": "Raw / Ecru Combed Cotton",
        "intended_end_fabric": "Premium tees, babywear, double-sided knitwear",
        "knitting_process_setup": "Interlock circular knitting machines",
        "inward_output_stage": FabricCategory.GREY,
        "inward_output_description": "Grey Fabric (GREY_FABRIC) - Greige interlock rolls",
        "next_production_pipeline": "Batch dyeing, softening, compacting",
    },
    {
        "yarn_category": YarnCategory.DYED,
        "yarn_description": "Package/Cone-Dyed Yarn",
        "intended_end_fabric": "Horizontal striped T-shirts, rugby shirts",
        "knitting_process_setup": "Circular machines with multiple feeders alternating colored yarn cones (feeder stripe)",
        "inward_output_stage": FabricCategory.DYED,
        "inward_output_description": "Yarn-Dyed Fabric (DYED_FABRIC) - Striped rolls ready without batch dyeing",
        "next_production_pipeline": "Direct scouring, tentering/stenter finishing, and compacting (no piece dyeing required)",
    },
    {
        "yarn_category": YarnCategory.DYED,
        "yarn_description": "Package/Cone-Dyed Yarn",
        "intended_end_fabric": "Branded polo bodies with custom chest bands",
        "knitting_process_setup": "Auto-striper circular knitting machines with programmable finger selectors (engineered stripes)",
        "inward_output_stage": FabricCategory.DYED,
        "inward_output_description": "Yarn-Dyed Fabric (DYED_FABRIC) - Engineered stripe rolls",
        "next_production_pipeline": "Slitting, finishing, stenter, compacting",
    },
    {
        "yarn_category": YarnCategory.DYED,
        "yarn_description": "Package/Cone-Dyed Yarn",
        "intended_end_fabric": "Polo neck collars and sleeve cuffs with tipping lines",
        "knitting_process_setup": "Flatbed knitting machines (e.g., Shima Seiki, Stoll)",
        "inward_output_stage": "TRIM",
        "inward_output_description": "Flat Knit Trims / Collars (TRIM / FABRIC) - Pieces or collar strips",
        "next_production_pipeline": "Ironing, cutting, inspection, directly attached during garment stitching",
    },
    {
        "yarn_category": YarnCategory.DYED,
        "yarn_description": "Package/Cone-Dyed Yarn",
        "intended_end_fabric": "Multi-color textured patterns, knit cardigans, sweaters",
        "knitting_process_setup": "Electronic jacquard circular or flat knitting machines",
        "inward_output_stage": FabricCategory.DYED,
        "inward_output_description": "Jacquard Knit Fabric (DYED_FABRIC) - Patterned rolls / panels",
        "next_production_pipeline": "Steam relaxing, washing/softening, compacting",
    },
    {
        "yarn_category": YarnCategory.MELANGE,
        "yarn_description": "Fibre-dyed blend (Heather)",
        "intended_end_fabric": "Heather grey athletic T-shirts, joggers, gym wear",
        "knitting_process_setup": "Circular single jersey, fleece, or French terry machines",
        "inward_output_stage": FabricCategory.DYED,
        "inward_output_description": "Melange Fabric (DYED_FABRIC) - Grey/color heather rolls",
        "next_production_pipeline": "Scouring, softening, compacting (no piece-dye bath needed)",
    },
]



