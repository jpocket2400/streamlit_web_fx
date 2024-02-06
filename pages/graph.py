import streamlit as st
from streamlit_autorefresh import st_autorefresh
import plotly.graph_objs as go
from plotly.subplots import make_subplots
import data.fxdefs as fxd

chk_chart = st.checkbox('チャート自動更新')

if chk_chart:

    st_autorefresh(interval=10000, key="dataframerefresh")


dfNow = fxd.get_data_now()
sel_pair = fxd.set_pair()
sel_intvl = fxd.set_intvl()

fxd.sidebar_set(dfNow)

df = fxd.get_data(sel_pair, sel_intvl)

fig = fxd.fig_chart(sel_pair, sel_intvl, df)
st.plotly_chart(fig)

fig = fxd.fig_macd(sel_pair, sel_intvl, df)
st.plotly_chart(fig)





