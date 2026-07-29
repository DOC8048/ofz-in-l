import streamlit as st
import pandas as pd

from model import run_model

st.title("📊 Модель ОФЗ-ИН")

doxod_za_period,itog_ofz_pd,itog_ofz_in_l_gos = run_model()

st.subheader("Итоговый доход по инструментам")
st.dataframe(doxod_za_period)

st.subheader("Нагрузка на государство (ОФЗ-ИН)")
st.dataframe(itog_ofz_in_l_gos)

st.subheader("Нагрузка на государство (ОФЗ-ПД)")
st.dataframe(itog_ofz_pd)