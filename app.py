import streamlit as st
import pandas as pd
from model import run_model

st.title("📊 Модель ОФЗ-ИН")

st.sidebar.header("Параметры модели")

# Дефолтные значения
DEFAULTS = {
    'attracted': 380_000_000_000,
    'people': 2_000_000,
    'coupon_oin': 2.5,
    'coupon_pd': 13.74,
    'nominal_oin': 10_000,
    'nominal_pd': 1000,
    'ndfl': 13.0
}

# Инициализация session_state (если ещё нет)
for key, value in DEFAULTS.items():
    if key not in st.session_state:
        st.session_state[key] = value

# Обработка сброса (выполняется ДО создания виджетов)
if st.session_state.get('reset', False):
    for key, value in DEFAULTS.items():
        st.session_state[key] = value
    st.session_state['reset'] = False
    # не нужно st.rerun(), так как скрипт уже перезапущен

# Виджеты с привязкой к session_state
attracted = st.sidebar.number_input(
    "Привлекаемые средства, руб",
    value=st.session_state.attracted,
    step=10_000_000_000,
    key='attracted'
)
st.sidebar.write(f"Введено: {attracted:,.0f}".replace(",", " "))

people = st.sidebar.number_input(
    "Количество человек, чел",
    value=st.session_state.people,
    step=100_000,
    key='people'
)
st.sidebar.write(f"Введено: {people:,.0f}".replace(",", " "))

coupon_oin = st.sidebar.number_input(
    "Ставка купона ОФЗ-ИН (л),%", 
    value=st.session_state.coupon_oin, 
    step=0.1, 
    format="%.1f",
    key='coupon_oin'
)
st.sidebar.write(f"Введено: {coupon_oin:.1f}")

coupon_pd = st.sidebar.number_input(
    "Ставка купона ОФЗ-ПД,%", 
    value=st.session_state.coupon_pd, 
    step=0.1, 
    format="%.2f",
    key='coupon_pd'
)
st.sidebar.write(f"Введено: {coupon_pd:.2f}")

nominal_oin = st.sidebar.number_input(
    "Номинал ОФЗ-ИН, руб", 
    value=st.session_state.nominal_oin, 
    step=1_000,
    key='nominal_oin'
)
st.sidebar.write(f"Введено: {nominal_oin:,.0f}".replace(",", " "))

nominal_pd = st.sidebar.number_input(
    "Номинал ОФЗ-ПД, руб", 
    value=st.session_state.nominal_pd, 
    step=100,
    key='nominal_pd'
)
st.sidebar.write(f"Введено: {nominal_pd:,.0f}".replace(",", " "))

ndfl = st.sidebar.number_input(
    "НДФЛ, %",
    value=st.session_state.ndfl,
    step=0.1,
    format="%.1f",
    key='ndfl'
)
st.sidebar.write(f"Введено: {ndfl:.1f}")

# Кнопка сброса
if st.sidebar.button("Сбросить все"):
    st.session_state['reset'] = True
    st.rerun()

# Собираем словарь констант
const = {
    'Привлекаемые_средства': attracted,
    'Количество_человек': people,
    'Ставка_купона_ОФЗ_ИН_л': coupon_oin/100,
    'Ставка_купона_ОФЗ_ПД': coupon_pd/100,
    'Номинал_ОФЗ_ИН': nominal_oin,
    'Номинал_ОФЗ_ПД': nominal_pd,
    'НДФЛ': ndfl/100
}

# Запускаем модель с пользовательскими параметрами
doxod_za_period, itog_ofz_pd_gos, itog_ofz_in_l_gos = run_model(const)

st.subheader("Итоговый доход по инструментам")
st.dataframe(doxod_za_period)

st.subheader("Нагрузка на государство (ОФЗ-ИН)")
st.dataframe(itog_ofz_in_l_gos)

st.subheader("Нагрузка на государство (ОФЗ-ПД)")
st.dataframe(itog_ofz_pd_gos)