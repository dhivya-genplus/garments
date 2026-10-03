---
name: db-schema-design
description: How to design tm_/tx_/tl_/tc_ tables without foreign keys, with company scope, soft delete and audit columns, for MySQL/MariaDB and PostgreSQL. Use when creating or changing any table or model.
---
# DB schema design

## Standard columns (every tm_/tx_/tl_ table)
| Column | Type | Note |
|---|---|---|
| id | BIGINT auto | PK |
| company_id | BIGINT | index; server-injected |
| record_status | CHAR(1) | A/I/D, default A |
| created_by, updated_by | BIGINT | user id |
| created_at, updated_at | DATETIME (UTC) / TIMESTAMPTZ | set by service |

Transaction tables add: branch_id, fy_id, doc_series_id, doc_no VARCHAR(30), doc_date DATE,
status CHAR(1) D/P/C, posted_at, posted_by, cancelled_at, cancelled_by, cancel_reason, remarks.

## Django model pattern (no FK)
```python
class Customer(BaseMaster):            # BaseMaster defines the standard columns
    code = models.CharField(max_length=30)
    name = models.CharField(max_length=150)
    state_id = models.BigIntegerField(null=True, db_index=True)   # reference, not FK
    credit_limit = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    class Meta:
        db_table = "tm_customer"
        constraints = [models.UniqueConstraint(fields=["company_id", "code"], name="uq_tm_customer_code")]
        indexes = [models.Index(fields=["company_id", "record_status"])]
```
Resolve references in selectors: `State.objects.filter(id__in=[...])` and map in Python, or a
read-model view for reports.

## Node (Prisma) pattern
Define `model TmCustomer { ... @@map("tm_customer") }` with `stateId BigInt?` and NO `@relation`.
Enforce integrity in services. Use `Decimal` types with `@db.Decimal(18,2)`.

## Checklist before approving a schema
- [ ] prefixes and singular snake_case names
- [ ] no FK / relation fields; every `_id` indexed
- [ ] standard columns present; tx_ extras present
- [ ] unique (company_id, code) on masters; (company_id, doc_series_id, doc_no) on tx_
- [ ] decimals not floats; UTC timestamps; DATE for business dates
- [ ] migration is additive; renames done as add + copy + drop in separate releases
