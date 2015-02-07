import pandas as pd
from datetime import datetime
import numpy as np
import QSTK.qstkutil.qsdateutil as du
import QSTK.qstkutil.tsutil as tsu
import QSTK.qstkutil.DataAccess as da
import datetime as dt
import sys
import matplotlib.pyplot as plt
from pylab import *


def marketsim(investment, orders_file, out_file):
    df = pd.read_csv(orders_file, parse_dates=[[0,1,2]], header=None)
    
    df.columns = ['date', 'stock', 'order', 'shares', 'no']
    df = df.drop('no',1)
    df = df.sort('date', 0)
    df = df.reset_index(drop=True)
    df['date'] = df['date'] + dt.timedelta(hours=16)
    
    start_date = df['date'][0]
    end_date = df['date'][df.shape[0]-1]
    dt_timeofday = dt.timedelta(hours=16)
    ldt_timestamps = du.getNYSEdays(start_date, end_date, dt_timeofday)
    c_dataobj = da.DataAccess('Yahoo')
    
    ls_keys = ['close']
    equities = list(df.stock.unique())

    data = c_dataobj.get_data(ldt_timestamps, equities, ls_keys)[0]
    data = data.fillna(method='ffill')
    data = data.fillna(method='bfill')
    data = data.fillna(1.0)
    
    data['cash'] = float(investment)
    for equity in equities:
        data['shares_'+equity] = 0
    for row in range(df.shape[0]):
        order = df.ix[row]
        if order['order'] == 'Buy':
            bought = order.shares
            data['shares_'+order.stock][data.index >= order.date] += bought
            cash_paid = bought * data[order.stock][data.index == order.date][0]
            data['cash'][data.index >= order.date] -= cash_paid
        elif order['order'] == 'Sell':
            sold = order.shares
            data['shares_'+order.stock][data.index >= order.date] -= sold
            cash_taken = sold * data[order.stock][data.index == order.date][0]
            data['cash'][data.index >= order.date] += cash_taken
    
    def compute_equities_value(row):
        return (row[:len(equities)].values * row[len(equities)+1:].values).sum() 
    
    data['eq_value'] = data.apply(lambda row: compute_equities_value(row), axis=1)
    data['portfolio'] = data['cash'] + data['eq_value']
    
    portfolio = data['portfolio'].copy()
    dret = tsu.returnize0(portfolio) 
    vol = dret.std()
    daily_ret = dret.mean()
    sharpe = np.sqrt(252)*daily_ret/vol
    cum_ret = data['portfolio'][data.shape[0]-1]/investment - 1 
    
    market = c_dataobj.get_data(ldt_timestamps, ['SPY'], ls_keys)[0]
    original = market.SPY.copy()
    market['dret'] = tsu.returnize0(market.SPY)
    market.SPY = original 
    mvol = market.dret.std()
    mdaily_ret = market.dret.mean()
    msharpe = np.sqrt(252)*mdaily_ret/mvol
    mcum_ret = original[market.shape[0]-1]/original[0] - 1
    
    fig = figure()
    ax = fig.add_subplot(111)
    ax.set_xticklabels(data.index, rotation=45)
    ax.yaxis.grid(color='gray', linestyle='dashed')
    ax.xaxis.grid(color='gray', linestyle='dashed')
    ax.xaxis.set_major_formatter(DateFormatter('%b %Y'))
    ax.legend(('Fund','Market'), loc='upper left')
    ax.set_title('Fund Performance VS Market (SPY)', 
                    fontsize=16, fontweight="bold")
    ax.set_xlabel('Date', fontsize=16)
    ax.set_ylabel('Normalized Fund Value', fontsize=16)
    
    port = data.portfolio/data.portfolio.max()
    mark = original/original.max()
    
    y_min = min(port.min(), mark.min())
    ax.set_ylim([y_min-0.02, 1.02])
    plt.plot(data.index, port, lw=2., label='Fund')
    plt.plot(data.index, mark, lw=2., label='Market')
    ax.legend(('Fund','Market'), loc='upper left', prop={"size":16})
    fig.autofmt_xdate()
    plt.show()

    data = data.reset_index()
    data.columns.values[0] = 'date'
    
    begin = pd.to_datetime(data.date[0]).strftime('%b %d %Y')    
    end = pd.to_datetime(data.date[data.shape[0]-1]).strftime('%b %d %Y')
    
    print 'Details of the Performance of the portfolio'
    print ''
    print 'Data Range: ', begin, ' - ', end
    print ''
    print 'Sharpe Ratio of Fund: ', sharpe
    print 'Sharpe Ratio of Market: ', msharpe
    print ''
    print 'Total Return of Fund: ', cum_ret
    print 'Total Return of Market: ', mcum_ret
    print ''
    print 'Volatily of Fund: ', vol
    print 'Volatily of Market: ', mvol
    print ''
    print 'Average Daily Return of Fund: ', daily_ret
    print 'Average Daily Return of Market: ', mdaily_ret
    print ''
    
    
    data.to_csv(out_file, index=False)
 
    

if __name__ == '__main__':
    marketsim(1000000, 'orders.csv', 'values.csv')

