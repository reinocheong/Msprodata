import os
import pandas as pd
import click
from flask.cli import with_appcontext
from extensions import db
from models import User, Property, FinancialReport

@click.command(name='seed-data')
@with_appcontext
def seed_data_command():
    """Scans excel_data, creates properties, and imports reports."""
    
    excel_dir = 'excel_data'
    if not os.path.exists(excel_dir):
        click.echo(f"Directory '{excel_dir}' not found. Skipping seed data.")
        return

    # We'll assign all properties to the first user.
    # In a real app, you'd have a better way to determine ownership.
    owner = db.session.get(User, 1)
    if not owner:
        click.echo("No user with ID 1 found. Please register a user first.")
        return

    click.echo("Starting data seeding...")
    
    for filename in os.listdir(excel_dir):
        if not filename.endswith('.xlsx'):
            continue

        file_path = os.path.join(excel_dir, filename)
        click.echo(f"Processing file: {filename}...")

        try:
            # Determine report type from filename
            if 'booking' in filename.lower():
                report_type = 'Booking'
            elif 'expense' in filename.lower():
                report_type = 'Expense'
            else:
                report_type = 'General'

            # Extract year and month from filename
            parts = filename.replace('.xlsx', '').split('_')
            month_str, year_str_part = parts[0], parts[1]
            year = int(year_str_part.split(' ')[0]) # Take only the year part
            month = int(month_str)

            # Read the first sheet to find the Unit Name
            df = pd.read_excel(file_path, sheet_name=0)
            
            if 'Unit Name' not in df.columns:
                click.echo(f"  - SKIPPING: 'Unit Name' column not found in {filename}.")
                continue
            
            unit_name = df['Unit Name'].dropna().iloc[0]

            # Find or create the property
            property_obj = Property.query.filter_by(name=unit_name, owner_id=owner.id).first()
            if not property_obj:
                click.echo(f"  - Creating new property: {unit_name}")
                property_obj = Property(name=unit_name, owner_id=owner.id)
                db.session.add(property_obj)
                # We need to commit here to get the property_obj.id for the report
                db.session.commit() 

            # Check if this exact report already exists
            report_exists = FinancialReport.query.filter_by(
                property_id=property_obj.id,
                year=year,
                month=month,
                report_type=report_type
            ).first()

            if not report_exists:
                click.echo(f"  - Importing report for {unit_name} for {year}-{month:02d}")
                # For simplicity, we're storing the file path. 
                # A more robust solution might store the data itself.
                new_report = FinancialReport(
                    property_id=property_obj.id,
                    year=year,
                    month=month,
                    report_type=report_type,
                    file_path=file_path # Storing the path
                )
                db.session.add(new_report)
            else:
                click.echo(f"  - SKIPPING: Report for {unit_name} for {year}-{month:02d} already exists.")

        except Exception as e:
            click.echo(f"  - ERROR processing {filename}: {e}")
            db.session.rollback()

    db.session.commit()
    click.echo("Data seeding finished.")

