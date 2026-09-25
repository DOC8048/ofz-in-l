from datetime import date

import pandas as pd

import function.cbr_inflation as cbr_inf
from function.api_in_function import get_deposit_rates
from function.display_rate_depo_and_key import avg_result


class InflationRatePreparer:
    """
    Класс для подготовки таблицы инфляции и ставки депозита.
    Хранит параметры и итоговый DataFrame.
    """
    def __init__(self, 
                 inf_override:  list[float] | float|  None = None,
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
            dec = avg_result()
        else:
            dec = self.deposit_decrement

        base = value # оставил для наглядности
        inf_res['Ставка депозита'] = base - dec * inf_res.index
        inf_res[['Инфляция','Ставка депозита']] = inf_res[['Инфляция','Ставка депозита']]/100
        self.data = inf_res

    def set_parameters(self, inf_override:  list[float] | float|  None = None, deposit_rate=None, deposit_decrement=None):
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