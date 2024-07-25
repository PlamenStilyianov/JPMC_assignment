from unittest import mock

import pandas as pd
import pytest

from trading.supper_simple_stock_market import Stock, Trade, StockMarket, GlobalBeverageCorporationExchange, datetime, \
    timedelta


@pytest.fixture(scope='module')
def stock_data():
    return pd.DataFrame.from_dict({'Stock Symbol': ['TEA', 'POP', 'ALE', 'GIN', 'JOE'],
                                   'Stock Type': ['Common', 'Common', 'Common', 'Preferred', 'Common'],
                                   'Last Dividend': [0, 8, 23, 8, 13],
                                   'Fixed Dividend': [None, None, None, 0.02, None],
                                   'Par Value': [100, 100, 60, 100, 250]},
                                  ).values.tolist()


@pytest.fixture(scope='module')
def stocks(stock_data):
    gen_stock = []
    for _ in range(7):
        stock = (Stock(symbol=stock[0], par_value=stock[4], stock_type=stock[1], last_dividend=stock[2],
                       fixed_dividend=stock[3]) for stock in stock_data)
        gen_stock.append(stock)

    return gen_stock


@pytest.fixture(scope='module')
def stocks_missing_data():
    stocks = []
    stocks.extend([Stock(symbol='TEA', par_value=100, stock_type='Common', last_dividend=0, fixed_dividend=None),
                   Stock(symbol='TEA', par_value=100, stock_type='Common', last_dividend=0),
                   Stock(symbol='GIN', par_value=100, stock_type='Preferred', last_dividend=0, fixed_dividend=0.03),
                   Stock(symbol='GIN', par_value=100, stock_type='Preferred', last_dividend=0, fixed_dividend=0.0)
                   ])
    return stocks


class TestStock:

    def test_init(self, stock_data):
        """Test creating Stock objects"""
        expected_stock = Stock(symbol='GIN', par_value=100, stock_type='Preferred', last_dividend=8,
                               fixed_dividend=0.02)
        stocks = [
            Stock(symbol=stock[0], par_value=stock[4], stock_type=stock[1], last_dividend=stock[2],
                  fixed_dividend=stock[3])
            for stock in stock_data]
        assert len(stocks) == len(stock_data)
        assert stocks[3].symbol == expected_stock.symbol
        assert stocks[3].par_value == expected_stock.par_value
        assert stocks[3].type == expected_stock.type
        assert stocks[3].last_dividend == expected_stock.last_dividend
        assert stocks[3].fixed_dividend == expected_stock.fixed_dividend

    @pytest.mark.parametrize("price, expected", [(110, 0.0),
                                                 (90, 0.0889),
                                                 (70, 0.3286),
                                                 (110, 0.0182),
                                                 (240, 0.0542),
                                                 (0, pytest.raises(ValueError))])
    def test_get_dividend_yield(self, price, expected, stocks):
        """ Test dividend yield """
        if price == 0:
            with pytest.raises(ValueError):
                Stock(symbol='GIN', par_value=100, stock_type='Preferred', last_dividend=8,
                      fixed_dividend=0.02).get_pe_ratio(
                    price)
        else:
            stock = next(stocks[0])
            if stock.last_dividend == 0.0:
                assert expected == 0.0
            else:
                assert expected == round((stock.last_dividend / price), 4) if stock.type == 'Common' else \
                    (round((stock.fixed_dividend * stock.par_value) / price, 4))
            assert stock.get_dividend_yield(price) == expected

    def test_get_dividend_yield_zero(self, stocks_missing_data):
        """Test zero dividend yield"""
        for stock in stocks_missing_data:
            if stock.type == 'Common':
                assert stock.get_dividend_yield(stock.par_value) == 0.0
            if stock.type == 'Preferred':
                assert stock.get_pe_ratio(stock.par_value) == 0.0

    @pytest.mark.parametrize("price, expected", [(110, 0.0),
                                                 (90, 11.25),
                                                 (70, 3.0435),
                                                 (110, 13.75),
                                                 (240, 18.4615),
                                                 (0, pytest.raises(ValueError))])
    def test_get_pe_ratio(self, price, expected, stocks):
        """ Test Stock P/E ratio """

        if price == 0:
            with pytest.raises(ValueError):
                Stock(symbol='GIN', par_value=100, stock_type='Preferred', last_dividend=8,
                      fixed_dividend=0.02).get_pe_ratio(
                    price)
        else:
            stock = next(stocks[1])
            if stock.last_dividend == 0:
                assert expected == 0.0
            else:
                assert expected == round((price / stock.last_dividend), 4)

            assert stock.get_pe_ratio(price) == expected


@pytest.fixture(scope='module')
def trade_data():
    return pd.DataFrame.from_dict({'Symbol': ['TEA', 'POP', 'ALE', 'GIN', 'JOE', 'TEA', 'POP', 'ALE', 'POP', 'ALE'],
                                   'Timestamp': [(datetime.now() - timedelta(minutes=i)) for i in range(10)],
                                   'Quantity': [10, 20, 20, 30, 30, 40, 50, 20, 40, 50],
                                   'Buy_or_Sell': ['Buy', 'Sell', 'Buy', 'Buy', 'Buy', 'Buy', 'Buy', 'Buy', 'Sell',
                                                   'Sell'],
                                   'Price': [100, 100, 90, 100, 100, 110, 120, 90, 100, 100], },
                                  ).values.tolist()


@pytest.fixture(scope='module')
def trade_data_last_5():
    return pd.DataFrame.from_dict({'Symbol': ['ALE'] * 10,
                                   'Timestamp': [(datetime.now() - timedelta(minutes=i)) for i in range(10)],
                                   'Quantity': [10] * 10,
                                   'Buy_or_Sell': ['Buy'] * 10,
                                   'Price': [100] * 10, },
                                  ).values.tolist()


class TestTrade:
    def test_init(self, trade_data, stocks):
        """Test creating Trade objects"""
        stocks_data = [stock for stock in stocks[2]]

        def get_stock(symbol):
            return [stock for stock in stocks_data if stock.symbol == symbol][0]

        expected_trade = Trade(stock=get_stock('POP'), timestamp=(datetime.now() + timedelta(minutes=1)), quantity=20,
                               buy_or_sell='Sell', price=100)
        trades = [Trade(stock=get_stock(trade[0]), timestamp=trade[1], quantity=trade[2], buy_or_sell=trade[3],
                        price=trade[4])
                  for trade in trade_data]
        assert len(trades) == len(trade_data)
        assert trades[1].stock.symbol == expected_trade.stock.symbol
        assert trades[1].timestamp <= expected_trade.timestamp
        assert trades[1].quantity == expected_trade.quantity
        assert trades[1].buy_or_sell == expected_trade.buy_or_sell
        assert trades[1].price == expected_trade.price


class TestStockMarket:
    def test_init(self, trade_data, stocks):
        stocks_data = [stock for stock in stocks[3]]

        def get_stock(symbol):
            return [stock for stock in stocks_data if stock.symbol == symbol][0]

        trades = [Trade(stock=get_stock(trade[0]), timestamp=trade[1], quantity=trade[2], buy_or_sell=trade[3],
                        price=trade[4])
                  for trade in trade_data]
        assert len(trades) == len(trade_data)

    def test_book_trade(self, trade_data, stocks):
        """ Test booking trades """

        stocks_data = [stock for stock in stocks[4]]

        def get_stock(symbol):
            return [stock for stock in stocks_data if stock.symbol == symbol][0]

        with pytest.raises(ValueError):
            StockMarket.book_trade(stock=get_stock('GIN'), quantity=0, buy_or_sell='Sell', price=0)

        trade_records = [
            (trade[1],
             StockMarket.book_trade(stock=get_stock(trade[0]), quantity=trade[2], buy_or_sell=trade[3], price=trade[4]))
            for trade in trade_data]
        stock_market = StockMarket()
        assert len(trade_records) == len(stock_market._trades)

    @mock.patch.object(StockMarket, "_StockMarket__trades", new_callable=mock.PropertyMock)
    def test_calculate_VWSP(self, trades_mock: mock.PropertyMock, trade_data_last_5, stocks):
        """ Test calculation of VWSP for trades booked in last 5 minutes """

        with pytest.raises(ValueError):
            StockMarket.calculate_VWSP('ALE', minutes=5)

        stocks_data = [stock for stock in stocks[5]]

        def get_stock(symbol):
            return [stock for stock in stocks_data if stock.symbol == symbol][0]

        trade_records = [
            (trade[1], Trade(stock=get_stock(trade[0]), timestamp=trade[1], quantity=trade[2], buy_or_sell=trade[3],
                             price=trade[4]))
            for trade in trade_data_last_5]
        trades_mock.return_value = trade_records
        vwsp = StockMarket.calculate_VWSP('ALE', minutes=5)
        price_qty = (100 * 10) * 5
        sum_qty = 10 * 5
        assert vwsp == round((price_qty / sum_qty), 4)


class TestGlobalBeverageCorporationExchange:
    def test_all_stock_index(self, trade_data, stocks):
        """ Test the geometric mean of the Volume Weighted Stock Price for all stocks"""

        stocks_data = [stock for stock in stocks[6]]

        def get_stock(symbol):
            return [stock for stock in stocks_data if stock.symbol == symbol][0]

        for trade in trade_data:
            GlobalBeverageCorporationExchange.book_trade(stock=get_stock(trade[0]), quantity=trade[2],
                                                         buy_or_sell=trade[3], price=trade[4])
        gbc_exchange = GlobalBeverageCorporationExchange()
        all_stocks = gbc_exchange.all_stock_index()
        assert all_stocks == float(102.8249)

    def test_all_stock_index_raise_error(self):
        """ Test ValueError for no trades"""

        with pytest.raises(ValueError):
            gbc_exchange = GlobalBeverageCorporationExchange()
            gbc_exchange._trades = []
            gbc_exchange.all_stock_index()
