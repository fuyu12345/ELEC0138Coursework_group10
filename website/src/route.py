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
from src.forms import PredictionForm,CheckHistoricalDataForm, AddSalesRecordForm, SalesBySeasonForm, CheckHistoricalDataForm_delete
import plotly.express as px
from src.functions_support_route import check_for_date_gaps, prepare_features, make_daily_predictions, get_period_label,\
generate_sales_chart, determine_pasta_id, determine_season, MAX_PASTA_IDS, validate_year_format, calculate_sales_and_promotions



@app.route('/', methods=['GET', 'POST'])
# @token_required
def index():
    """
    IT handles both GET and POST requests for the homepage.
    If the user is not logged in, they are redirected to the login page.
    For POST requests, if the form is valid, it processes a prediction.
    It queries the database for the specified pasta and its sales records to generate a sales prediction
    and a corresponding chart if no gaps in the sales data exist.

    Returns:
        The rendered homepage template with the prediction form, prediction text, and chart HTML as context.
    """
    # Check if user is logged in, otherwise redirect to login
    if 'user_id' not in session:
        return redirect(url_for('login'))

    # Initialize form and context variables
    form = PredictionForm()
    chart_html = ""
    prediction_text = ""

    # Process valid form submission
    if form.validate_on_submit() and request.method == 'POST':
        brand = form.brand.data
        specific_pasta = form.pasta_number.data
        future_time = form.prediction_period.data

        # Query the specified pasta
        pasta = Pasta.query.filter_by(brand=brand, specific_pasta=specific_pasta).first()

        if pasta:
            # Query sales records for the last year
            sales_records = SalesRecord.query.filter_by(pasta_id=pasta.pasta_id).order_by(SalesRecord.date.desc()).limit(365).all()
            
            if sales_records:
                # Check for data gaps
                if check_for_date_gaps(sales_records):
                    features = prepare_features(sales_records)
                    total_sales, daily_predictions = make_daily_predictions(features, future_time)
                    prediction_text = f"Predicted total sales for the next {get_period_label(future_time)}: {total_sales}"
                    
                    # Generate chart HTML
                    latest_date = sales_records[0].date
                    chart_html = generate_sales_chart(daily_predictions, latest_date, future_time)
                else:
                    flash("Predictor cannot work because there are gaps in the sales records' dates. Please ensure data continuity.", 'info')
            else:
                flash("No sales records found for the specified pasta.", 'info')
        else:
            flash("Specified pasta not found.", 'info')

    return render_template('index.html', form=form, prediction_text=prediction_text, chart_html=chart_html)






# AUTHENTICATION ROUTES
@app.route('/register', methods=['GET', 'POST'])
def register():
    """
    Handles both GET and POST requests for the user registration page.
    On POST, it attempts to register a new user with the provided email and password.
    If the email already exists, it redirects back to the registration page with a warning.
    Upon successful registration, the user is redirected to the login page with a success message.
    
    Returns:
        For GET requests, it renders the registration form.
        For POST requests, it redirects based on the outcome of the registration attempt.
    """
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        # Check if the email already exists
        user_exists = User.query.filter_by(email=email).first()

        if user_exists:
            flash('Email already exists. Please log in.', 'warning')
            return redirect(url_for('register'))

        try:
            # Create and add new user to the database
            new_user = User(email=email)
            new_user.set_password(password)  # This method hashes the password before storing it
            db.session.add(new_user)
            db.session.commit()

            flash('Successfully registered. Please log in.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            # Log the exception and flash an error message
            app.logger.error(f'Registration error: {e}')
            flash('An error occurred during registration. Please try again.', 'danger')
            return redirect(url_for('register'))

    # Render the registration form for GET requests
    return render_template('register.html')






@app.route('/login', methods=['GET', 'POST'])
def login():
    """
    Handles user login via both GET and POST requests.
    For POST requests, it verifies the user's email and password.
    If authentication is successful, it generates a token and stores it along with the user's ID in the session.
    Redirects to the index page upon successful login, or flashes an error message

    Returns:
        For GET requests, renders the login page.
        For POST requests, redirects to the page based on the outcome of the login attempt.
    """
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        # Validate form input
        if not email or not password:
            flash('Missing email or password.', 'danger')
            return redirect(url_for('login'))

        # Authenticate user
        user = db.session.query(User).filter_by(email=email).first()
        if not user or not user.check_password(password):
            flash('Incorrect email or password.', 'danger')
            return redirect(url_for('login'))

        # Generate authentication token
        token_response = encode_auth_token(user.id)
        if isinstance(token_response, str):  # Token generated successfully
            session['user_id'] = user.id  # Store user ID in session
            session['token'] = token_response  # Store token in session
            flash('Login successful!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Failed to generate authentication token.', 'error')
            return redirect(url_for('login'))

    # Render login page for GET request
    print("Session after login:", session)

    return render_template('login.html')





@app.route('/logout')
def logout():
    """
    Logs out the current user by removing their 'user_id' and 'token' from the session.
    After logging out, the user is redirected to the login page with a success message.

    Returns:
        A redirect to the login page.
    """
    # Remove 'user_id' and 'token' from session to log the user out
    session.pop('user_id', None)
    session.pop('token', None)

    flash('You have been logged out.', 'success')
    return redirect(url_for('login'))


@app.route('/reset_password', methods=['GET', 'POST'])
# @token_required
def reset_password():
    """
    Handles the password reset process for logged-in users. Users must be logged in to access this route.
    If accessed via POST, it attempts to reset the user's password if the old password is correctly provided..

    Returns:
        A redirect to the index page upon successful password reset,
        or the reset_password page with  error messages upon failure.
    """
    # Ensure user is logged in
    if 'user_id' not in session:
        flash('You must be logged in to reset your password.', 'warning')
        return redirect(url_for('login'))

    if request.method == 'POST':
        email = request.form.get('email')
        old_password = request.form.get('old_password')
        new_password = request.form.get('new_password')

        user = User.query.filter_by(email=email).first()

        if user and user.check_password(old_password):
            try:
                user.set_password(new_password)  # Assumes a method exists to hash and set new password
                db.session.commit()
                flash('Your password has been updated.', 'success')
                return redirect(url_for('index'))
            except Exception as e:
                db.session.rollback()  # Rollback in case of exception to avoid corrupting the DB
                app.logger.error(f'Error resetting password: {e}')
                flash('An error occurred while resetting your password. Please try again.', 'danger')
        else:
            flash('Invalid email or old password.', 'danger')

    return render_template('reset_password.html')




 
@app.route('/sales_management', methods=['GET'])
@token_required
def sales_management():
    """
    Renders the sales management page, which provides interfaces for checking historical sales data
    and adding new sales records. Three forms are made available on this page for different functionalities:

    Returns:
        The rendered 'sales_management.html' template with three form instances passed as context.
    """
    # Initialize forms
    check_form = CheckHistoricalDataForm()
    add_form = AddSalesRecordForm()
    form = CheckHistoricalDataForm_delete()

    # Render and return the sales management page with forms
    return render_template('sales_management.html', check_form=check_form, add_form=add_form, form=form)



@app.route("/sales_management1", methods=['GET', 'POST'])
@token_required
def sales_management1():
    """
    Handles both GET and POST requests for an enhanced sales management page.
    Allows users to check historical sales data, add new sales records, or delete existing ones.

    The function validates the submitted data, queries the database based on the input,
    and displays relevant sales information or errors as flash messages.

    Returns:
        The rendered 'sales_management.html' template with the forms and queried sales record.
    """
     # Keep these form to pass into the render_template call
    check_form = CheckHistoricalDataForm()
    add_form = AddSalesRecordForm() 
    form = CheckHistoricalDataForm_delete()
    if request.method == 'POST' and check_form.validate_on_submit():
        brand = check_form.brandd.data
        specific_pasta = check_form.specific_pastad.data
        date = str(check_form.dated.data)
        
        try:
            specific_pasta_int = int(specific_pasta)
            sales_date = datetime.strptime(date, '%Y-%m-%d').date()
        except ValueError as e:
            flash(f'Error: {str(e)}', 'error')
            return redirect(url_for('sales_management1'))

        pasta = db.session.query(Pasta).filter_by(brand=brand, specific_pasta=specific_pasta_int).first()
        if pasta:
            #use pasta_id to query the sales record
            sales_record = db.session.query(SalesRecord).filter_by(pasta_id=pasta.pasta_id, date=sales_date).one_or_none()
            if sales_record:
                text = f"Pasta sales on {sales_date} is {sales_record.quantity} and promotion condition is {sales_record.is_promotion} (1:Yes,0:No)"
                flash(text, 'success')
                return render_template('sales_management.html', sales_record=sales_record, check_form=check_form, add_form=add_form,form=form)
            else:
                flash('No sales record found for the given criteria.', 'info')
        else:
            text='Pasta details not found.'
            flash(text, 'danger')
            return render_template('sales_management.html', check_form=check_form,add_form=add_form, form=form)

    return render_template('sales_management.html', check_form=check_form,add_form=add_form, form=form)




@app.route('/add_sales_record', methods=['GET', 'POST'])
# @token_required
def add_sales_record():
    """
    Handles the addition of new sales records through a form submission. Validates the form data and
    checks for the existence of the specified pasta and any existing sales record for the given date.
    On successful validation and absence of duplicates, a new sales record is created and saved.

    Returns:
        The rendered 'sales_management.html' template, with forms for adding sales records,
    """
    add_form = AddSalesRecordForm()
    check_form = CheckHistoricalDataForm()  # Keep this form to pass into the render_template call
    form = CheckHistoricalDataForm_delete()

    if request.method == 'POST' and add_form.validate_on_submit():
        brand = add_form.brand.data
        specific_pasta = add_form.specific_pasta.data
        date = str(add_form.date.data)
        sales = add_form.sales.data
        promotion = add_form.promotion.data
        is_promotion = int(promotion)

        # Check if the specific pasta ID exceeds its maximum for the selected brand
        if specific_pasta > MAX_PASTA_IDS[brand]:
            text= f'Specific Pasta ID for {brand} cannot exceed {MAX_PASTA_IDS[brand]}.'
            flash(text, 'danger')
            return render_template('sales_management.html', add_form=add_form, check_form=check_form,form=form)
        
        try:
            # Convert the date string to a datetime object
            sales_date = datetime.strptime(date, '%Y-%m-%d').date()

        except ValueError:
            flash('Invalid date format. Use YYYY-MM-DD.', 'error')
            return redirect(url_for('add_sales_record'))
        
        pasta = db.session.query(Pasta).filter_by(brand=brand, specific_pasta=int(specific_pasta)).first()
        existing_sales_record = SalesRecord.query.filter_by(date=sales_date, pasta_id=(pasta.pasta_id-1)).first()

        # Check for an existing sales record for the given date and pasta ID
        if existing_sales_record:
            text = f'Sales record for the given date and pasta_id already exists, please check it again.'
            flash(text, 'danger')
            return render_template('sales_management.html', add_form=add_form, check_form=check_form, form=form)
        
        else:
            season= determine_season(sales_date)
            new_sales_record = SalesRecord(date=sales_date, pasta_id=(pasta.pasta_id-1), quantity=sales, is_promotion=is_promotion, season=season)
            db.session.add(new_sales_record)

            try:
                db.session.commit()
                text=f'New sales record added successfully,Added sales record for {brand}, Pasta {specific_pasta-1} on {sales_date}, Quantity: {sales}, Promotion: {is_promotion}.'
                flash(text, 'success')
                return render_template('sales_management.html', add_form=add_form,check_form=check_form,form=form)
            
            except IntegrityError as e:
                db.session.rollback()
                error_info = str(e.orig) 
                flash(f'Could not add the sales record due to an integrity error: {error_info}', 'error')
                
    return render_template('sales_management.html', add_form=add_form, check_form=check_form,form=form)


# @app.route('/add_sales_record', methods=['GET', 'POST'])
# def add_sales_record():
#     add_form = AddSalesRecordForm()
#     check_form = CheckHistoricalDataForm()
#     form = CheckHistoricalDataForm_delete()

#     # Allow POST from either form or raw payload
#     if request.method == 'POST':

#         # Try form-based input first
#         if add_form.validate_on_submit():
#             brand = add_form.brand.data
#             specific_pasta = add_form.specific_pasta.data
#             date = str(add_form.date.data)
#             sales = add_form.sales.data
#             promotion = add_form.promotion.data
#         else:
#             # Fallback: parse raw POST data (simulates attacker injection)
#             brand = request.form.get('brand')
#             specific_pasta = request.form.get('specific_pasta')
#             date = request.form.get('date')
#             sales = request.form.get('sales')
#             promotion = request.form.get('promotion')

#             if not (brand and specific_pasta and date and sales and promotion):
#                 flash('Missing one or more required fields.', 'danger')
#                 return render_template('sales_management.html', add_form=add_form, check_form=check_form, form=form)

#             try:
#                 specific_pasta = int(specific_pasta)
#                 sales = int(sales)
#                 is_promotion = int(promotion)
#                 sales_date = datetime.strptime(date, '%Y-%m-%d').date()
#             except Exception as e:
#                 flash(f'Invalid data format: {e}', 'danger')
#                 return render_template('sales_management.html', add_form=add_form, check_form=check_form, form=form)

#         # Check if pasta exists
#         pasta = db.session.query(Pasta).filter_by(brand=brand, specific_pasta=specific_pasta).first()
#         if not pasta:
#             flash('Pasta details not found.', 'danger')
#             return render_template('sales_management.html', add_form=add_form, check_form=check_form, form=form)

#         # Check if record already exists
#         existing_sales_record = SalesRecord.query.filter_by(date=sales_date, pasta_id=(pasta.pasta_id - 1)).first()
#         if existing_sales_record:
#             flash('Sales record for this pasta and date already exists.', 'danger')
#             return render_template('sales_management.html', add_form=add_form, check_form=check_form, form=form)

#         # All good — insert record
#         season = determine_season(sales_date)
#         new_sales_record = SalesRecord(
#             date=sales_date,
#             pasta_id=pasta.pasta_id - 1,
#             quantity=sales,
#             is_promotion=is_promotion,
#             season=season
#         )
#         db.session.add(new_sales_record)
#         try:
#             db.session.commit()
#             flash(f'New sales record added successfully: {brand}, Pasta {specific_pasta}, {sales_date}, Sales: {sales}, Promo: {promotion}', 'success')
#         except IntegrityError as e:
#             db.session.rollback()
#             flash(f'Integrity Error: {str(e.orig)}', 'danger')

#         return render_template('sales_management.html', add_form=add_form, check_form=check_form, form=form)

#     return render_template('sales_management.html', add_form=add_form, check_form=check_form, form=form)

  
@app.route('/delete_sales_record', methods=['POST'])
# @token_required
def delete_sales_record_by_details():
    """
    Deletes a sales record based on details provided through a form submission.
    Validates the form input and attempts to find and delete a sales record matching the criteria.
    Flashes success or failure messages based on the outcome of the deletion attempt.

    Returns:
        A redirect to the 'sales_management1' route, with messages.
    """
    form = CheckHistoricalDataForm_delete()

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
        
        # Check if the sales record exists and delete it
        if sales_record:
            db.session.delete(sales_record)
            db.session.commit()
            text=f"successful, Deleted sales record for {brand}, Pasta {specific_pasta} on {sales_date}"
            flash(text, 'success')
        else:
            flash('Sales record not found.', 'danger')
            
    return redirect(url_for('sales_management1'))




@app.route('/sales_by_season', methods=['GET', 'POST'])
# @token_required
def sales_by_season():
    """
    Displays a form to filter sales data by brand, specific pasta, and year. On form submission, validates the year format,
    checks for the existence of the specified pasta, and calculates sales and promotions data if valid.
    Generates a bar chart representing sales data by season if the provided details are correct.

    Returns:
        The 'sales_by_season.html' template rendered with the form and, upon valid submission,
        a bar chart of sales by season and corresponding data as context.
    """
    form = SalesBySeasonForm()
    if request.method == 'POST' and form.validate_on_submit():
        brand = form.brand.data
        specific_pasta = form.specific_pasta.data
        year = form.year.data
        
        # Validate the year format
        is_valid_year, error_message = validate_year_format(year)
        if not is_valid_year:
            flash(error_message, 'error')
            return render_template('sales_by_season.html', form=form)
        
        pasta = db.session.query(Pasta).filter_by(brand=brand, specific_pasta=specific_pasta).first()
        if not pasta:
            flash('Pasta details not found.', 'danger')
            return render_template('sales_by_season.html', form=form)  
        
        # the year enter, if the data is not complete
        if len(db.session.query(SalesRecord).filter(SalesRecord.date.between(f'{year}-01-01', f'{year}-12-31')).all()) < 320:
            flash(f'Not enough sales records for {year}.', 'info')
            return render_template('sales_by_season.html', form=form)
        
        data, total_yearly_sales, total_promotions = calculate_sales_and_promotions(pasta.pasta_id, year)
        text = f'The total sales in {year} is {total_yearly_sales}, and total promotions is {total_promotions}'
        flash(text, 'success')
        fig = px.bar(data, x='Season', y='Sales', title=f'Sales for {brand} - Specific Pasta {specific_pasta} in {year}',
                      labels={'Sales': 'Total Sales'}, color='Season', barmode='group')
        graph_html = fig.to_html(full_html=False)
        
        return render_template('sales_by_season.html', graph_html=graph_html, form=form)
    
    return render_template('sales_by_season.html', form=form)



@app.context_processor
def inject_latest_date():
    """
    A context processor to inject the 'latest_date' variable into the context of all templates.
    Retrieves the most recent date from SalesRecord entries. 

    Returns:
        A dictionary with 'latest_date' key and its value being the most recent date from SalesRecord entries
        formatted as 'YYYY-MM-DD' or a message indicating no data is available.
    """
    # Query the most recent date from the SalesRecord entries
    last_record = SalesRecord.query.order_by(SalesRecord.sales_id.desc()).first()
    if last_record:
        latest_date = last_record.date.strftime('%Y-%m-%d')
    else:
        latest_date = 'No data available'

    return {'latest_date': latest_date}




