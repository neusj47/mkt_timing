import requests
import pandas as pd
from datetime import datetime
from pykrx import stock
import numpy as np
from dateutil.relativedelta import relativedelta
import math
import warnings
warnings.filterwarnings('ignore')

# BV/PQ Spread 산출
# 0. 섹터별 PBR 불러오기
# 1. BP Spread 산출


def get_bdate_info(start_date, end_date) :
    end_date = stock.get_nearest_business_day_in_a_week(datetime.strftime(datetime.strptime(end_date, "%Y%m%d") + relativedelta(days=1),"%Y%m%d"))
    date = pd.DataFrame(stock.get_previous_business_days(fromdate=start_date, todate=end_date)).rename(columns={0: '일자'})
    prevbdate = date.shift(1).rename(columns={'일자': '전영업일자'})
    date = pd.concat([date, prevbdate], axis=1).fillna(
        datetime.strftime(datetime.strptime(stock.get_nearest_business_day_in_a_week(datetime.strftime(datetime.strptime(start_date, "%Y%m%d") - relativedelta(days=1), "%Y%m%d")), "%Y%m%d"),"%Y-%m-%d %H:%M:%S"))
    date['주말'] = ''
    for i in range(0, len(date) - 1):
        if abs(datetime.strptime(datetime.strftime(date.iloc[i + 1].일자, "%Y%m%d"), "%Y%m%d") - datetime.strptime(datetime.strftime(date.iloc[i].일자, "%Y%m%d"), "%Y%m%d")).days > 1:
            date['주말'].iloc[i] = 1
        else:
            date['주말'].iloc[i] = 0
    month_list = date.일자.map(lambda x: datetime.strftime(x, '%Y-%m')).unique()
    monthly = pd.DataFrame()
    for m in month_list:
        try:
            monthly = monthly.append(date[date.일자.map(lambda x: datetime.strftime(x, '%Y-%m')) == m].iloc[-1])
        except Exception as e:
            print("Error : ", str(e))
        pass
    date['월말'] = np.where(date['일자'].isin(monthly.일자.tolist()), 1, 0)
    return date

def get_sector_valuation(end_date) :
    end_date = stock.get_nearest_business_day_in_a_week(datetime.strftime(datetime.strptime(end_date, "%Y%m%d") + relativedelta(days=1), "%Y%m%d"))
    start_date = stock.get_nearest_business_day_in_a_week(datetime.strftime(datetime.strptime(end_date, "%Y%m%d") - relativedelta(years=7),"%Y%m%d"))
    bdate = get_bdate_info(start_date, end_date)['일자'].sort_values(ascending=False)
    start_date = datetime.strftime(bdate.iloc[len(bdate)-1], "%Y-%m-%d")
    end_date = datetime.strftime(bdate.iloc[0], "%Y-%m-%d")
    idx = {'WI100': '에너지',
           'WI110': '화학',
           'WI200': '비철금속',
           'WI210': '철강',
           'WI220': '건설',
           'WI230': '기계',
           'WI240': '조선',
           'WI250': '상사,자본재',
           'WI260': '운송',
           'WI300': '자동차',
           'WI310': '화장품,의류',
           'WI320': '호텔,레저',
           'WI330': '미디어,교육',
           'WI340': '소매(유통)',
           'WI400': '필수소비재',
           'WI410': '건강관리',
           'WI500': '은행',
           'WI510': '증권',
           'WI520': '보험',
           'WI600': '소프트웨어',
           'WI610': '하드웨어',
           'WI620': '반도체',
           'WI630': 'IT가전',
           'WI640': '디스플레이',
           'WI700': '전기통신서비스',
           'WI800': '유틸리티'
           }
    df = pd.DataFrame(columns=['일자', '지수코드', '지수명', 'EPS', 'BPS', 'SPS', 'PER', 'PBR', 'PSR', 'EVEBITDA', '매출성장률', '영업이익성장률', '배당수익률'])

    for keys, values in enumerate(idx.items()):
        response = requests.get('https://www.wiseindex.com/DataCenter/GridData?currentPage=1&endDT=' + end_date + '&fromDT=' + start_date + '&index_ids='+str(values[0])+'&isEnd=1&itemType=3&perPage=2000&term=1')
        if (response.status_code == 200):
            json_list = response.json()
            for i in json_list:
                일자 = datetime.strftime(bdate.iloc[i['ROW_IDX']-1], "%Y-%m-%d")
                지수코드 = values[0]
                지수명 = values[1]
                EPS = i['IDX1_VAL1']
                BPS = i['IDX1_VAL2']
                SPS = i['IDX1_VAL3']
                PER = i['IDX1_VAL4']
                PBR = i['IDX1_VAL5']
                PSR = i['IDX1_VAL6']
                EVEBITDA = i['IDX1_VAL7']
                매출성장률 = i['IDX1_VAL8']
                영업이익성장률 = i['IDX1_VAL9']
                배당수익률 = i['IDX1_VAL10']
                df = df.append(
                    {'일자': 일자, '지수코드': 지수코드, '지수명': 지수명, 'EPS': EPS, 'BPS': BPS, 'SPS': SPS, 'PER': PER, 'PBR': PBR, 'PSR': PSR, 'EVEBITDA': EVEBITDA, '매출성장률': 매출성장률, '영업이익성장률': 영업이익성장률, '배당수익률': 배당수익률,}, ignore_index=True).fillna(0)
    return df

end_date = '20220609'

def get_bp_sprd(end_date) :
    df = get_sector_valuation(end_date).sort_values('일자', ascending=True)
    date = df.일자.unique().tolist()
    dfs = pd.DataFrame()
    for i in range(0,len(date)) :
        df_temp = df[df.일자 == date[i]].reset_index(drop=True)[['일자','지수명','BPS','PBR']]
        df_temp['BP'] = 1/df_temp['PBR']
        df_temp = df_temp.sort_values('BP', ascending = False)
        df_high = df_temp[0:6]
        df_low = df_temp[20:len(df_temp)]
        high_bp = df_high.groupby('일자').mean()['BP'][0]
        low_bp = df_low.groupby('일자').mean()['BP'][0]
        dfs_temp = pd.DataFrame({'날짜' : date[i], 'BP_Sprd' : (high_bp - low_bp)}, index = [0])
        dfs = pd.concat([dfs, dfs_temp]).reset_index(drop=True)
    df_kospi = stock.get_index_ohlcv_by_date(datetime.strftime(datetime.strptime(date[0], "%Y-%m-%d"), "%Y%m%d"),
                                             datetime.strftime(datetime.strptime(date[len(date) - 1], "%Y-%m-%d"),"%Y%m%d"), '1001').reset_index(drop=False)[['날짜', '종가']]
    for i in range(0, len(df_kospi)):
        df_kospi['날짜'].iloc[i] = datetime.strftime(df_kospi['날짜'].iloc[i], "%Y-%m-%d")
    dfs = pd.merge(dfs, df_kospi, on ='날짜', how ='inner')
    return dfs
dfs =  get_bp_sprd(end_date)

# num_periods_fast = 5                 # time period for the fast EMA
# K_fast = 2 / (num_periods_fast + 1) # smoothing factor for fast EMA
# num_periods_slow = 20               # time period for slow EMA
# K_slow = 2 / (num_periods_slow + 1) # smoothing factor for slow EMA
# num_periods_macd = 20 # MACD EMA time period
# K_macd = 2 / (num_periods_macd + 1) # MACD EMA smoothing factor
#
# def get_MACD_signal(close, K_fast, K_slow, K_macd) :
#     ema_fast = 0
#     ema_slow = 0
#     ema_macd = 0
#     ema_fast_values = []
#     ema_slow_values = []
#     macd_values = []
#     macd_signal_values = []
#     macd_histogram_values = []
#     for close_price in close:
#         if (ema_fast == 0):  # first observation
#             ema_fast = close_price
#             ema_slow = close_price
#         else:
#             ema_fast = (close_price - ema_fast) * K_fast + ema_fast
#             ema_slow = (close_price - ema_slow) * K_slow + ema_slow
#         ema_fast_values.append(ema_fast)
#         ema_slow_values.append(ema_slow)
#         macd = ema_fast - ema_slow  # MACD is fast_MA - slow_EMA
#         if ema_macd == 0:
#             ema_macd = macd
#         else:
#             ema_macd = (macd - ema_macd) * K_macd + ema_macd  # signal is EMA of MACD values
#         macd_values.append(macd)
#         macd_signal_values.append(ema_macd)
#         macd_histogram_values.append(macd - ema_macd)
#     df_result = dfs.assign(F_EMA=pd.Series(ema_fast_values, index=dfs.index))
#     df_result = df_result.assign(S_EMA=pd.Series(ema_slow_values, index=dfs.index))
#     df_result = df_result.assign(MACD=pd.Series(macd_values, index=df_result.index))
#     df_result = df_result.assign(MA_MACD=pd.Series(macd_signal_values, index=df_result.index))
#     df_result = df_result.assign(HIS_MACD=pd.Series(macd_histogram_values, index=df_result.index))
#     df_result['Signal'] = df_result['MACD'].apply(lambda x: 1 if x > 0 else 0)
#     return df_result
#
# df_result = get_MACD_signal(dfs['종가'], K_fast, K_slow, K_macd)

mon_date = get_bdate_info(datetime.strftime(datetime.strptime(dfs.날짜.iloc[0], "%Y-%m-%d"), "%Y%m%d"), end_date)
mon_date = mon_date[mon_date.월말 == 1].rename(columns = {'일자':'날짜'})
for i in range(0, len(mon_date)):
    mon_date['날짜'].iloc[i] = datetime.strftime(mon_date['날짜'].iloc[i], "%Y-%m-%d")
dfss = pd.merge(dfs, mon_date[['날짜','월말']], on ='날짜', how ='inner')


dfss.to_excel('C:/Users/ysj/Desktop/dㅇsd.xlsx')
