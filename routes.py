from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file, session
from flask_login import login_required, current_user
from models import db, User, Property, FinancialReport
from utils import generate_pdf_report, generate_excel_report
import pandas as pd
import os

main = Blueprint('main', __name__)

@main.route('/')
@login_required
def index():
    """
    Main dashboard page. Shows a list of properties and financial reports.
    """
    # Default to the first property if none is selected
    selected_property_id = request.args.get('property_id')
    # For debugging, show all properties to any logged-in user
    user_properties = Property.query.all()

    if not selected_property_id and user_properties:
        selected_property_id = user_properties[0].id
    
    # Fetch reports for the selected property
    if selected_property_id:
        reports = FinancialReport.query.filter_by(property_id=selected_property_id).order_by(FinancialReport.year.desc(), FinancialReport.month.desc()).all()
    else:
        reports = []

    return render_template(
        'index.html', 
        properties=user_properties, 
        selected_property_id=int(selected_property_id) if selected_property_id else None,
        reports=reports
    )

@main.route('/upload', methods=['POST'])
@login_required
def upload_file():
    """
    Handles file uploads for financial reports.
    """
    file = request.files.get('file')
    property_id = request.form.get('property_id')

    if not file or not property_id:
        flash('No file or property selected.', 'danger')
        return redirect(url_for('main.index'))

    if file.filename == '':
        flash('No selected file.', 'danger')
        return redirect(url_for('main.index'))

    try:
        # Assume it's an Excel file and process it
        df = pd.read_excel(file, sheet_name=None) # Read all sheets
        
        # Iterate through sheets and save data
        for sheet_name, sheet_data in df.items():
            # Simple example: Assume year and month are in the sheet name or columns
            # This logic needs to be robust based on the Excel file's structure
            year, month = 2025, 1 # Placeholder
            
            new_report = FinancialReport(
                year=year,
                month=month,
                property_id=property_id,
                data=sheet_data.to_dict('records')
            )
            db.session.add(new_report)
            
        db.session.commit()
        flash('File processed and data saved successfully!', 'success')

    except Exception as e:
        db.session.rollback()
        flash(f'An error occurred: {e}', 'danger')

    return redirect(url_for('main.index', property_id=property_id))


@main.route('/report/download/<int:report_id>/<string:format>')
@login_required
def download_report(report_id, format):
    """
    Generates and downloads a financial report in either PDF or Excel format.
    """
    report = FinancialReport.query.get_or_404(report_id)
    
    # Ensure the report belongs to the current user
    if report.property.user_id != current_user.id:
        flash('You are not authorized to view this report.', 'danger')
        return redirect(url_for('main.index'))

    if format == 'pdf':
        # Generate PDF
        pdf = generate_pdf_report(report.data)
        return send_file(
            pdf,
            as_attachment=True,
            download_name=f'report_{report.year}_{report.month}.pdf',
            mimetype='application/pdf'
        )
    elif format == 'excel':
        # Generate Excel
        return generate_excel_report(report.data)

    flash('Invalid report format specified.', 'warning')
    return redirect(url_for('main.index'))
