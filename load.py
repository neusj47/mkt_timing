import requests
import pandas as pd
from datetime import datetime
from pykrx import stock
import numpy as np
from dateutil.relativedelta import relativedelta
import math
import warnings
warnings.filterwarnings('ignore')

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
    start_date = stock.get_nearest_business_day_in_a_week(datetime.strftime(datetime.strptime(end_date, "%Y%m%d") - relativedelta(years=1),"%Y%m%d"))
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
        response = requests.get('https://www.wiseindex.com/DataCenter/GridData?currentPage=1&endDT=' + end_date + '&fromDT=' + start_date + '&index_ids='+str(values[0])+'&isEnd=1&itemType=3&perPage=600&term=1')
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
df = get_sector_valuation(end_date)

