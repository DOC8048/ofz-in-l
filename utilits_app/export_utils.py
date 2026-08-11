import pandas as pd
import io
def generate_excel(
        doxod_za_period: pd.DataFrame,
        itog_ofz_in_l_gos: pd.DataFrame,
        itog_ofz_pd_gos: pd.DataFrame,
        const: dict,
        user_params: dict,
        include_income: bool = True,
        include_burden_oin: bool = True,
        include_burden_pd: bool = True,
        include_params: bool = True,
        include_user_params: bool = True 
    ) -> bytes:
    """Функция генерации байтов Excel.

    Параметры:
        doxod_za_period: итоговая таблица доходов
        itog_ofz_in_l_gos: нагрузка ОФЗ-ИН
        itog_ofz_pd_gos: нагрузка ОФЗ-ПД
        const: словарь с константами модели
        user_params: словарь с пользовательскими параметрами
        include_income,include_burden_oin,include_burden_pd,include_params,include_user_params : булево значение по умолчанию = True
    """
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        if include_user_params:
            param_label = {
                'inf_override': 'Пользовательское значение инфляции',
                'deposit_rate': 'Пользовательская ставка депозита',
                'deposit_decrement': 'Коэффициент снижения ставки депозита'
            }
            rows = []
            for key,value in user_params.items():
                label = param_label.get(key,key)
                rows.append([label,value])
            pd.DataFrame(rows, columns=['Параметр', 'Значение']).to_excel(writer, sheet_name='Ставки', index=False)
            # pd.DataFrame(list(user_params.items()), columns=['Параметр', 'Значение']).to_excel(writer, sheet_name='Ставки', index=False)
        if include_params:
            pd.DataFrame(list(const.items()), columns=['Параметр', 'Значение']).to_excel(writer, sheet_name='Параметры', index=False)
        if include_income:
            doxod_za_period.to_excel(writer, sheet_name='Доход', index=False)
        if include_burden_oin:
            itog_ofz_in_l_gos.to_excel(writer, sheet_name='Нагрузка_ОФЗ_ИН', index=False)
        if include_burden_pd:
            itog_ofz_pd_gos.to_excel(writer, sheet_name='Нагрузка_ОФЗ_ПД', index=False)
        
    output.seek(0)
    return output.getvalue()