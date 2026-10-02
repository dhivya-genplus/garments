from __future__ import annotations
from decimal import Decimal
from typing import Dict, Any, List, Optional
from django.db import transaction
from django.utils import timezone
from core.base_services import BaseService
from core.exceptions import ValidationError, ResourceNotFound, ConflictError
from core.constants import YarnCategory
from apps.purchase.models import parent_po_table, child_po_table, yarn_po_delivery_table
from apps.purchase.repositories import YarnPORepository


class YarnPOService(BaseService):
    """
    Business logic and workflow orchestration for Yarn Purchase Orders.
    Enforces authorization locks, delivery allocation constraints,
    Grey vs. Dyed yarn rules, and atomic multi-line/delivery creation.
    """

    @staticmethod
    def generate_po_number(company_id: int) -> str:
        """Generate formatted PO number: YPO-YYYYMM-XXXX"""
        now = timezone.now()
        prefix = f"YPO-{now.strftime('%Y%m')}-"
        last_po = (
            parent_po_table.objects
            .filter(company_id=company_id, po_number__startswith=prefix)
            .order_by("-po_number")
            .first()
        )
        if last_po:
            try:
                seq = int(last_po.po_number.split("-")[-1]) + 1
            except (ValueError, IndexError):
                seq = 1
        else:
            seq = 1
        return f"{prefix}{seq:04d}"

    @classmethod
    @transaction.atomic
    def create_yarn_po(
        cls,
        company_id: int,
        data: Dict[str, Any],
        line_items_data: Optional[List[Dict[str, Any]]] = None,
        deliveries_data: Optional[List[Dict[str, Any]]] = None,
        user=None
    ) -> parent_po_table:
        # 1. Validate Yarn Type (Grey vs Dyed Yarn condition)
        yarn_type = data.get("yarn_type", YarnCategory.GREY)
        if yarn_type not in [YarnCategory.GREY, YarnCategory.DYED]:
            raise ValidationError(f"Invalid yarn type '{yarn_type}'. Must be '{YarnCategory.GREY}' (Grey Yarn) or '{YarnCategory.DYED}' (Dyed Yarn).")

        color_shade_id = data.get("color_shade_id") or data.get("color_shade")
        if yarn_type == YarnCategory.DYED and not color_shade_id:
            raise ValidationError("Color shade is required for Dyed Yarn Purchase Orders.")

        # 2. Standard bag weight defaults
        per_bag = Decimal(str(data.get("per_bag", "45.360")))
        if per_bag <= 0:
            raise ValidationError("Per bag weight must be positive (typically 45.360 or 50.000 Kg/bag).")

        # 3. Generate PO Number if not provided
        po_number = data.get("po_number") or cls.generate_po_number(company_id)
        if parent_po_table.objects.filter(company_id=company_id, po_number=po_number, status=1).exists():
            raise ConflictError(f"Purchase Order #{po_number} already exists.")

        # 4. Compute quantities and values
        bag = int(data.get("bag", 0))
        rate = Decimal(str(data.get("rate", "0.00")))
        discount = Decimal(str(data.get("discount", "0.00")))
        net_rate = rate - discount
        quantity = Decimal(str(bag)) * per_bag
        amount = quantity * net_rate

        # 5. Delivery Allocation Constraint
        if deliveries_data:
            total_delivery_bags = sum(int(d.get("bag", 0)) for d in deliveries_data)
            if total_delivery_bags > bag:
                raise ValidationError(
                    f"Total scheduled delivery bags ({total_delivery_bags}) cannot exceed total PO bags ({bag})."
                )

        # 6. Create Parent PO Header
        po_data = {
            "po_number": po_number,
            "po_date": data.get("po_date") or timezone.now().date(),
            "yarn_type": yarn_type,
            "color_shade_id": color_shade_id if yarn_type == YarnCategory.DYED else None,
            "name": data.get("name"),
            "company_id": company_id,
            "cfyear_id": data.get("cfyear_id") or data.get("cfyear"),
            "party_id": data.get("party_id") or data.get("party"),
            "mill_id": data.get("mill_id") or data.get("mill"),
            "yarn_count_id": data.get("yarn_count_id") or data.get("yarn_count"),
            "bag": bag,
            "per_bag": per_bag,
            "quantity": quantity,
            "gross_quantity": data.get("gross_quantity") or quantity,
            "rate": rate,
            "discount": discount,
            "net_rate": net_rate,
            "amount": amount,
            "remarks": data.get("remarks"),
            "is_delivery": 1 if deliveries_data else data.get("is_delivery", 0),
            "is_complete": 0,
            "is_authorized": 0,
            "is_active": 1,
            "status": 1,
            "created_by": user,
            "updated_by": user,
        }
        po = parent_po_table.objects.create(**po_data)

        # 7. Create Line Items (Child PO)
        if line_items_data:
            line_objs = []
            for item in line_items_data:
                item_yarn_type = item.get("yarn_type", yarn_type)
                item_shade = item.get("color_shade_id") or item.get("color_shade")
                if item_yarn_type == YarnCategory.DYED and not item_shade:
                    item_shade = color_shade_id

                item_bag = int(item.get("bag", 0))
                item_per_bag = Decimal(str(item.get("per_bag", per_bag)))
                item_qty = Decimal(str(item_bag)) * item_per_bag
                act_rate = Decimal(str(item.get("actual_rate", rate)))
                disc = Decimal(str(item.get("discount", "0.00")))
                eff_rate = act_rate - disc
                line_amt = item_qty * eff_rate

                line_objs.append(
                    child_po_table(
                        tm_po=po,
                        yarn_type=item_yarn_type,
                        yarn_count_id=item.get("yarn_count_id") or item.get("yarn_count") or po.yarn_count_id,
                        color_shade_id=item_shade,
                        bag=item_bag,
                        per_bag=item_per_bag,
                        quantity=item_qty,
                        gross_wt=item.get("gross_wt") or item_qty,
                        actual_rate=act_rate,
                        discount=disc,
                        rate=eff_rate,
                        amount=line_amt,
                        remaining_bag=item_bag,
                        remaining_quantity=item_qty,
                        remaining_amount=line_amt,
                        is_active=1,
                        status=1,
                    )
                )
            child_po_table.objects.bulk_create(line_objs)

        # 8. Create Split Delivery Schedules
        if deliveries_data:
            delivery_objs = []
            for d in deliveries_data:
                d_bag = int(d.get("bag", 0))
                d_bag_wt = Decimal(str(d.get("bag_wt", per_bag)))
                d_qty = Decimal(str(d_bag)) * d_bag_wt

                delivery_objs.append(
                    yarn_po_delivery_table(
                        tm_po=po,
                        yarn_count_id=d.get("yarn_count_id") or d.get("yarn_count") or po.yarn_count_id,
                        party_id=d.get("party_id") or d.get("party"),
                        delivery_date=d.get("delivery_date"),
                        bag=d_bag,
                        bag_wt=d_bag_wt,
                        quantity=d_qty,
                        company_id=company_id,
                        cfyear_id=po.cfyear_id,
                        is_active=1,
                        status=1,
                    )
                )
            yarn_po_delivery_table.objects.bulk_create(delivery_objs)

        return po

    @classmethod
    @transaction.atomic
    def update_yarn_po(
        cls,
        po_id: int,
        company_id: int,
        data: Dict[str, Any],
        line_items_data: Optional[List[Dict[str, Any]]] = None,
        deliveries_data: Optional[List[Dict[str, Any]]] = None,
        user=None
    ) -> parent_po_table:
        po = YarnPORepository.get_by_id(po_id)
        if not po or po.company_id != company_id:
            raise ResourceNotFound(f"Purchase Order with ID {po_id} not found.")

        # Authorization Lock Rule
        if po.is_authorized == 1:
            raise ValidationError(
                f"Purchase Order #{po.po_number} is Authorized and locked. It must be un-authorized before editing."
            )

        # Update Yarn Type and Color Shade
        yarn_type = data.get("yarn_type", po.yarn_type)
        if yarn_type not in [YarnCategory.GREY, YarnCategory.DYED]:
            raise ValidationError("Invalid yarn type. Must be GREY or DYED.")
        po.yarn_type = yarn_type

        color_shade_id = data.get("color_shade_id") or (po.color_shade_id if yarn_type == YarnCategory.DYED else None)
        if yarn_type == YarnCategory.DYED and not color_shade_id:
            raise ValidationError("Color shade is required for Dyed Yarn Purchase Orders.")
        po.color_shade_id = color_shade_id

        # Update standard fields
        for field in ["po_date", "name", "remarks", "party_id", "mill_id", "yarn_count_id", "cfyear_id"]:
            if field in data and data[field] is not None:
                setattr(po, field, data[field])

        if "bag" in data:
            po.bag = int(data["bag"])
        if "per_bag" in data:
            po.per_bag = Decimal(str(data["per_bag"]))
        if "rate" in data:
            po.rate = Decimal(str(data["rate"]))
        if "discount" in data:
            po.discount = Decimal(str(data["discount"]))

        po.clean()
        po.updated_by = user
        po.save()

        # Update line items if provided
        if line_items_data is not None:
            child_po_table.objects.filter(tm_po=po).delete()
            line_objs = [
                child_po_table(
                    tm_po=po,
                    yarn_type=item.get("yarn_type", po.yarn_type),
                    yarn_count_id=item.get("yarn_count_id") or po.yarn_count_id,
                    color_shade_id=item.get("color_shade_id") or po.color_shade_id,
                    bag=int(item.get("bag", 0)),
                    per_bag=Decimal(str(item.get("per_bag", po.per_bag))),
                    actual_rate=Decimal(str(item.get("actual_rate", po.rate))),
                    discount=Decimal(str(item.get("discount", "0.00"))),
                    is_active=1,
                    status=1,
                )
                for item in line_items_data
            ]
            child_po_table.objects.bulk_create(line_objs)

        # Update deliveries if provided
        if deliveries_data is not None:
            total_delivery_bags = sum(int(d.get("bag", 0)) for d in deliveries_data)
            if total_delivery_bags > po.bag:
                raise ValidationError(
                    f"Total scheduled delivery bags ({total_delivery_bags}) exceeds PO bags ({po.bag})."
                )

            yarn_po_delivery_table.objects.filter(tm_po=po).delete()
            delivery_objs = [
                yarn_po_delivery_table(
                    tm_po=po,
                    yarn_count_id=d.get("yarn_count_id") or po.yarn_count_id,
                    party_id=d.get("party_id") or d.get("party"),
                    delivery_date=d.get("delivery_date"),
                    bag=int(d.get("bag", 0)),
                    bag_wt=Decimal(str(d.get("bag_wt", po.per_bag))),
                    company_id=company_id,
                    cfyear_id=po.cfyear_id,
                    is_active=1,
                    status=1,
                )
                for d in deliveries_data
            ]
            yarn_po_delivery_table.objects.bulk_create(delivery_objs)
            po.is_delivery = 1 if delivery_objs else 0
            po.save(update_fields=["is_delivery"])

        return po

    @classmethod
    @transaction.atomic
    def authorize_yarn_po(cls, po_id: int, company_id: int, user) -> parent_po_table:
        """Lock and authorize the Purchase Order."""
        po = YarnPORepository.get_by_id(po_id)
        if not po or po.company_id != company_id:
            raise ResourceNotFound(f"Purchase Order with ID {po_id} not found.")

        if po.is_authorized == 1:
            raise ValidationError(f"Purchase Order #{po.po_number} is already authorized.")

        po.is_authorized = 1
        po.authorized_by = user
        po.authorized_on = timezone.now()
        po.updated_by = user
        po.save(update_fields=["is_authorized", "authorized_by", "authorized_on", "updated_by", "updated_on"])
        return po

    @classmethod
    @transaction.atomic
    def unauthorize_yarn_po(cls, po_id: int, company_id: int, user) -> parent_po_table:
        """Unlock/Re-open the Purchase Order for edits."""
        po = YarnPORepository.get_by_id(po_id)
        if not po or po.company_id != company_id:
            raise ResourceNotFound(f"Purchase Order with ID {po_id} not found.")

        if po.is_complete == 1:
            raise ValidationError("Completed/Fulfilled purchase orders cannot be un-authorized.")

        po.is_authorized = 0
        po.authorized_by = None
        po.authorized_on = None
        po.updated_by = user
        po.save(update_fields=["is_authorized", "authorized_by", "authorized_on", "updated_by", "updated_on"])
        return po

    @classmethod
    def check_and_update_completion(cls, po_id: int, tolerance_threshold: Decimal = Decimal("10.000")) -> bool:
        """
        Auto-completion check:
        Transitions is_complete = 1 when total received inward weight >= PO Quantity - tolerance.
        """
        po = parent_po_table.objects.get(id=po_id)
        # Check total inward received weight from child line items remaining quantity
        total_remaining = sum(item.remaining_quantity for item in po.line_items.filter(status=1))
        if total_remaining <= tolerance_threshold:
            po.is_complete = 1
            po.save(update_fields=["is_complete", "updated_on"])
            return True
        return False
