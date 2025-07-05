import os
import pandas as pd
import click
from flask.cli import with_appcontext
from extensions import db
from models import User, Property, FinancialReport

@click.command(name='seed-data')
@with_appcontext
def seed_data_command():
    """Scans excel_data, creates properties, and imports reports with detailed logging."""
    
    click.echo("--- Seeding data command started ---")
    excel_dir = 'excel_data'
    if not os.path.exists(excel_dir):
        click.echo(f"ERROR: Directory '{excel_dir}' not found. Skipping seed data.")
        return

    # We'll assign all properties to the first user.
    # In a real app, you'd have a better way to determine ownership.
    owner = db.session.get(User, 1)
    if not owner:
        click.echo("ERROR: No user with ID 1 found. Please ensure you have registered at least one user.")
        return
    click.echo(f"Found owner: {owner.name} (ID: {owner.id})")

    all_files = os.listdir(excel_dir)
    click.echo(f"Found {len(all_files)} files in '{excel_dir}': {all_files}")
    
    for filename in all_files:
        if not filename.endswith('.xlsx') or filename.startswith('~$'):
            click.echo(f"Skipping non-xlsx or temporary file: {filename}")
            continue

        file_path = os.path.join(excel_dir, filename)
        click.echo(f"--- Processing file: {filename} ---")

        try:
            # Determine report type from filename
            if 'booking' in filename.lower():
                report_type = 'Booking'
            elif 'expense' in filename.lower():
                report_type = 'Expense'
            else:
                report_type = 'General'
            click.echo(f"  - Determined report type: {report_type}")

            # Extract year and month from filename
            parts = filename.replace('.xlsx', '').split('_')
            month_str, year_str_part = parts[0], parts[1]
            year = int(year_str_part.split(' ')[0])
            month = int(month_str)
            click.echo(f"  - Parsed Year: {year}, Month: {month}")

            # Read the first sheet to find the Unit Name
            df = pd.read_excel(file_path, sheet_name=0)
            
            if 'Unit Name' not in df.columns:
                click.echo(f"  - ERROR: 'Unit Name' column not found in {filename}. Skipping.")
                continue
            
            unit_name = df['Unit Name'].dropna().iloc[0]
            click.echo(f"  - Found Unit Name: {unit_name}")

            # Find or create the property
            property_obj = Property.query.filter_by(name=unit_name, owner_id=owner.id).first()
            if not property_obj:
                click.echo(f"  - Property '{unit_name}' not found in DB. Creating new one.")
                property_obj = Property(name=unit_name, owner_id=owner.id)
                db.session.add(property_obj)
                db.session.flush() # Use flush to get the ID before commit
                click.echo(f"  - Created new property with ID: {property_obj.id}")
            else:
                click.echo(f"  - Found existing property with ID: {property_obj.id}")

            # Check if this exact report already exists
            report_exists = FinancialReport.query.filter_by(
                property_id=property_obj.id,
                year=year,
                month=month,
                report_type=report_type
            ).first()

            if not report_exists:
                click.echo(f"  - Importing report for {unit_name} for {year}-{month:02d}")
                new_report = FinancialReport(
                    property_id=property_obj.id,
                    year=year,
                    month=month,
                    report_type=report_type,
                    file_path=file_path
                )
                db.session.add(new_report)
                click.echo(f"  - Added report to session.")
            else:
                click.echo(f"  - SKIPPING: Report for {unit_name} for {year}-{month:02d} already exists.")

        except Exception as e:
            click.echo(f"  - FATAL ERROR processing {filename}: {e}")
            db.session.rollback()
            click.echo("  - Rolled back database session due to error.")

    try:
        click.echo("Attempting to commit all changes to database...")
        db.session.commit()
        click.echo("Commit successful.")
    except Exception as e:
        click.echo(f"FATAL ERROR during final commit: {e}")
        db.session.rollback()

    click.echo("--- Seeding data command finished ---")