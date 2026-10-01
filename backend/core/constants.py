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
    ]


class PartyTypes:
    MILL = "MILL"
    TRADER = "TRADER"
    KNITTING_UNIT = "KNITTING_UNIT"
    DYEING_UNIT = "DYEING_UNIT"
    CUSTOMER = "CUSTOMER"
    SUPPLIER = "SUPPLIER"
    JOB_WORKER = "JOB_WORKER"

    CHOICES = [
        (MILL, "Yarn / Fabric Mill"),
        (TRADER, "Trader / Broker"),
        (KNITTING_UNIT, "Knitting Unit"),
        (DYEING_UNIT, "Dyeing / Processing Unit"),
        (CUSTOMER, "Customer"),
        (SUPPLIER, "Supplier / Vendor"),
        (JOB_WORKER, "Job Worker"),
    ]


class YarnCategory:
    GREY = "GREY"
    DYED = "DYED"

    CHOICES = [
        (GREY, "Grey Yarn"),
        (DYED, "Dyed Yarn"),
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
