from flask import request, jsonify,abort,make_response,flash,session
from flask import current_app as app
from src import db
from sqlalchemy import exc
from src.model import User, SalesRecord, Pasta
from src.schemas import SalesRecordSchema, PastaSchema
from sqlalchemy.exc import IntegrityError
from marshmallow import ValidationError
from sqlalchemy.exc import SQLAlchemyError, NoResultFound
from datetime import datetime
from src.helper import token_required, encode_auth_token
from flask import current_app as app
from flask import render_template, redirect, url_for
from src.forms import PredictionForm,CheckHistoricalDataForm, AddSalesRecordForm, SalesBySeasonForm, CheckHistoricalDataForm1
import numpy as np
import pickle
from pathlib import Path
import pandas as pd
import plotly.express as px
from datetime import timedelta


@app.route('/', methods=['GET', 'POST'])
def index():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    form = PredictionForm()
    chart_html = ""  # Ensure chart_html is always defined
    prediction_text = ""  # Initialize prediction_text to ensure it's always defined

    if form.validate_on_submit():
        brand = form.brand.data
        specific_pasta = form.pasta_number.data
        future_time = form.prediction_period.data

        pasta = Pasta.query.filter_by(brand=brand, specific_pasta=specific_pasta).first()

        if pasta:
            sales_records = SalesRecord.query.filter_by(pasta_id=pasta.pasta_id).order_by(SalesRecord.date.desc()).limit(365).all()
            
            if sales_records:
                if check_for_date_gaps(sales_records):
                    # Proceed if no gaps are found
                    features = prepare_features(sales_records)
                    total_sales, daily_predictions = make_daily_predictions(features, future_time)
                    prediction_text = f"Predicted total sales for the next {get_period_label(future_time)}: {total_sales}"
                    
                    latest_date = sales_records[0].date
                    chart_html = generate_sales_chart(daily_predictions, latest_date, future_time)
                else:
                # Handle the case where gaps are found
                    flash("There are gaps in the sales records' dates. Please ensure data continuity.",'info')
            else:
                flash("No sales records found for the specified pasta.")
        else:
            flash("Specified pasta not found.")

    return render_template('index.html', form=form, prediction_text=prediction_text, chart_html=chart_html)

def check_for_date_gaps(sales_records):
    # Ensure the list is not empty and contains more than one record for comparison
    if len(sales_records) < 2:
        return True  # No gaps can exist in a single record

    # Iterate through the list, comparing each date with the next
    for i in range(len(sales_records) - 1):
        current_record_date = sales_records[i].date
        next_record_date = sales_records[i + 1].date

        # Check if the next date is exactly one day before the current date
        if (current_record_date - next_record_date) != timedelta(days=1):
            # A gap is found
            return False

    # No gaps were found
    return True


def prepare_features(sales_records):
    # Extract sales data
    sales = np.array([record.quantity for record in sales_records])
    
    # Since the model expects a 2D array, we'll need to reshape our sales data
    features = sales.reshape(-1, 1)
    
    return features

def make_daily_predictions(features, future_time):
    # Load your model
    pickle_file = Path(__file__).parent.joinpath("model.pkl")
    model = pickle.load(open(pickle_file, "rb"))

    # Make daily predictions
    daily_predictions = model.predict(features)

    # Round the daily predictions to the nearest integer
    daily_predictions_rounded = np.round(daily_predictions).astype(int)

    # Select the range of predictions based on future_time
    if future_time == '1':  
        prediction_range = daily_predictions_rounded[:7]
    elif future_time == '4':  
        prediction_range = daily_predictions_rounded[:30]
    elif future_time == '52':  
        prediction_range = daily_predictions_rounded

    total_sales_prediction = np.sum(prediction_range)
    return total_sales_prediction, prediction_range.tolist()


def get_period_label(future_time):
    if future_time == '1':
        return 'week'
    elif future_time == '4':
        return 'month'
    elif future_time == '52':
        return 'year'

def generate_sales_chart(predictions, start_date, label="Predicted Sales"):
    # start_date is expected to be a datetime.date object representing the latest date in your database
    # predictions should be the list of predicted sales

    # Generate a date range starting from the day after the latest date in the database
    dates = pd.date_range(start=start_date + pd.Timedelta(days=1), periods=len(predictions), freq='D')
    data = pd.DataFrame({"Date": dates, "Sales": predictions})
    
    fig = px.line(data, x="Date", y="Sales")
   
    return fig.to_html(full_html=False, include_plotlyjs=True)




# AUTHENTICATION ROUTES
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        # Check if the email already exists in the database
        user_exists = User.query.filter_by(email=email).first()

        if user_exists:
            flash('Email already exists. Please log in.', 'warning')
            return redirect(url_for('register'))

        try:
            # Create a new User object and set password
            new_user = User(email=email)
            new_user.set_password(password)  # This hashes the password and stores it

            # Add new user to the database
            db.session.add(new_user)
            db.session.commit()

            flash('Successfully registered. Please log in.', 'success')
            return redirect(url_for('login'))

        except Exception as e:
            # Log the exception and flash an error message
            app.logger.error(f'Registration error: {e}')
            flash('An error occurred during registration. Please try again.', 'danger')
            return redirect(url_for('register'))

    # If the request is GET, just render the registration form
    return render_template('register.html')






@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        if not email or not password:
            flash('Missing email or password', 'error')
            return redirect(url_for('login'))

        user = db.session.query(User).filter_by(email=email).first()

        if not user or not user.check_password(password):
            flash('Incorrect email or password.', 'error')
            return redirect(url_for('login'))

        # If login is successful, generate a token
        token_response = encode_auth_token(user.id)
        if isinstance(token_response, str):  # If a token string was successfully generated
            session['user_id'] = user.id  # Store user ID in session
            session['token'] = token_response  # Store the token in session for web app flows
            
            flash('Login successful!', 'success')
            return redirect(url_for('index'))  # Redirect to the index page
        else:
            # Handle the error case where token generation failed
            flash('Failed to generate authentication token.', 'error')
            return redirect(url_for('login'))

    return render_template('login.html')





@app.route('/logout')
def logout():
    # Remove 'user_id' from session to log the user out
    session.pop('user_id', None)
    
    

    flash('You have been logged out.', 'success')
    return redirect(url_for('login'))













@app.route('/reset_password', methods=['GET', 'POST'])
@token_required
def reset_password():
    if 'user_id' not in session:
        flash('You must be logged in to reset your password.', 'warning')
        return redirect(url_for('login'))

    if request.method == 'POST':
        email = request.form['email']
        old_password = request.form['old_password']
        new_password = request.form['new_password']

        user = User.query.filter_by(email=email).first()

        if user and user.check_password(old_password):
            try:
                user.set_password(new_password)
                db.session.commit()
                flash('Your password has been updated.', 'success')
                return redirect(url_for('index'))
            except Exception as e:
                db.session.rollback()
                app.logger.error(f'Error resetting password: {e}')
                flash('An error occurred while resetting your password. Please try again.', 'danger')
                return render_template('reset_password.html')
        else:
            flash('Invalid email or old password.', 'danger')
            return render_template('reset_password.html')

    return render_template('reset_password.html')






@app.route('/sales_management', methods=['GET'])
@token_required
def sales_management():
    check_form = CheckHistoricalDataForm()
    add_form = AddSalesRecordForm()
    form = CheckHistoricalDataForm1()
    return render_template('sales_management.html', check_form=check_form, add_form=add_form,form=form)













    

@app.route("/sales_management1", methods=['GET', 'POST'])
@token_required
def sales_management1():
    check_form = CheckHistoricalDataForm()
    add_form = AddSalesRecordForm()  # Keep this form to pass into the render_template call
    form = CheckHistoricalDataForm1()
    if request.method == 'POST' and check_form.validate_on_submit():
        brand = check_form.brandd.data
        specific_pasta = check_form.specific_pastad.data
        date = str(check_form.dated.data)
            # check if the year of date has 4 digits
        
        try:
            specific_pasta_int = int(specific_pasta)
            sales_date = datetime.strptime(date, '%Y-%m-%d').date()
        except ValueError as e:
            flash(f'Error: {str(e)}', 'error')
            return redirect(url_for('sales_management1'))

        pasta = db.session.query(Pasta).filter_by(brand=brand, specific_pasta=specific_pasta_int).first()
        if pasta:
            sales_record = db.session.query(SalesRecord).filter_by(pasta_id=pasta.pasta_id, date=sales_date).one_or_none()
            if sales_record:
                text = f"Pasta sales on{sales_date} is {sales_record.quantity} and is_promotion is {sales_record.is_promotion}"
                # Pass the sales_record to the template if needed
                return render_template('sales_management.html',text=text, sales_record=sales_record, check_form=check_form, add_form=add_form,form=form)
            else:
                flash('No sales record found for the given criteria.', 'info')
        else:
            text='Pasta details not found.'
            return render_template('sales_management.html', check_form=check_form,add_form=add_form, form=form,text=text)

    return render_template('sales_management.html', check_form=check_form,add_form=add_form, form=form)




@app.route('/add_sales_record', methods=['GET', 'POST'])
@token_required
def add_sales_record():
    add_form = AddSalesRecordForm()
    check_form = CheckHistoricalDataForm()  # Keep this form to pass into the render_template call
    form = CheckHistoricalDataForm1()
    if request.method == 'POST' and add_form.validate_on_submit():
        brand = add_form.brand.data
        specific_pasta = add_form.specific_pasta.data
        date = str(add_form.date.data)
        sales = add_form.sales.data
        promotion = add_form.promotion.data
        is_promotion = int(promotion)
        if not all([brand, specific_pasta, date, sales]):
            flash('All fields are required except promotion.', 'error')
            return redirect(url_for('add_sales_record'))
        # Check if the specific pasta ID exceeds its maximum for the selected brand
        if specific_pasta > MAX_PASTA_IDS[brand]:
            text= f'Specific Pasta ID for {brand} cannot exceed {MAX_PASTA_IDS[brand]}.'
            return render_template('sales_management.html', add_form=add_form, check_form=check_form,form=form,text=text)
        try:
            sales_date = datetime.strptime(date, '%Y-%m-%d').date()
        except ValueError:
            flash('Invalid date format. Use YYYY-MM-DD.', 'error')
            return redirect(url_for('add_sales_record'))
        
        pasta = db.session.query(Pasta).filter_by(brand=brand, specific_pasta=int(specific_pasta)).first()
        
        existing_sales_record = SalesRecord.query.filter_by(date=sales_date, pasta_id=(pasta.pasta_id-1)).first()
        if existing_sales_record:
            text = f'Sales record for the given date and pasta_id already exists, please check it again.'
            return render_template('sales_management.html', add_form=add_form, check_form=check_form, form=form,text=text)
        else:
            season= determine_season(sales_date)
            new_sales_record = SalesRecord(date=sales_date, pasta_id=(pasta.pasta_id-1), quantity=sales, is_promotion=is_promotion, season=season)
            
            db.session.add(new_sales_record)
            try:
                db.session.commit()
                text=f'New sales record added successfully,Added sales record for {brand}, Pasta {specific_pasta-1} on {sales_date}, Quantity: {sales}, Promotion: {is_promotion}.'
             
                return render_template('sales_management.html', add_form=add_form,check_form=check_form,form=form,text=text)
            except IntegrityError as e:
                db.session.rollback()
                error_info = str(e.orig) 
                flash(f'Could not add the sales record due to an integrity error: {error_info}', 'error')
                
    
    return render_template('sales_management.html', add_form=add_form, check_form=check_form,form=form)

# This function determines the pasta_id based on the brand and specific_pasta
def determine_pasta_id(brand, specific_pasta):
    # Define the starting pasta_id for each brand
    brand_start_ids = {'B1': 1, 'B2': 43, 'B3': 88, 'B4': 109}
    # Calculate the pasta_id based on the brand's starting ID and the specific pasta number
    pasta_id = brand_start_ids[brand] + specific_pasta - 1
    return pasta_id
# Define maximum pasta IDs for each brand
MAX_PASTA_IDS = {
    'B1': 42,
    'B2': 45,
    'B3': 21,
    'B4': 10,
}
def get_brand_for_pasta_id(pasta_id):
    """
    Mock-up function to determine the brand for the next pasta ID.
    Implement this based on your application's logic.
    """
    # Example: Determine the brand based on the pasta ID ranges.
    if pasta_id <= 42:
        return 'Brand1'
    elif pasta_id <= 87:  # Assuming 42 + 45 for Brand2
        return 'Brand2'
    elif pasta_id <= 108:  # Assuming 87 + 21 for Brand3
        return 'Brand3'
    else:
        return 'Brand4'


def determine_season(date):
    """Determine the season of the given date."""
    if date.month in [3, 4, 5]:
        return 'Spring'
    elif date.month in [6, 7, 8]:
        return 'Summer'
    elif date.month in [9, 10, 11]:
        return 'Autumn'
    else:
        return 'Winter'
    
@app.route('/delete_sales_record', methods=['POST'])
@token_required
def delete_sales_record_by_details():
    form = CheckHistoricalDataForm1()
    if form.validate_on_submit():
        brand = form.branddd.data
        specific_pasta = form.specific_pastadd.data
        date = str(form.datedd.data)
        
        try:
            specific_pasta_int = int(specific_pasta)
            sales_date = datetime.strptime(date, '%Y-%m-%d').date()
        except ValueError as e:
            flash(f'Error: {str(e)}', 'error')
            return redirect(url_for('sales_management1'))
        
        pasta_id = determine_pasta_id(brand, specific_pasta_int)
        sales_record = db.session.query(SalesRecord).filter_by(pasta_id=pasta_id, date=sales_date).one_or_none()
        
        if sales_record:
            db.session.delete(sales_record)
            db.session.commit()
            flash(f"successful, Deleted sales record for {brand}, Pasta {specific_pasta} on {sales_date}", 'success')
        else:
            flash('Sales record not found.', 'info')
            
    return redirect(url_for('sales_management1'))


@app.route('/sales_by_season', methods=['GET', 'POST'])
@token_required
def sales_by_season():
    form = SalesBySeasonForm()
    if request.method == 'POST' and form.validate_on_submit():
        brand = form.brand.data
        specific_pasta = form.specific_pasta.data
        year = form.year.data
        
        is_valid_year, error_message = validate_year_format(year)
        if not is_valid_year:
            flash(error_message, 'error')
            return render_template('sales_by_season.html', form=form)
        
        pasta = db.session.query(Pasta).filter_by(brand=brand, specific_pasta=specific_pasta).first()
        if not pasta:
            flash('Pasta details not found.', 'error')
            return render_template('sales_by_season.html', form=form)

        data, total_yearly_sales, total_promotions = calculate_sales_and_promotions(pasta.pasta_id, year)
        text = f'The total sales in {year} is {total_yearly_sales}, and total promotions is {total_promotions}'

        fig = px.bar(data, x='Season', y='Sales', title=f'Sales for {brand} - Specific Pasta {specific_pasta} in {year}', labels={'Sales': 'Total Sales'}, color='Season', barmode='group')
        graph_html = fig.to_html(full_html=False)
        
        return render_template('sales_by_season.html', graph_html=graph_html, form=form, text=text)
    
    return render_template('sales_by_season.html', form=form)



def calculate_sales_and_promotions(pasta_id, year):
    date_start = f'{year}-01-01'
    date_end = f'{year}-12-31'
    data = []
    total_yearly_sales = 0
    total_promotions = 0
    for season in ['Spring', 'Summer', 'Autumn', 'Winter']:
        season_sales = db.session.query(db.func.sum(SalesRecord.quantity)) \
            .filter_by(pasta_id=pasta_id, season=season) \
            .filter(SalesRecord.date.between(date_start, date_end)) \
            .scalar() or 0
        data.append({'Season': season, 'Sales': season_sales})
        total_yearly_sales += season_sales

        season_promotions = db.session.query(db.func.count(SalesRecord.is_promotion)) \
            .filter_by(pasta_id=pasta_id, season=season, is_promotion=1) \
            .filter(SalesRecord.date.between(date_start, date_end)) \
            .scalar() or 0
        total_promotions += season_promotions
    return data, total_yearly_sales, total_promotions


def validate_year_format(year):
    year_str = str(year)
    if len(year_str) != 4 or not year_str.isdigit():
        return False, 'Invalid year format. Please enter a four-digit year.'
    try:
        datetime.strptime(year_str, '%Y')
        return True, None
    except ValueError:
        return False, 'Error parsing year. Please ensure it is a valid year.'



@app.context_processor
def inject_latest_date():
    # Assuming `id` is your auto-incremented primary key
    last_record = SalesRecord.query.order_by(SalesRecord.sales_id.desc()).first()
    if last_record:
        latest_date = last_record.date.strftime('%Y-%m-%d')
    else:
        latest_date = 'No data available'
    print(f'Latest date is: {latest_date}')  # For debugging
    return {'latest_date': latest_date}