# Backtesting Project: RSI Trading Strategy

The following project was conducted in order to test the BackTrader library. Prior to this, previous algo trading strategies were tested using quick backtest which investigated the profit/loss following a signal. Having recently come across the BackTrader backtesting library, I was interested in implementing the framework to test ease of use and accuracy. This project implements a backtesting framework for analysing the performance of a simple multi-order RSI-based mean reversion trading strategy. Selling at overbought levels (70) and buying at oversold (30).

## Installation

1.  **Clone the Repository**
    ```bash
    git clone https://github.com/johnnyy-f/backtesting-project.git
    cd backtesting-project
    ```
2.  **Create a Virtual Environment**
    ```bash
    python -m venv .venv
    source .venv/bin/activate  # On Windows: .venv\Scripts\activate
    ```
3.  **Install Dependencies**
    ```bash
    pip install -r requirements.txt
    ```

## Configuration

This project requires environment variables for API keys from OANDA to access instrument data.

1.  Create a file named `.env` in the root directory.
2.  Fill in your specific credentials e.g.:

OANDA_ACCOUNT_ID='INSERT ACCOUNT ID HERE'
OANDA_API_KEY='INSERT API KEY HERE'

These can be obtained through creating a free demo account with Oanda.

## Results and analysis

### Running the Backtest

Execute the note book:

RSI_TRADING_STRATEGY_ANALYSIS.ipynb 

Simply running this notebook as is will create a backtest strategy for NATGAS_USD for the period: 03-11-2025 to 27-11-2025. To investigate yourself, you may alter the instrument according to availability as shown by 'print_acceptable_instruments()' as well as change dates to liking.

The notebook was conducted mainly to play around with the BackTrader library understanding its ease of use and to see whether using a simple RSI strategy could be profitable. With this being said, further studies need to conducted looking at numerous different time frames and investigating combining with other strategies such as Bollinger Bandsl.

For now I'll park this project as I focus on projects that will help propel my Data Science career being currently unemployed.

To do:
- Drawdown Calcs
- Fix Sharpe Calcs
- Add bollinger bands and compare
- Conduct over multiple different time frames to check for consistency of profit. 
- Look at other instruments which tend to work with indicators better. Avoid macroevents time periods.
