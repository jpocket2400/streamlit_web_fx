import streamlit as st
import pandas as pd
import requests
import json
import time
import datetime as dt
from dateutil.relativedelta import relativedelta
import numpy as np
import talib as ta
import plotly.graph_objs as go
import matplotlib.pyplot as plt
from plotly.subplots import make_subplots
import streamlit as st

def set_pair():
    sel_pair = st.radio('pair',
             ('USD_JPY','EUR_JPY','GBP_JPY','AUD_JPY','NZD_JPY','CAD_JPY',
              'CHF_JPY','EUR_USD','GBP_USD','AUD_USD','NZD_USD'),
              horizontal=True)
    return(sel_pair)

def set_intvl():
    sel_intvl = st.radio('intvl',
             ('1min','5min','10min','15min','30min',
              '1hour','4hour','8hour','12hour','1day'), 
              horizontal=True)
    return(sel_intvl)
        

def sidebar_set(dfNow):
    with st.sidebar:

        st.dataframe(dfNow)
        
#移動平均線(EMA)
def EMA_create(df,tm_period):
    credata = ta.EMA(df['Close'], timeperiod=tm_period)
    return(credata)

def df_const_time(intvl):
    df_time = pd.DataFrame((
    ['1min','1T',60000,'0T'],
    ['5min','5T',300000,'0T'],
    ['10min','10T',600000,'0T'],
    ['15min','15T',900000,'0T'],
    ['30min','30T',1800000,'0T'],
    ['1hour','1H',3600000,'0H'],
    ['4hour','4H',14400000,'1H'],
    ['8hour','8H',28800000,'1H'],
    ['12hour','12H',43200000,'9H'],
    ['1day','1D',86400000,'6H']
    )
    ,columns=['Intvl','Resample','ms','Offset']     
    )
    df_time.set_index('Intvl',inplace=True)

    return(df_time.loc[intvl,'Resample'],df_time.loc[intvl,'ms'],df_time.loc[intvl,'Offset'])

def get_data(pair, intvl):
    df_all = pd.DataFrame()
    
    if intvl in ['1min','5min','10min','15min','30min','1hour']:
        #10日分
        for num in reversed(range(10)):
            #0～6時は前日で取得
            if dt.datetime.now().hour >= 0 and dt.datetime.now().hour <= 5:
                day = dt.datetime.strftime(dt.datetime.now(dt.timezone.utc) - relativedelta( days = num ), '%Y%m%d' )
            else:
                day = dt.datetime.strftime(dt.datetime.now() - relativedelta( days = num ), '%Y%m%d' )
            if num == 5:
                time.sleep(1)
                    
            df1 = get_data_all(pair,intvl,day)
            if df_all.empty:
                df_all = df1
            else:
                df_all = pd.concat([df_all,df1])    
    else:
        #2年分
        day = dt.datetime.strftime( dt.datetime.today() - relativedelta( months = 12 ), '%Y' )
        df1 = get_data_all(pair,intvl,day)
        df_all = df1
        day = dt.datetime.strftime( dt.datetime.today(), '%Y' )
        df1 = get_data_all(pair,intvl,day)
        df_all = pd.concat([df_all,df1])

    #pandasデータ表示したいとき用
    #pd.reset_option('display.max_rows')
    #pd.reset_option('display.max_columns')

    #EMA/MACDの計算

    #移動平均線(EMA)
    #短期3・5・8・10・12・15日線
    #長期30・35・40・45・50・60日線

    df = df_all
    df['EMA3'] = EMA_create(df,3)
    df['EMA5'] = EMA_create(df,5)
    df['EMA8'] = EMA_create(df,8)
    df['EMA10'] = EMA_create(df,10)
    df['EMA12'] = EMA_create(df,12)
    df['EMA15'] = EMA_create(df,15)
    df['EMA30'] = EMA_create(df,30)
    df['EMA35'] = EMA_create(df,35)
    df['EMA40'] = EMA_create(df,40)
    df['EMA45'] = EMA_create(df,45)
    df['EMA50'] = EMA_create(df,50)
    df['EMA60'] = EMA_create(df,60)
    df['SMin'] = df.iloc[:, 4:10].min(axis=1)
    df['LMin'] = df.iloc[:, 10:16].min(axis=1)
    df['SMax'] = df.iloc[:, 4:10].max(axis=1)
    df['LMax'] = df.iloc[:, 10:16].max(axis=1)

    df['TrendU'] = np.nan
    df['TrendD'] = np.nan
    df.loc[(df['SMin'] > df['LMax'] ),'TrendU']  = df['LMax']
    df.loc[(df['SMax'] < df['LMin'] ),'TrendD']  = df['LMin']

    
    df['macd'], df['macdsignal'], df['macdhist'] = ta.MACD(df['Close'], fastperiod=12, slowperiod=26, signalperiod=9)

    df['macdCloss'] = np.nan
    df.loc[(df['macdhist'].shift(+1) >= 0 ) & (df['macdhist'] <= 0),'macdCloss'] = df['macdsignal']
    df.loc[(df['macdhist'].shift(+1) <= 0 ) & (df['macdhist'] >= 0),'macdCloss'] = df['macdsignal']

    return(df)

def get_data_all(pair,intvl,day):
    df1 = pd.DataFrame()
    endPoint = 'https://forex-api.coin.z.com/public'
    path     = f'/v1/klines?symbol={pair}&priceType=ASK&interval={intvl}&date={day}'

    response = requests.get(f'{endPoint}{path}')
    d = response.json()
    df1 = pd.json_normalize(d, record_path="data")
    df1 = df1.astype("float64")
    if 'openTime' in df1.columns:
        df1["openTime"] = pd.to_datetime(df1["openTime"].astype('datetime64[ms]'), utc=True).dt.tz_convert('Asia/Tokyo')
        df1.set_index("openTime", inplace=True)
        df1.columns = ["Open", "High", "Low", "Close"]
    return(df1)

def get_data_now():
    
    #GMOコインから最新値の取得
    endPoint = 'https://forex-api.coin.z.com/public'
    path     = '/v1/ticker'
    response = requests.get(f'{endPoint}{path}')
    d =response.json()
    dfNow = pd.json_normalize(d, record_path='data')
    dfNow = dfNow.set_index(['symbol'],inplace=False)
    dfNow = dfNow.drop(['timestamp','status'], axis=1)
    dfNow = dfNow.reindex(['bid', 'ask'], axis=1)
    return(dfNow)

def fig_chart(sel_pair, sel_intvl, df):
        ######################チャート作成
    
    fig, dfp = fig_com(sel_pair, sel_intvl, df)

    #y軸定義。１行目にローソク、２行目にMACD
    fig.update_yaxes(separatethousands=True, title_text="為替")
    #fig.update_yaxes(title_text="MACD", row=2, col=1)
    
    # Candlestick
    fig.add_trace(
        go.Candlestick(x=dfp.index, open=dfp["Open"], high=dfp["High"], low=dfp["Low"], close=dfp["Close"], showlegend=False)
    )
    
    #移動平均線(EMA)
    #短期3・5・8・10・12・15日線
    #長期30・35・40・45・50・60日線
    #fig.add_trace(go.Scatter(x=dfp.index, y=dfp["EMA3"], name="EMA3", mode="lines",connectgaps=True, marker=dict(color='blue')), row=1, col=1)
    #fig.add_trace(go.Scatter(x=dfp.index, y=dfp["EMA5"], name="EMA5", mode="lines",connectgaps=True, marker=dict(color='blue')),  row=1, col=1)
    #fig.add_trace(go.Scatter(x=dfp.index, y=dfp["EMA8"], name="EMA8", mode="lines",connectgaps=True,  marker=dict(color='blue')), row=1, col=1)
    #fig.add_trace(go.Scatter(x=dfp.index, y=dfp["EMA10"], name="EMA10", mode="lines",connectgaps=True, marker=dict(color='blue')), row=1, col=1)
    #fig.add_trace(go.Scatter(x=dfp.index, y=dfp["EMA12"], name="EMA12", mode="lines",connectgaps=True, marker=dict(color='blue')), row=1, col=1)
    #fig.add_trace(go.Scatter(x=dfp.index, y=dfp["EMA15"], name="EMA15", mode="lines",connectgaps=True, marker=dict(color='blue')),  row=1, col=1)
    #fig.add_trace(go.Scatter(x=dfp.index, y=dfp["EMA30"], name="EMA30", mode="lines",connectgaps=True, marker=dict(color='red')),  row=1, col=1)
    #fig.add_trace(go.Scatter(x=dfp.index, y=dfp["EMA35"], name="EMA35", mode="lines",connectgaps=True, marker=dict(color='red')),  row=1, col=1)
    #fig.add_trace(go.Scatter(x=dfp.index, y=dfp["EMA40"], name="EMA40", mode="lines",connectgaps=True, marker=dict(color='red')),  row=1, col=1)
    #fig.add_trace(go.Scatter(x=dfp.index, y=dfp["EMA45"], name="EMA45", mode="lines",connectgaps=True, marker=dict(color='red')),  row=1, col=1)
    #fig.add_trace(go.Scatter(x=dfp.index, y=dfp["EMA50"], name="EMA50", mode="lines",connectgaps=True, marker=dict(color='red')),  row=1, col=1)
    #fig.add_trace(go.Scatter(x=dfp.index, y=dfp["EMA60"], name="EMA60", mode="lines",connectgaps=True, marker=dict(color='red')),  row=1, col=1)
    fig.add_trace(go.Scatter(x=dfp.index, y=dfp["TrendU"], name="上昇トレンド", mode="markers",connectgaps=True, marker=dict(color='black',size=6,symbol='arrow-bar-up')))
    fig.add_trace(go.Scatter(x=dfp.index, y=dfp["TrendD"], name="下降トレンド", mode="markers",connectgaps=True, marker=dict(color='black',size=6,symbol='arrow-bar-down')))
    fig.add_trace(go.Scatter(x=dfp.index, y=dfp["SMin"], name="EMA短期最小", mode="lines",connectgaps=True, marker=dict(color='blue')))
    fig.add_trace(go.Scatter(x=dfp.index, y=dfp["SMax"], name="EMA短期最大", mode="lines",connectgaps=True, marker=dict(color='blue')))
    fig.add_trace(go.Scatter(x=dfp.index, y=dfp["LMin"], name="EMA長期最小", mode="lines",connectgaps=True, marker=dict(color='red')))
    fig.add_trace(go.Scatter(x=dfp.index, y=dfp["LMax"], name="EMA長期最小", mode="lines",connectgaps=True, marker=dict(color='red')))
    fig.add_trace(go.Scatter(x=dfp.index, y=dfp["SMin"], name="", fill=None, line=dict(width=0, color="aqua"), showlegend=False, connectgaps=True))
    fig.add_trace(go.Scatter(x=dfp.index, y=dfp["SMax"], name="", fill="tonexty" ,line=dict(width=0, color="aqua"), showlegend=False, connectgaps=True))
    fig.add_trace(go.Scatter(x=dfp.index, y=dfp["LMax"], name="", fill=None, line=dict(width=0, color="pink"), showlegend=False, connectgaps=True))
    fig.add_trace(go.Scatter(x=dfp.index, y=dfp["LMin"], name="", fill="tonexty" ,line=dict(width=0, color="pink"), showlegend=False, connectgaps=True))

    return(fig)


def fig_macd(sel_pair, sel_intvl, df):

    fig, dfp = fig_com(sel_pair, sel_intvl, df)

    #y軸定義。１行目にローソク、２行目にMACD
    fig.update_yaxes(separatethousands=True, title_text="MACD")
    #fig.update_yaxes(title_text="MACD", row=2, col=1)
    # MACD
    fig.add_trace(go.Scatter(x=dfp.index, y=dfp["macd"], name="MACD", mode="lines", connectgaps=True, marker=dict(color='red')))
    fig.add_trace(go.Scatter(x=dfp.index, y=dfp["macdsignal"], name="MACDシグナル", mode="lines", connectgaps=True, marker=dict(color='blue')))
    fig.add_trace(go.Bar(x=dfp.index, y=dfp["macdhist"], name="MACDヒストグラム",marker=dict(color='gray')))
    fig.add_trace(go.Scatter(x=dfp.index, y=dfp["macdCloss"], name="MACDクロス", mode="markers",connectgaps=True, marker=dict(color='black',size=6)))

    return(fig)

def fig_com(sel_pair, sel_intvl, df):

    dfp = df.tail(150)  #チャートにするのは150データ程度で。
    #figを定義
    fig = go.Figure()
    #非営業日・時間は削除するのでリストを作成（NaN行の日時を抽出）
    get_resample, get_ms, get_offset = df_const_time(sel_intvl)
    df_resample = df.resample(get_resample, offset=get_offset).max() #時間軸毎にデータをまとめる。
    timegap = df_resample.index[df_resample['Open'].isna()]
    fig.update_xaxes(
        rangebreaks=[
            dict(values=timegap, dvalue = get_ms)
        ],
        #range=(dt.datetime(dfp.index[0].year,dfp.index[0].month,dfp.index[0].day,dfp.index[0].hour,dfp.index[0].minute,dfp.index[0].second),
        #       dt.datetime(dfp.index[-1].year,dfp.index[-1].month,dfp.index[-1].day,dfp.index[-1].hour,dfp.index[-1].minute,dfp.index[-1].second)
        #),
        tickformat='%Y/%m/%d %H:%M:%S' # 日時のフォーマット変更
    )

    # Layout
    fig.update_layout(
        title={
            "text":f'{sel_pair}：{dfp.index[-1].strftime("%Y/%m/%d %H:%M:%S")}[{sel_intvl}]',
            "y":0.9,
            "x":0.5,
        },
        width=800,
        height=500,
        hovermode='closest',
        xaxis_rangeslider_visible=False,
        )

    return(fig,dfp)
