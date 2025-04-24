import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from flask_marshmallow import Marshmallow


class Base(DeclarativeBase):
    pass
db = SQLAlchemy(model_class=Base)
# Create a global Flask-Marshmallow object
ma = Marshmallow()


def create_app(test_config=None):
    # create the Flask app
    app = Flask(__name__, instance_relative_config=True)
    # configure the Flask app (see later notes on how to generate your own SECRET_KEY)
    app.config.from_mapping(
        SECRET_KEY='Mcty7QLG95RMMi0Y1uEQ8A',
        # Set the location of the database file called pasta.sqlite which will be in the app's instance folder
        SQLALCHEMY_DATABASE_URI= "sqlite:///" + os.path.join(app.instance_path, 'pasta.sqlite'),  
    )

    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile('config.py', silent=True)
    else:
        # load the test config if passed in
        app.config.from_mapping(test_config)

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # Initialise Flask with the SQLAlchemy database extension
    db.init_app(app)
     # Initialise Flask-Marshmallow
    ma.init_app(app)

    # Models are defined in the models module, so you must import them before calling create_all, otherwise SQLAlchemy
    # will not know about them.
    from src.model import User, Pasta, SalesRecord
       
    with app.app_context():
        db.create_all()
        # Register the routes with the app in the context
        add_sales_record_data_from_csv()
        from src import route
    return app


import csv
from pathlib import Path
from datetime import datetime
from src.model import Pasta,SalesRecord 


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


def add_sales_record_data_from_csv():
    """Add sales record data from a CSV file to the database."""
    pasta_file = Path(__file__).resolve().parent.parent / "data" / "processed_dataset1.csv"
    
    with pasta_file.open('r') as file:
        csv_reader = csv.DictReader(file)
        for row in csv_reader:
            sale_date = datetime.strptime(row['DATE'], '%Y/%m/%d').date()
            season = determine_season(sale_date)

            existing_sales_record = db.session.query(SalesRecord).filter_by(date=sale_date).first()
            if existing_sales_record:
                continue  # Skip existing records to avoid duplicates
            
            for header, value in row.items():
                if header.startswith('QTY_') and value:
                    brand, specific = header.split('_')[1:]
                    existing_pasta = db.session.query(Pasta).filter_by(brand=brand, specific_pasta=specific).first()
                    if not existing_pasta:
                        new_pasta = Pasta(brand=brand, specific_pasta=specific)
                        db.session.add(new_pasta)
                        db.session.flush()  # Flush to get the pasta_id for the new pasta

                    pasta_id = existing_pasta.pasta_id if existing_pasta else new_pasta.pasta_id
                    is_promotion = int(row.get(f'PROMO_{brand}_{specific}', 0))

                    new_sales_record = SalesRecord(
                        date=sale_date,
                        quantity=int(value),
                        is_promotion=is_promotion,
                        season=season,
                        pasta_id=pasta_id
                    )
                    
                    db.session.add(new_sales_record)
        db.session.commit()