from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [("ledger", "0002_immutable_when_signed")]

    operations = [
        migrations.AddField(
            model_name="certificate",
            name="reemplaza",
            field=models.OneToOneField(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.RESTRICT,
                related_name="reemplazado_por",
                to="ledger.certificate",
                verbose_name="reemplaza a",
            ),
        ),
    ]
