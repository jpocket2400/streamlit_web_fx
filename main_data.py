import streamlit as st
from streamlit_autorefresh import st_autorefresh
import data.fxdefs as fxd
import time
import pandas as pd

#ページの自動更新
st_autorefresh(interval=10000, key="dataframerefresh")
####ウィジェット作成    
#サイドバーに最新のレートを表示

dfNow = fxd.get_data_now()
sel_pair = fxd.set_pair()
sel_intvl = fxd.set_intvl()

fxd.sidebar_set(dfNow)
    
df = fxd.get_data(sel_pair, sel_intvl)
st.dataframe(df.sort_index(ascending=False).head(20))
