import json
import os

collection = {
    "info": {
        "_postman_id": "garments-erp-yarn-api-v2-1",
        "name": "Garments ERP - Yarn Complete API Suite",
        "description": "Comprehensive Postman Collection for all Yarn operations in Garments ERP & CRM.\n\nIncludes:\n1. Authentication (Super Admin & Company Admin with auto-extracted tokens)\n2. Yarn Master Catalog (CRUD, filtering by category/yarn_type, count, searching)\n3. Supporting Masters (Yarn Counts, Color Shades, UOM, Company Yarn Types, Mills)\n4. Yarn Procurement (Purchase Orders with schedules, authorization, live balance)\n5. Godown Inventory (Live Stock Ledger, GRN Inwards, DC Outwards for Knitting/Dyeing)\n6. Commercial Sales & Customer Returns\n7. Knitting Production (Yarn consumption & planned vs issued reconciliation)\n\nEnvironment / Collection Variables:\n- base_url: http://127.0.0.1:8000\n- access_token: auto-populated by login scripts\n- company_id: 1",
        "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
    },
    "variable": [
        {"key": "base_url", "value": "http://127.0.0.1:8000", "type": "string"},
        {"key": "access_token", "value": "", "type": "string"},
        {"key": "refresh_token", "value": "", "type": "string"},
        {"key": "company_id", "value": "1", "type": "string"},
        {"key": "yarn_id", "value": "1", "type": "string"},
        {"key": "yarn_count_id", "value": "1", "type": "string"},
        {"key": "color_shade_id", "value": "1", "type": "string"},
        {"key": "uom_id", "value": "1", "type": "string"},
        {"key": "po_id", "value": "1", "type": "string"},
        {"key": "warehouse_id", "value": "1", "type": "string"},
        {"key": "mill_party_id", "value": "1", "type": "string"},
        {"key": "customer_party_id", "value": "5", "type": "string"},
        {"key": "voucher_id", "value": "1", "type": "string"},
        {"key": "process_stage_id", "value": "1", "type": "string"},
        {"key": "process_program_id", "value": "1", "type": "string"},
        {"key": "price_list_id", "value": "2", "type": "string"}
    ],
    "auth": {
        "type": "bearer",
        "bearer": [
            {"key": "token", "value": "{{access_token}}", "type": "string"}
        ]
    },
    "item": [
        {
            "name": "1. Authentication",
            "item": [
                {
                    "name": "1.1 Login - Super Admin (auto-sets token)",
                    "event": [{
                        "listen": "test",
                        "script": {
                            "exec": [
                                "var jsonData = pm.response.json();",
                                "if (jsonData.success && jsonData.data && jsonData.data.access) {",
                                "    pm.collectionVariables.set('access_token', jsonData.data.access);",
                                "    pm.collectionVariables.set('refresh_token', jsonData.data.refresh);",
                                "    console.log('Super Admin Token auto-saved to {{access_token}}');",
                                "}"
                            ],
                            "type": "text/javascript"
                        }
                    }],
                    "request": {
                        "auth": {"type": "noauth"},
                        "method": "POST",
                        "header": [{"key": "Content-Type", "value": "application/json"}],
                        "body": {
                            "mode": "raw",
                            "raw": json.dumps({"email": "superadmin@gmail.com", "password": "Password123!"}, indent=4)
                        },
                        "url": {
                            "raw": "{{base_url}}/api/v1/auth/login/",
                            "host": ["{{base_url}}"],
                            "path": ["api", "v1", "auth", "login", ""]
                        }
                    }
                },
                {
                    "name": "1.2 Login - Company Admin (auto-sets token & company)",
                    "event": [{
                        "listen": "test",
                        "script": {
                            "exec": [
                                "var jsonData = pm.response.json();",
                                "if (jsonData.success && jsonData.data && jsonData.data.access) {",
                                "    pm.collectionVariables.set('access_token', jsonData.data.access);",
                                "    pm.collectionVariables.set('refresh_token', jsonData.data.refresh);",
                                "    if (jsonData.data.user && jsonData.data.user.company) {",
                                "        pm.collectionVariables.set('company_id', jsonData.data.user.company.id);",
                                "    }",
                                "    console.log('Company Admin Token auto-saved to {{access_token}}');",
                                "}"
                            ],
                            "type": "text/javascript"
                        }
                    }],
                    "request": {
                        "auth": {"type": "noauth"},
                        "method": "POST",
                        "header": [{"key": "Content-Type", "value": "application/json"}],
                        "body": {
                            "mode": "raw",
                            "raw": json.dumps({"email": "admin@gmail.com", "password": "Password123!"}, indent=4)
                        },
                        "url": {
                            "raw": "{{base_url}}/api/v1/auth/login/",
                            "host": ["{{base_url}}"],
                            "path": ["api", "v1", "auth", "login", ""]
                        }
                    }
                },
                {
                    "name": "1.3 Refresh Access Token",
                    "request": {
                        "auth": {"type": "noauth"},
                        "method": "POST",
                        "header": [{"key": "Content-Type", "value": "application/json"}],
                        "body": {
                            "mode": "raw",
                            "raw": json.dumps({"refresh": "{{refresh_token}}"}, indent=4)
                        },
                        "url": {
                            "raw": "{{base_url}}/api/v1/auth/refresh/",
                            "host": ["{{base_url}}"],
                            "path": ["api", "v1", "auth", "refresh", ""]
                        }
                    }
                }
            ]
        },
        {
            "name": "2. Yarn Master Catalog (mx_yarn)",
            "item": [
                {
                    "name": "2.1 List All Yarns (paginated)",
                    "event": [{
                        "listen": "test",
                        "script": {
                            "exec": [
                                "var jsonData = pm.response.json();",
                                "var list = jsonData.results || (jsonData.data ? (jsonData.data.results || jsonData.data) : null);",
                                "if (list && list.length > 0) {",
                                "    pm.collectionVariables.set('yarn_id', list[0].id);",
                                "    console.log('Sample yarn_id set to: ' + list[0].id);",
                                "}"
                            ],
                            "type": "text/javascript"
                        }
                    }],
                    "request": {
                        "method": "GET",
                        "header": [{"key": "X-Company-ID", "value": "{{company_id}}"}],
                        "url": {
                            "raw": "{{base_url}}/api/v1/masters/yarns/?page=1&page_size=20",
                            "host": ["{{base_url}}"],
                            "path": ["api", "v1", "masters", "yarns", ""],
                            "query": [
                                {"key": "page", "value": "1"},
                                {"key": "page_size", "value": "20"}
                            ]
                        }
                    }
                },
                {
                    "name": "2.2 Filter Yarns by Category (e.g. GREY)",
                    "request": {
                        "method": "GET",
                        "header": [{"key": "X-Company-ID", "value": "{{company_id}}"}],
                        "url": {
                            "raw": "{{base_url}}/api/v1/masters/yarns/?category=GREY",
                            "host": ["{{base_url}}"],
                            "path": ["api", "v1", "masters", "yarns", ""],
                            "query": [
                                {"key": "category", "value": "GREY"}
                            ]
                        }
                    }
                },
                {
                    "name": "2.3 Filter Yarns by Yarn Type Alias (e.g. MELANGE)",
                    "request": {
                        "method": "GET",
                        "header": [{"key": "X-Company-ID", "value": "{{company_id}}"}],
                        "url": {
                            "raw": "{{base_url}}/api/v1/masters/yarns/?yarn_type=MELANGE",
                            "host": ["{{base_url}}"],
                            "path": ["api", "v1", "masters", "yarns", ""],
                            "query": [
                                {"key": "yarn_type", "value": "MELANGE"}
                            ]
                        }
                    }
                },
                {
                    "name": "2.4 Search Yarns (Count, Shade or Code)",
                    "request": {
                        "method": "GET",
                        "header": [{"key": "X-Company-ID", "value": "{{company_id}}"}],
                        "url": {
                            "raw": "{{base_url}}/api/v1/masters/yarns/?search=30s",
                            "host": ["{{base_url}}"],
                            "path": ["api", "v1", "masters", "yarns", ""],
                            "query": [
                                {"key": "search", "value": "30s"}
                            ]
                        }
                    }
                },
                {
                    "name": "2.5 Create Yarn - Grey Yarn",
                    "event": [{
                        "listen": "test",
                        "script": {
                            "exec": [
                                "var jsonData = pm.response.json();",
                                "var y = jsonData.data || jsonData;",
                                "if (y && y.id) {",
                                "    pm.collectionVariables.set('yarn_id', y.id);",
                                "    console.log('New Yarn ID set to: ' + y.id);",
                                "}"
                            ],
                            "type": "text/javascript"
                        }
                    }],
                    "request": {
                        "method": "POST",
                        "header": [
                            {"key": "Content-Type", "value": "application/json"},
                            {"key": "X-Company-ID", "value": "{{company_id}}"}
                        ],
                        "body": {
                            "mode": "raw",
                            "raw": json.dumps({
                                "yarn_code": "YRN-30S-COT-GRY-SAMPLE",
                                "yarn_count": 1,
                                "category": "GREY",
                                "uom": 1,
                                "hsn_code": "5205",
                                "reorder_level": "1000.00",
                                "description": "30s 100% Combed Cotton Grey Knitting Yarn",
                                "is_active": True
                            }, indent=4)
                        },
                        "url": {
                            "raw": "{{base_url}}/api/v1/masters/yarns/",
                            "host": ["{{base_url}}"],
                            "path": ["api", "v1", "masters", "yarns", ""]
                        }
                    }
                },
                {
                    "name": "2.6 Create Yarn - Dyed Yarn (requires color_shade)",
                    "request": {
                        "method": "POST",
                        "header": [
                            {"key": "Content-Type", "value": "application/json"},
                            {"key": "X-Company-ID", "value": "{{company_id}}"}
                        ],
                        "body": {
                            "mode": "raw",
                            "raw": json.dumps({
                                "yarn_code": "YRN-30S-COT-NVY-SAMPLE",
                                "yarn_count": 1,
                                "category": "DYED",
                                "color_shade": 1,
                                "uom": 1,
                                "hsn_code": "5205",
                                "reorder_level": "800.00",
                                "description": "30s Dyed Navy Blue 100% Cotton Yarn",
                                "is_active": True
                            }, indent=4)
                        },
                        "url": {
                            "raw": "{{base_url}}/api/v1/masters/yarns/",
                            "host": ["{{base_url}}"],
                            "path": ["api", "v1", "masters", "yarns", ""]
                        }
                    }
                },
                {
                    "name": "2.7 Create Yarn - Melange Yarn",
                    "request": {
                        "method": "POST",
                        "header": [
                            {"key": "Content-Type", "value": "application/json"},
                            {"key": "X-Company-ID", "value": "{{company_id}}"}
                        ],
                        "body": {
                            "mode": "raw",
                            "raw": json.dumps({
                                "yarn_code": "YRN-30S-COT-MEL-SAMPLE",
                                "yarn_count": 1,
                                "category": "MELANGE",
                                "color_shade": 2,
                                "uom": 1,
                                "hsn_code": "5205",
                                "reorder_level": "600.00",
                                "description": "30s Cotton Grey Melange Yarn",
                                "is_active": True
                            }, indent=4)
                        },
                        "url": {
                            "raw": "{{base_url}}/api/v1/masters/yarns/",
                            "host": ["{{base_url}}"],
                            "path": ["api", "v1", "masters", "yarns", ""]
                        }
                    }
                },
                {
                    "name": "2.8 Retrieve Yarn by ID",
                    "request": {
                        "method": "GET",
                        "header": [{"key": "X-Company-ID", "value": "{{company_id}}"}],
                        "url": {
                            "raw": "{{base_url}}/api/v1/masters/yarns/{{yarn_id}}/",
                            "host": ["{{base_url}}"],
                            "path": ["api", "v1", "masters", "yarns", "{{yarn_id}}", ""]
                        }
                    }
                },
                {
                    "name": "2.9 Update Yarn (PUT full replacement)",
                    "request": {
                        "method": "PUT",
                        "header": [
                            {"key": "Content-Type", "value": "application/json"},
                            {"key": "X-Company-ID", "value": "{{company_id}}"}
                        ],
                        "body": {
                            "mode": "raw",
                            "raw": json.dumps({
                                "yarn_code": "YRN-30S-COT-GRY-SAMPLE",
                                "yarn_count": 1,
                                "category": "GREY",
                                "uom": 1,
                                "hsn_code": "5205",
                                "reorder_level": "1250.00",
                                "description": "30s 100% Combed Cotton Grey Knitting Yarn (Updated)",
                                "is_active": True
                            }, indent=4)
                        },
                        "url": {
                            "raw": "{{base_url}}/api/v1/masters/yarns/{{yarn_id}}/",
                            "host": ["{{base_url}}"],
                            "path": ["api", "v1", "masters", "yarns", "{{yarn_id}}", ""]
                        }
                    }
                },
                {
                    "name": "2.10 Partial Update Yarn (PATCH)",
                    "request": {
                        "method": "PATCH",
                        "header": [
                            {"key": "Content-Type", "value": "application/json"},
                            {"key": "X-Company-ID", "value": "{{company_id}}"}
                        ],
                        "body": {
                            "mode": "raw",
                            "raw": json.dumps({
                                "reorder_level": "1500.00",
                                "description": "Priority reorder level updated via PATCH"
                            }, indent=4)
                        },
                        "url": {
                            "raw": "{{base_url}}/api/v1/masters/yarns/{{yarn_id}}/",
                            "host": ["{{base_url}}"],
                            "path": ["api", "v1", "masters", "yarns", "{{yarn_id}}", ""]
                        }
                    }
                },
                {
                    "name": "2.11 Soft Delete Yarn",
                    "request": {
                        "method": "DELETE",
                        "header": [{"key": "X-Company-ID", "value": "{{company_id}}"}],
                        "url": {
                            "raw": "{{base_url}}/api/v1/masters/yarns/{{yarn_id}}/",
                            "host": ["{{base_url}}"],
                            "path": ["api", "v1", "masters", "yarns", "{{yarn_id}}", ""]
                        }
                    }
                }
            ]
        },
        {
            "name": "3. Supporting Masters (Prerequisites)",
            "item": [
                {
                    "name": "3.1 List Yarn Counts (mx_yarn_count)",
                    "request": {
                        "method": "GET",
                        "header": [{"key": "X-Company-ID", "value": "{{company_id}}"}],
                        "url": {
                            "raw": "{{base_url}}/api/v1/masters/yarn-counts/",
                            "host": ["{{base_url}}"],
                            "path": ["api", "v1", "masters", "yarn-counts", ""]
                        }
                    }
                },
                {
                    "name": "3.2 Create Yarn Count (e.g. 34s, 40s)",
                    "request": {
                        "method": "POST",
                        "header": [
                            {"key": "Content-Type", "value": "application/json"},
                            {"key": "X-Company-ID", "value": "{{company_id}}"}
                        ],
                        "body": {
                            "mode": "raw",
                            "raw": json.dumps({
                                "count": "34s",
                                "description": "34s Combed Cotton Yarn Count",
                                "is_active": True
                            }, indent=4)
                        },
                        "url": {
                            "raw": "{{base_url}}/api/v1/masters/yarn-counts/",
                            "host": ["{{base_url}}"],
                            "path": ["api", "v1", "masters", "yarn-counts", ""]
                        }
                    }
                },
                {
                    "name": "3.3 List Color Shades (mx_color_shade)",
                    "request": {
                        "method": "GET",
                        "header": [{"key": "X-Company-ID", "value": "{{company_id}}"}],
                        "url": {
                            "raw": "{{base_url}}/api/v1/masters/colors/",
                            "host": ["{{base_url}}"],
                            "path": ["api", "v1", "masters", "colors", ""]
                        }
                    }
                },
                {
                    "name": "3.4 Create Color Shade (for Dyed/Melange yarn)",
                    "request": {
                        "method": "POST",
                        "header": [
                            {"key": "Content-Type", "value": "application/json"},
                            {"key": "X-Company-ID", "value": "{{company_id}}"}
                        ],
                        "body": {
                            "mode": "raw",
                            "raw": json.dumps({
                                "shade_code": "BLK-001",
                                "color_name": "Jet Black",
                                "hex_code": "#0B0B0B",
                                "pantone_ref": "19-4008 TCX",
                                "description": "Deep reactive black for dyed cotton yarn",
                                "is_active": True
                            }, indent=4)
                        },
                        "url": {
                            "raw": "{{base_url}}/api/v1/masters/colors/",
                            "host": ["{{base_url}}"],
                            "path": ["api", "v1", "masters", "colors", ""]
                        }
                    }
                },
                {
                    "name": "3.5 List Units of Measurement (mx_uom)",
                    "request": {
                        "method": "GET",
                        "header": [{"key": "X-Company-ID", "value": "{{company_id}}"}],
                        "url": {
                            "raw": "{{base_url}}/api/v1/masters/uom/",
                            "host": ["{{base_url}}"],
                            "path": ["api", "v1", "masters", "uom", ""]
                        }
                    }
                },
                {
                    "name": "3.6 Active Company Yarn Process Types (Configured)",
                    "request": {
                        "method": "GET",
                        "header": [{"key": "X-Company-ID", "value": "{{company_id}}"}],
                        "url": {
                            "raw": "{{base_url}}/api/v1/purchase/yarn-types/active/",
                            "host": ["{{base_url}}"],
                            "path": ["api", "v1", "purchase", "yarn-types", "active", ""]
                        }
                    }
                },
                {
                    "name": "3.7 List Parties (Filter by party_type or search)",
                    "request": {
                        "method": "GET",
                        "header": [{"key": "X-Company-ID", "value": "{{company_id}}"}],
                        "url": {
                            "raw": "{{base_url}}/api/v1/masters/parties/?party_type=MILL&page=1&page_size=20",
                            "host": ["{{base_url}}"],
                            "path": ["api", "v1", "masters", "parties", ""],
                            "query": [
                                {"key": "party_type", "value": "MILL"},
                                {"key": "page", "value": "1"},
                                {"key": "page_size", "value": "20"}
                            ]
                        }
                    }
                },
                {
                    "name": "3.8 Create Party - Spinning Mill (Sets Opening Balance & Auto-sets mill_party_id)",
                    "event": [{
                        "listen": "test",
                        "script": {
                            "exec": [
                                "var jsonData = pm.response.json();",
                                "var p = jsonData.data || jsonData;",
                                "if (p && p.id) {",
                                "    pm.collectionVariables.set('mill_party_id', p.id);",
                                "    console.log('New Mill Party ID auto-saved to: ' + p.id);",
                                "}"
                            ],
                            "type": "text/javascript"
                        }
                    }],
                    "request": {
                        "method": "POST",
                        "header": [
                            {"key": "Content-Type", "value": "application/json"},
                            {"key": "X-Company-ID", "value": "{{company_id}}"}
                        ],
                        "body": {
                            "mode": "raw",
                            "raw": json.dumps({
                                "code": "MILL-VRD-001",
                                "name": "Vardhman Spinning Mills Ltd",
                                "party_type": "MILL",
                                "contact_person": "Ramesh Gupta",
                                "phone": "+91 98765 43210",
                                "email": "sales@vardhmanmills.com",
                                "gst_number": "03AAACV1234F1Z8",
                                "pan_number": "AAACV1234F",
                                "address_line1": "Industrial Focal Point, Phase IV",
                                "city": "Ludhiana",
                                "state": "Punjab",
                                "pincode": "141010",
                                "credit_days": 30,
                                "credit_limit": "2500000.00",
                                "opening_balance": "50000.00",
                                "is_active": True
                            }, indent=4)
                        },
                        "url": {
                            "raw": "{{base_url}}/api/v1/masters/parties/",
                            "host": ["{{base_url}}"],
                            "path": ["api", "v1", "masters", "parties", ""]
                        }
                    }
                },
                {
                    "name": "3.9 Create Party - Garment Customer (Sets Opening Balance & Auto-sets customer_party_id)",
                    "event": [{
                        "listen": "test",
                        "script": {
                            "exec": [
                                "var jsonData = pm.response.json();",
                                "var p = jsonData.data || jsonData;",
                                "if (p && p.id) {",
                                "    pm.collectionVariables.set('customer_party_id', p.id);",
                                "    console.log('New Customer Party ID auto-saved to: ' + p.id);",
                                "}"
                            ],
                            "type": "text/javascript"
                        }
                    }],
                    "request": {
                        "method": "POST",
                        "header": [
                            {"key": "Content-Type", "value": "application/json"},
                            {"key": "X-Company-ID", "value": "{{company_id}}"}
                        ],
                        "body": {
                            "mode": "raw",
                            "raw": json.dumps({
                                "code": "CUST-TEX-001",
                                "name": "Tirupur Global Exports & Apparels",
                                "party_type": "CUSTOMER",
                                "contact_person": "Murugan S",
                                "phone": "+91 94432 10987",
                                "email": "orders@tirupurexports.com",
                                "gst_number": "33AABCT9876A1ZB",
                                "pan_number": "AABCT9876A",
                                "address_line1": "Avinashi Road, Kangeyam Cross",
                                "city": "Tirupur",
                                "state": "Tamil Nadu",
                                "pincode": "641602",
                                "credit_days": 45,
                                "credit_limit": "1500000.00",
                                "opening_balance": "25000.00",
                                "is_active": True
                            }, indent=4)
                        },
                        "url": {
                            "raw": "{{base_url}}/api/v1/masters/parties/",
                            "host": ["{{base_url}}"],
                            "path": ["api", "v1", "masters", "parties", ""]
                        }
                    }
                },
                {
                    "name": "3.10 Retrieve Party by ID (mx_party)",
                    "request": {
                        "method": "GET",
                        "header": [{"key": "X-Company-ID", "value": "{{company_id}}"}],
                        "url": {
                            "raw": "{{base_url}}/api/v1/masters/parties/{{mill_party_id}}/",
                            "host": ["{{base_url}}"],
                            "path": ["api", "v1", "masters", "parties", "{{mill_party_id}}", ""]
                        }
                    }
                },
                {
                    "name": "3.11 Update Party / Adjust Opening Balance (PATCH mx_party)",
                    "request": {
                        "method": "PATCH",
                        "header": [
                            {"key": "Content-Type", "value": "application/json"},
                            {"key": "X-Company-ID", "value": "{{company_id}}"}
                        ],
                        "body": {
                            "mode": "raw",
                            "raw": json.dumps({
                                "credit_limit": "3000000.00",
                                "opening_balance": "60000.00",
                                "phone": "+91 98765 00000"
                            }, indent=4)
                        },
                        "url": {
                            "raw": "{{base_url}}/api/v1/masters/parties/{{mill_party_id}}/",
                            "host": ["{{base_url}}"],
                            "path": ["api", "v1", "masters", "parties", "{{mill_party_id}}", ""]
                        }
                    }
                },
                {
                    "name": "3.12 List Warehouses / Godowns (mx_warehouse)",
                    "request": {
                        "method": "GET",
                        "header": [{"key": "X-Company-ID", "value": "{{company_id}}"}],
                        "url": {
                            "raw": "{{base_url}}/api/v1/masters/warehouses/",
                            "host": ["{{base_url}}"],
                            "path": ["api", "v1", "masters", "warehouses", ""]
                        }
                    }
                },
                {
                    "name": "3.13 Create Warehouse / Godown",
                    "event": [{
                        "listen": "test",
                        "script": {
                            "exec": [
                                "var jsonData = pm.response.json();",
                                "var w = jsonData.data || jsonData;",
                                "if (w && w.id) {",
                                "    pm.collectionVariables.set('warehouse_id', w.id);",
                                "    console.log('New Warehouse ID auto-saved to: ' + w.id);",
                                "}"
                            ],
                            "type": "text/javascript"
                        }
                    }],
                    "request": {
                        "method": "POST",
                        "header": [
                            {"key": "Content-Type", "value": "application/json"},
                            {"key": "X-Company-ID", "value": "{{company_id}}"}
                        ],
                        "body": {
                            "mode": "raw",
                            "raw": json.dumps({
                                "code": "WH-YRN-MAIN",
                                "name": "Central Yarn Godown No 1",
                                "warehouse_type": "YARN",
                                "address": "Shed 4, SIPCOT Industrial Park",
                                "city": "Perundurai",
                                "state": "Tamil Nadu",
                                "is_active": True
                            }, indent=4)
                        },
                        "url": {
                            "raw": "{{base_url}}/api/v1/masters/warehouses/",
                            "host": ["{{base_url}}"],
                            "path": ["api", "v1", "masters", "warehouses", ""]
                        }
                    }
                },
                {
                    "name": "3.14 List Tax Master (GST Slabs: 0%, 5%, 12%, 18%, 28%)",
                    "request": {
                        "method": "GET",
                        "header": [{"key": "X-Company-ID", "value": "{{company_id}}"}],
                        "url": {
                            "raw": "{{base_url}}/api/v1/masters/taxes/",
                            "host": ["{{base_url}}"],
                            "path": ["api", "v1", "masters", "taxes", ""]
                        }
                    }
                }
            ]
        },
        {
            "name": "4. Yarn Procurement (Purchase Orders)",
            "item": [
                {
                    "name": "4.1 List Yarn Purchase Orders",
                    "event": [{
                        "listen": "test",
                        "script": {
                            "exec": [
                                "var jsonData = pm.response.json();",
                                "var list = jsonData.results || (jsonData.data ? (jsonData.data.results || jsonData.data) : null);",
                                "if (list && list.length > 0) {",
                                "    pm.collectionVariables.set('po_id', list[0].id);",
                                "    console.log('Sample po_id set to: ' + list[0].id);",
                                "}"
                            ],
                            "type": "text/javascript"
                        }
                    }],
                    "request": {
                        "method": "GET",
                        "header": [{"key": "X-Company-ID", "value": "{{company_id}}"}],
                        "url": {
                            "raw": "{{base_url}}/api/v1/purchase/yarn-pos/",
                            "host": ["{{base_url}}"],
                            "path": ["api", "v1", "purchase", "yarn-pos", ""]
                        }
                    }
                },
                {
                    "name": "4.2 Create Yarn PO (Draft status)",
                    "event": [{
                        "listen": "test",
                        "script": {
                            "exec": [
                                "var jsonData = pm.response.json();",
                                "var po = jsonData.data || jsonData;",
                                "if (po && po.id) {",
                                "    pm.collectionVariables.set('po_id', po.id);",
                                "    console.log('Created PO ID: ' + po.id);",
                                "}"
                            ],
                            "type": "text/javascript"
                        }
                    }],
                    "request": {
                        "method": "POST",
                        "header": [
                            {"key": "Content-Type", "value": "application/json"},
                            {"key": "X-Company-ID", "value": "{{company_id}}"}
                        ],
                        "body": {
                            "mode": "raw",
                            "raw": json.dumps({
                                "po_number": "YPO-202610-5001",
                                "po_date": "13/10/2026",
                                "yarn_type": "GREY",
                                "party": 1,
                                "mill": 1,
                                "yarn_count": 1,
                                "uom": 1,
                                "quantity": "5000.000",
                                "rate_per_kg": "290.00",
                                "payment_terms": "30 Days Credit"
                            }, indent=4)
                        },
                        "url": {
                            "raw": "{{base_url}}/api/v1/purchase/yarn-pos/",
                            "host": ["{{base_url}}"],
                            "path": ["api", "v1", "purchase", "yarn-pos", ""]
                        }
                    }
                },
                {
                    "name": "4.3 Authorize Yarn PO (Locks against edit)",
                    "request": {
                        "method": "POST",
                        "header": [
                            {"key": "Content-Type", "value": "application/json"},
                            {"key": "X-Company-ID", "value": "{{company_id}}"}
                        ],
                        "url": {
                            "raw": "{{base_url}}/api/v1/purchase/yarn-pos/{{po_id}}/authorize/",
                            "host": ["{{base_url}}"],
                            "path": ["api", "v1", "purchase", "yarn-pos", "{{po_id}}", "authorize", ""]
                        }
                    }
                },
                {
                    "name": "4.4 Unauthorize Yarn PO (Reopen for change)",
                    "request": {
                        "method": "POST",
                        "header": [
                            {"key": "Content-Type", "value": "application/json"},
                            {"key": "X-Company-ID", "value": "{{company_id}}"}
                        ],
                        "url": {
                            "raw": "{{base_url}}/api/v1/purchase/yarn-pos/{{po_id}}/unauthorize/",
                            "host": ["{{base_url}}"],
                            "path": ["api", "v1", "purchase", "yarn-pos", "{{po_id}}", "unauthorize", ""]
                        }
                    }
                },
                {
                    "name": "4.5 Live PO Balance Tracking",
                    "request": {
                        "method": "GET",
                        "header": [{"key": "X-Company-ID", "value": "{{company_id}}"}],
                        "url": {
                            "raw": "{{base_url}}/api/v1/purchase/balances/",
                            "host": ["{{base_url}}"],
                            "path": ["api", "v1", "purchase", "balances", ""]
                        }
                    }
                }
            ]
        },
        {
            "name": "5. Yarn Godown Inventory & Stock Ledger",
            "item": [
                {
                    "name": "5.1 Live Godown Yarn Stock Ledger (Bags & Kgs)",
                    "request": {
                        "method": "GET",
                        "header": [{"key": "X-Company-ID", "value": "{{company_id}}"}],
                        "url": {
                            "raw": "{{base_url}}/api/v1/inventory/yarn-stock/",
                            "host": ["{{base_url}}"],
                            "path": ["api", "v1", "inventory", "yarn-stock", ""]
                        }
                    }
                },
                {
                    "name": "5.2 Post Yarn Inward GRN (Credits Stock, reduces PO)",
                    "request": {
                        "method": "POST",
                        "header": [
                            {"key": "Content-Type", "value": "application/json"},
                            {"key": "X-Company-ID", "value": "{{company_id}}"}
                        ],
                        "body": {
                            "mode": "raw",
                            "raw": json.dumps({
                                "inward_number": "GRN-202610-8001",
                                "inward_date": "13/10/2026",
                                "yarn_type": "GREY",
                                "warehouse": 1,
                                "po": 1,
                                "party": 1,
                                "mill": 1,
                                "yarn_count": 1,
                                "uom": 1,
                                "total_bags": 50,
                                "gross_weight": "2525.000",
                                "tare_weight": "25.000",
                                "net_weight": "2500.000",
                                "rate_per_kg": "290.00",
                                "lot_number": "LOT-CT-901"
                            }, indent=4)
                        },
                        "url": {
                            "raw": "{{base_url}}/api/v1/inventory/yarn-inwards/",
                            "host": ["{{base_url}}"],
                            "path": ["api", "v1", "inventory", "yarn-inwards", ""]
                        }
                    }
                },
                {
                    "name": "5.3 Post Yarn Outward DC (For Knitting/Dyeing)",
                    "request": {
                        "method": "POST",
                        "header": [
                            {"key": "Content-Type", "value": "application/json"},
                            {"key": "X-Company-ID", "value": "{{company_id}}"}
                        ],
                        "body": {
                            "mode": "raw",
                            "raw": json.dumps({
                                "dc_number": "DC-202610-8001",
                                "dc_date": "13/10/2026",
                                "outward_type": "KNITTING",
                                "yarn_type": "GREY",
                                "warehouse": 1,
                                "destination_party": 3,
                                "yarn_count": 1,
                                "uom": 1,
                                "total_bags": 20,
                                "gross_weight": "1010.000",
                                "tare_weight": "10.000",
                                "net_weight": "1000.000",
                                "lot_number": "LOT-CT-901",
                                "vehicle_number": "TN-38-AA-1234"
                            }, indent=4)
                        },
                        "url": {
                            "raw": "{{base_url}}/api/v1/inventory/yarn-outwards/",
                            "host": ["{{base_url}}"],
                            "path": ["api", "v1", "inventory", "yarn-outwards", ""]
                        }
                    }
                },
                {
                    "name": "5.4 Stock Ledger Audit Movements (All Stage Movements)",
                    "request": {
                        "method": "GET",
                        "header": [{"key": "X-Company-ID", "value": "{{company_id}}"}],
                        "url": {
                            "raw": "{{base_url}}/api/v1/ledger/stock-movements/?stage=YARN&page=1&page_size=20",
                            "host": ["{{base_url}}"],
                            "path": ["api", "v1", "ledger", "stock-movements", ""],
                            "query": [
                                {"key": "stage", "value": "YARN"},
                                {"key": "page", "value": "1"},
                                {"key": "page_size", "value": "20"}
                            ]
                        }
                    }
                },
                {
                    "name": "5.5 Stock Ledger Filtered by Party (Mill/Supplier / Customer)",
                    "request": {
                        "method": "GET",
                        "header": [{"key": "X-Company-ID", "value": "{{company_id}}"}],
                        "url": {
                            "raw": "{{base_url}}/api/v1/ledger/stock-movements/?party_id={{mill_party_id}}&stage=YARN",
                            "host": ["{{base_url}}"],
                            "path": ["api", "v1", "ledger", "stock-movements", ""],
                            "query": [
                                {"key": "party_id", "value": "{{mill_party_id}}"},
                                {"key": "stage", "value": "YARN"}
                            ]
                        }
                    }
                },
                {
                    "name": "5.6 Party Physical Stock Summary (In/Out & Net Qty)",
                    "request": {
                        "method": "GET",
                        "header": [{"key": "X-Company-ID", "value": "{{company_id}}"}],
                        "url": {
                            "raw": "{{base_url}}/api/v1/ledger/stock-movements/party-summary/?party_id={{mill_party_id}}&stage=YARN",
                            "host": ["{{base_url}}"],
                            "path": ["api", "v1", "ledger", "stock-movements", "party-summary", ""],
                            "query": [
                                {"key": "party_id", "value": "{{mill_party_id}}"},
                                {"key": "stage", "value": "YARN"}
                            ]
                        }
                    }
                },
                {
                    "name": "5.7 Live Yarn Stock by Process Type (GREY / DYED / MELANGE / BLENDED / WOUND)",
                    "request": {
                        "method": "GET",
                        "header": [{"key": "X-Company-ID", "value": "{{company_id}}"}],
                        "url": {
                            "raw": "{{base_url}}/api/v1/inventory/yarn-stock/?yarn_type=GREY",
                            "host": ["{{base_url}}"],
                            "path": ["api", "v1", "inventory", "yarn-stock", ""],
                            "query": [
                                {"key": "yarn_type", "value": "GREY", "description": "GREY, DYED, MELANGE, BLENDED, WOUND"}
                            ]
                        }
                    }
                },
                {
                    "name": "5.8 Live Stage Stock on Hand (Stage-wise: YARN / GREY_FABRIC / DYED_FABRIC)",
                    "request": {
                        "method": "GET",
                        "header": [{"key": "X-Company-ID", "value": "{{company_id}}"}],
                        "url": {
                            "raw": "{{base_url}}/api/v1/ledger/stage-stocks/?stage=YARN",
                            "host": ["{{base_url}}"],
                            "path": ["api", "v1", "ledger", "stage-stocks", ""],
                            "query": [
                                {"key": "stage", "value": "YARN", "description": "YARN, GREY_FABRIC, DYED_FABRIC, CUT_PANELS, GARMENTS"}
                            ]
                        }
                    }
                },
                {
                    "name": "5.9 Stock Ledger Movements Filtered by Stage",
                    "request": {
                        "method": "GET",
                        "header": [{"key": "X-Company-ID", "value": "{{company_id}}"}],
                        "url": {
                            "raw": "{{base_url}}/api/v1/ledger/stock-movements/?stage=YARN&page=1&page_size=20",
                            "host": ["{{base_url}}"],
                            "path": ["api", "v1", "ledger", "stock-movements", ""],
                            "query": [
                                {"key": "stage", "value": "YARN"},
                                {"key": "page", "value": "1"},
                                {"key": "page_size", "value": "20"}
                            ]
                        }
                    }
                }
            ]
        },
        {
            "name": "6. Yarn Commercial Sales & Customer Returns",
            "item": [
                {
                    "name": "6.1 Issue Commercial Yarn Sales Tax Invoice (Deducts stock)",
                    "request": {
                        "method": "POST",
                        "header": [
                            {"key": "Content-Type", "value": "application/json"},
                            {"key": "X-Company-ID", "value": "{{company_id}}"}
                        ],
                        "body": {
                            "mode": "raw",
                            "raw": json.dumps({
                                "invoice_number": "YSI-202610-8001",
                                "invoice_date": "13/10/2026",
                                "customer": 5,
                                "warehouse": 1,
                                "yarn_type": "GREY",
                                "yarn_count": 1,
                                "uom": 1,
                                "total_bags": 10,
                                "net_weight": "500.000",
                                "rate_per_kg": "315.00",
                                "tax_percent": "5.00",
                                "payment_terms": "30 Days Credit"
                            }, indent=4)
                        },
                        "url": {
                            "raw": "{{base_url}}/api/v1/sales/yarn-sales/",
                            "host": ["{{base_url}}"],
                            "path": ["api", "v1", "sales", "yarn-sales", ""]
                        }
                    }
                },
                {
                    "name": "6.2 Post Customer Yarn Sales Return (Re-credits stock)",
                    "request": {
                        "method": "POST",
                        "header": [
                            {"key": "Content-Type", "value": "application/json"},
                            {"key": "X-Company-ID", "value": "{{company_id}}"}
                        ],
                        "body": {
                            "mode": "raw",
                            "raw": json.dumps({
                                "return_number": "YSR-202610-8001",
                                "return_date": "13/10/2026",
                                "customer": 5,
                                "warehouse": 1,
                                "yarn_type": "GREY",
                                "yarn_count": 1,
                                "uom": 1,
                                "total_bags": 2,
                                "net_weight": "100.000",
                                "rate_per_kg": "315.00",
                                "tax_percent": "5.00",
                                "reason": "Shade variation slightly out of tolerance"
                            }, indent=4)
                        },
                        "url": {
                            "raw": "{{base_url}}/api/v1/sales/yarn-sales-returns/",
                            "host": ["{{base_url}}"],
                            "path": ["api", "v1", "sales", "yarn-sales-returns", ""]
                        }
                    }
                }
            ]
        },
        {
            "name": "7. Knitting Production (Yarn Requirements)",
            "item": [
                {
                    "name": "7.1 List Knitting Programs",
                    "request": {
                        "method": "GET",
                        "header": [{"key": "X-Company-ID", "value": "{{company_id}}"}],
                        "url": {
                            "raw": "{{base_url}}/api/v1/knitting/programs/",
                            "host": ["{{base_url}}"],
                            "path": ["api", "v1", "knitting", "programs", ""]
                        }
                    }
                },
                {
                    "name": "7.2 Knitting Program Live Yarn Reconciliation Summary",
                    "request": {
                        "method": "GET",
                        "header": [{"key": "X-Company-ID", "value": "{{company_id}}"}],
                        "url": {
                            "raw": "{{base_url}}/api/v1/knitting/programs/1/summary/",
                            "host": ["{{base_url}}"],
                            "path": ["api", "v1", "knitting", "programs", "1", "summary", ""]
                        }
                    }
                }
            ]
        },
        {
            "name": "8. Party Financial Ledger & Payments",
            "item": [
                {
                    "name": "8.1 Party Ledger Statement - Mill / Supplier (Dr/Cr Running Balance)",
                    "request": {
                        "method": "GET",
                        "header": [{"key": "X-Company-ID", "value": "{{company_id}}"}],
                        "url": {
                            "raw": "{{base_url}}/api/v1/ledger/vouchers/party-statement/?party_id={{mill_party_id}}&from_date=01/04/2026&to_date=31/03/2027",
                            "host": ["{{base_url}}"],
                            "path": ["api", "v1", "ledger", "vouchers", "party-statement", ""],
                            "query": [
                                {"key": "party_id", "value": "{{mill_party_id}}"},
                                {"key": "from_date", "value": "01/04/2026"},
                                {"key": "to_date", "value": "31/03/2027"}
                            ]
                        }
                    }
                },
                {
                    "name": "8.2 Party Ledger Statement - Customer (Dr/Cr Running Balance)",
                    "request": {
                        "method": "GET",
                        "header": [{"key": "X-Company-ID", "value": "{{company_id}}"}],
                        "url": {
                            "raw": "{{base_url}}/api/v1/ledger/vouchers/party-statement/?party_id={{customer_party_id}}&from_date=01/04/2026&to_date=31/03/2027",
                            "host": ["{{base_url}}"],
                            "path": ["api", "v1", "ledger", "vouchers", "party-statement", ""],
                            "query": [
                                {"key": "party_id", "value": "{{customer_party_id}}"},
                                {"key": "from_date", "value": "01/04/2026"},
                                {"key": "to_date", "value": "31/03/2027"}
                            ]
                        }
                    }
                },
                {
                    "name": "8.3 Party Ledger Filtered by Transaction Against / Reference",
                    "request": {
                        "method": "GET",
                        "header": [{"key": "X-Company-ID", "value": "{{company_id}}"}],
                        "url": {
                            "raw": "{{base_url}}/api/v1/ledger/vouchers/party-statement/?party_id={{mill_party_id}}&reference_no=YIN-202610",
                            "host": ["{{base_url}}"],
                            "path": ["api", "v1", "ledger", "vouchers", "party-statement", ""],
                            "query": [
                                {"key": "party_id", "value": "{{mill_party_id}}"},
                                {"key": "reference_no", "value": "YIN-202610"}
                            ]
                        }
                    }
                },
                {
                    "name": "8.4 Record Party Payment (Settlement against Inward GRN Invoice)",
                    "event": [{
                        "listen": "test",
                        "script": {
                            "exec": [
                                "var jsonData = pm.response.json();",
                                "var v = jsonData.data || jsonData;",
                                "if (v && v.id) {",
                                "    pm.collectionVariables.set('voucher_id', v.id);",
                                "    console.log('Recorded Payment Voucher ID set to: ' + v.id);",
                                "}"
                            ],
                            "type": "text/javascript"
                        }
                    }],
                    "request": {
                        "method": "POST",
                        "header": [
                            {"key": "Content-Type", "value": "application/json"},
                            {"key": "X-Company-ID", "value": "{{company_id}}"}
                        ],
                        "body": {
                            "mode": "raw",
                            "raw": json.dumps({
                                "party_id": 1,
                                "amount": "50000.00",
                                "doc_date": "13/10/2026",
                                "payment_mode": "BANK",
                                "reference_no": "NEFT/20261013/8821",
                                "against_doc_type": "INWARD_GRN",
                                "against_doc_number": "YIN-202610-8001",
                                "narration": "Payment towards Mill Yarn PO Inward settlement"
                            }, indent=4)
                        },
                        "url": {
                            "raw": "{{base_url}}/api/v1/ledger/vouchers/record-payment/",
                            "host": ["{{base_url}}"],
                            "path": ["api", "v1", "ledger", "vouchers", "record-payment", ""]
                        }
                    }
                },
                {
                    "name": "8.5 Record Party Receipt (Collection against Commercial Sales Invoice)",
                    "event": [{
                        "listen": "test",
                        "script": {
                            "exec": [
                                "var jsonData = pm.response.json();",
                                "var v = jsonData.data || jsonData;",
                                "if (v && v.id) {",
                                "    pm.collectionVariables.set('voucher_id', v.id);",
                                "    console.log('Recorded Receipt Voucher ID set to: ' + v.id);",
                                "}"
                            ],
                            "type": "text/javascript"
                        }
                    }],
                    "request": {
                        "method": "POST",
                        "header": [
                            {"key": "Content-Type", "value": "application/json"},
                            {"key": "X-Company-ID", "value": "{{company_id}}"}
                        ],
                        "body": {
                            "mode": "raw",
                            "raw": json.dumps({
                                "party_id": 5,
                                "amount": "75000.00",
                                "doc_date": "13/10/2026",
                                "receipt_mode": "BANK",
                                "reference_no": "RTGS/20261013/9931",
                                "against_doc_type": "TAX_INVOICE",
                                "against_doc_number": "YSI-202610-8001",
                                "narration": "Receipt from Customer towards Commercial Yarn Invoice"
                            }, indent=4)
                        },
                        "url": {
                            "raw": "{{base_url}}/api/v1/ledger/vouchers/record-receipt/",
                            "host": ["{{base_url}}"],
                            "path": ["api", "v1", "ledger", "vouchers", "record-receipt", ""]
                        }
                    }
                },
                {
                    "name": "8.6 List All Vouchers (General Ledger)",
                    "request": {
                        "method": "GET",
                        "header": [{"key": "X-Company-ID", "value": "{{company_id}}"}],
                        "url": {
                            "raw": "{{base_url}}/api/v1/ledger/vouchers/?page=1&page_size=20",
                            "host": ["{{base_url}}"],
                            "path": ["api", "v1", "ledger", "vouchers", ""],
                            "query": [
                                {"key": "page", "value": "1"},
                                {"key": "page_size", "value": "20"}
                            ]
                        }
                    }
                },
                {
                    "name": "8.7 Reverse Financial Voucher (Atomic Contra)",
                    "request": {
                        "method": "POST",
                        "header": [
                            {"key": "Content-Type", "value": "application/json"},
                            {"key": "X-Company-ID", "value": "{{company_id}}"}
                        ],
                        "body": {
                            "mode": "raw",
                            "raw": json.dumps({
                                "reversal_date": "13/10/2026",
                                "reason": "Accidental duplicate entry"
                            }, indent=4)
                        },
                        "url": {
                            "raw": "{{base_url}}/api/v1/ledger/vouchers/{{voucher_id}}/reverse/",
                            "host": ["{{base_url}}"],
                            "path": ["api", "v1", "ledger", "vouchers", "{{voucher_id}}", "reverse", ""]
                        }
                    }
                }
            ]
        },
        {
            "name": "9. Production Process Stages & Routing (Process Wise)",
            "item": [
                {
                    "name": "9.1 List All Configured Process Stages (Knitting, Dyeing, Cutting, etc.)",
                    "request": {
                        "method": "GET",
                        "header": [{"key": "X-Company-ID", "value": "{{company_id}}"}],
                        "url": {
                            "raw": "{{base_url}}/api/v1/process/stages/",
                            "host": ["{{base_url}}"],
                            "path": ["api", "v1", "process", "stages", ""]
                        }
                    }
                },
                {
                    "name": "9.2 Seed Default Production Stages (Standard 6 Stages)",
                    "request": {
                        "method": "POST",
                        "header": [
                            {"key": "Content-Type", "value": "application/json"},
                            {"key": "X-Company-ID", "value": "{{company_id}}"}
                        ],
                        "url": {
                            "raw": "{{base_url}}/api/v1/process/stages/seed-defaults/",
                            "host": ["{{base_url}}"],
                            "path": ["api", "v1", "process", "stages", "seed-defaults", ""]
                        }
                    }
                },
                {
                    "name": "9.3 Create Custom Process Stage (e.g. Embroidery / Washing)",
                    "event": [{
                        "listen": "test",
                        "script": {
                            "exec": [
                                "var jsonData = pm.response.json();",
                                "var st = jsonData.data || jsonData;",
                                "if (st && st.id) {",
                                "    pm.collectionVariables.set('process_stage_id', st.id);",
                                "    console.log('Created Process Stage ID set to: ' + st.id);",
                                "}"
                            ],
                            "type": "text/javascript"
                        }
                    }],
                    "request": {
                        "method": "POST",
                        "header": [
                            {"key": "Content-Type", "value": "application/json"},
                            {"key": "X-Company-ID", "value": "{{company_id}}"}
                        ],
                        "body": {
                            "mode": "raw",
                            "raw": json.dumps({
                                "name": "Embroidery Floor",
                                "code": "EMBROIDERY",
                                "sequence_order": 45,
                                "input_from_stage": "CUT_PANELS",
                                "input_item_category": "CUT_PANELS",
                                "input_unit_type": "PIECES",
                                "output_to_stage": "PRINTED_PANELS",
                                "output_item_category": "PRINTED_PANELS",
                                "output_unit_type": "PIECES",
                                "standard_loss_percent": "0.50",
                                "standard_rate": "8.50",
                                "has_recipe": False,
                                "has_shrinkage": False,
                                "has_sizes": True,
                                "description": "Chest and sleeve multi-head embroidery"
                            }, indent=4)
                        },
                        "url": {
                            "raw": "{{base_url}}/api/v1/process/stages/",
                            "host": ["{{base_url}}"],
                            "path": ["api", "v1", "process", "stages", ""]
                        }
                    }
                },
                {
                    "name": "9.4 List All Process Programs (Production Job Orders)",
                    "request": {
                        "method": "GET",
                        "header": [{"key": "X-Company-ID", "value": "{{company_id}}"}],
                        "url": {
                            "raw": "{{base_url}}/api/v1/process/programs/?page=1&page_size=20",
                            "host": ["{{base_url}}"],
                            "path": ["api", "v1", "process", "programs", ""],
                            "query": [
                                {"key": "page", "value": "1"},
                                {"key": "page_size", "value": "20"}
                            ]
                        }
                    }
                },
                {
                    "name": "9.5 Filter Process Programs by Stage (e.g. KNITTING / DYEING)",
                    "request": {
                        "method": "GET",
                        "header": [{"key": "X-Company-ID", "value": "{{company_id}}"}],
                        "url": {
                            "raw": "{{base_url}}/api/v1/process/programs/?process_stage__code=KNITTING",
                            "host": ["{{base_url}}"],
                            "path": ["api", "v1", "process", "programs", ""],
                            "query": [
                                {"key": "process_stage__code", "value": "KNITTING", "description": "KNITTING, DYEING, CUTTING, STITCHING"}
                            ]
                        }
                    }
                },
                {
                    "name": "9.6 Create Knitting Process Program (Job Card with Yarn Input -> Fabric Output)",
                    "event": [{
                        "listen": "test",
                        "script": {
                            "exec": [
                                "var jsonData = pm.response.json();",
                                "var prg = jsonData.data || jsonData;",
                                "if (prg && prg.id) {",
                                "    pm.collectionVariables.set('process_program_id', prg.id);",
                                "    console.log('Created Process Program ID set to: ' + prg.id);",
                                "}"
                            ],
                            "type": "text/javascript"
                        }
                    }],
                    "request": {
                        "method": "POST",
                        "header": [
                            {"key": "Content-Type", "value": "application/json"},
                            {"key": "X-Company-ID", "value": "{{company_id}}"}
                        ],
                        "body": {
                            "mode": "raw",
                            "raw": json.dumps({
                                "process_stage": 1,
                                "job_worker": 3,
                                "source_warehouse": 1,
                                "dest_warehouse": 2,
                                "program_date": "13/10/2026",
                                "input_from": "YARN",
                                "input_item": "30s Combed 100% Cotton Grey Yarn",
                                "input_type": "BAG_WT_KG",
                                "input_units": 25,
                                "input_quantity": "1134.000",
                                "output_to": "GREY_FABRIC",
                                "output_item": "30s Single Jersey 160 GSM 24 Dia Fabric",
                                "output_type": "ROLL_WT_KG",
                                "expected_output_units": 55,
                                "expected_output_qty": "1111.320",
                                "planned_loss_percent": "2.00",
                                "dia": "24",
                                "gsm": 160,
                                "gauge": "24GG",
                                "loop_length": "2.70mm",
                                "rate_per_unit": "18.00",
                                "remarks": "Knitting order for Summer Crew Neck T-Shirt"
                            }, indent=4)
                        },
                        "url": {
                            "raw": "{{base_url}}/api/v1/process/programs/",
                            "host": ["{{base_url}}"],
                            "path": ["api", "v1", "process", "programs", ""]
                        }
                    }
                },
                {
                    "name": "9.7 Get Process Program Summary & Loss Analysis",
                    "request": {
                        "method": "GET",
                        "header": [{"key": "X-Company-ID", "value": "{{company_id}}"}],
                        "url": {
                            "raw": "{{base_url}}/api/v1/process/programs/{{process_program_id}}/summary/",
                            "host": ["{{base_url}}"],
                            "path": ["api", "v1", "process", "programs", "{{process_program_id}}", "summary", ""]
                        }
                    }
                },
                {
                    "name": "9.8 Authorize Process Program (Locks for Production)",
                    "request": {
                        "method": "POST",
                        "header": [
                            {"key": "Content-Type", "value": "application/json"},
                            {"key": "X-Company-ID", "value": "{{company_id}}"}
                        ],
                        "url": {
                            "raw": "{{base_url}}/api/v1/process/programs/{{process_program_id}}/authorize/",
                            "host": ["{{base_url}}"],
                            "path": ["api", "v1", "process", "programs", "{{process_program_id}}", "authorize", ""]
                        }
                    }
                },
                {
                    "name": "9.9 Unauthorize Process Program (Reopen Job Order)",
                    "request": {
                        "method": "POST",
                        "header": [
                            {"key": "Content-Type", "value": "application/json"},
                            {"key": "X-Company-ID", "value": "{{company_id}}"}
                        ],
                        "url": {
                            "raw": "{{base_url}}/api/v1/process/programs/{{process_program_id}}/unauthorize/",
                            "host": ["{{base_url}}"],
                            "path": ["api", "v1", "process", "programs", "{{process_program_id}}", "unauthorize", ""]
                        }
                    }
                },
                {
                    "name": "9.10 Cancel / Soft Delete Process Program",
                    "request": {
                        "method": "DELETE",
                        "header": [{"key": "X-Company-ID", "value": "{{company_id}}"}],
                        "url": {
                            "raw": "{{base_url}}/api/v1/process/programs/{{process_program_id}}/",
                            "host": ["{{base_url}}"],
                            "path": ["api", "v1", "process", "programs", "{{process_program_id}}", ""]
                        }
                    }
                }
            ]
        },
        {
            "name": "8. Commercial Pricing & Price Lists",
            "item": [
                {
                    "name": "8.1 List All Price Lists",
                    "request": {
                        "method": "GET",
                        "header": [{"key": "X-Company-ID", "value": "{{company_id}}"}],
                        "url": {
                            "raw": "{{base_url}}/api/v1/pricing/lists/",
                            "host": ["{{base_url}}"],
                            "path": ["api", "v1", "pricing", "lists", ""]
                        }
                    }
                },
                {
                    "name": "8.2 Seed Default Price Lists",
                    "request": {
                        "method": "POST",
                        "header": [
                            {"key": "Content-Type", "value": "application/json"},
                            {"key": "X-Company-ID", "value": "{{company_id}}"}
                        ],
                        "url": {
                            "raw": "{{base_url}}/api/v1/pricing/seed-defaults/",
                            "host": ["{{base_url}}"],
                            "path": ["api", "v1", "pricing", "seed-defaults", ""]
                        }
                    }
                },
                {
                    "name": "8.3 Get Price List Details (Header & Slabs)",
                    "request": {
                        "method": "GET",
                        "header": [{"key": "X-Company-ID", "value": "{{company_id}}"}],
                        "url": {
                            "raw": "{{base_url}}/api/v1/pricing/lists/{{price_list_id}}/",
                            "host": ["{{base_url}}"],
                            "path": ["api", "v1", "pricing", "lists", "{{price_list_id}}", ""]
                        }
                    }
                },
                {
                    "name": "8.4 Create Custom Purchase Price List",
                    "request": {
                        "method": "POST",
                        "header": [
                            {"key": "Content-Type", "value": "application/json"},
                            {"key": "X-Company-ID", "value": "{{company_id}}"}
                        ],
                        "body": {
                            "mode": "raw",
                            "raw": json.dumps({
                                "price_list_code": "PL-PUR-CUSTOM-2026",
                                "price_list_name": "Custom Yarn Procurement Rates",
                                "list_type": "PURCHASE",
                                "scope": "GENERAL",
                                "valid_from": "2026-10-01",
                                "valid_to": "2027-03-31",
                                "is_default": False,
                                "items": [
                                    {
                                        "item_type": "YARN",
                                        "yarn_count_id": 1,
                                        "yarn_type": "GREY",
                                        "min_quantity": "0.000",
                                        "max_quantity": "2000.000",
                                        "base_rate": "278.0000",
                                        "discount_percent": "2.00"
                                    }
                                ]
                            }, indent=4)
                        },
                        "url": {
                            "raw": "{{base_url}}/api/v1/pricing/lists/",
                            "host": ["{{base_url}}"],
                            "path": ["api", "v1", "pricing", "lists", ""]
                        }
                    }
                },
                {
                    "name": "8.5 Add Volume Slab Item Line to Price List",
                    "request": {
                        "method": "POST",
                        "header": [
                            {"key": "Content-Type", "value": "application/json"},
                            {"key": "X-Company-ID", "value": "{{company_id}}"}
                        ],
                        "body": {
                            "mode": "raw",
                            "raw": json.dumps({
                                "item_type": "YARN",
                                "yarn_count_id": 1,
                                "yarn_type": "GREY",
                                "min_quantity": "2001.000",
                                "max_quantity": "10000.000",
                                "base_rate": "270.0000",
                                "discount_percent": "3.50",
                                "remarks": "Volume order tier 2"
                            }, indent=4)
                        },
                        "url": {
                            "raw": "{{base_url}}/api/v1/pricing/lists/{{price_list_id}}/items/",
                            "host": ["{{base_url}}"],
                            "path": ["api", "v1", "pricing", "lists", "{{price_list_id}}", "items", ""]
                        }
                    }
                },
                {
                    "name": "8.6 Rate Resolution - Mill Party Contract Priority",
                    "request": {
                        "method": "POST",
                        "header": [
                            {"key": "Content-Type", "value": "application/json"},
                            {"key": "X-Company-ID", "value": "{{company_id}}"}
                        ],
                        "body": {
                            "mode": "raw",
                            "raw": json.dumps({
                                "context_type": "PURCHASE",
                                "party_id": 1,
                                "doc_date": "2026-10-15",
                                "yarn_count_id": 1,
                                "yarn_type": "GREY",
                                "quantity": "1500.000"
                            }, indent=4)
                        },
                        "url": {
                            "raw": "{{base_url}}/api/v1/pricing/resolve/",
                            "host": ["{{base_url}}"],
                            "path": ["api", "v1", "pricing", "resolve", ""]
                        }
                    }
                },
                {
                    "name": "8.7 Rate Resolution - General Base List Fallback",
                    "request": {
                        "method": "POST",
                        "header": [
                            {"key": "Content-Type", "value": "application/json"},
                            {"key": "X-Company-ID", "value": "{{company_id}}"}
                        ],
                        "body": {
                            "mode": "raw",
                            "raw": json.dumps({
                                "context_type": "PURCHASE",
                                "party_id": 2,
                                "doc_date": "2026-10-15",
                                "yarn_count_id": 1,
                                "yarn_type": "GREY",
                                "quantity": "800.000"
                            }, indent=4)
                        },
                        "url": {
                            "raw": "{{base_url}}/api/v1/pricing/resolve/",
                            "host": ["{{base_url}}"],
                            "path": ["api", "v1", "pricing", "resolve", ""]
                        }
                    }
                },
                {
                    "name": "8.8 Rate Resolution - Volume Slab Matching (>5000 Kg)",
                    "request": {
                        "method": "POST",
                        "header": [
                            {"key": "Content-Type", "value": "application/json"},
                            {"key": "X-Company-ID", "value": "{{company_id}}"}
                        ],
                        "body": {
                            "mode": "raw",
                            "raw": json.dumps({
                                "context_type": "PURCHASE",
                                "party_id": 2,
                                "doc_date": "2026-10-15",
                                "yarn_count_id": 1,
                                "yarn_type": "GREY",
                                "quantity": "6500.000"
                            }, indent=4)
                        },
                        "url": {
                            "raw": "{{base_url}}/api/v1/pricing/resolve/",
                            "host": ["{{base_url}}"],
                            "path": ["api", "v1", "pricing", "resolve", ""]
                        }
                    }
                },
                {
                    "name": "8.9 Rate Resolution - Commercial Sales Customer Contract",
                    "request": {
                        "method": "POST",
                        "header": [
                            {"key": "Content-Type", "value": "application/json"},
                            {"key": "X-Company-ID", "value": "{{company_id}}"}
                        ],
                        "body": {
                            "mode": "raw",
                            "raw": json.dumps({
                                "context_type": "SALES",
                                "party_id": 5,
                                "doc_date": "2026-10-15",
                                "yarn_count_id": 1,
                                "yarn_type": "GREY",
                                "quantity": "2500.000"
                            }, indent=4)
                        },
                        "url": {
                            "raw": "{{base_url}}/api/v1/pricing/resolve/",
                            "host": ["{{base_url}}"],
                            "path": ["api", "v1", "pricing", "resolve", ""]
                        }
                    }
                },
                {
                    "name": "8.10 List All Pricing Audit Logs (Company-wide)",
                    "request": {
                        "method": "GET",
                        "header": [{"key": "X-Company-ID", "value": "{{company_id}}"}],
                        "url": {
                            "raw": "{{base_url}}/api/v1/pricing/audit/",
                            "host": ["{{base_url}}"],
                            "path": ["api", "v1", "pricing", "audit", ""]
                        }
                    }
                },
                {
                    "name": "8.10a Record Rate Override Audit Log",
                    "request": {
                        "method": "POST",
                        "header": [
                            {"key": "Content-Type", "value": "application/json"},
                            {"key": "X-Company-ID", "value": "{{company_id}}"}
                        ],
                        "body": {
                            "mode": "raw",
                            "raw": json.dumps({
                                "document_type": "YARN_PO",
                                "document_id": 2,
                                "line_item_id": 1,
                                "resolved_price_list_id": 1,
                                "resolved_rule_id": 1,
                                "system_rate": "275.0000",
                                "actual_rate": "268.0000",
                                "override_reason": "Director approved special spot discount",
                                "approved_by": 1
                            }, indent=4)
                        },
                        "url": {
                            "raw": "{{base_url}}/api/v1/pricing/audit/",
                            "host": ["{{base_url}}"],
                            "path": ["api", "v1", "pricing", "audit", ""]
                        }
                    }
                },
                {
                    "name": "8.10b Pricing Audit Log by Document",
                    "request": {
                        "method": "GET",
                        "header": [{"key": "X-Company-ID", "value": "{{company_id}}"}],
                        "url": {
                            "raw": "{{base_url}}/api/v1/pricing/audit/?document_type=YARN_PO&document_id=1",
                            "host": ["{{base_url}}"],
                            "path": ["api", "v1", "pricing", "audit", ""],
                            "query": [
                                {"key": "document_type", "value": "YARN_PO"},
                                {"key": "document_id", "value": "1"}
                            ]
                        }
                    }
                },
                {
                    "name": "8.11 List Job Work Rules for Price List",
                    "request": {
                        "method": "GET",
                        "header": [{"key": "X-Company-ID", "value": "{{company_id}}"}],
                        "url": {
                            "raw": "{{base_url}}/api/v1/pricing/lists/{{price_list_id}}/job-rules/",
                            "host": ["{{base_url}}"],
                            "path": ["api", "v1", "pricing", "lists", "{{price_list_id}}", "job-rules", ""]
                        }
                    }
                },
                {
                    "name": "8.12 Add Job Work Conversion Rule",
                    "request": {
                        "method": "POST",
                        "header": [
                            {"key": "Content-Type", "value": "application/json"},
                            {"key": "X-Company-ID", "value": "{{company_id}}"}
                        ],
                        "body": {
                            "mode": "raw",
                            "raw": json.dumps({
                                "process_stage_id": 1,
                                "fabric_type_id": 1,
                                "machine_gauge": "24GG",
                                "dia_range": "24-34",
                                "job_rate": "18.5000",
                                "allowed_loss_percent": "2.50",
                                "lycra_surcharge": "4.0000",
                                "min_quantity": "0.000",
                                "max_quantity": "5000.000"
                            }, indent=4)
                        },
                        "url": {
                            "raw": "{{base_url}}/api/v1/pricing/lists/{{price_list_id}}/job-rules/",
                            "host": ["{{base_url}}"],
                            "path": ["api", "v1", "pricing", "lists", "{{price_list_id}}", "job-rules", ""]
                        }
                    }
                },
                {
                    "name": "8.13 Rate Resolution - Job Work Knitting with Lycra Plating",
                    "request": {
                        "method": "POST",
                        "header": [
                            {"key": "Content-Type", "value": "application/json"},
                            {"key": "X-Company-ID", "value": "{{company_id}}"}
                        ],
                        "body": {
                            "mode": "raw",
                            "raw": json.dumps({
                                "context_type": "JOB_WORK",
                                "process_stage_id": 1,
                                "fabric_type_id": 1,
                                "machine_gauge": "24GG",
                                "is_lycra_plated": True,
                                "quantity": "1500.000",
                                "doc_date": "2026-10-15"
                            }, indent=4)
                        },
                        "url": {
                            "raw": "{{base_url}}/api/v1/pricing/resolve/",
                            "host": ["{{base_url}}"],
                            "path": ["api", "v1", "pricing", "resolve", ""]
                        }
                    }
                },
                {
                    "name": "8.14 Rate Resolution - Job Work Dyeing by Shade Depth (Dark + Bio-wash)",
                    "request": {
                        "method": "POST",
                        "header": [
                            {"key": "Content-Type", "value": "application/json"},
                            {"key": "X-Company-ID", "value": "{{company_id}}"}
                        ],
                        "body": {
                            "mode": "raw",
                            "raw": json.dumps({
                                "context_type": "JOB_WORK",
                                "process_stage_id": 2,
                                "shade_category": "DARK",
                                "special_finish_requested": True,
                                "quantity": "2000.000",
                                "doc_date": "2026-10-15"
                            }, indent=4)
                        },
                        "url": {
                            "raw": "{{base_url}}/api/v1/pricing/resolve/",
                            "host": ["{{base_url}}"],
                            "path": ["api", "v1", "pricing", "resolve", ""]
                        }
                    }
                },
                {
                    "name": "8.15 Rate Resolution - Job Work Party Knitter Contract Priority",
                    "request": {
                        "method": "POST",
                        "header": [
                            {"key": "Content-Type", "value": "application/json"},
                            {"key": "X-Company-ID", "value": "{{company_id}}"}
                        ],
                        "body": {
                            "mode": "raw",
                            "raw": json.dumps({
                                "context_type": "JOB_WORK",
                                "party_id": 3,
                                "process_stage_id": 1,
                                "fabric_type_id": 1,
                                "doc_date": "2026-10-15"
                            }, indent=4)
                        },
                        "url": {
                            "raw": "{{base_url}}/api/v1/pricing/resolve/",
                            "host": ["{{base_url}}"],
                            "path": ["api", "v1", "pricing", "resolve", ""]
                        }
                    }
                }
            ]
        }
    ]
}

os.makedirs("d:/Codebase/Garments/docs/postman", exist_ok=True)
os.makedirs("d:/Codebase/Garments/postman", exist_ok=True)

target_docs = "d:/Codebase/Garments/docs/postman/Garments_ERP_Yarn_API.postman_collection.json"
target_root = "d:/Codebase/Garments/postman/Garments_ERP_Yarn_API.postman_collection.json"
target_backend = "d:/Codebase/Garments/backend/Garments_ERP_Postman_Collection.json"

with open(target_docs, "w", encoding="utf-8") as f:
    json.dump(collection, f, indent=4)

with open(target_root, "w", encoding="utf-8") as f:
    json.dump(collection, f, indent=4)

with open(target_backend, "w", encoding="utf-8") as f:
    json.dump(collection, f, indent=4)

print(f"Generated: {target_docs}")
print(f"Generated: {target_root}")
print(f"Generated: {target_backend}")

