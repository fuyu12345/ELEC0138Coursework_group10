from pathlib import Path
import pandas as pd
from sklearn.linear_model import LinearRegression
import pickle

# Load the dataset
data = Path(__file__).parent.parent.joinpath("data", "processed_dataset1.csv")
df = pd.read_csv(data)

# Convert the 'DATE' column to datetime format
df['DATE'] = pd.to_datetime(df['DATE'])

# Filter the dataset for the years 2017 and 2018
df_2017 = df[(df['DATE'] >= '2017-01-01') & (df['DATE'] <= '2017-12-31')]
df_2018 = df[(df['DATE'] >= '2018-01-01') & (df['DATE'] <= '2018-12-31')]

# Prepare the features for 2017: sales for 'QTY_B1_1'
X_2017 = df_2017[['QTY_B1_1']]

# Prepare the target values
y_2018 = df_2018['QTY_B1_1']

# Train the Linear Regression model with the corrected setup
model_final = LinearRegression()
model_final.fit(X_2017, y_2018)

# Save the trained model
pickle_file = Path(__file__).parent.joinpath("model.pkl")
with open(pickle_file, "wb") as f:
    pickle.dump(model_final, f)