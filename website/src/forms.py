# forms.py
from flask_wtf import FlaskForm
from wtforms.validators import DataRequired
from wtforms import StringField, SelectField, SubmitField, IntegerField, DateField, BooleanField

class PredictionForm(FlaskForm):
    brand = SelectField('Brand', choices=[('B1', 'B1'), ('B2', 'B2'), ('B3', 'B3'), ('B4', 'B4')], validators=[DataRequired()])
    pasta_number = StringField('Pasta Number', validators=[DataRequired()])
    prediction_period = SelectField('Prediction Period', choices=[('1', 'Next One Week'), ('4', 'Next One Month'), ('52', 'Next One Year')], validators=[DataRequired()])
    submit = SubmitField('Predict')

class CheckHistoricalDataForm(FlaskForm):
    brandd = SelectField('Brand', choices=[('B1', 'Brand 1'), ('B2', 'Brand 2'), ('B3', 'Brand 3'), ('B4', 'Brand 4')], validators=[DataRequired()])
    specific_pastad = IntegerField('Pasta Number', validators=[DataRequired()])
    dated = DateField('Date', format='%Y-%m-%d', validators=[DataRequired()])
    submit = SubmitField('Search', name='search')

class CheckHistoricalDataForm_delete(FlaskForm):
    branddd = SelectField('Brand', choices=[('B1', 'Brand 1'), ('B2', 'Brand 2'), ('B3', 'Brand 3'), ('B4', 'Brand 4')], validators=[DataRequired()])
    specific_pastadd = IntegerField('Pasta Number', validators=[DataRequired()])
    datedd = DateField('Date', format='%Y-%m-%d', validators=[DataRequired()])
    submit = SubmitField('Search', name='search')

class AddSalesRecordForm(FlaskForm):
    date = DateField('Date', format='%Y-%m-%d', validators=[DataRequired()])
    brand = SelectField('Brand', choices=[('B1', 'Brand 1'), ('B2', 'Brand 2'), ('B3', 'Brand 3'), ('B4', 'Brand 4')], validators=[DataRequired()])
    specific_pasta = IntegerField('Specific Pasta ID', validators=[DataRequired()])
    sales = IntegerField('Sales (Quantity)', validators=[DataRequired()])
    promotion = BooleanField('Promotion')
    submit = SubmitField('Submit', name='add')

class SalesBySeasonForm(FlaskForm):
    brand = SelectField('Brand', choices=[('B1', 'Brand 1'), ('B2', 'Brand 2'), ('B3', 'Brand 3'), ('B4', 'Brand 4')], validators=[DataRequired()])
    specific_pasta = IntegerField('Specific Pasta', validators=[DataRequired()])
    year = IntegerField('Year', validators=[DataRequired()])
    submit = SubmitField('Show Sales')