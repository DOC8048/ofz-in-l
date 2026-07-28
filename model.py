# %% [markdown]
# # 1. Импорт библиотек и настройки

# %%
import pandas as pd
# загружаем функии из модуля cbr_inflation
import function.cbr_inflation as cbr_inf
# загружаем из модуля new_function
from function.API_in_function import get_deposit_rates
from datetime import date

# %% [markdown]
# # 2. Загрузка констант и динамики

# %%
def get_constants():
    const = {'Привлекаемые_средства': 380_000_000_000,
            'Ставка_купона_ОФЗ_ИН_л': 0.025,
            'Ставка_купона_ОФЗ_ПД': 0.1374,
            'Номинал_ОФЗ_ИН': 10_000,
            'Номинал_ОФЗ_ПД': 1000,
            'Количество_человек': 2_000_000,
            'НДФЛ': 0.13
        }
    return const

const = get_constants()

# %%
# загружаем функии из модуля cbr_inflation

def prepare_inflation_and_rate():
    inf = cbr_inf.get_inflation()
# выбираем только последний год и последнее значение инфляции
    inf_d = inf.copy()
    inf_d['Год'] = inf_d['date'].dt.year
    inf_d.rename(columns={
    'inflation': 'Инфляция',
    'target': 'Цель по инфляции'},inplace=True)
    inf_d = inf_d[['Год','Инфляция']]
    inf_d = inf_d.tail(1)
# автоматизируем продлжения ряда лет,и настраиваем вывод целовой инфляции
    current_year = date.today().year
    forecast_years = [ current_year + 1, current_year + 2]
    inf2 = pd.DataFrame({
    'Год': forecast_years,
    'Инфляция': inf['target'].iloc[-1]})
    inf_res = pd.concat([inf_d,inf2],ignore_index=True)

# %%
    df = get_deposit_rates()
    sd = df.tail(1)
# создаем переменную имеющую единственную последнюю актуальную ставку
    value = sd['rate'].iloc[0]

# %%
    DEPOSIT_DECREMENT = 2.5 # коэфициент снижения 
    base = value
    inf_res['Ставка депозита'] = base - (DEPOSIT_DECREMENT/100) * inf_res.index
    inf_res[['Инфляция','Ставка депозита']] = inf_res[['Инфляция','Ставка депозита']]/100 # переводим проценты в числа
    return inf_res

inf_res = prepare_inflation_and_rate()

# %% [markdown]
# # 3. ОФЗ ИН (л)

# %%
def calculate_ofz_in_l(const, inf_res):
    ofz_in_l =inf_res.copy()

# %%
    ofz_in_l['Привлекаемые средства'] = const['Привлекаемые_средства']
    ofz_in_l['Количество человек'] = const['Количество_человек']
    ofz_in_l['Ставка купона'] = const['Ставка_купона_ОФЗ_ИН_л']

# %%
    ofz_in_l['На руках у человека, руб'] = ofz_in_l['Привлекаемые средства'] / ofz_in_l['Количество человек']

# %%
    ofz_in_l['Облигаций штук'] = ofz_in_l['На руках у человека, руб'] / const ['Номинал_ОФЗ_ИН']

# %%
    ofz_in_l['Инфляционный множитель']= (1 + inf_res['Инфляция']).cumprod()

# %%
    ofz_in_l['Номинал после индексации'] = const['Номинал_ОФЗ_ИН']*ofz_in_l['Инфляционный множитель']

# %%
    ofz_in_l['Номинал на начало'] = float(const['Номинал_ОФЗ_ИН'])
    ofz_in_l.loc[ofz_in_l.index > 0, 'Номинал на начало'] = ofz_in_l['Номинал после индексации'].shift(1).fillna(const['Номинал_ОФЗ_ИН'])

# %%
    ofz_in_l['Индексация номинала'] = ofz_in_l['Номинал на начало'] * ofz_in_l['Инфляция']

# %%
    ofz_in_l['Купон, руб'] = ofz_in_l['Номинал после индексации'] * ofz_in_l['Ставка купона']

# %%
    ofz_in_l['Доход без вычета'] = ofz_in_l['Купон, руб'] * ofz_in_l['Облигаций штук']

# %%
    ofz_in_l ['Налоговый вычет, руб']= ofz_in_l['На руках у человека, руб'] * const['НДФЛ']

# %%
    ofz_in_l['Доход с вычетом'] = ofz_in_l['Налоговый вычет, руб'] + ofz_in_l['Доход без вычета']

# %%
    ofz_in_l = ofz_in_l[['Год', # перезаписываем в нужном порядке
 'Привлекаемые средства',
 'Количество человек',
 'Инфляция',
 'Ставка купона',
 'На руках у человека, руб',
 'Облигаций штук',
 'Инфляционный множитель',
 'Номинал на начало',
 'Индексация номинала',
 'Номинал после индексации',
 'Купон, руб',
 'Доход без вычета',
 'Налоговый вычет, руб',
 'Доход с вычетом']]
    return ofz_in_l

ofz_in_l = calculate_ofz_in_l(const, inf_res)


# %% [markdown]
# # 4. ОФЗ ПД

# %%
def calculate_ofz_pd(const, ofz_in_l):
    ofz_pd = ofz_in_l [['Год']].copy()
    ofz_pd['Привлекаемые средства'] = const ["Привлекаемые_средства"]
    ofz_pd ["Количество человек"] = const ["Количество_человек"]
    ofz_pd ["Ставка купона"] = const ['Ставка_купона_ОФЗ_ПД']
    ofz_pd ["На руках у человека"] = ofz_in_l [["На руках у человека, руб"]].copy()
    ofz_pd ['Облигаций, штук'] = ofz_pd ['На руках у человека'] / const ['Номинал_ОФЗ_ПД']
    ofz_pd ['Купон'] = const ['Номинал_ОФЗ_ПД'] * const ['Ставка_купона_ОФЗ_ПД']
    ofz_pd ["Доход, руб"] = ofz_pd ["Купон"] * ofz_pd ['Облигаций, штук']
    ofz_pd ['НДФЛ'] = ofz_pd ['Доход, руб'] * const ['НДФЛ']
    ofz_pd ['Доход после вычета налога'] = ofz_pd['Доход, руб'] - ofz_pd ['НДФЛ']
    return ofz_pd

ofz_pd = calculate_ofz_pd(const, ofz_in_l)

# %% [markdown]
# # 5. Депозит

# %%
def calculate_depozit(const, inf_res, ofz_in_l):
    depozit = ofz_in_l[['Год']].copy()
    depozit ['Привлекаемые средства'] = const ['Привлекаемые_средства']
    depozit ['Количество человек'] = const ['Количество_человек']
    depozit ['На руках у человека'] = ofz_in_l ['На руках у человека, руб']
    depozit ['Ставка депозита'] = inf_res['Ставка депозита'] 


# %%
    depozit ['Коэфициент'] = (1 + inf_res['Ставка депозита'] / 12) **12
# %%
    depozit ['Накопленный множитель'] = depozit ['Коэфициент'].cumprod()

# %%
    initial_amount = depozit['На руках у человека'].iloc[0]

# %%
    depozit ['Сумма на конец года'] = initial_amount * depozit ['Накопленный множитель']

# %%
    depozit ['Сумма на начало года'] = initial_amount
    depozit.loc [depozit.index > 0, 'Сумма на начало года'] = depozit['Сумма на конец года']. shift (1)

# %%
    depozit['Проценты']= depozit['Сумма на конец года'] - depozit['Сумма на начало года']

# %%
    depozit = depozit [["Год", "Привлекаемые средства", # перезаписываем в нужном порядке
                   "Количество человек", 
                   "На руках у человека",
                   "Ставка депозита",
                   "Коэфициент",
                   "Накопленный множитель",
                   "Сумма на начало года",
                   "Сумма на конец года",
                    "Проценты"]]
    return depozit

depozit = calculate_depozit(const, inf_res, ofz_in_l)         

# %% [markdown]
# # Итоговая таблица доходов

# %%
def build_summary_table(inf_res, ofz_in_l, ofz_pd, depozit):
    df_s_merge = ofz_in_l[['Год', 'На руках у человека, руб']].copy()
    df_s_merge.rename(columns={'На руках у человека, руб': 'Вложения'}, inplace=True)

# %%
    df_s_merge['ОФЗ ИН доход'] = ofz_in_l['Индексация номинала']* ofz_in_l['Облигаций штук'] + ofz_in_l['Доход без вычета']

# %%
    df_s_merge = df_s_merge.merge(ofz_pd[['Год', 'Доход, руб']], on='Год', how='left')
    df_s_merge.rename(columns={'Доход, руб': 'ОФЗ ПД доход'}, inplace=True)

# %%
    df_s_merge = df_s_merge.merge(depozit[['Год', 'Проценты']], on='Год', how='left')
    df_s_merge.rename(columns={'Проценты': 'Депозит доход'}, inplace=True)

# %% [markdown]
# # Делаем длинную 
# 

# %%
# Теперь применяем melt к данным 
    df_long = df_s_merge.melt(
    id_vars=['Год', 'Вложения'],
    value_vars=['ОФЗ ИН доход', 'ОФЗ ПД доход', 'Депозит доход'],
    var_name='Инструмент',
    value_name='Доход'
)

# Сортируем по году и инструменту
    df_long = df_long.sort_values(['Год', 'Инструмент']).reset_index(drop=True)

# %%
    doxod_za_period = pd.DataFrame()
    doxod_za_period =  df_long.groupby('Инструмент', as_index=False)['Доход'].sum()

# %%
# Вычисляем итоговые суммы
    total_oin = ofz_in_l['На руках у человека, руб'].iloc[0] + doxod_za_period.loc[doxod_za_period['Инструмент'] == 'ОФЗ ИН доход','Доход'].iloc[0] + ofz_in_l['Налоговый вычет, руб'].iloc[0]
    total_pd = ofz_in_l['На руках у человека, руб'].iloc[0] + ofz_pd['Доход, руб'].sum()
    total_dep = ofz_in_l['На руках у человека, руб'].iloc[0] + depozit['Проценты'].sum()

# Словарь соответствий
    total_dict = {
    'ОФЗ ИН доход': total_oin,
    'ОФЗ ПД доход': total_pd,
    'Депозит доход': total_dep
}

# Добавляем колонку Итоговая сумма
    doxod_za_period['Итоговая сумма'] = doxod_za_period['Инструмент'].map(total_dict)
    inf_factor = (1 + inf_res['Инфляция']).prod()
# %%
    doxod_za_period['Очистка инфляции'] = doxod_za_period['Итоговая сумма']/inf_factor
    doxod_za_period['Реальный доход'] = doxod_za_period['Итоговая сумма'] - ofz_in_l['На руках у человека, руб']
    doxod_za_period.loc[doxod_za_period['Инструмент'] == 'ОФЗ ИН доход', 'Очистка инфляции'] = None
    return doxod_za_period
dohod_za_period = build_summary_table(inf_res, ofz_in_l, ofz_pd, depozit)


# %% [markdown]
# # Нагрузка на государство
# 

# %%
def build_government_ofz_in(const, inf_res):
    ofz_in_l_gos = inf_res.copy()
    ofz_in_l_gos['Прибавка от инфляции'] = const['Привлекаемые_средства']*ofz_in_l_gos['Инфляция']
    ofz_in_l_gos['Инфляционный множитель'] = (1+ofz_in_l_gos ['Инфляция']).cumprod()
    ofz_in_l_gos['Тело долга'] = const['Привлекаемые_средства'] * ofz_in_l_gos['Инфляционный множитель']
    ofz_in_l_gos['Расходы на купоны'] = ofz_in_l_gos['Тело долга'] * const['Ставка_купона_ОФЗ_ИН_л']
    ofz_in_l_gos['Общие затраты'] = ofz_in_l_gos['Прибавка от инфляции']+ofz_in_l_gos['Расходы на купоны']
    ofz_in_l_gos = ofz_in_l_gos[['Год','Инфляция','Прибавка от инфляции','Тело долга','Расходы на купоны','Общие затраты']]

# %%
    cols = ['Прибавка от инфляции', 'Тело долга', 'Расходы на купоны','Общие затраты']
    total_ofz_in_l_gos = pd.DataFrame(ofz_in_l_gos[cols].sum()).T
    total_ofz_in_l_gos['Год'] = 'Итого'
    itog_ofz_in_l_gos = pd.concat([ofz_in_l_gos,total_ofz_in_l_gos],ignore_index=True)
    return itog_ofz_in_l_gos

ofz_in_l_gos = build_government_ofz_in(const, inf_res)

# %%
def build_government_ofz_pd(const, ofz_pd, ofz_in_l_gos):
    ofz_pd_gos = ofz_in_l_gos[['Год']].copy()
    ofz_pd_gos['Тело долга'] = const['Привлекаемые_средства']
    ofz_pd_gos['Расходы на купон'] = ofz_pd_gos['Тело долга'] * const['Ставка_купона_ОФЗ_ПД']
    ofz_pd_gos['Сумма возврата,НДФЛ'] = ofz_pd['НДФЛ']*const['Количество_человек']
    ofz_pd_gos['Итого при учете возврата НДФЛ'] = ofz_pd_gos['Расходы на купон']-ofz_pd_gos['Сумма возврата,НДФЛ']


# %%
    cols2 = ['Тело долга', 'Расходы на купон','Сумма возврата,НДФЛ','Итого при учете возврата НДФЛ']
    total_ofz_pd_gos = pd.DataFrame(ofz_pd_gos[cols2].sum()).T
    total_ofz_pd_gos['Год'] = 'Итого'
    itog_ofz_pd_gos = pd.concat([ofz_pd_gos,total_ofz_pd_gos],ignore_index=True)
    return itog_ofz_pd_gos

itog_ofz_pd_gos = build_government_ofz_pd(const, ofz_pd, ofz_in_l_gos)

# ============================================
# 8. Главная функция, запускающая всю модель
# ============================================
def run_model():
    inf_res = prepare_inflation_and_rate()
    const = get_constants()
    ofz_in_l = calculate_ofz_in_l(const, inf_res)
    ofz_pd = calculate_ofz_pd(const,ofz_in_l)
    depozit = calculate_depozit(const,inf_res,ofz_in_l)
    doxod_za_period = build_summary_table(inf_res,ofz_in_l,ofz_pd,depozit)
    itog_ofz_in_l_gos  = build_government_ofz_in(const,inf_res)
    itog_ofz_pd = build_government_ofz_pd (const,ofz_pd,ofz_in_l_gos,)
    return doxod_za_period,itog_ofz_pd,itog_ofz_in_l_gos

if __name__ == "__main__":
    doxod_za_period ,itog_ofz_pd,itog_ofz_in_l_gos = run_model()
    print("=== Доход по инструментам ===")
    print(doxod_za_period)
    print("\n=== Нагрузка ОФЗ-ИН ===")
    print(itog_ofz_in_l_gos)
    print("\n=== Нагрузка ОФЗ-ПД ===")
    print(itog_ofz_pd)

