import numpy as np
import pickle
from pathlib import Path
import pandas as pd
from datetime import timedelta
import plotly.express as px
from src import db
from datetime import datetime
from src.model import SalesRecord

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
            
            return False
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
    # start_date is expected to be a datetime.date object representing the latest date in your databas
    # Generate a date range starting from the day after the latest date in the database
    dates = pd.date_range(start=start_date + pd.Timedelta(days=1), periods=len(predictions), freq='D')
    data = pd.DataFrame({"Date": dates, "Sales": predictions})
    fig = px.line(data, x="Date", y="Sales")
   
    return fig.to_html(full_html=False, include_plotlyjs=True)


# This function determines the pasta_id based on the brand and specific_pasta
def determine_pasta_id(brand, specific_pasta):
    # Define the starting pasta_id for each brand
    brand_start_ids = {'B1': 1, 'B2': 43, 'B3': 88, 'B4': 109}
    # Calculate the pasta_id based on the brand's starting ID and the specific pasta number
    pasta_id = brand_start_ids[brand] + specific_pasta - 1
    return pasta_id


# Define maximum pasta IDs for each brand
MAX_PASTA_IDS = {'B1': 42,'B2': 45,'B3': 21,'B4': 10,}

def get_brand_for_pasta_id(pasta_id):
    """
    Mock-up function to determine the brand for the next pasta ID.
    Implement this based on your application's logic.
    """
    # Example: Determine the brand based on the pasta ID ranges.
    if pasta_id <= 42:
        return 'Brand1'
    elif pasta_id <= 87:  #42 + 45 for Brand2
        return 'Brand2'
    elif pasta_id <= 108:  #87 + 21 for Brand3
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
    

def calculate_sales_and_promotions(pasta_id, year):
    date_start = f'{year}-01-01'
    date_end = f'{year}-12-31'
    data = []
    total_yearly_sales = 0
    total_promotions = 0
    for season in ['Spring', 'Summer', 'Autumn', 'Winter']:
        # Calculate sales for the season
        season_sales = db.session.query(db.func.sum(SalesRecord.quantity)) \
            .filter_by(pasta_id=pasta_id, season=season) \
            .filter(SalesRecord.date.between(date_start, date_end)) \
            .scalar() or 0
        data.append({'Season': season, 'Sales': season_sales})
        total_yearly_sales += season_sales
        # Calculate promotions for the season
        season_promotions = db.session.query(db.func.count(SalesRecord.is_promotion)) \
            .filter_by(pasta_id=pasta_id, season=season, is_promotion=1) \
            .filter(SalesRecord.date.between(date_start, date_end)) \
            .scalar() or 0
        total_promotions += season_promotions
    return data, total_yearly_sales, total_promotions


def validate_year_format(year):
    year_str = str(year)
    # Check if the year is a four-digit number
    if len(year_str) != 4 or not year_str.isdigit():
        return False, 'Invalid year format. Please enter a four-digit year.'
    try:
        datetime.strptime(year_str, '%Y')
        return True, None
    except ValueError:
        return False, 'Error parsing year. Please ensure it is a valid year.'