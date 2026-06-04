import re

class LocalChatService:
    @staticmethod
    def generate_reply(intent: str, analytics_summary: dict, user_message: str) -> str:
        # Extract core metrics
        sales = analytics_summary.get("total_sales", 0.0)
        settlement = analytics_summary.get("total_settlement", 0.0)
        profit = analytics_summary.get("total_profit", 0.0)
        margin = analytics_summary.get("profit_margin", 0.0)
        orders = analytics_summary.get("total_orders", 0)
        ret_rate = analytics_summary.get("return_rate", 0.0)
        rto = analytics_summary.get("rto_rate", 0.0)
        low_stock = analytics_summary.get("low_stock_count", 0)
        dead_stock = analytics_summary.get("dead_inventory_count", 0)
        mismatch = analytics_summary.get("settlement_mismatch_count", 0)
        top_products = analytics_summary.get("top_products", [])
        platforms = analytics_summary.get("platform_performance", [])
        dead_examples = analytics_summary.get("dead_inventory_examples", [])
        alerts = analytics_summary.get("alerts", [])

        if intent == "profit_analysis":
            reply = (
                f"Profit Analysis Report:\n"
                f"• Total Revenue / Sales: ₹{sales:,.2f}\n"
                f"• Settled Amount: ₹{settlement:,.2f}\n"
                f"• Net Profit: ₹{profit:,.2f}\n"
                f"• Average Profit Margin: {margin:.2f}%\n\n"
            )
            if margin < 15:
                reply += "Your profit margin is currently below 15%. Consider analyzing product cost structures or increasing prices to optimize profitability."
            else:
                reply += "Your profit margins look healthy. Keep monitoring operating costs and return rates to maintain this trend."
            return reply

        elif intent == "sales_analysis":
            platform_str = ""
            if platforms:
                platform_str = "\nSales by Marketplace:\n" + "\n".join(
                    [f"• {p['platform']}: {p['orders']} orders, Sales: ₹{p['sales']:,.2f}" for p in platforms]
                )
            reply = (
                f"Sales Performance Overview:\n"
                f"• Total Orders: {orders}\n"
                f"• Total Gross Revenue: ₹{sales:,.2f}"
                f"{platform_str}"
            )
            return reply

        elif intent == "inventory_analysis":
            reply = (
                f"Inventory Status:\n"
                f"• Low Stock Items (< 10 units): {low_stock}\n"
                f"• Slow-Moving / Dead Inventory Items: {dead_stock}\n\n"
            )
            if low_stock > 0:
                reply += f"Urgent: You have {low_stock} product variants running low on stock. Please restock soon to avoid stockouts.\n"
            if dead_stock > 0:
                reply += f"Consider running promotion campaigns or discounts to liquidate the {dead_stock} stale items."
            if low_stock == 0 and dead_stock == 0:
                reply += "Your inventory levels are stable. No immediate restocking actions are required."
            return reply

        elif intent == "top_products":
            if not top_products:
                return "No top-performing product data is available at the moment."
            
            product_list = []
            for i, p in enumerate(top_products, 1):
                product_list.append(
                    f"{i}. SKU: {p['sku']} | {p['product_name']}\n"
                    f"   Sales: ₹{p['sales']:,.2f} | Profit: ₹{p['profit']:,.2f} | Orders: {p['order_count']} | Stock: {p['stock']}"
                )
            
            reply = "Top Performing Products:\n" + "\n".join(product_list)
            return reply

        elif intent == "dead_stock":
            reply = f"Stale / Dead Stock Summary:\n• Total Dead Stock Count: {dead_stock}\n"
            if dead_examples:
                reply += "\nSlow-Moving Examples:\n"
                for i, item in enumerate(dead_examples, 1):
                    reply += f"• SKU: {item['variant_sku']} - {item['product_name']} (Stock: {item['variant_stock']}, Last Sold: {item['last_sold_date'] or 'Never'})\n"
                reply += "\nWe recommend bundling these items or offering markdown discounts to free up warehouse space."
            else:
                reply += "No dead stock variants identified in the last 90 days."
            return reply

        elif intent == "pricing_recommendation":
            reply = (
                f"Pricing Insights & Optimization:\n"
                f"• Current average profit margin is {margin:.2f}%\n"
                f"• Current return rate is {ret_rate:.2f}%\n\n"
                f"To boost profits, focus on pricing adjustments:\n"
            )
            low_margin_products = [p for p in top_products if p['profit'] < p['sales'] * 0.1]
            if low_margin_products:
                reply += "• Increase prices slightly on low-margin fast-moving items, such as:\n"
                for p in low_margin_products[:3]:
                    reply += f"  - SKU: {p['sku']} (Current profit is low relative to sales volume)\n"
            else:
                reply += "• Your top products have solid margins. Consider dynamic pricing on high-demand items to test price elasticity.\n"
            
            if ret_rate > 10:
                reply += "• High return rates are eating into your margins. Review listing descriptions and product quality parameters."
            return reply

        elif intent == "rto_analysis":
            reply = (
                f"Return and RTO (Return to Origin) Report:\n"
                f"• Overall Return Rate: {ret_rate:.2f}%\n"
                f"• RTO Rate: {rto:.2f}%\n\n"
            )
            if ret_rate > 8:
                reply += "Warning: High customer return rate detected! This reduces your profit margins due to double shipping charges. Inspect quality control or product description accuracy.\n"
            if rto > 5:
                reply += "Warning: High RTO rate! Consider verifying customer addresses before dispatch or minimizing COD orders in high-risk locations."
            if ret_rate <= 8 and rto <= 5:
                reply += "Return and RTO rates are well within healthy operational thresholds."
            return reply

        elif intent == "settlement_analysis":
            reply = (
                f"Settlement & Payout Reconciliation:\n"
                f"• Total Ordered Amount: ₹{sales:,.2f}\n"
                f"• Settled/Disbursed Amount: ₹{settlement:,.2f}\n"
                f"• Mismatched Settlement Records: {mismatch}\n\n"
            )
            if mismatch > 0:
                reply += f"Alert: We detected {mismatch} orders with a mismatch between selling price and payout from the marketplace platform. Please download the settlement mismatch sheet to dispute these claims."
            else:
                reply += "All order settlements match the marketplace payouts perfectly."
            return reply
        
        
        elif intent == "marketplace_growth":
            if not platforms:
                return "No marketplace growth data is currently available."
            
            reply = "Marketplace Growth Performance Matrix:\n"
            total_orders = sum(p['orders'] for p in platforms)
            for p in platforms:
                share = (p['orders'] / total_orders * 100) if total_orders else 0
                reply += (
                    f"• {p['platform']}:\n"
                    f"  Sales: ₹{p['sales']:,.2f} | Profit: ₹{p['profit']:,.2f} | Orders: {p['orders']} ({share:.1f}% share)\n"
                )
            
            # Growth recommendations
            best_platform = max(platforms, key=lambda x: x['sales']) if platforms else None
            if best_platform:
                reply += f"\nRecommendation: {best_platform['platform']} is your leading channel. Double down on listing optimizations and advertising spend there."
            return reply

        # Fallback / General help
        overview = (
            f"Hello! I am your personal local E-commerce Profit Analyst chatbot.\n\n"
            f"Current Business Health Overview:\n"
            f"• Revenue: ₹{sales:,.2f} | Net Profit: ₹{profit:,.2f} ({margin:.2f}% margin)\n"
            f"• Total Orders: {orders}\n"
            f"• Inventory Alerts: {low_stock} low stock, {dead_stock} dead stock items\n"
            f"• Returns: Return Rate {ret_rate:.2f}%, RTO Rate {rto:.2f}%\n"
            f"• Payout Reconciliation: {mismatch} mismatched payout records\n\n"
            f"Ask me about: profit margin, sales trends, inventory, top products, dead stock, pricing recommendations, return rate, or settlement mismatches."
        )
        return overview
