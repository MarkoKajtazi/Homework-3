import os.path
from _pydatetime import timedelta
from concurrent.futures import ThreadPoolExecutor

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
    # indicators['Stochastic'] = ((df['Close'] - df['Low'].rolling(window=14).min()) /
    #                             (df['High'].rolling(window=14).max() - df['Low'].rolling(window=14).min())) * 100

    for name, values in indicators.items():
        df[name] = values

    print(f"Indicators columns: {df.columns}")

    return df


def generate_signals(df):
    df['Buy_Signal'] = (df['SMA_20'] > df['SMA_50']) & (df['RSI'] < 30)
    df['Sell_Signal'] = (df['SMA_20'] < df['SMA_50']) & (df['RSI'] > 70)
    return df


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

    # Load the original data and analysis data
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

    # Merge on 'Date' after ensuring consistent date format
    data_df['Date'] = pd.to_datetime(data_df['Date'])
    analysis_df['Date'] = pd.to_datetime(analysis_df['Date'])

    combined_df = pd.merge(data_df, analysis_df, on='Date', how='inner')

    # Add 'Company Code' column if it doesn't already exist
    if 'Company Code' not in combined_df.columns:
        combined_df.insert(0, 'Company Code', code)

    # Specify the desired column order
    column_order = [
        'Company Code', 'Date', 'Price of last transaction (mkd)', 'Max', 'Min',
        'Average Price', '%change.', 'Quantity', 'Turnover in BEST in denars',
        'Total turnover in denars', 'SMA_20', 'SMA_50', 'EMA_20', 'EMA_50',
        'BB_Mid', 'RSI', 'OBV', 'Momentum', 'Buy_Signal', 'Sell_Signal'
    ]

    # Reorder and save the combined DataFrame
    combined_df = combined_df[column_order]
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


if __name__ == "__main__":
    start_time = time.time()
    main()
    end_time = time.time()
    print(start_time, end_time, (end_time - start_time) / 60)
    app.run(port=5000)
