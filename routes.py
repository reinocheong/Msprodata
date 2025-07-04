from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file, session
from flask_login import login_required, current_user
from models import db, User, Property, FinancialReport
from utils import generate_pdf_report, generate_excel_report
import pandas as pd
import os

main = Blueprint('main', __name__)

# ... (rest of the file remains the same)
