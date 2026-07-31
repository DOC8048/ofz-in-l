import streamlit as st
import pandas as pd
from model import run_model

st.title("📊 Модель ОФЗ-ИН")

# Создаём виджеты для параметров
st.sidebar.header("Параметры модели")

attracted = st.sidebar.number_input("Привлекаемые средства", value=380_000_000_000, step=10_000_000_000)
st.sidebar.write(f"Введено: {attracted:,.0f}".replace(",", " "))

people = st.sidebar.number_input("Количество человек", value=2_000_000, step=100_000)
st.sidebar.write(f"Введено: {people:,.0f}".replace(",", " "))

coupon_oin = st.sidebar.number_input("Ставка купона ОФЗ-ИН (л)", value=0.025, step=0.001, format="%.3f")
st.sidebar.write(f"Введено: {coupon_oin:.3f}")

coupon_pd = st.sidebar.number_input("Ставка купона ОФЗ-ПД", value=0.1374, step=0.001, format="%.3f")
st.sidebar.write(f"Введено: {coupon_pd:.3f}")

nominal_oin = st.sidebar.number_input("Номинал ОФЗ-ИН", value=10_000, step=1_000)
st.sidebar.write(f"Введено: {nominal_oin:,.0f}".replace(",", " "))

nominal_pd = st.sidebar.number_input("Номинал ОФЗ-ПД", value=1000, step=100)
st.sidebar.write(f"Введено: {nominal_pd:,.0f}".replace(",", " "))

ndfl = st.sidebar.number_input("НДФЛ, %", value=0.13, step=0.01, format="%.2f")
st.sidebar.write(f"Введено: {ndfl:.2f}")

#st.sidebar.header("Параметры модели")
#attracted = st.sidebar.number_input("Привлекаемые средства", value=380_000_000_000, step=10_000_000_000)
#st.sidebar.write(f"Введено: {attracted:,.0f}".replace(",", " "))
#people = st.sidebar.number_input("Количество человек", value=2_000_000, step=100_000)
#coupon_oin = st.sidebar.number_input("Ставка купона ОФЗ-ИН (л)", value=0.025, step=0.001, format="%.3f")
#coupon_pd = st.sidebar.number_input("Ставка купона ОФЗ-ПД", value=0.1374, step=0.001, format="%.3f")
#nominal_oin = st.sidebar.number_input("Номинал ОФЗ-ИН", value=10_000, step=1_000)
#nominal_pd = st.sidebar.number_input("Номинал ОФЗ-ПД", value=1000, step=100)
#ndfl = st.sidebar.number_input("НДФЛ, %", value=0.13, step=0.01, format="%.2f")

# Собираем словарь констант
const = {
    'Привлекаемые_средства': attracted,
    'Количество_человек': people,
    'Ставка_купона_ОФЗ_ИН_л': coupon_oin,
    'Ставка_купона_ОФЗ_ПД': coupon_pd,
    'Номинал_ОФЗ_ИН': nominal_oin,
    'Номинал_ОФЗ_ПД': nominal_pd,
    'НДФЛ': ndfl
}

# Запускаем модель с пользовательскими параметрами
doxod_za_period, itog_ofz_pd_gos, itog_ofz_in_l_gos = run_model(const)

st.subheader("Итоговый доход по инструментам")
st.dataframe(doxod_za_period)

st.subheader("Нагрузка на государство (ОФЗ-ИН)")
st.dataframe(itog_ofz_in_l_gos)

st.subheader("Нагрузка на государство (ОФЗ-ПД)")
st.dataframe(itog_ofz_pd_gos)
