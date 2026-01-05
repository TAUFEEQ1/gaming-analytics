# Generated manually on 2026-01-05

from django.db import migrations


def drop_tax_variance_tables(apps, schema_editor):
    """Drop tax variance tables directly using SQL"""
    with schema_editor.connection.cursor() as cursor:
        # Drop tables in correct order (respecting foreign keys)
        tables = [
            'dashboard_weeklygamingtaxvariance',
            'dashboard_monthlywhtvariance',
            'dashboard_lgrbsubmission',
            'dashboard_urapayment',
            'dashboard_auditlog',
            'dashboard_excelupload',
        ]
        
        for table in tables:
            try:
                cursor.execute(f"DROP TABLE IF EXISTS `{table}`")
            except Exception as e:
                print(f"Warning: Could not drop table {table}: {e}")


class Migration(migrations.Migration):

    dependencies = [
        ("dashboard", "0002_alter_lgrbsubmission_operator_category"),
    ]

    operations = [
        migrations.RunPython(drop_tax_variance_tables, reverse_code=migrations.RunPython.noop),
    ]
