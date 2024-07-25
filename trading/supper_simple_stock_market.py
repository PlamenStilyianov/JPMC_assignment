from datetime import datetime, timedelta
from typing import List, Tuple

import numpy as np


class Stock:
    """ Stock class used for calculating dividend yield and P/E ratio"""

    def __init__(self, symbol: str, par_value: int, stock_type: str, last_dividend: int = 0,
                 fixed_dividend: float = 0.0) -> None:
        self.symbol = symbol
        self.par_value = par_value
        self.type = stock_type
        self.last_dividend = last_dividend
        self.fixed_dividend = fixed_dividend

    def get_dividend_yield(self, price: int) -> float:
        """ Calculate the dividend yield, given any price as input. """
        if price <= 0:
            raise ValueError("Price must be greater than 0")

        if (self.fixed_dividend is not None and self.fixed_dividend <= 0.0 and self.type == 'Preferred' ) or (
                self.fixed_dividend is not None and self.last_dividend <= 0 and self.type == 'Common'):
            return 0.0

        dividend_yield = (self.fixed_dividend * self.par_value) / price \
            if self.type == 'Preferred' else (self.last_dividend / price)

        return round(dividend_yield, 4)

    def get_pe_ratio(self, price: int) -> float:
        """ Calculate the P/E Ratio, given any price as input. """

        if price <= 0:
            raise ValueError("Price must be greater than 0")

        if self.last_dividend <= 0:
            return 0.0

        pe_ratio = (price / self.last_dividend)
        return round(pe_ratio, 4)


class Trade:
    """ Trade class used to store trade records """

    def __init__(self, stock: Stock, timestamp: datetime, quantity: int, buy_or_sell: str, price: int) -> None:
        self.stock: Stock = stock
        self.timestamp = timestamp
        self.quantity = quantity
        self.buy_or_sell = buy_or_sell
        self.price = price


class StockMarket:
    """ StockMarket class used to book trades and calculate Volume Weighted Stock Price """
    __trades: List[Tuple[datetime, Trade]] = []

    def __init__(self):
        self._trades: List[Tuple[datetime, Trade]] = StockMarket.__trades

    @classmethod
    def book_trade(cls, stock: Stock, buy_or_sell: str, quantity: int = 0, price: int = 0) -> None:
        """ Record a trade, with timestamp, quantity, buy or sell indicator and price. """

        if quantity < 1 or price < 1:
            raise ValueError("Price and Quantity must be greater than 0")

        timestamp = datetime.now()
        trade = Trade(stock, timestamp, quantity, buy_or_sell, price)
        record = (trade.timestamp, trade)
        cls.__trades.append(record)

    @classmethod
    def calculate_VWSP(cls, symbol: str, minutes: int = 5) -> float:
        """ Calculate Volume Weighted Stock Price based on trades in past 5 minutes. """

        if len(cls.__trades) == 0:
            raise ValueError("No trades booked for this market")

        if minutes > 0:
            timestamp = datetime.now() - timedelta(minutes=minutes)
            trades = [trade[1] for trade in reversed(cls.__trades) if
                      trade[0] >= timestamp and trade[1].stock.symbol == symbol]
        else:
            trades = [trade[1] for trade in StockMarket.__trades if trade[1].stock.symbol == symbol]

        price_qty = sum([trade.price * trade.quantity for trade in trades])
        sum_qty = sum([trade.quantity for trade in trades])
        return round((price_qty / sum_qty), 4)


class GlobalBeverageCorporationExchange(StockMarket):
    """ The Global Beverage Corporation Exchange is a new stock market trading in drinks companies """

    def __init__(self):
        super().__init__()

    def all_stock_index(self) -> float:
        """ All Share Index using the geometric mean of the Volume Weighted Stock Price for all stocks """

        if len(self._trades) == 0:
            raise ValueError("No trades booked for this market")

        prices = [self.calculate_VWSP(trade[1].stock.symbol, 0) for trade in self._trades]
        prod = np.prod(np.array(prices), axis=0)
        return float(round(prod ** (1 / len(prices)), 4))
