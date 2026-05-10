from django.db.models import Sum, Q
from datetime import timedelta
from django.utils import timezone
from django.contrib.auth.models import User

from notifications.models import Notification
from orders.models import Order
from products.models import Product, ProductVariant
from platforms.models import Platform


class NotificationController:

    @staticmethod
    def generate_notifications(current_user=None, platform_code: str = None):
        """Generate notifications for the user based on various business rules"""
        try:
            if current_user is None:
                raise ValueError("current_user must be provided")

            # Platform filter
            platform_filter = {}
            if platform_code:
                try:
                    platform = Platform.objects.get(code__iexact=platform_code)
                    platform_filter["platform_id"] = platform.id
                except Platform.DoesNotExist:
                    return

            # Clear old notifications (keep only last 30 days)
            thirty_days_ago = timezone.now() - timedelta(days=30)
            Notification.objects.filter(
                user=current_user,
                created_at__lt=thirty_days_ago
            ).delete()

            # 1. Low stock products (stock < 10)
            low_stock_variants = ProductVariant.objects.filter(
                product__owner=current_user,
                stock__lt=10,
                stock__gt=0
            ).select_related('product')

            for variant in low_stock_variants:
                # Check if notification already exists
                existing = Notification.objects.filter(
                    user=current_user,
                    product=variant.product,
                    type='warning',
                    title='Low Stock Alert',
                    message__icontains=f"has only {variant.stock} units"
                ).exists()

                if not existing:
                    Notification.objects.create(
                        user=current_user,
                        type='warning',
                        title='Low Stock Alert',
                        message=f"Product '{variant.product.name}' (SKU: {variant.sku}) has only {variant.stock} units left",
                        priority='high',
                        product=variant.product,
                        data={'variant_id': variant.id, 'stock': variant.stock}
                    )

            # 2. Out of stock products
            out_of_stock_variants = ProductVariant.objects.filter(
                product__owner=current_user,
                stock=0
            ).select_related('product')

            for variant in out_of_stock_variants:
                existing = Notification.objects.filter(
                    user=current_user,
                    product=variant.product,
                    type='error',
                    title='Out of Stock'
                ).exists()

                if not existing:
                    Notification.objects.create(
                        user=current_user,
                        type='error',
                        title='Out of Stock',
                        message=f"Product '{variant.product.name}' (SKU: {variant.sku}) is out of stock",
                        priority='high',
                        product=variant.product,
                        data={'variant_id': variant.id}
                    )

            # 3. Most sold products (by quantity in last 30 days)
            thirty_days_ago_date = timezone.now().date() - timedelta(days=30)
            most_sold_products = Order.objects.filter(
                product__owner=current_user,
                marketplace_order__order_date__gte=thirty_days_ago_date
            ).values('product__name', 'product__id').annotate(
                total_quantity=Sum('quantity')
            ).order_by('-total_quantity')[:3]

            for product in most_sold_products:
                existing = Notification.objects.filter(
                    user=current_user,
                    product_id=product['product__id'],
                    type='info',
                    title='Top Selling Product',
                    created_at__gte=timezone.now() - timedelta(days=1)  # Only one per day
                ).exists()

                if not existing:
                    Notification.objects.create(
                        user=current_user,
                        type='info',
                        title='Top Selling Product',
                        message=f"'{product['product__name']}' sold {product['total_quantity']} units in the last 30 days",
                        priority='medium',
                        product_id=product['product__id'],
                        data={'total_quantity': product['total_quantity']}
                    )

            # 4. Most profitable products (revenue - cost in last 30 days)
            profitable_products = Order.objects.filter(
                product__owner=current_user,
                marketplace_order__order_date__gte=thirty_days_ago_date
            ).values(
                'product__name',
                'product__id'
            ).annotate(
                total_revenue=Sum('selling_price') * Sum('quantity'),
                total_cost=Sum('variant__cost_price') * Sum('quantity'),
                profit=Sum('selling_price') * Sum('quantity') - Sum('variant__cost_price') * Sum('quantity')
            ).order_by('-profit')[:3]

            for product in profitable_products:
                if product['profit'] > 0:
                    existing = Notification.objects.filter(
                        user=current_user,
                        product_id=product['product__id'],
                        type='success',
                        title='High Profit Product',
                        created_at__gte=timezone.now() - timedelta(days=1)
                    ).exists()

                    if not existing:
                        Notification.objects.create(
                            user=current_user,
                            type='success',
                            title='High Profit Product',
                            message=f"'{product['product__name']}' generated ₹{product['profit']:.2f} profit in the last 30 days",
                            priority='medium',
                            product_id=product['product__id'],
                            data={'profit': product['profit']}
                        )

            # 5. Products with losses (negative profit)
            loss_products = Order.objects.filter(
                product__owner=current_user,
                marketplace_order__order_date__gte=thirty_days_ago_date
            ).values(
                'product__name',
                'product__id'
            ).annotate(
                total_revenue=Sum('selling_price') * Sum('quantity'),
                total_cost=Sum('variant__cost_price') * Sum('quantity'),
                profit=Sum('selling_price') * Sum('quantity') - Sum('variant__cost_price') * Sum('quantity')
            ).filter(profit__lt=0).order_by('profit')[:3]

            for product in loss_products:
                existing = Notification.objects.filter(
                    user=current_user,
                    product_id=product['product__id'],
                    type='error',
                    title='Loss Making Product',
                    created_at__gte=timezone.now() - timedelta(days=1)
                ).exists()

                if not existing:
                    Notification.objects.create(
                        user=current_user,
                        type='error',
                        title='Loss Making Product',
                        message=f"'{product['product__name']}' incurred ₹{abs(product['profit']):.2f} loss in the last 30 days",
                        priority='high',
                        product_id=product['product__id'],
                        data={'loss': abs(product['profit'])}
                    )

        except Exception as e:
            print(f"Error in NotificationController.generate_notifications: {str(e)}")

    @staticmethod
    def get_notifications(current_user=None, platform_code: str = None, include_read: bool = False):
        """Get notifications for the user"""
        try:
            if current_user is None:
                raise ValueError("current_user must be provided")

            # Generate fresh notifications first
            NotificationController.generate_notifications(current_user, platform_code)

            # Get notifications
            query = Notification.objects.filter(user=current_user)
            if not include_read:
                query = query.filter(is_read=False)

            notifications = query.order_by('-created_at')[:20]  # Get latest 20

            return {
                "notifications": [
                    {
                        "id": n.id,
                        "type": n.type,
                        "title": n.title,
                        "message": n.message,
                        "priority": n.priority,
                        "is_read": n.is_read,
                        "created_at": n.created_at.isoformat(),
                        "product_id": n.product.id if n.product else None,
                        "order_id": n.order.id if n.order else None,
                        "data": n.data
                    }
                    for n in notifications
                ]
            }

        except Exception as e:
            print(f"Error in NotificationController.get_notifications: {str(e)}")
            return {"notifications": []}

    @staticmethod
    def mark_as_read(notification_id, current_user):
        """Mark a notification as read"""
        try:
            notification = Notification.objects.get(id=notification_id, user=current_user)
            notification.mark_as_read()
            return True
        except Notification.DoesNotExist:
            return False
        except Exception as e:
            print(f"Error in NotificationController.mark_as_read: {str(e)}")
            return False

    @staticmethod
    def mark_all_as_read(current_user):
        """Mark all notifications as read for the user"""
        try:
            Notification.objects.filter(user=current_user, is_read=False).update(is_read=True)
            return True
        except Exception as e:
            print(f"Error in NotificationController.mark_all_as_read: {str(e)}")
            return False