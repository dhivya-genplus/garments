from __future__ import annotations
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional, Dict, Any


class TaxEngine:
    """
    Standard Tax Calculation Engine for GST (Goods & Services Tax).
    
    Determines whether a transaction is Intrastate (CGST + SGST) or Interstate (IGST)
    by comparing place of supply / party state against company registration state.
    """

    @staticmethod
    def compute(
        subtotal: Decimal,
        tax=None,
        tax_percent: Optional[Decimal] = None,
        company=None,
        party=None,
        place_of_supply: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Compute GST breakdown.
        
        Args:
            subtotal: Taxable base amount
            tax: TaxMaster model instance (optional)
            tax_percent: Explicit total tax percent if TaxMaster not provided (optional)
            company: Company model instance (for company.state)
            party: PartyMaster model instance (for party.state)
            place_of_supply: State string override for delivery/billing location
        
        Returns:
            Dictionary containing tax amounts, rates, interstate flag, and total amount.
        """
        subtotal = Decimal(str(subtotal or "0.000"))

        if tax:
            total_tax_pct = Decimal(str(tax.tax_percent or "0.00"))
            cgst_pct = Decimal(str(tax.cgst_percent or "0.00"))
            sgst_pct = Decimal(str(tax.sgst_percent or "0.00"))
            igst_pct = Decimal(str(tax.igst_percent or "0.00"))
        elif tax_percent is not None:
            total_tax_pct = Decimal(str(tax_percent or "0.00"))
            cgst_pct = (total_tax_pct / Decimal("2.00")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            sgst_pct = (total_tax_pct / Decimal("2.00")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            igst_pct = total_tax_pct
        else:
            total_tax_pct = Decimal("0.00")
            cgst_pct = Decimal("0.00")
            sgst_pct = Decimal("0.00")
            igst_pct = Decimal("0.00")

        # Determine place of supply vs company state
        company_state = (getattr(company, "state", None) or "").strip().lower()
        party_state = (place_of_supply or getattr(party, "state", None) or "").strip().lower()

        # If both states are known and different -> Interstate (IGST)
        # If either state is empty or they match -> Intrastate (CGST + SGST)
        if company_state and party_state and company_state != party_state:
            is_interstate = True
            cgst_rate = Decimal("0.00")
            sgst_rate = Decimal("0.00")
            igst_rate = igst_pct

            cgst_amount = Decimal("0.000")
            sgst_amount = Decimal("0.000")
            igst_amount = (subtotal * (igst_rate / Decimal("100.00"))).quantize(Decimal("0.001"), rounding=ROUND_HALF_UP)
        else:
            is_interstate = False
            cgst_rate = cgst_pct
            sgst_rate = sgst_pct
            igst_rate = Decimal("0.00")

            cgst_amount = (subtotal * (cgst_rate / Decimal("100.00"))).quantize(Decimal("0.001"), rounding=ROUND_HALF_UP)
            sgst_amount = (subtotal * (sgst_rate / Decimal("100.00"))).quantize(Decimal("0.001"), rounding=ROUND_HALF_UP)
            igst_amount = Decimal("0.000")

        tax_amount = cgst_amount + sgst_amount + igst_amount
        total_amount = subtotal + tax_amount

        return {
            "subtotal": subtotal,
            "tax": tax,
            "tax_percent": total_tax_pct,
            "tax_amount": tax_amount,
            "cgst_percent": cgst_rate,
            "cgst_amount": cgst_amount,
            "sgst_percent": sgst_rate,
            "sgst_amount": sgst_amount,
            "igst_percent": igst_rate,
            "igst_amount": igst_amount,
            "is_interstate": is_interstate,
            "total_amount": total_amount,
        }
