# %%
class ModelConfig:
    def __init__(
        self, 
        attract_funds=380_000_000_000,
        coupon_ofz_in=0.025,
        coupon_ofz_pd=0.1374,
        face_ofz_in=10000,
        face_ofz_pd=1000,
        people_count=2_000_000,
        ndfl=0.13
    ):
       
        self.attract_funds = attract_funds   # Теперь это не ключ, а свойство объекта
        self.coupon_ofz_in = coupon_ofz_in
        self.coupon_ofz_pd = coupon_ofz_pd
        self.face_ofz_in = face_ofz_in
        self.face_ofz_pd = face_ofz_pd
        self.people_count = people_count
        self.ndfl = ndfl

    def set_parameters(
            self,
            attract_funds= None,
            coupon_ofz_in= None,
            coupon_ofz_pd= None,
            face_ofz_in= None,
            face_ofz_pd= None,
            people_count= None,
            ndfl= None
        ):
            if attract_funds is not None:
                self.attract_funds = attract_funds
            if coupon_ofz_in is not None:
                self.coupon_ofz_in = coupon_ofz_in
            if coupon_ofz_pd is not None:
                self.coupon_ofz_pd = coupon_ofz_pd
            if face_ofz_in is not None:
                self.face_ofz_in = face_ofz_in
            if face_ofz_pd is not None:    
                self.face_ofz_pd = face_ofz_pd
            if people_count is not None:
                self.people_count = people_count
            if ndfl is not None:
                self.ndfl = ndfl


# %%
from datetime import date

import pandas as pd
from pandas import DataFrame

import function.cbr_inflation as cbr_inf
from function.API_in_function import get_deposit_rates


class InflationRatePreparer:
    """
    Класс для подготовки таблицы инфляции и ставки депозита.
    Хранит параметры и итоговый DataFrame.
    """
    def __init__(self, 
                 inf_override: list[float] | None = None,
                 deposit_rate: float | None = None,
                 deposit_decrement: float | None = None):
        """
        Конструктор: задаём начальные параметры.
        Если параметры не заданы, будут использованы данные из API.
        """
        self.inf_override = inf_override
        self.deposit_rate = deposit_rate
        self.deposit_decrement = deposit_decrement
        self.data = None          # здесь будет итоговая таблица
        self.update()             # сразу считаем
        # self.forecast_years = None
    def _normalize_inf(self, value):
    # Если это число или float - превращаем в список
        if isinstance(value, (int, float)):
            return [value] * len(self.forecast_years)
        # Если это уже список/кортеж - возвращаем как есть
        return list(value)  # на всякий случай приводим к списку
    def update(self):
        """Пересчитать таблицу с текущими параметрами."""
        # 1. Получаем базовую инфляцию из API (всегда свежая)
        inf = cbr_inf.get_inflation()
        inf_d = inf.copy()
        inf_d['Год'] = inf_d['date'].dt.year
        inf_d.rename(columns={'inflation': 'Инфляция', 'target': 'Цель по инфляции'}, inplace=True)
        inf_d = inf_d[['Год', 'Инфляция']].tail(1)

        # 2. Прогнозные годы
        current_year = date.today().year  # noqa: DTZ011
        self.forecast_years = [current_year + 1, current_year + 2]

        # 3. Определяем значения инфляции для прогнозных лет
        if self.inf_override is not None:
            inf_vals = self._normalize_inf(self.inf_override)
            # Защита от отрицательной инфляции
            if any(x < 0 for x in inf_vals):
                raise ValueError("Инфляция не может быть отрицательной")
            # Защита от инфляции в долях (если все значения < 1, вероятно, это ошибка)
            if all(0 < x < 1 for x in inf_vals):
                raise ValueError(
                "Похоже, вы передали инфляцию в долях (например, 0.05). "
                "Ожидаются значения в процентах (например, 5)."
            )
        else:
            inf_bas = inf['target'].iloc[-1]
            inf_vals = [inf_bas] * len(self.forecast_years)

        inf2 = pd.DataFrame({'Год': self.forecast_years, 'Инфляция': inf_vals})
        inf_res = pd.concat([inf_d, inf2], ignore_index=True)

        # 4. Ставка депозита
        if self.deposit_rate is None:
            df = get_deposit_rates()
            value = df.tail(1)['rate'].iloc[0]
        else:
            value = self.deposit_rate

        # 5. Снижение ставки
        if self.deposit_decrement is None:
            dec = 2
        else:
            dec = self.deposit_decrement

        base = value # оставил для наглядности
        inf_res['Ставка депозита'] = base - dec * inf_res.index
        inf_res[['Инфляция','Ставка депозита']] = inf_res[['Инфляция','Ставка депозита']]/100
        self.data = inf_res

    def set_parameters(self, inf_override: list[float] | None = None, deposit_rate=None, deposit_decrement=None):
        """Обновить параметры и пересчитать."""
        if inf_override is not None:
            # Защита от отрицательной инфляции
            # if any(x < 0 for x in inf_override):
            #     raise ValueError("Инфляция не может быть отрицательной")
            # Защита от инфляции в долях (если все значения < 1, вероятно, это ошибка)
            # if all(0 < x < 1 for x in inf_override):
            #     raise ValueError(
            #     "Похоже, вы передали инфляцию в долях (например, 0.05). "
            #     "Ожидаются значения в процентах (например, 5)."
            # )
            self.inf_override = inf_override
        if deposit_rate is not None:
            self.deposit_rate = deposit_rate
        if deposit_decrement is not None:
            self.deposit_decrement = deposit_decrement
        self.update()

# %%
class OFZ_IN_L:
    """
    Класс для ОФЗ-ИН (индексируемые).
    """
    
    # Это метод класса (как твоя функция, но внутри класса)
    def __init__(self, config: ModelConfig, inf_res: pd.DataFrame):
        """
        Принимаем готовые настройки и данные по инфляции.
        Сразу все считаем и сохраняем результат в self.
        """
        self.config = config          # Сохраняем настройки в объект
        self.inf_data = inf_res # Сохраняем инфляцию
        
        # Сразу запускаем расчет, чтобы не вызывать отдельную функцию
        self._calculate()  # Подчеркивание _ говорит: "Это внутренний метод, не вызывай снаружи"
    
    def _calculate(self):
        """
        Сюда переносим тело твоей функции calculate_ofz_in_l.
        Обрати внимание: нет никакого 'const' и 'inf_res' в аргументах!
        Мы берем их из self (из самого себя).
        """
        # Создаем копию данных (как у тебя было)
        ofz_in_l = self.inf_data.copy()
        
        # Вместо const['...'] пишем self.config.attract_funds
        ofz_in_l['Привлекаемые средства'] = self.config.attract_funds
        ofz_in_l['Количество человек'] = self.config.people_count 
        ofz_in_l['Ставка купона'] = self.config.coupon_ofz_in
        ofz_in_l['На руках у человека, руб'] = ofz_in_l['Привлекаемые средства'] / ofz_in_l['Количество человек']
        ofz_in_l['Облигаций штук'] = ofz_in_l['На руках у человека, руб'] / self.config.face_ofz_in  # Номинал можно вынести в конфиг
        ofz_in_l['Инфляционный множитель']= (1 + self.inf_data['Инфляция']).cumprod()
        ofz_in_l['Номинал после индексации'] = self.config.face_ofz_in*ofz_in_l['Инфляционный множитель']
        ofz_in_l['Номинал на начало'] = float(self.config.face_ofz_in)
        ofz_in_l.loc[ofz_in_l.index > 0, 'Номинал на начало'] = ofz_in_l['Номинал после индексации'].shift(1).fillna(self.config.face_ofz_in)
        ofz_in_l['Индексация номинала'] = ofz_in_l['Номинал на начало'] * ofz_in_l['Инфляция']
        ofz_in_l['Купон, руб'] = ofz_in_l['Номинал после индексации'] * ofz_in_l['Ставка купона']
        ofz_in_l['Доход без вычета'] = ofz_in_l['Купон, руб'] * ofz_in_l['Облигаций штук']
        ofz_in_l ['Налоговый вычет, руб']= ofz_in_l['На руках у человека, руб'] * self.config.ndfl
        ofz_in_l['Доход с вычетом'] = ofz_in_l['Налоговый вычет, руб'] + ofz_in_l['Доход без вычета']
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

        self.data = ofz_in_l  
    
    def get_hand_amount(self):
        return self.data['На руках у человека, руб'].iloc[0] # подумать оставить iloc[0] или нет

# %%
class OFZ_PD:
    def __init__(self,config: ModelConfig, inf_res: pd.DataFrame,hand_column):
        self.config = config
        self.hand_people = hand_column.copy()
        self.year = inf_res['Год'].copy()
        self._calculate()

    def _calculate(self):
        ofz_pd = pd.DataFrame()
        ofz_pd['Год'] = self.year
        ofz_pd['Привлекаемые средства'] = self.config.attract_funds
        ofz_pd ["Количество человек"] = self.config.people_count
        ofz_pd ["Ставка купона"] = self.config.coupon_ofz_pd
        ofz_pd ["На руках у человека"] = self.hand_people
        ofz_pd ['Облигаций, штук'] = ofz_pd ['На руках у человека'] / self.config.face_ofz_pd
        ofz_pd ['Купон'] = self.config.face_ofz_pd * self.config.coupon_ofz_pd
        ofz_pd ["Доход, руб"] = ofz_pd ["Купон"] * ofz_pd ['Облигаций, штук']
        ofz_pd ['НДФЛ'] = ofz_pd ['Доход, руб'] * self.config.ndfl
        ofz_pd ['Доход после вычета налога'] = ofz_pd['Доход, руб'] - ofz_pd ['НДФЛ']
        self.data = ofz_pd

# %%
class DEPOZIT:
    def __init__(self,config,inf_res,hand_column) -> None:
        self.config = config
        self.year = inf_res[['Год']].copy()
        self.dep_rate = inf_res['Ставка депозита'].copy()
        self.hand_people = hand_column.copy()
        self._calculate()
    def _calculate(self):
        depozit = self.year
        depozit['Привлекаемые средства'] = self.config.attract_funds
        depozit['Количество человек'] = self.config.people_count 
        depozit['На руках у человека'] = self.hand_people
        depozit ['Ставка депозита'] = self.dep_rate
        depozit ['Коэффициент'] = (1 + self.dep_rate / 12) **12
        depozit ['Накопленный множитель'] = depozit ['Коэффициент'].cumprod()
        initial_amount = self.hand_people
        depozit ['Сумма на конец года'] = initial_amount * depozit ['Накопленный множитель']
        depozit ['Сумма на начало года'] = initial_amount
        depozit.loc [depozit.index > 0, 'Сумма на начало года'] = depozit['Сумма на конец года']. shift (1)
        depozit['Проценты']= depozit['Сумма на конец года'] - depozit['Сумма на начало года']
        depozit = depozit [["Год", 
                            "Привлекаемые средства", # перезаписываем в нужном порядке
                           "Количество человек", 
                           "На руках у человека",
                           "Ставка депозита",
                           "Коэффициент",
                           "Накопленный множитель",
                           "Сумма на начало года",
                           "Сумма на конец года",
                            "Проценты"]]
        self.data = depozit

# %%
def build_summary_table(
        inf_res: pd.DataFrame, 
        ofz_in_l: pd.DataFrame, 
        ofz_pd: pd.DataFrame, 
        depozit: pd.DataFrame 
        )-> pd.DataFrame:
    """
    Строит итоговую таблицу доходов по трём инструментам (ОФЗ-ИН, ОФЗ-ПД, депозит) с учётом инфляции и налогов
    Параметры:
        inf_res (pd.DataFrame): таблица с инфляцией (для расчёта инфляционного фактора).
        ofz_in_l, ofz_pd, depozit (pd.DataFrame): результаты соответствующих функций расчёта.
    Возвращает:
        pd.DataFrame: сводная таблица по инструментам с колонками:
            - Инструмент
            - Доход (суммарный за период)
            - Итоговая сумма (номинал + доход с вычетом/налогом)
            - Очистка инфляции
            - Реальный доход
    """
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
    return doxod_za_period # pyright: ignore[reportReturnType]

# %%
def build_government_ofz_in(
        config: ModelConfig, 
        inf_res: pd.DataFrame
        ) -> pd.DataFrame:
    """
    Параметры:
        const (dict): словарь с константами
        inf_res (pd.DataFrame): таблица с инфляцией.
    Возвращает:
        pd.DataFrame: таблица с колонками:
            - Год ('Итого' в последней строке)
            - Прибавка от инфляции
            - Тело долга
            - Расходы на купоны
            - Общие затраты
    """
    ofz_in_l_gos = inf_res.copy()
    ofz_in_l_gos['Прибавка от инфляции'] =config.attract_funds*ofz_in_l_gos['Инфляция']
    ofz_in_l_gos['Инфляционный множитель'] = (1+ofz_in_l_gos ['Инфляция']).cumprod()
    ofz_in_l_gos['Тело долга'] = config.attract_funds * ofz_in_l_gos['Инфляционный множитель']
    ofz_in_l_gos['Расходы на купоны'] = ofz_in_l_gos['Тело долга'] *config.coupon_ofz_in 
    ofz_in_l_gos['Общие затраты'] = ofz_in_l_gos['Прибавка от инфляции']+ofz_in_l_gos['Расходы на купоны']
    ofz_in_l_gos = ofz_in_l_gos[['Год','Инфляция','Прибавка от инфляции','Тело долга','Расходы на купоны','Общие затраты']]

# %%
    cols = ['Прибавка от инфляции', 'Тело долга', 'Расходы на купоны','Общие затраты']
    total_ofz_in_l_gos = pd.DataFrame(ofz_in_l_gos[cols].sum()).T
    total_ofz_in_l_gos['Год'] = 'Итого'
    itog_ofz_in_l_gos = pd.concat([ofz_in_l_gos,total_ofz_in_l_gos],ignore_index=True)
    return itog_ofz_in_l_gos


# %%
def build_government_ofz_pd(
            config: ModelConfig,
            ofz_pd: pd.DataFrame, 
            inf_res: pd.DataFrame) -> pd.DataFrame:
    """
    Рассчитывает нагрузку на государство по ОФЗ-ПД (купоны, возврат НДФЛ).
    Параметры:
        const (dict): словарь с константами 
        ofz_pd (pd.DataFrame): результат calculate_ofz_pd (нужен 'НДФЛ').
        ofz_in_l_gos (pd.DataFrame): результат build_government_ofz_in (нужен для фильтрации по годам).
    Возвращает:
        pd.DataFrame: таблица с колонками:
            - Год ('Итого' в последней строке)
            - Тело долга
            - Расходы на купон
            - Сумма возврата НДФЛ
            - Итого при учёте возврата НДФЛ
        """
    # Берем только строки, где Год != 'Итого'
    ofz_pd_gos = inf_res.copy()
    # ofz_pd_gos = ofz_in_l_gos[['Год']].copy()
    ofz_pd_gos['Тело долга'] = config.attract_funds
    ofz_pd_gos['Расходы на купон'] = ofz_pd_gos['Тело долга'] *config.coupon_ofz_pd 
    ofz_pd_gos['Сумма возврата,НДФЛ'] = ofz_pd['НДФЛ']* config.people_count
    ofz_pd_gos['Итого при учете возврата НДФЛ'] = ofz_pd_gos['Расходы на купон']-ofz_pd_gos['Сумма возврата,НДФЛ']
    ofz_pd_gos = ofz_pd_gos.drop(columns=['Ставка депозита'])


# %%
    cols2 = ['Расходы на купон','Сумма возврата,НДФЛ','Итого при учете возврата НДФЛ']
    total_ofz_pd_gos = pd.DataFrame([ofz_pd_gos[cols2].sum()])
    total_ofz_pd_gos['Год'] = 'Итого'
    itog_ofz_pd_gos = pd.concat([ofz_pd_gos,total_ofz_pd_gos],ignore_index=True)
    return itog_ofz_pd_gos

# %%
class FinancialModel:
    def __init__(self, config: ModelConfig | None = None, preparer: InflationRatePreparer | None = None):
        # Если конфиг не передали, создаем по умолчанию
        if config is None:
            config = ModelConfig()
        self.config = config

        if preparer is None:
            preparer = InflationRatePreparer()
        # self.inflation = None
        self.summary = None
        self.government_ofz_pd = None
        self.government_ofz_in_l = None
        self.preparer = preparer
        self.ofz_in = None
        # self._inflate()
        self.run_all()
        # self.inflation = preparer.data
    
    @property
    def inflation(self):
        return self.preparer.data
        
    # def _inflate(self):
    #     cb_data = InflationRatePreparer()
    #     self.inflation = cb_data.data        
    
    def run_all(self) -> tuple[DataFrame, DataFrame, DataFrame]:
        if self.inflation is None:
            raise ValueError("Данные инфляции не загружены — расчёт невозможен")
        self.ofz_in = OFZ_IN_L(config=self.config, inf_res=self.inflation)
        ofz_pd = OFZ_PD(config=self.config,inf_res=self.inflation,hand_column=self.ofz_in.get_hand_amount())
        dep = DEPOZIT(config=self.config,inf_res=self.inflation,hand_column=self.ofz_in.get_hand_amount())
        self.summary = build_summary_table(inf_res=self.inflation,ofz_in_l=self.ofz_in.data,ofz_pd=ofz_pd.data,depozit=dep.data)
        self.government_ofz_in_l = build_government_ofz_in(config=self.config,inf_res=self.inflation)
        self.government_ofz_pd = build_government_ofz_pd(config=self.config,ofz_pd=ofz_pd.data,inf_res=self.inflation)
        return self.summary,self.government_ofz_in_l,self.government_ofz_pd

    def update(self, 
               inf_override: list[float] | None = None, 
               deposit_rate=None, 
               deposit_decrement=None,
               attract_funds= None,
                coupon_ofz_in= None,
                coupon_ofz_pd= None,
                face_ofz_in= None,
                face_ofz_pd= None,
                people_count= None,
                ndfl= None):  # любые параметры для конфига
        """
        Обновить параметры модели и пересчитать.
        """
        # 1. Обновляем препаратор, если переданы параметры
        # if inf_override is not None or deposit_rate is not None or deposit_decrement is not None:
        #     self.preparer.set_parameters(
        #         inf_override=inf_override,
        #         deposit_rate=deposit_rate,
        #         deposit_decrement=deposit_decrement
        #     )

        # 2. Обновляем конфиг, если переданы параметры
        self.preparer.set_parameters(inf_override, deposit_rate, deposit_decrement)
        self.config.set_parameters(attract_funds, coupon_ofz_in, coupon_ofz_pd,
                               face_ofz_in, face_ofz_pd, people_count, ndfl)
        # 3. Пересчитываем модель
        self.run_all()
        # for key, value in config_kwargs.items():
        #     print(f"Пробуем установить {key} = {value}")
        #     if hasattr(self.config, key):
        #         setattr(self.config, key, value)
        #         print(f"Установлено, новое значение: {getattr(self.config, key)}")
        #     else:
        #         raise AttributeError(f"ModelConfig не имеет атрибута {key}")
