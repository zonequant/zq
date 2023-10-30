#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2023/4/13 19:52
# @Author  : Dominolu
# @File    : gridbacktest.py
# @Software: PyCharm

import numpy as np


class GridStrategyBacktest:
    def __init__(self, data, grid_size=0.05, grid_stop_loss=0.10,
                 grid_take_profit=0.15, grid_count=10, grid_start_price=None):
        self.data = data.to_numpy()
        self.grid_size = grid_size
        self.grid_stop_loss = grid_stop_loss
        self.grid_take_profit = grid_take_profit
        self.grid_count = grid_count
        self.grid_start_price = grid_start_price

        if not self.grid_start_price:
            self.grid_start_price = self.data[0, 1]

        self.buy_prices = self.get_buy_prices()
        self.sell_prices = self.get_sell_prices()
        self.order_side = np.empty(len(self.data), dtype=object)
        self.order_price = np.zeros(len(self.data))
        self.order_grid_index = np.zeros(len(self.data), dtype=int)
        self.order_pending = np.zeros(len(self.data), dtype=bool)

    def run_backtest(self):
        trades = []
        for i in range(1, len(self.data)):
            if self.order_pending[i - 1]:
                continue

            current_price = self.data[i, 4]
            grid_index = self.order_grid_index[i - 1]
            order_side = self.order_side[i - 1]

            if not order_side:
                if current_price <= self.buy_prices[-1]:
                    order_side = 'buy'
                elif current_price >= self.sell_prices[-1]:
                    order_side = 'sell'
            else:
                if order_side == 'buy':
                    if current_price <= self.buy_prices[grid_index - 1] * (1 - self.grid_stop_loss):
                        order_price = (1 - self.grid_take_profit) * self.buy_prices[grid_index - 1]
                        trades.append(('sell', order_price))
                    elif current_price >= self.buy_prices[grid_index - 1]:
                        order_price = self.buy_prices[grid_index - 1]
                        trades.append(('buy', order_price))
                elif order_side == 'sell':
                    if current_price >= self.sell_prices[grid_index - 1] * (1 + self.grid_stop_loss):
                        order_price = (1 + self.grid_take_profit) * self.sell_prices[grid_index - 1]
                        trades.append(('buy', order_price))
                    elif current_price <= self.sell_prices[grid_index - 1]:
                        order_price = self.sell_prices[grid_index - 1]
                        trades.append(('sell', order_price))

                    self.update_grid_prices(i, order_side, order_price)

        return trades

    def update_grid_prices(self, i, order_side, order_price):
        grid_index = self.order_grid_index[i - 1]
        if order_side == 'buy':
            self.sell_prices[grid_index - 1] = order_price
        elif order_side == 'sell':
            self.buy_prices[grid_index - 1] = order_price

    def get_buy_prices(self):
        buy_prices = np.zeros(self.grid_count)
        for i in range(self.grid_count):
            price = self.grid_start_price - i * self.grid_size
            buy_prices[i] = price
        return buy_prices

    def get_sell_prices(self):
        sell_prices = np.zeros(self.grid_count)
        for i in range(self.grid_count):
            price = self.grid_start_price + i * self.grid_size
            sell_prices[i] = price
        return sell_prices
