import pandas as pd
import numpy as np
import math
import copy
import QSTK.qstkutil.qsdateutil as du
import datetime as dt
import QSTK.qstkutil.DataAccess as da
import QSTK.qstkutil.tsutil as tsu
import QSTK.qstkstudy.EventProfiler as ep
from marketsim import marketsim

def find_events(ls_symbols, d_data, shares=100):
    ''' Finding the event dataframe '''
    df_close = d_data['actual_close']
    orders = ''
    print "Finding Events"

    df_events = copy.deepcopy(df_close)
    df_events = df_events * np.NAN

    ldt_timestamps = df_close.index
    
    for s_sym in ls_symbols:
        for i in range(1, len(ldt_timestamps)-5):
            
            f_symprice_today = df_close[s_sym].ix[ldt_timestamps[i]]
            f_symprice_yest = df_close[s_sym].ix[ldt_timestamps[i - 1]]
 
            if f_symprice_today < 10 and f_symprice_yest >=10 :
                buy_time = pd.to_datetime(ldt_timestamps[i]).strftime('%Y,%m,%d,')
                buy_order = buy_time+str(s_sym)+',Buy,'+str(shares)+',\n'
                orders += buy_order
                
                sell_time = pd.to_datetime(ldt_timestamps[i+5]).strftime('%Y,%m,%d,')
                sell_order = sell_time+str(s_sym)+',Sell,'+str(shares)+',\n'
                orders += sell_order
    
    with open('event-orders.csv', 'w') as ord:
        ord.write(orders)
    
    print 'Saved orders to csv file'


if __name__ == '__main__':
    # test begin = 1 January 2008
    dt_start = dt.datetime(2008, 1, 1)
    # test begin = 31 December 2009
    dt_end = dt.datetime(2009, 12, 31)
    # getting only the trading days in the timeframe
    ldt_timestamps = du.getNYSEdays(dt_start, dt_end, dt.timedelta(hours=16))
    # downloading prices for all the stocks contained in the list of S&P-500 in 2012
    dataobj = da.DataAccess('Yahoo')
    ls_symbols = dataobj.get_symbols_from_list('sp5002012')
    ls_symbols.append('SPY')

    ls_keys = ['open', 'high', 'low', 'close', 'volume', 'actual_close']
    ldf_data = dataobj.get_data(ldt_timestamps, ls_symbols, ls_keys)
    d_data = dict(zip(ls_keys, ldf_data))
     
    # taking care of missing values
    for s_key in ls_keys:
        d_data[s_key] = d_data[s_key].fillna(method='ffill')
        d_data[s_key] = d_data[s_key].fillna(method='bfill')
        d_data[s_key] = d_data[s_key].fillna(1.0)
    
    # finding events and preparing trading strategy
    find_events(ls_symbols, d_data)
    # evaluating the strategy against the market
    marketsim(50000, 'event-orders.csv', 'event-values.csv')
    
    
    
