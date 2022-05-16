# -*- coding:utf-8 -*-
"""
@Time : 2022/2/7 10:37
@Author : domionlu@zquant.io
@File : Risk
"""
import  numpy as np

class Risk(object):



    def __init__(self, daily_returns, benchmark_daily_returns=None ):
        """
        :param daily_returns: DataFrame
            date return pnl commission values
        :param benchmark_daily_returns:DataFrame
            date return
        """
        self._returns={}
        self._portfolio = daily_returns
        self._annual_factor = 365
        # 总交易日

    def calculate_statistics(self):
        dt= self._portfolio
        start_date = dt.index[0]
        end_date = dt.index[-1]

        values=dt["values"]
        capital = values[0]
        end_balance = values[-1]
        rt=dt["return"]
        pnl=dt["pnl"]
        commission=dt["commission"]
        sharpe = np.sqrt(self._annual_factor) * values.mean() / values.std()
        ret = end_balance/capital-1
        annual_return =pow(1+ret,self._annual_factor/len(rt))-1
        max_drawdown = ((values.cummax()-values)/values.cummax()).max()
        total_net_pnl=end_balance-capital
        total_commission=(commission).sum()
        profit_return =len(rt[rt>0.0])
        zeno=len(rt[rt==0.0])
        loss_return =len(rt[rt<0.0])
        win_rate = profit_return/(profit_return+loss_return)
        if profit_return==0:
            avg_profit=0
        else:
            avg_profit=pnl[pnl>0].sum()/profit_return
        if loss_return==0:
            avg_loss=0
            pl_radio=1
        else:
            avg_loss=pnl[pnl<0].sum()/loss_return
            pl_radio=avg_profit/abs(avg_loss)
        self._returns={
            "start_date":start_date,
            "end_date":end_date,
            "capital":capital,
            "end_balance":end_balance,
            "return":ret,
            "sharpe":sharpe,
            "annual_return":annual_return,
            "max_drawdown":max_drawdown,
            "total_net_pnl":total_net_pnl,
            "total_commission":total_commission,
            "profit_return":profit_return,
            "loss_return":loss_return,
            "win_rate":win_rate,
            "avg_profit":avg_profit,
            "avg_loss":avg_loss,
            "pl_radio":pl_radio
        }
        return self._returns

    @property
    def start_date(self):
        # 首个交易日
        return self._returns["start_date"]

    @property
    def end_date(self):
        # 最后交易日
        return self._returns["end_date"]

    @property
    def capital(self):
        # 起始资金
        return self._returns["capital"]

    @property
    def end_balance(self):
        # 结束资金
        return self._returns["end_balance"]

    @property
    def alpha(self):
        # 阿尔法
        return self._returns["alpha"]

    @property
    def beta(self):
        # 贝塔
        return self._returns["beta"]

    @property
    def sharpe(self):
        # 夏普
        return self._returns["sharpe"]

    @property
    def return_rate(self):
        # 总收益率
        return self._returns["return"]

    @property
    def annual_return(self):
        # 年化收益率
        return self._returns["annual_return"]

    @property
    def benchmark_return(self):
        # 基准收益率
        return self._returns["benchmark_return"]

    @property
    def benchmark_annual_return(self):
        # 基准年化收益率
        return self._returns["benchmark_annual_return"]

    @property
    def max_drawdown(self):
        # 最大回撤
        return self._returns["max_drawdown"]

    @property
    def total_net_pnl(self):
        # 总盈亏
        return self._returns["total_net_pnl"]

    @property
    def total_commission(self):
        # 总手续费
        return self._returns["total_commission"]

    @property
    def profit_return(self):
        # 盈利笔数
        return self._returns["profit_return"]

    @property
    def loss_return(self):
        # 亏损笔数
        return self._returns["loss_return"]

    @property
    def win_rate(self):
        # 胜率
        return self._returns["win_rate"]

    @property
    def avg_profit(self):
        # 平均盈利
        return self._returns["avg_profit"]

    @property
    def avg_loss(self):
        # 平均亏损
        return self._returns["avg_loss"]

    @property
    def pl_radio(self):
        # 盈亏比
        return self._returns["pl_radio"]


