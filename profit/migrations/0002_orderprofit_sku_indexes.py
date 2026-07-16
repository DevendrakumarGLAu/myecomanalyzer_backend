from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('profit', '0001_initial'),
    ]

    operations = [
        migrations.AddIndex(
            model_name='orderprofit',
            index=models.Index(fields=['sku'], name='order_profit_sku_idx'),
        ),
        migrations.AddIndex(
            model_name='orderprofit',
            index=models.Index(fields=['created_by', 'sku'], name='order_profit_created_sku_idx'),
        ),
    ]
