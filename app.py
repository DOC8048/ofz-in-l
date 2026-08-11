import streamlit as st
import pandas as pd
from model import run_model
import function.cbr_inflation as cbr_inf
from datetime import datetime
# загружаем из модуля new_function
from function.API_in_function import get_deposit_rates
from utilits_app.export_utils import generate_excel
@st.cache_data(ttl=14400)
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
    except Exception:
        return None

@st.cache_data(ttl=14400)
def get_target_deposit() -> float | None:
    """
    Функция полует ставку по депозиту (по вкладам физ.лиц довостребования), 
    также кэш на 4 часа
    Возвращает:
        float | None: значение ставки депозита в процентах (float), или None при ошибке
    """
    try:
        dep =get_deposit_rates()
        if dep.empty or 'rate' not in dep.columns:
            return None
        return dep['rate'].iloc[-1]
    except Exception:
        return None

@st.cache_data(ttl=14400)
def get_current_inflation():
    """
    Функция получает последнее заначение текущей инфляции 
    """
    try:
        value1 = cbr_inf.get_latest_inflation()
        if value1 is None:
            return None
        return float(value1)
    except Exception:
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
    st.info("Кэш обновится автоматически через ~4 часа. Либо попробуйте перезагрузить страницу позже.")
    
    # Важно: дальше код не выполняется, модель не запускается
    st.stop()
# Дефолтные значения
DEFAULTS = {
    'attracted': 380_000_000_000,
    'people': 2_000_000,
    'coupon_oin': 2.5,
    'coupon_pd': 13.74,
    'nominal_oin': 10_000,
    'nominal_pd': 1000,
    'ndfl': 13.0
    #'inf_forecast': get_target_inflation()
}

# Инициализация session_state (если ещё нет)
for key, value in DEFAULTS.items():
    if key not in st.session_state:
        st.session_state[key] = value
if 'inf_forecast' not in st.session_state:
    st.session_state['inf_forecast'] = target_inf
if 'deposit_rate' not in st.session_state:
    st.session_state['deposit_rate'] = target_dep
if 'deposit_decrement' not in st.session_state:
    st.session_state['deposit_decrement'] = 2.5


# Обработка сброса (выполняется ДО создания виджетов)
if st.session_state.get('reset', False):
    for key, value in DEFAULTS.items():
        st.session_state[key] = value     
    # Удаляем пользовательские ключи, чтобы при следующем запуске они взялись из API
    st.session_state['inf_forecast'] = target_inf
    st.session_state['deposit_rate'] = target_dep
    st.session_state['deposit_decrement'] = 2.5
    st.session_state['reset'] = False   
    # не нужно st.rerun(), так как скрипт уже перезапущен       

# В app.py после инициализации session_state
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
        value=st.session_state.attracted,
        step=10_000_000_000,
        key='attracted'
    )
    st.write(f"Введено: {attracted:,.0f}".replace(",", " "))

    people = st.number_input(
        "Количество человек, чел",
        value=st.session_state.people,
        step=100_000,
        key='people'
    )
    st.write(f"Введено: {people:,.0f}".replace(",", " "))

    coupon_oin = st.number_input(
        "Ставка купона ОФЗ-ИН (л),%", 
        value=st.session_state.coupon_oin, 
        step=0.1, 
        format="%.1f",
        key='coupon_oin'
    )
    st.write(f"Введено: {coupon_oin:.1f}")

    coupon_pd = st.number_input(
        "Ставка купона ОФЗ-ПД,%", 
        value=st.session_state.coupon_pd, 
        step=0.1, 
        format="%.2f",
        key='coupon_pd'
    )
    st.write(f"Введено: {coupon_pd:.2f}")

    nominal_oin = st.number_input(
        "Номинал ОФЗ-ИН, руб", 
        value=st.session_state.nominal_oin, 
        step=1_000,
        key='nominal_oin'
    )
    st.write(f"Введено: {nominal_oin:,.0f}".replace(",", " "))

    nominal_pd = st.number_input(
        "Номинал ОФЗ-ПД, руб", 
        value=st.session_state.nominal_pd, 
        step=100,
        key='nominal_pd'
    )
    st.write(f"Введено: {nominal_pd:,.0f}".replace(",", " "))

    ndfl = st.number_input(
        "НДФЛ, %",
        value=st.session_state.ndfl,
        step=0.1,
        format="%.1f",
        key='ndfl'
    )
    st.write(f"Введено: {ndfl:.1f}")

# Кнопка сброса
if st.sidebar.button("Сбросить все"):
    st.session_state['reset'] = True
    st.rerun()

# Словарь пользовательских параметров
user_params = {
    'inf_override': [inf_forecast / 100, inf_forecast / 100],  # для двух прогнозных лет
    'deposit_rate': deposit_rate / 100,  # переводим в десятичную дробь
    'deposit_decrement': deposit_decrement,
    
}
# Собираем словарь констант
const = {
    'Привлекаемые_средства': attracted,
    'Количество_человек': people,
    'Ставка_купона_ОФЗ_ИН_л': coupon_oin/100,
    'Ставка_купона_ОФЗ_ПД': coupon_pd/100,
    'Номинал_ОФЗ_ИН': nominal_oin,
    'Номинал_ОФЗ_ПД': nominal_pd,
    'НДФЛ': ndfl/100,
}

# Запускаем модель с пользовательскими параметрами
doxod_za_period, itog_ofz_pd_gos, itog_ofz_in_l_gos = run_model(
    const,
    inf_override=user_params['inf_override'],
    deposit_rate=user_params['deposit_rate'],
    deposit_decrement=user_params['deposit_decrement'],
)
st.subheader("Итоговый доход по инструментам")
st.dataframe(doxod_za_period)

st.subheader("Нагрузка на государство (ОФЗ-ИН)")
st.dataframe(itog_ofz_in_l_gos)

st.subheader("Нагрузка на государство (ОФЗ-ПД)")
st.dataframe(itog_ofz_pd_gos)

with st.popover("📥 Скачать выбранное"):
    # Создаем переменные состояния для чекбоксов
    include_income = st.checkbox("Итоговый доход по инструментам", value=True)
    include_burden_oin = st.checkbox("Нагрузка ОФЗ-ИН", value=True)
    include_burden_pd = st.checkbox("Нагрузка ОФЗ-ПД", value=True)
    include_params = st.checkbox("Параметры модели", value=True)
    include_user_params = st.checkbox("Ставки", value=True)
    
    st.divider()
    
    # Логика отображения кнопки
    if not any([include_income, include_burden_oin, include_burden_pd, include_params, include_user_params]):
        st.warning("Выберите хотя бы один раздел для экспорта.")
    else:
        st.download_button(
            label="💾 Скачать отчёт",
            data=lambda: generate_excel(
                doxod_za_period,
                itog_ofz_in_l_gos,
                itog_ofz_pd_gos,
                const,
                user_params,
                include_income,
                include_burden_oin,
                include_burden_pd,
                include_params,
                include_user_params
            ),
            file_name=f"model_report_{datetime.now().strftime('%Y-%m-%d')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )