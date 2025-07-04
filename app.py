import os
import pandas as pd
from flask import Flask, render_template, request, jsonify, send_file, make_response, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from datetime import datetime
import numpy as np
import calendar
from io import BytesIO
import pdfkit
import json
import uuid
import random
import string
from functools import wraps
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import or_, extract
import click
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = 'login'

class User(UserMixin, db.Model):
    id = db.Column(db.String(80), primary_key=True)
    password_hash = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(80), nullable=False, default='owner')
    allowed_units = db.Column(db.JSON, nullable=True, default=[])
    def set_password(self, password): self.password_hash = generate_password_hash(password)
    def check_password(self, password): return check_password_hash(self.password_hash, password)
    def get_id(self): return self.id

class Booking(db.Model):
    id = db.Column(db.String(80), primary_key=True, default=lambda: str(uuid.uuid4()))
    unit_name = db.Column(db.String(120)); checkin = db.Column(db.Date); checkout = db.Column(db.Date)
    channel = db.Column(db.String(80)); on_offline = db.Column(db.String(80)); pax = db.Column(db.Integer)
    duration = db.Column(db.Integer); price = db.Column(db.Float); cleaning_fee = db.Column(db.Float)
    platform_charge = db.Column(db.Float); total = db.Column(db.Float)

class Expense(db.Model):
    id = db.Column(db.String(80), primary_key=True, default=lambda: str(uuid.uuid4()))
    date = db.Column(db.Date); unit_name = db.Column(db.String(120))
    description = db.Column(db.String(200)); debit = db.Column(db.Float)

def get_filtered_data(year, month, room_type):
    bookings_query = db.session.query(Booking); expenses_query = db.session.query(Expense)
    if current_user.is_authenticated and current_user.role == 'owner':
        allowed_units = current_user.allowed_units
        if allowed_units:
            bookings_query = bookings_query.filter(Booking.unit_name.in_(allowed_units))
            expenses_query = expenses_query.filter(Expense.unit_name.in_(allowed_units))
    if year:
        bookings_query = bookings_query.filter(extract('year', Booking.checkin) == int(year)); expenses_query = expenses_query.filter(extract('year', Expense.date) == int(year))
    if month:
        bookings_query = bookings_query.filter(extract('month', Booking.checkin) == int(month)); expenses_query = expenses_query.filter(extract('month', Expense.date) == int(month))
    if room_type and room_type != '所有房型':
        bookings_query = bookings_query.filter(Booking.unit_name == room_type); expenses_query = expenses_query.filter(Expense.unit_name == room_type)
    return pd.read_sql(bookings_query.statement, db.engine), pd.read_sql(expenses_query.statement, db.engine)

def calculate_dashboard_data(bookings_df, expenses_df, year, month):
    total_booking_revenue = bookings_df['total'].sum() if 'total' in bookings_df.columns else 0
    total_monthly_expenses = expenses_df['debit'].sum() if 'debit' in expenses_df.columns else 0
    gross_profit = total_booking_revenue - total_monthly_expenses; management_fee = gross_profit * 0.30
    monthly_income = gross_profit - management_fee; total_occupancy_rate = 0
    if year and month and current_user.is_authenticated and current_user.allowed_units:
        _, num_days_in_month = calendar.monthrange(int(year), int(month)); total_room_nights = len(current_user.allowed_units) * num_days_in_month
        occupied_nights = bookings_df['duration'].sum() if 'duration' in bookings_df.columns else 0
        total_occupancy_rate = (occupied_nights / total_room_nights * 100) if total_room_nights > 0 else 0
    summary = {'total_booking_revenue': float(total_booking_revenue),'total_monthly_expenses': float(total_monthly_expenses),'gross_profit': float(gross_profit),'management_fee': float(management_fee),'monthly_income': float(monthly_income),'total_occupancy_rate': float(total_occupancy_rate),}
    analysis = {'total_bookings_count': 0, 'average_duration': 0,'average_daily_rate': 0, 'revpar': 0,'average_monthly_revenue': 0, 'average_monthly_expenses': 0,}
    if not month and not bookings_df.empty:
        total_bookings_count = len(bookings_df); average_duration = bookings_df['duration'].mean()
        with np.errstate(divide='ignore', invalid='ignore'): adr_series = bookings_df['price'] / bookings_df['duration']
        average_daily_rate = adr_series.replace([np.inf, -np.inf], np.nan).mean()
        total_nights_in_year = len(current_user.allowed_units) * 365 if current_user.allowed_units else 0
        revpar = total_booking_revenue / total_nights_in_year if total_nights_in_year > 0 else 0
        average_monthly_revenue = total_booking_revenue / 12; average_monthly_expenses = total_monthly_expenses / 12
        analysis.update({'total_bookings_count': int(total_bookings_count),'average_duration': float(average_duration),'average_daily_rate': float(average_daily_rate),'revpar': float(revpar),'average_monthly_revenue': float(average_monthly_revenue),'average_monthly_expenses': float(average_monthly_expenses),})
    return summary, analysis

def create_app():
    app = Flask(__name__, template_folder='templates')
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'a_very_secret_key_for_dev')
    database_url = os.environ.get('DATABASE_URL')
    if database_url:
        # 确保 SQLAlchemy 使用 psycopg2 驱动，并替换协议头
        if database_url.startswith("postgres://"):
            database_url = database_url.replace("postgres://", "postgresql+psycopg2://", 1)
        elif database_url.startswith("postgresql://"):
            database_url = database_url.replace("postgresql://", "postgresql+psycopg2://", 1)
    else:
        # 为本地开发提供回退
        database_url = 'sqlite:///msprodata.db'
    
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url; app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app); login_manager.init_app(app)

    @app.cli.command('init-db')
    @click.option('--migrate-data', is_flag=True)
    def init_db_command(migrate_data):
        with app.app_context():
            db.drop_all(); db.create_all(); click.echo('Initialized the database.')
            if migrate_data:
                try:
                    with open('users.json', 'r') as f:
                        users_data = json.load(f)
                        for username, data in users_data.items():
                            user = User(id=username, role=data['role'], allowed_units=data.get('allowed_units', []))
                            user.set_password(data['password']); db.session.add(user)
                    db.session.commit(); click.echo('Successfully migrated users.')
                except Exception as e:
                    click.echo(f'Error migrating users: {e}'); db.session.rollback()

    # --- Main Routes ---
    @app.route('/')
    @app.route('/index')
    @login_required
    def index():
        today = datetime.today(); default_year = request.args.get('year', str(today.year)); default_month = request.args.get('month', ''); years_query = db.session.query(extract('year', Booking.checkin)).distinct().all()
        years_options = sorted([y[0] for y in years_query if y[0] is not None], reverse=True)
        if today.year not in years_options: years_options.insert(0, today.year)
        months_options = [{'value': i, 'text': f'{i}月'} for i in range(1, 13)]
        room_types_query = db.session.query(Booking.unit_name).distinct().all()
        room_types = ['所有房型'] + sorted([r[0] for r in room_types_query if r[0] is not None])
        bookings_df, expenses_df = get_filtered_data(default_year, default_month or None, '所有房型')
        summary, analysis = calculate_dashboard_data(bookings_df, expenses_df, int(default_year), int(default_month) if default_month else None)
        return render_template('index.html', years_options=years_options, default_year=default_year, months_options=months_options, room_types=room_types, summary=summary, analysis=analysis, current_user_role=current_user.role)

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if current_user.is_authenticated: return redirect(url_for('index'))
        if request.method == 'POST':
            username = request.form['username']; password = request.form['password']
            user = User.query.get(username)
            if user and user.check_password(password): login_user(user); return redirect(url_for('index'))
            else: flash('用户名或密码错误', 'danger')
        return render_template('login.html')
    
    @app.route('/register', methods=['GET', 'POST'])
    def register():
        if request.method == 'POST': flash('注册功能开发中。', 'info'); return redirect(url_for('login'))
        return render_template('register.html')

    @app.route('/logout')
    @login_required
    def logout():
        logout_user(); flash('您已成功登出。', 'success'); return redirect(url_for('login'))

    @app.route('/reports')
    @login_required
    def reports():
        today = datetime.today()
        years_query = db.session.query(extract('year', Booking.checkin)).distinct().all()
        years_options = sorted([y[0] for y in years_query if y[0] is not None], reverse=True)
        if not years_options: years_options.append(today.year)
        if today.year not in years_options: years_options.insert(0, today.year)
        months_options = [{'value': i, 'text': f'{i}月'} for i in range(1, 13)]
        room_types_query = db.session.query(Booking.unit_name).distinct().all()
        room_types = ['所有房型'] + sorted([r[0] for r in room_types_query if r[0] is not None])
        return render_template('reports.html', years_options=years_options, default_year=str(today.year), months_options=months_options, room_types=room_types)

    @app.route('/calendar_view')
    @login_required
    def calendar_view():
        today = datetime.today()
        years_query = db.session.query(extract('year', Booking.checkin)).distinct().all()
        years_options = sorted([y[0] for y in years_query if y[0] is not None], reverse=True)
        if not years_options: years_options.append(today.year)
        if today.year not in years_options: years_options.insert(0, today.year)
        months_options = [{'value': i, 'text': f'{i}月'} for i in range(1, 13)]
        room_types_query = db.session.query(Booking.unit_name).distinct().all()
        room_types = ['所有房型'] + sorted([r[0] for r in room_types_query if r[0] is not None])
        return render_template('calendar.html', years_options=years_options, default_year=str(today.year), months_options=months_options, room_types=room_types)

    @app.route('/admin_panel')
    @login_required
    def admin_panel():
        if current_user.role != 'admin': flash('您没有权限访问此页面。', 'danger'); return redirect(url_for('index'))
        all_users_from_db = User.query.all(); users_dict = {}
        for user in all_users_from_db:
            users_dict[user.id] = {'role': user.role, 'allowed_units': user.allowed_units}
        return render_template('admin.html', users=users_dict)

    @app.route('/add_booking', methods=['GET', 'POST'])
    @login_required
    def add_booking():
        if current_user.role != 'admin': return redirect(url_for('index'))
        all_units = sorted([unit.unit_name for unit in Booking.query.with_entities(Booking.unit_name).distinct()])
        if request.method == 'POST': flash('预订已成功添加！', 'success'); return redirect(url_for('index'))
        return render_template('add_booking.html', all_units=all_units)

    @app.route('/edit_booking/<booking_id>', methods=['GET', 'POST'])
    @login_required
    def edit_booking(booking_id):
        if current_user.role != 'admin': return redirect(url_for('index'))
        booking_to_edit = Booking.query.get_or_404(booking_id)
        all_units = sorted([unit.unit_name for unit in Booking.query.with_entities(Booking.unit_name).distinct()])
        if request.method == 'POST': flash('预订已成功更新！', 'success'); return redirect(request.args.get('next') or url_for('index'))
        return render_template('edit_booking.html', booking=booking_to_edit, all_units=all_units)
    
    @app.route('/edit_expense/<expense_id>', methods=['GET', 'POST'])
    @login_required
    def edit_expense(expense_id):
        if current_user.role != 'admin': return redirect(url_for('index'))
        expense_to_edit = Expense.query.get_or_404(expense_id)
        all_units = sorted([unit.unit_name for unit in Booking.query.with_entities(Booking.unit_name).distinct()])
        if request.method == 'POST': 
            expense_to_edit.date = datetime.strptime(request.form['date'], '%Y-%m-%d').date()
            expense_to_edit.unit_name = request.form['unit_name']; expense_to_edit.description = request.form['description']
            expense_to_edit.debit = float(request.form['debit']); db.session.commit()
            flash('支出已成功更新！', 'success'); return redirect(request.args.get('next') or url_for('index'))
        return render_template('edit_expense.html', expense=expense_to_edit, all_units=all_units)

    @app.route('/edit_user/<username>', methods=['GET', 'POST'])
    @login_required
    def edit_user(username):
        if current_user.role != 'admin': flash('您没有权限执行此操作。', 'danger'); return redirect(url_for('admin_panel'))
        user_to_edit = User.query.get_or_404(username)
        if request.method == 'POST':
            user_to_edit.role = request.form.get('role'); allowed_units_str = request.form.get('allowed_units', '')
            user_to_edit.allowed_units = [unit.strip() for unit in allowed_units_str.split(',') if unit.strip()]
            db.session.commit(); flash(f'用户 {username} 的信息已成功更新！', 'success'); return redirect(url_for('admin_panel'))
        return render_template('edit_user.html', user=user_to_edit)

    @app.route('/delete_user/<username>', methods=['POST'])
    @login_required
    def delete_user(username):
        if current_user.role != 'admin': flash('您没有权限执行此操作。', 'danger'); return redirect(url_for('admin_panel'))
        user_to_delete = User.query.get_or_404(username); db.session.delete(user_to_delete); db.session.commit()
        flash(f'用户 {username} 已被删除。', 'success'); return redirect(url_for('admin_panel'))
    
    @app.route('/reset_password/<username>', methods=['POST'])
    @login_required
    def reset_password(username):
        if current_user.role != 'admin': flash('您没有权限执行此操作。', 'danger'); return redirect(url_for('admin_panel'))
        user_to_reset = User.query.get_or_404(username); new_password = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
        user_to_reset.set_password(new_password); db.session.commit()
        flash(f'用户 {username} 的密码已被重置为: {new_password}', 'success'); return redirect(url_for('edit_user', username=username))
        
    # --- API Endpoints ---
    @app.route('/api/filter_data')
    @login_required
    def filter_data_api():
        year, month, room_type = request.args.get('year'), request.args.get('month'), request.args.get('room_type')
        bookings_df, expenses_df = get_filtered_data(year, month or None, room_type); summary, analysis = calculate_dashboard_data(bookings_df, expenses_df, int(year), int(month) if month else None)
        return jsonify(summary=summary, analysis=analysis)

    @app.route('/api/chart_data')
    @login_required
    def chart_data_api():
        year, room_type = request.args.get('year'), request.args.get('room_type')
        monthly_revenue, monthly_expenses = [], []
        for m in range(1, 13):
            bookings_df, expenses_df = get_filtered_data(year, m, room_type); summary, _ = calculate_dashboard_data(bookings_df, expenses_df, int(year), m)
            monthly_revenue.append(summary['total_booking_revenue']); monthly_expenses.append(summary['total_monthly_expenses'])
        return jsonify({'months': [f'{i}月' for i in range(1, 13)],'monthly_revenue': monthly_revenue,'monthly_expenses': monthly_expenses})
        
    @app.route('/api/calendar_events')
    @login_required
    def calendar_events_api():
        today = datetime.today(); year = request.args.get('year', default=str(today.year)); month = request.args.get('month', default=''); room_type = request.args.get('room_type', default='所有房型')
        bookings_df, _ = get_filtered_data(year, month or None, room_type); events = []
        if not bookings_df.empty:
            bookings_df['checkin'] = pd.to_datetime(bookings_df['checkin']); bookings_df['checkout'] = pd.to_datetime(bookings_df['checkout'])
            for index, row in bookings_df.iterrows():
                events.append({'id': row['id'], 'title': row['unit_name'], 'start': row['checkin'].strftime('%Y-%m-%d'), 'end': row['checkout'].strftime('%Y-%m-%d')})
        return jsonify(events)

    @app.route('/api/detailed_data')
    @login_required
    def detailed_data_api():
        year, month, room_type = request.args.get('year'), request.args.get('month'), request.args.get('room_type')
        bookings_df, expenses_df = get_filtered_data(year, month or None, room_type)
        if not bookings_df.empty:
            for col in ['checkin', 'checkout']: bookings_df[col] = pd.to_datetime(bookings_df[col]).dt.strftime('%Y-%m-%d')
            bookings_df['date'] = bookings_df['checkin']; bookings_df['type'] = 'booking'
            bookings_df['booking_number'] = bookings_df['id']; bookings_df.rename(columns={'total': 'total_booking_revenue'}, inplace=True)
        if not expenses_df.empty:
            expenses_df['date'] = pd.to_datetime(expenses_df['date']).dt.strftime('%Y-%m-%d'); expenses_df['type'] = 'expense'
            expenses_df.rename(columns={'debit': 'additional_expense_amount', 'description': 'additional_expense_category', 'id': 'expense_id'}, inplace=True)
        combined_df = pd.concat([bookings_df, expenses_df], ignore_index=True)
        if not combined_df.empty: combined_df.sort_values(by='date', ascending=False, inplace=True)
        combined_df.replace([np.inf, -np.inf], np.nan, inplace=True); combined_df.fillna('-', inplace=True)
        return jsonify(data=combined_df.to_dict(orient='records'))

    @app.route('/api/annual_summary')
    @login_required
    def annual_summary_api():
        year, room_type = request.args.get('year'), request.args.get('room_type')
        bookings_df, expenses_df = get_filtered_data(year, None, room_type)
        total_revenue = bookings_df['total'].sum(); total_expenses = expenses_df['debit'].sum(); gross_profit = total_revenue - total_expenses; management_fee = gross_profit * 0.3; net_profit = gross_profit - management_fee
        return jsonify({'year': year, 'total_revenue': total_revenue, 'total_expenses': total_expenses, 'gross_profit': gross_profit, 'management_fee': management_fee, 'net_profit': net_profit})

    @app.route('/api/quarterly_summary')
    @login_required
    def quarterly_summary_api():
        year, room_type = request.args.get('year'), request.args.get('room_type')
        results = {}
        for q, months in {'Q1': [1,2,3], 'Q2': [4,5,6], 'Q3': [7,8,9], 'Q4': [10,11,12]}.items():
            q_b_df, q_e_df = pd.DataFrame(), pd.DataFrame()
            for month in months:
                b, e = get_filtered_data(year, month, room_type)
                q_b_df = pd.concat([q_b_df, b]); q_e_df = pd.concat([q_e_df, e])
            total_revenue = q_b_df['total'].sum(); total_expenses = q_e_df['debit'].sum(); gross_profit = total_revenue - total_expenses; management_fee = gross_profit * 0.3; net_profit = gross_profit - management_fee
            results[q] = {'total_revenue': total_revenue, 'total_expenses': total_expenses, 'gross_profit': gross_profit, 'management_fee': management_fee, 'net_profit': net_profit}
        return jsonify(results)

    def get_report_data_as_df(year, month, room_type, report_type):
        if report_type == 'detailed':
            b_df, e_df = get_filtered_data(year, month or None, room_type)
            if not b_df.empty: b_df.loc[:,'type'] = 'booking'; b_df.rename(columns={'id': 'booking_number', 'total': 'total_booking_revenue'}, inplace=True)
            if not e_df.empty: e_df.loc[:,'type'] = 'expense'; e_df.rename(columns={'id': 'expense_id', 'debit': 'additional_expense_amount', 'description': 'additional_expense_category'}, inplace=True)
            return pd.concat([b_df, e_df], ignore_index=True).fillna('-')
        elif report_type == 'annual':
            b_df, e_df = get_filtered_data(year, None, room_type)
            tr = b_df['total'].sum(); te = e_df['debit'].sum(); gp = tr - te; mf = gp * 0.3; np = gp - mf
            return pd.DataFrame([{'year': year, 'total_revenue': tr, 'total_expenses': te, 'gross_profit': gp, 'management_fee': mf, 'net_profit': np}])
        elif report_type == 'quarterly':
            results = []
            for q, months in {'Q1': [1,2,3], 'Q2': [4,5,6], 'Q3': [7,8,9], 'Q4': [10,11,12]}.items():
                qb_df, qe_df = pd.DataFrame(), pd.DataFrame()
                for m in months: b, e = get_filtered_data(year, m, room_type); qb_df = pd.concat([qb_df, b]); qe_df = pd.concat([qe_df, e])
                tr = qb_df['total'].sum(); te = qe_df['debit'].sum(); gp = tr - te; mf = gp * 0.3; np = gp - mf
                results.append({'季度': q, 'total_revenue': tr, 'total_expenses': te, 'gross_profit': gp, 'management_fee': mf, 'net_profit': np})
            return pd.DataFrame(results)
        return pd.DataFrame()

    @app.route('/download_csv_report')
    @login_required
    def download_csv_report():
        year, month, room_type, report_type, columns = request.args.get('year'), request.args.get('month'), request.args.get('room_type'), request.args.get('report_type'), request.args.get('columns')
        df = get_report_data_as_df(year, month, room_type, report_type)
        if not df.empty and columns: df = df[columns.split(',')]
        output = BytesIO(); df.to_csv(output, index=False, encoding='utf-8-sig'); output.seek(0)
        return send_file(output, mimetype='text/csv', download_name=f'{report_type}_report.csv', as_attachment=True)

    @app.route('/download_excel_report')
    @login_required
    def download_excel_report():
        year, month, room_type, report_type, columns = request.args.get('year'), request.args.get('month'), request.args.get('room_type'), request.args.get('report_type'), request.args.get('columns')
        df = get_report_data_as_df(year, month, room_type, report_type)
        if not df.empty and columns: df = df[columns.split(',')]
        output = BytesIO();
        with pd.ExcelWriter(output, engine='openpyxl') as writer: df.to_excel(writer, sheet_name=report_type, index=False)
        output.seek(0)
        return send_file(output, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', download_name=f'{report_type}_report.xlsx', as_attachment=True)

    @app.route('/download_monthly_statement')
    @login_required
    def download_monthly_statement():
        year = request.args.get('year')
        month = request.args.get('month')
        room_type = request.args.get('room_type')
        
        if not year or not month:
            flash("请选择具体的年份和月份来下载月结单。", "warning")
            return redirect(url_for('reports', error='missing_params', message='Year and month are required.'))

        try:
            bookings_df, expenses_df = get_filtered_data(year, month, room_type)
            original_bookings_df, original_expenses_df = bookings_df.copy(), expenses_df.copy()

            if original_bookings_df.empty and original_expenses_df.empty:
                flash(f"所选年份 {year} 和月份 {month} 没有可供下载的数据。", "info")
                return redirect(url_for('reports', error='no_data', message=f'No data available for {year}-{month}.'))

            if not bookings_df.empty:
                bookings_df['checkin'] = pd.to_datetime(bookings_df['checkin']).dt.strftime('%Y-%m-%d')
                bookings_df['checkout'] = pd.to_datetime(bookings_df['checkout']).dt.strftime('%Y-%m-%d')
                bookings_df['date'] = bookings_df['checkin']
                bookings_df['type'] = 'booking'
                bookings_df.rename(columns={'id': 'booking_number', 'total': 'total_booking_revenue'}, inplace=True)

            if not expenses_df.empty:
                expenses_df['date'] = pd.to_datetime(expenses_df['date']).dt.strftime('%Y-%m-%d')
                expenses_df['type'] = 'expense'
                expenses_df.rename(columns={'debit': 'additional_expense_amount', 'description': 'additional_expense_category', 'id': 'expense_id'}, inplace=True)

            df = pd.concat([bookings_df, expenses_df], ignore_index=True)
            if not df.empty:
                df.sort_values(by='date', ascending=False, inplace=True)
            df.replace([np.inf, -np.inf], np.nan, inplace=True)
            df.fillna('-', inplace=True)

            summary, _ = calculate_dashboard_data(original_bookings_df, original_expenses_df, int(year), int(month))
            
            html_string = render_template('monthly_statement.html', 
                                          records=df.to_dict('records'), 
                                          summary=summary, 
                                          year=year, 
                                          month_name=f'{month}月', 
                                          room_type=room_type, 
                                          current_date=datetime.now().strftime('%Y-%m-%d'))
            
            options = {
                'page-size': 'A4',
                'orientation': 'Landscape',
                'margin-top': '0.5in',
                'margin-right': '0.5in',
                'margin-bottom': '0.5in',
                'margin-left': '0.5in',
                'encoding': "UTF-8",
                'no-outline': None,
                '--enable-local-file-access': None
            }
            config = pdfkit.configuration(wkhtmltopdf=r'C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe')
            pdf = pdfkit.from_string(html_string, False, options=options, configuration=config)
            
            response = make_response(pdf)
            response.headers['Content-Type'] = 'application/pdf'
            response.headers['Content-Disposition'] = f'attachment; filename={year}-{month}_statement.pdf'
            return response

        except IOError as e:
            if "No wkhtmltopdf executable found" in str(e):
                app.logger.error(f"wkhtmltopdf not found: {e}", exc_info=True)
                flash("服务器错误：找不到PDF生成工具(wkhtmltopdf)。请确认已正确安装并将其添加至系统PATH。", "danger")
                return redirect(url_for('reports', error='pdf_tool_not_found', message=str(e)))
            else:
                app.logger.error(f"PDFKit IO Error: {e}", exc_info=True)
                flash(f"生成PDF时发生IO错误，请联系管理员。", "danger")
                return redirect(url_for('reports', error='pdf_generation_failed', message=str(e)))
        except Exception as e:
            app.logger.error(f"Error generating monthly statement for {year}-{month}: {e}", exc_info=True)
            flash(f"生成月结单时发生严重错误，请联系管理员。", "danger")
            return redirect(url_for('reports', error='pdf_generation_failed', message=str(e)))

    return app

@login_manager.user_loader
def load_user(user_id): return User.query.get(user_id)

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)