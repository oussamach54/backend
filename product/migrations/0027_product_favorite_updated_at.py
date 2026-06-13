from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('product', '0026_alter_product_category'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='favorite_updated_at',
            field=models.DateTimeField(blank=True, db_index=True, null=True),
        ),
    ]
