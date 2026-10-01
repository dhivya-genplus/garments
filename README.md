# Garments ERP & CRM

Enterprise Garments Manufacturing ERP and CRM Backend Monolith built with Django and Django REST Framework.

## Architecture & Features
- **Layered Architecture:** Views -> Services -> Repositories -> Models
- **Authentication & RBAC:** Multi-tenant company isolation, dynamic roles, permissions, JWT auth
- **Masters:** Customer master, vendor master, item & bill of materials (BOM), fabric, color, size, etc.
- **REST APIs:** DRF endpoints with standardized response structure
