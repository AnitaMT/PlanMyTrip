# Generated by Django 5.2.1 on 2025-05-31 18:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('viajes', '0004_alter_destino_categoria'),
    ]

    operations = [
        migrations.AddField(
            model_name='viaje',
            name='visibilidad',
            field=models.CharField(choices=[('PRIVADO', 'Privado'), ('PUBlICO', 'Público')], default='PRIVADO', max_length=20),
        ),
    ]
