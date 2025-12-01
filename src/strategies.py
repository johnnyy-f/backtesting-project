import backtrader as bt
import pandas as pd


# =============================================================
# MULTI-ORDER RSI STRATEGY
# =============================================================
class MultiOrderRSI(bt.Strategy):
    params = dict(
        rsi_period=14,
        buy_rsi=30,  # open buys below this
        sell_rsi=70,  # open sells above this
        exit_buy_rsi=70,  # close buys here
        exit_sell_rsi=30,  # close sells here
    )

    def __init__(self):
        self.rsi = bt.indicators.RSI(self.data.close, period=self.p.rsi_period)
        # Track trades manually
        self.open_positions = []  # list of dicts for open trades
        self.closed_positions = []  # completed trades

    # ---------------------------------------------------------
    # MAIN LOGIC: ENTRY & EXIT
    # ---------------------------------------------------------
    def next(self):
        rsi = self.rsi[0]
        price = self.data.close[0]
        now = self.data.datetime.datetime(0)

        # --------------------------
        # 1. OPEN BUY ORDERS BELOW BUY RSI
        # --------------------------
        if rsi < self.p.buy_rsi:
            order = self.buy()
            self.open_positions.append(
                {
                    "type": "long",
                    "entry_rsi": rsi,
                    "entry_price": price,
                    "entry_time": now,
                    "order_ref": order,
                }
            )

        # --------------------------
        # 2. OPEN SELL ORDERS ABOVE SELL RSI
        # --------------------------
        if rsi > self.p.sell_rsi:
            order = self.sell()
            self.open_positions.append(
                {
                    "type": "short",
                    "entry_rsi": rsi,
                    "entry_price": price,
                    "entry_time": now,
                    "order_ref": order,
                }
            )

        # --------------------------
        # 3. CHECK EXIT CONDITIONS
        # --------------------------
        positions_to_close = []

        for pos in self.open_positions:
            # Close long trades when RSI exceeds exit_buy_rsi
            if pos["type"] == "long" and rsi > self.p.exit_buy_rsi:
                order = self.sell()
                positions_to_close.append((pos, order))

            # Close short trades when RSI drops below exit_sell_rsi
            if pos["type"] == "short" and rsi < self.p.exit_sell_rsi:
                order = self.buy()
                positions_to_close.append((pos, order))

        # Move closed trades to closed_positions
        for pos, order in positions_to_close:
            pos["exit_order"] = order
            pos["exit_rsi"] = rsi
            pos["exit_time"] = now
            pos["exit_price"] = price

            # Calculate PnL
            if pos["type"] == "long":
                pos["pnl"] = pos["exit_price"] - pos["entry_price"]
            else:
                pos["pnl"] = pos["entry_price"] - pos["exit_price"]

            self.closed_positions.append(pos)
            self.open_positions.remove(pos)

    # ---------------------------------------------------------
    # ORDER NOTIFICATION
    # ---------------------------------------------------------
    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            return  # Nothing to do

        if order.status in [order.Completed]:
            if order.isbuy():
                print(
                    f"BUY EXECUTED @ {order.executed.price:.4f} | RSI {self.rsi[0]:.2f}"
                )
            else:
                print(
                    f"SELL EXECUTED @ {order.executed.price:.4f} | RSI {self.rsi[0]:.2f}"
                )

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            print("Order Canceled/Margin/Rejected")
