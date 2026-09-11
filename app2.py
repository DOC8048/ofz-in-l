# from datetime import datetime

import streamlit as st

import function.cbr_inflation as cbr_inf
import model_2 as md

# загружаем из модуля new_function
from function.api_in_function import get_deposit_rates


@st.cache_data(ttl=600)
def get_target_inflation() -> float | None:
    """
    Функция получает значение целевой инфляции 
    Результат кэшируется на 4 часа.
    
    Возвращает:
        float | None: значение целевой инфляции в процентах (float), или None при ошибке
    """
    try:
        value = cbr_inf.get_latest_target()
        if value is None:
            return None
        return float(value)
    except Exception:  # noqa: BLE001
        return None

@st.cache_data(ttl=600)
def get_target_deposit() -> float | None:
    """
    Функция получает ставку по депозиту (по вкладам физ.лиц до востребования), 
    также кэш на 4 часа
    Возвращает:
        float | None: значение ставки депозита в процентах (float), или None при ошибке
    """
    try:
        dep =get_deposit_rates()
        if dep.empty or 'rate' not in dep.columns:
            return None
        return dep['rate'].iloc[-1]
    except Exception:  # noqa: BLE001
        return None

@st.cache_data(ttl=600)
def get_current_inflation():
    """
    Функция получает последнее значение текущей инфляции 
    """
    try:
        value1 = cbr_inf.get_latest_inflation()
        if value1 is None:
            return None
        return float(value1)
    except Exception:  # noqa: BLE001
        return None
target_inf = get_target_inflation()
target_dep = get_target_deposit()
current_inflation = get_current_inflation()
st.title("📊 Модель ОФЗ-ИН")

st.sidebar.header("Параметры модели")    

# Если хотя бы один из ключевых источников не ответил — показываем большую ошибку
if target_inf is None or target_dep is None or current_inflation is None:
    st.error("⚠️ Серверы ЦБ или внешние API временно недоступны. Без этих данных расчёт модели невозможен.")
    
    # Подсказка, сколько ждать до следующей попытки
    st.info("Попробуйте перезагрузить страницу.")
    
    # Важно: дальше код не выполняется, модель не запускается
    st.stop()
# Дефолтные настройки
config = md.ModelConfig()

if 'inf_forecast' not in st.session_state:
    st.session_state['inf_forecast'] = target_inf
if 'deposit_rate' not in st.session_state:
    st.session_state['deposit_rate'] = target_dep
if 'deposit_decrement' not in st.session_state:
    st.session_state['deposit_decrement'] = 2.5


if st.session_state.get('reset', False):
     st.session_state['inf_forecast'] = target_inf
     st.session_state['deposit_rate'] = target_dep
     st.session_state['deposit_decrement'] = 2.5
     st.session_state['reset'] = False 

st.sidebar.info(f"Фактическая инфляция (ЦБ): {current_inflation}%")
st.sidebar.caption("Слайдер ниже — позволяет строить модель по сценарному предположению о будущей инфляции (ежегодно).")
with st.sidebar.expander("Ставки", expanded=False):
    # Параметры для депозита и инфляции
    inf_forecast = st.number_input(
        "Прогноз инфляции на будущие годы, %",
        value=st.session_state["inf_forecast"],
        step=0.1,
        format="%.1f",
        key="inf_forecast"
    )
    st.write(f"Введено: {inf_forecast:.1f}%")

    deposit_rate = st.number_input(
        "Текущая ставка депозита, %",
        value=st.session_state["deposit_rate"],
        step=0.1,
        format="%.2f",
        key="deposit_rate"
    )
    st.write(f"Введено: {deposit_rate:.2f}%")

    deposit_decrement = st.number_input(
        "Коэффициент снижения ставки, %",
        value=st.session_state["deposit_decrement"],
        step=0.1,
        format="%.1f",
        key="deposit_decrement"
    )
    st.write(f"Введено: {deposit_decrement:.1f}%")

with st.sidebar.expander('Параметры модели', expanded=False):
    # Виджеты с привязкой к словарю
    attracted = st.number_input(
        "Привлекаемые средства, руб",
        value=config.attract_funds,
        step=10_000_000_000
    )
    st.write(f"Введено: {attracted:,.0f}".replace(",", " "))

if st.sidebar.button("Сбросить все"):
    st.session_state['reset'] = True
    st.rerun()

base_model = md.FinancialModel()

opt_model = md.FinancialModel(config=None,preparer=md.InflationRatePreparer(inf_override=4.5,deposit_decrement=0.5))

pes_model = md.FinancialModel(config=None,preparer=md.InflationRatePreparer(inf_override=15,deposit_rate=14))

tab1, tab2, tab3 = st.tabs(["Базовый ", "Оптимистичный", "Пессимистичный"])

with tab1:
    st.subheader("Итоговый доход по инструментам")
    st.dataframe(base_model.summary)
    st.subheader("Нагрузка на государство (ОФЗ-ИН)")
    st.dataframe(base_model.government_ofz_in_l)
    st.subheader("Нагрузка на государство (ОФЗ-ПД)")
    st.dataframe(base_model.government_ofz_pd)

with tab2:
    st.subheader("Итоговый доход по инструментам")
    st.dataframe(opt_model.summary)
    st.subheader("Нагрузка на государство (ОФЗ-ИН)")
    st.dataframe(opt_model.government_ofz_in_l)
    st.subheader("Нагрузка на государство (ОФЗ-ПД)")
    st.dataframe(opt_model.government_ofz_pd)
with tab3:
    st.subheader("Итоговый доход по инструментам")
    st.dataframe(pes_model.summary)
    st.subheader("Нагрузка на государство (ОФЗ-ИН)")
    st.dataframe(pes_model.government_ofz_in_l)
    st.subheader("Нагрузка на государство (ОФЗ-ПД)")
    st.dataframe(pes_model.government_ofz_pd)
