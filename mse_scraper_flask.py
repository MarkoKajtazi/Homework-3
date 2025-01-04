import os.path
from _pydatetime import timedelta
from concurrent.futures import ThreadPoolExecutor
from xmlrpc.client import DateTime

import numpy as np
from bs4 import BeautifulSoup
import requests
import pandas as pd
from datetime import datetime, timedelta
import time

from ta.momentum import RSIIndicator
from ta.trend import SMAIndicator, EMAIndicator
from ta.volatility import BollingerBands
from ta.volume import OnBalanceVolumeIndicator

from flask import Flask, jsonify, request, abort
from flask_cors import CORS

from sklearn.model_selection import train_test_split
from tensorflow.keras.callbacks import EarlyStopping

from sklearn.preprocessing import MinMaxScaler

from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout

app = Flask(__name__)
CORS(app)

pd.set_option('display.max_columns', None)

def fetch_issuers_codes(base_url, url_history):
    response = requests.get(base_url)
    html = response.text
    soup = BeautifulSoup(html, 'html.parser')
    first_issuer = soup.select_one("#otherlisting-table > tbody > tr > td:nth-of-type(1)").text

    response = requests.get(url_history + first_issuer)
    html = response.text
    soup = BeautifulSoup(html, 'html.parser')

    element_codes = soup.select("#Code > option")
    issuers_codes = []
    for code in element_codes:
        if not any(char.isdigit() for char in code.text):
            issuers_codes.append(code.text)

    return issuers_codes


def fetch_issuer_data(code, from_date, to_date):
    url = (
        f"https://www.mse.mk/mk/stats/symbolhistory/{code}"
        f"?FromDate={from_date.strftime('%d.%m.%Y')}"
        f"&ToDate={to_date.strftime('%d.%m.%Y')}"
    )

    response = requests.get(url)
    html = response.text
    soup = BeautifulSoup(html, 'html.parser')

    element_data_rows = soup.select("#resultsTable tbody tr")
    matrix = []
    for row in element_data_rows:
        data = [code]
        for cell in row.select("td"):
            data.append(cell.text)

        matrix.append(data)

    return matrix
def fetch_issuers_history_sync(issuers_codes):
    current_date = datetime.now()

    for code in issuers_codes:
        from_date = current_date - timedelta(days=365 * 10)
        matrix = []
        while from_date <= current_date:
            to_date = from_date + timedelta(days=365)
            matrix.extend(fetch_issuer_data(code, from_date, to_date))
            from_date = to_date

        columns = ['Company Code', 'Date', 'Price of last transaction (mkd)', 'Max', 'Min', 'Average Price', '%change.', 'Quantity', 'Volume in BEST in denars', 'Total volume in denars']
        data_frame = pd.DataFrame(matrix, columns=columns)
        data_frame.to_csv("data/data_frame_" + code + ".csv", index=False)

        print(f"Data for {code} saved with {data_frame.shape[0]} rows")

def fetch_issuers_history_threads(issuers_codes):
    current_date = datetime.now()

    def process_issuer(code):
        from_date = current_date - timedelta(days=365 * 10)
        matrix = []

        while from_date < current_date:
            to_date = from_date + timedelta(days=365)
            matrix.extend(fetch_issuer_data(code, from_date, to_date))
            from_date = to_date

        columns = ['Company Code', 'Date', 'Price of last transaction (mkd)', 'Max', 'Min', 'Average Price', '%change.', 'Quantity', 'Turnover in BEST in denars', 'Total turnover in denars']
        data_frame = pd.DataFrame(matrix, columns=columns)
        data_frame['Date'] = pd.to_datetime(data_frame['Date'], format='%d.%m.%Y')
        data_frame.sort_values(by='Date', ascending=True, inplace=True)

        data_frame = data_frame.replace('', pd.NA)
        data_frame = data_frame.replace('', pd.NA)

        data_frame['Price of last transaction (mkd)'] = data_frame['Price of last transaction (mkd)'].dropna()


        data_frame.to_csv("data/data_frame_" + code + ".csv", index=False)
        print(f"Data for {code} saved with {data_frame.shape[0]} rows")

    with ThreadPoolExecutor(max_workers=10) as executor:
        executor.map(process_issuer, issuers_codes)

    merge_companies_data(issuers_codes)

def merge_companies_data(issuers_codes):
    data = pd.DataFrame()

    for code in issuers_codes:
        current_data = pd.read_csv(f"data/data_frame_{code}.csv")
        data = pd.concat([data, current_data], ignore_index=True, axis=0)

    data.to_csv("data/companies_data.csv", index=False)

def merge_combined_companies_data(issuers_codes):
    data = pd.DataFrame()

    for code in issuers_codes:
        current_data = pd.read_csv(f"data/combined_data_frame_{code}.csv")
        data = pd.concat([data, current_data], ignore_index=True, axis=0)

    data.to_csv("data/combined_companies_data.csv", index=False)

def get_last_available_date(issuer_code):
    file_path = "data/data_frame_" + issuer_code + ".csv"
    if not os.path.exists(file_path):
        return None

    df = pd.read_csv(file_path)
    df["Date"] = pd.to_datetime(df["Date"])
    available_date = df['Date'].max().date()

    return available_date


def check_last_update(issuer_codes):
    empty_codes = []
    for issuer_code in issuer_codes:
        last_available = get_last_available_date(issuer_code)
        if (last_available != datetime.today().date() and datetime.today().weekday() <= 5) or last_available is None:
            empty_codes.append(issuer_code)

    fetch_issuers_history_threads(empty_codes)


def calculate_technical_indicators(df):
    indicators = {}

    indicators['SMA_20'] = SMAIndicator(df['Close'], window=20).sma_indicator()
    indicators['SMA_50'] = SMAIndicator(df['Close'], window=50).sma_indicator()
    indicators['EMA_20'] = EMAIndicator(df['Close'], window=20).ema_indicator()
    indicators['EMA_50'] = EMAIndicator(df['Close'], window=50).ema_indicator()
    indicators['BB_Mid'] = BollingerBands(df['Close'], window=20).bollinger_mavg()

    indicators['RSI'] = RSIIndicator(df['Close'], window=14).rsi()
    indicators['OBV'] = OnBalanceVolumeIndicator(df['Close'], df['Volume']).on_balance_volume()
    indicators['Momentum'] = df['Close'].diff(periods=10)

    for name, values in indicators.items():
        df[name] = values

    print(f"Indicators columns: {df.columns}")

    return df

def generate_signals(df):
    df['Buy_Signal'] = (df['SMA_20'] > df['SMA_50']) & (df['RSI'] < 30)
    df['Sell_Signal'] = (df['SMA_20'] < df['SMA_50']) & (df['RSI'] > 70)
    return df

# Function to create sequences for LSTM model
def create_sequences(df, window=60):
    features = ['Close', 'SMA_20', 'SMA_50', 'EMA_20', 'EMA_50', 'RSI', 'OBV', 'Momentum']
    df = df[features].dropna()

    if df.empty:
        raise ValueError("The DataFrame is empty after dropping NaN values.")

    print("Data types:\n", df.dtypes)
    print("Data summary:\n", df.describe())

    # Normalize the data
    scaler = MinMaxScaler(feature_range=(0, 1))
    try:
        scaled_data = scaler.fit_transform(df)
    except ValueError as e:
        print(f"Error during scaling: {e}")
        print(df.head())
        raise

    X, y = [], []
    for i in range(window, len(scaled_data)):
        X.append(scaled_data[i - window:i])  # sequence of past prices
        y.append(scaled_data[i, 0])  # next day's price (Close)

    return np.array(X), np.array(y), scaler


def build_lstm_model(input_shape):
    model = Sequential()
    model.add(LSTM(units=64, return_sequences=True, input_shape=input_shape))
    model.add(Dropout(0.2))
    model.add(LSTM(units=64, return_sequences=True))
    model.add(Dropout(0.2))
    model.add(LSTM(units=32, return_sequences=False))
    model.add(Dropout(0.2))
    model.add(Dense(units=16, activation='relu'))
    model.add(Dense(units=1))
    model.compile(optimizer='adam', loss='mean_squared_error', metrics=['mae'])
    return model

def train_lstm_model(df):
    X, y, scaler = create_sequences(df)

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, shuffle=False)

    model = build_lstm_model(X_train.shape[1:])

    early_stopping = EarlyStopping(monitor='val_loss', patience=15, restore_best_weights=True)

    model.fit(X_train, y_train, epochs=100, batch_size=32, validation_data=(X_test, y_test), callbacks=[early_stopping])

    return model, scaler, X_test, y_test


def evaluate_and_predict(model, scaler, X_test, y_test):
    predictions = model.predict(X_test)

    predictions = scaler.inverse_transform(np.hstack((predictions, np.zeros((predictions.shape[0], X_test.shape[2]-1)))))[:,0]

    rmse = np.sqrt(np.mean((predictions - y_test)**2))
    print(f"Root Mean Squared Error: {rmse}")

    return predictions


def analyze_stock(file_path):
    df = pd.read_csv(file_path)

    df = df.replace('', pd.NA)
    df = df.replace('', pd.NA)

    df['Date'] = pd.to_datetime(df['Date'])
    df.set_index('Date', inplace=True)

    if df.index.duplicated().any():
        df = df.reset_index().drop_duplicates(subset='Date').set_index('Date')

    df['Price of last transaction (mkd)'] = df['Price of last transaction (mkd)'].dropna()

    df['Price of last transaction (mkd)'] = df['Price of last transaction (mkd)'].astype(str)
    df['Max'] = df['Max'].astype(str)
    df['Min'] = df['Min'].astype(str)
    df['Turnover in BEST in denars'] = df['Turnover in BEST in denars'].astype(str)

    df['Price of last transaction (mkd)'] = df['Price of last transaction (mkd)'].str.replace('.', '', regex=False).str.replace(',', '.').astype(float)
    df['Max'] = df['Max'].str.replace('.', '', regex=False).str.replace(',', '.').astype(float)
    df['Min'] = df['Min'].str.replace('.', '', regex=False).str.replace(',', '.').astype(float)
    df['Turnover in BEST in denars'] = df['Turnover in BEST in denars'].str.replace('.', '',regex=False).str.replace(',', '.').astype(float)

    df['Min'] = df['Min'].fillna(df['Price of last transaction (mkd)'])
    df['Max'] = df['Max'].fillna(df['Price of last transaction (mkd)'])

    df.rename(columns={
        'Price of last transaction (mkd)': 'Close',
        'Max': 'High',
        'Min': 'Low',
        'Turnover in BEST in denars': 'Volume'
    }, inplace=True)

    df = df[['Close', 'High', 'Low', 'Volume']].dropna()

    df = calculate_technical_indicators(df)

    df = generate_signals(df)

    df.dropna(inplace=True)

    output_file = file_path.replace('.csv', '_analysis.csv')
    df.to_csv(output_file)
    print(f"Analysis completed for {file_path}, saved as {output_file}")


def combine_data_and_analysis(code):
    data_file = f"data/data_frame_{code}.csv"
    analysis_file = f"data/data_frame_{code}_analysis.csv"
    combined_file = f"demo/src/main/resources/combined_data_frame_{code}.csv"

    if not os.path.exists(data_file):
        print(f"Data file for {code} not found.")
        return

    if not os.path.exists(analysis_file):
        print(f"Analysis file for {code} not found.")
        return

    data_df = pd.read_csv(data_file)
    analysis_df = pd.read_csv(analysis_file)

    data_df['Price of last transaction (mkd)'] = data_df['Price of last transaction (mkd)'].astype(str)
    data_df['Max'] = data_df['Max'].astype(str)
    data_df['Min'] = data_df['Min'].astype(str)
    data_df['Turnover in BEST in denars'] = data_df['Turnover in BEST in denars'].astype(str)

    data_df['Price of last transaction (mkd)'] = data_df['Price of last transaction (mkd)'].str.replace('.', '',regex=False).str.replace(',', '.').astype(float)
    data_df['Max'] = data_df['Max'].str.replace('.', '', regex=False).str.replace(',', '.').astype(float)
    data_df['Min'] = data_df['Min'].str.replace('.', '', regex=False).str.replace(',', '.').astype(float)
    data_df['Turnover in BEST in denars'] = data_df['Turnover in BEST in denars'].str.replace('.', '', regex=False).str.replace(',', '.').astype(float)

    data_df['Date'] = pd.to_datetime(data_df['Date'])
    analysis_df['Date'] = pd.to_datetime(analysis_df['Date'])

    combined_df = pd.merge(data_df, analysis_df, on='Date', how='inner')

    if 'Company Code' not in combined_df.columns:
        combined_df.insert(0, 'Company Code', code)

    column_order = [
        'Company Code', 'Date', 'Close', 'High', 'Low',
        'Average Price', '%change.', 'Quantity', 'Turnover in BEST in denars',
        'Total turnover in denars', 'SMA_20', 'SMA_50', 'EMA_20', 'EMA_50',
        'BB_Mid', 'RSI', 'OBV', 'Momentum', 'Buy_Signal', 'Sell_Signal'
    ]

    combined_df = combined_df[column_order]

    combined_df.rename(columns={
        'Close': 'Price of last transaction (mkd)',
        'High': 'Max',
        'Low': 'Min'
    }, inplace=True)

    combined_df.to_csv(combined_file, index=False)

    print(f"Combined data and analysis saved as {combined_file}")

def main():
    base_url = "https://www.mse.mk/mk/issuers/free-market"
    url_history = 'https://www.mse.mk/mk/stats/symbolhistory/'

    codes = fetch_issuers_codes(base_url, url_history)

    if not os.path.exists("data"):
        os.mkdir("data")
        fetch_issuers_history_threads(codes)
    else:
        check_last_update(codes)

    input_files_paths = []
    for code in codes:
        path = f"data/data_frame_{code}.csv"
        input_files_paths.append(path)

    for file_path in input_files_paths:
        analyze_stock(file_path)

    for code in codes:
        combine_data_and_analysis(code)

    # for code in codes:
    #     print(code)
    #     df = pd.read_csv(f'data/data_frame_{code}_analysis.csv')
    #     print(df.isnull().sum(), '\n')



@app.route("/api/data/<string:issuer_code>", methods=["GET"])
def get_issuer_data(issuer_code):
    file_path = f"demo/src/main/resources/combined_data_frame_{issuer_code}.csv"
    if not os.path.exists(file_path):
        return abort(404, description=f"Data for issuer code {issuer_code} not found.")

    df = pd.read_csv(file_path)
    return df.to_json(orient="records")

@app.route("/api/companies", methods=["GET"])
def get_company_codes():
    codes = fetch_issuers_codes("https://www.mse.mk/mk/issuers/free-market", 'https://www.mse.mk/mk/stats/symbolhistory/')
    return jsonify(codes)

@app.route("/api/update", methods=["GET"])
def update_data():
    main()
    return "Data updated successfully", 200


@app.route("/api/predict/<string:issuer_code>", methods=["GET"])
def get_prediction(issuer_code):
    # Read the historical data and the analysis data for the issuer
    df = pd.read_csv(f"data/data_frame_{issuer_code}_analysis.csv")

    # Train the LSTM model on the historical data
    model, scaler, X_test, y_test = train_lstm_model(df)

    # Evaluate the model and get predictions for the test set
    predictions = evaluate_and_predict(model, scaler, X_test, y_test)

    # Initialize the prediction column in the DataFrame
    df['Predicted_Price'] = np.nan
    df.iloc[-len(predictions):, df.columns.get_loc('Predicted_Price')] = predictions

    # Get the last sequence of data to predict the next two days
    last_sequence = df[['Close', 'SMA_20', 'SMA_50', 'EMA_20', 'EMA_50', 'RSI', 'OBV', 'Momentum']].iloc[-1:].copy()
    last_sequence_scaled = scaler.transform(last_sequence)

    # Predict the next day (Day 1)
    next_day_1 = model.predict(
        last_sequence_scaled.reshape(1, last_sequence_scaled.shape[0], last_sequence_scaled.shape[1]))
    next_day_1 = scaler.inverse_transform(
        np.hstack((next_day_1, np.zeros((next_day_1.shape[0], last_sequence_scaled.shape[1] - 1)))))[:, 0]

    last_date = pd.to_datetime(df['Date'].iloc[-1])

    # Add the prediction for the next day
    next_day_1_predicted_df = pd.DataFrame({
        'Date': [last_date + timedelta(days=1)],
        'Predicted_Price': [next_day_1[0]],
        'Buy_Signal': [np.nan],  # Optionally, you can add logic to generate a signal for the next day
        'Sell_Signal': [np.nan]  # Optionally, you can add logic to generate a signal for the next day
    })

    # Now predict the second day based on the first prediction
    # Append the predicted next day data and update the sequence
    last_sequence.iloc[0, 0] = next_day_1[0]  # Update 'Close' for the next day
    last_sequence_scaled = scaler.transform(last_sequence)

    # Predict the second day (Day 2)
    next_day_2 = model.predict(
        last_sequence_scaled.reshape(1, last_sequence_scaled.shape[0], last_sequence_scaled.shape[1]))
    next_day_2 = scaler.inverse_transform(
        np.hstack((next_day_2, np.zeros((next_day_2.shape[0], last_sequence_scaled.shape[1] - 1)))))[:, 0]

    # Add the prediction for the second next day
    next_day_2_predicted_df = pd.DataFrame({
        'Date': [last_date + timedelta(days=1)],
        'Predicted_Price': [next_day_2[0]],
        'Buy_Signal': [np.nan],  # Optionally, you can add logic to generate a signal for the second next day
        'Sell_Signal': [np.nan]  # Optionally, you can add logic to generate a signal for the second next day
    })

    next_day_2_predicted_df['Date'] = next_day_2_predicted_df['Date'].dt.strftime('%Y-%m-%d')
    next_day_1_predicted_df['Date'] = next_day_1_predicted_df['Date'].dt.strftime('%Y-%m-%d')


    # Combine the historical data with the predictions for the next two days
    predictions_df = pd.concat([df, next_day_1_predicted_df, next_day_2_predicted_df], ignore_index=True)

    # Return the data as JSON
    return predictions_df.to_json(orient="records")


if __name__ == "__main__":
    start_time = time.time()
    main()
    end_time = time.time()
    print(start_time, end_time, (end_time - start_time) / 60)
    app.run(port=5000)
