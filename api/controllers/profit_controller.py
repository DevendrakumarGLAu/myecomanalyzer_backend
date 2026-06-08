from decimal import Decimal
from profit.models import OrderProfit
from payments.models import OrderSettlement


class ProfitCalculationService:

    @staticmethod
    def calculate_order_profit(order, settlement):

        variant = order.variant

        # --------------------------------
        # BASIC VALUES
        # --------------------------------

        quantity = order.quantity or 1

        selling_price = Decimal(str(order.selling_price or 0))

        gross_revenue = Decimal(str(
            settlement.total_sale_amount or 0
        ))

        # --------------------------------
        # PRODUCT COSTS
        # --------------------------------

        product_cost = Decimal(str(
            variant.cost_price or 0
        )) * quantity

        shipping_cost = Decimal(str(
            settlement.shipping_fee or 0
        ))

        rto_cost = Decimal(str(
            variant.rto_cost or 0
        ))

        packaging_cost = Decimal("10")  # optional default

        # --------------------------------
        # MARKETPLACE FEES
        # --------------------------------

        commission_fee = Decimal(str(
            settlement.commission_fee or 0
        ))

        fixed_fee = Decimal(str(
            settlement.fixed_fee or 0
        ))

        warehousing_fee = Decimal(str(
            settlement.warehousing_fee or 0
        ))

        return_shipping_charge = Decimal(str(
            settlement.return_shipping_charge or 0
        ))

        # --------------------------------
        # RETURNS / CLAIMS
        # --------------------------------

        total_return_amount = Decimal(str(
            settlement.total_return_amount or 0
        ))

        claim_amount = Decimal(str(
            settlement.claim_amount or 0
        ))

        # --------------------------------
        # TOTAL COST
        # --------------------------------

        total_cost = (
            product_cost
            + shipping_cost
            + rto_cost
            + packaging_cost
        )

        # --------------------------------
        # TOTAL DEDUCTIONS
        # --------------------------------

        total_deductions = (
            commission_fee
            + fixed_fee
            + warehousing_fee
            + return_shipping_charge
            + abs(total_return_amount)
        )

        # --------------------------------
        # NET PROFIT
        # --------------------------------

        net_profit = (
            gross_revenue
            - total_cost
            - total_deductions
            + claim_amount
        )

        # --------------------------------
        # PROFIT %
        # --------------------------------

        margin = Decimal("0")

        if gross_revenue > 0:
            margin = (
                net_profit / gross_revenue
            ) * Decimal("100")

        roi = Decimal("0")

        if total_cost > 0:
            roi = (
                net_profit / total_cost
            ) * Decimal("100")

        # --------------------------------
        # SAVE SNAPSHOT
        # --------------------------------

        OrderProfit.objects.update_or_create(

            order=order,

            defaults={

                "settlement": settlement,

                "product_name": order.product.name,
                "sku": variant.sku,

                "quantity": quantity,

                "selling_price": selling_price,

                "gross_revenue": gross_revenue,

                "product_cost": product_cost,

                "shipping_cost": shipping_cost,

                "rto_cost": rto_cost,

                "packaging_cost": packaging_cost,

                "commission_fee": commission_fee,

                "fixed_fee": fixed_fee,

                "warehousing_fee": warehousing_fee,

                "return_shipping_charge": return_shipping_charge,

                "total_return_amount": total_return_amount,

                "claim_amount": claim_amount,

                "total_cost": total_cost,

                "total_deductions": total_deductions,

                "net_profit": net_profit,

                "profit_margin_percent": margin,

                "roi_percent": roi,

                "is_loss": net_profit < 0,
            }
        )