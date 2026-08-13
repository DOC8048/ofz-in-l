# ==== ВЕРСИЯ 1 РАЗОБРАТСЯ====
# import io

# # Создаём Excel-файл в памяти
# output = io.BytesIO()
# with pd.ExcelWriter(output, engine='openpyxl') as writer:
#     # Лист 1: Доход по инструментам
#     doxod_za_period.to_excel(writer, sheet_name='Доход', index=False)
    
#     # Лист 2: Нагрузка по ОФЗ-ИН
#     itog_ofz_in_l_gos.to_excel(writer, sheet_name='Нагрузка_ОФЗ_ИН', index=False)
    
#     # Лист 3: Нагрузка по ОФЗ-ПД
#     itog_ofz_pd_gos.to_excel(writer, sheet_name='Нагрузка_ОФЗ_ПД', index=False)
    
#     # Лист 4: Параметры модели (входные данные)
#     # Превращаем словарь const в DataFrame для сохранения
#     params_df = pd.DataFrame(list(const.items()), columns=['Параметр', 'Значение'])
#     params_df.to_excel(writer, sheet_name='Параметры', index=False)
    
#     # (Опционально) можно добавить лист с пользовательскими параметрами (inf_forecast, deposit_rate и т.д.)
#     user_params_df = pd.DataFrame(list(user_params.items()), columns=['Параметр', 'Значение'])
#     user_params_df.to_excel(writer, sheet_name='Пользовательские_параметры', index=False)

# # Подготовить данные для скачивания
# output.seek(0)

# # Кнопка скачивания
# st.sidebar.download_button(
#     label="📥 Скачать отчёт (Excel)",
#     data=output,
#     file_name="model_report.xlsx",
#     mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
# )
# В боковой панели (после кнопки сброса или в отдельном блоке)
# ===== ВЕРСИЯ 2 (ИЗУЧИТЬ ПРО sidebar) ЗДЕСЬ ИСПОЛЬЗЕТСЯ 2 КНОПКИ НЕ НРАВИТСЯ
import streamlit as st
import pandas as pd
from datetime import datetime
import io
def export_report_popover(
    doxod_za_period: pd.DataFrame,
    itog_ofz_in_l_gos: pd.DataFrame,
    itog_ofz_pd_gos: pd.DataFrame,
    const: dict,
    user_params: dict,
    sidebar: bool = True
    ):

    """
    Создаёт popover с настройками экспорта в Excel.

    Параметры:
        doxod_za_period: итоговая таблица доходов
        itog_ofz_in_l_gos: нагрузка ОФЗ-ИН
        itog_ofz_pd_gos: нагрузка ОФЗ-ПД
        const: словарь с константами модели
        user_params: словарь с пользовательскими параметрами
        sidebar: размещать в боковой панели (True) или в основной области (False)
    """
    container = st.sidebar if sidebar else st
    with container.popover("⚙️ Настройка экспорта"):
        st.markdown("**Выберите, что включить в отчёт:**")
        
        include_income = st.checkbox("Итоговый доход по инструментам", value=True)
        include_burden_oin = st.checkbox("Нагрузка ОФЗ-ИН", value=True)
        include_burden_pd = st.checkbox("Нагрузка ОФЗ-ПД", value=True)
        include_params = st.checkbox("Параметры модели", value=True)
        include_user_params = st.checkbox("Ставки", value=True)
        
        st.divider()
        
        # Кнопка скачивания внутри popover
        if st.button("📥 Скачать выбранное", use_container_width=True):
            # Проверяем, выбрано ли хоть что-то
            if not any([include_income, include_burden_oin, include_burden_pd, include_params, include_user_params]):
                st.error("Выберите хотя бы один раздел для экспорта.")
            else:
                # Генерируем Excel с выбранными листами
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    if include_income:
                        doxod_za_period.to_excel(writer, sheet_name='Доход', index=False)
                    if include_burden_oin:
                        itog_ofz_in_l_gos.to_excel(writer, sheet_name='Нагрузка_ОФЗ_ИН', index=False)
                    if include_burden_pd:
                        itog_ofz_pd_gos.to_excel(writer, sheet_name='Нагрузка_ОФЗ_ПД', index=False)
                    if include_params:
                        pd.DataFrame(list(const.items()), columns=['Параметр', 'Значение']).to_excel(writer, sheet_name='Параметры', index=False)
                    if include_user_params:
                        pd.DataFrame(list(user_params.items()), columns=['Параметр', 'Значение']).to_excel(writer, sheet_name='Ставки', index=False)
                
                output.seek(0)
                
                # Скачиваем
                st.download_button(
                    label="💾 Скачать файл",
                    data=output,
                    file_name=f"model_report_{datetime.now().strftime('%Y-%m-%d')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )
# ===== ВЕРСИЯ 3 ИЗУЧАЕМ ====== 
import streamlit as st
import pandas as pd
from datetime import datetime
import io

def export_report_popover_v2(
    doxod_za_period: pd.DataFrame,
    itog_ofz_in_l_gos: pd.DataFrame,
    itog_ofz_pd_gos: pd.DataFrame,
    const: dict,
    user_params: dict,
):
    """
    Создаёт popover с настройками экспорта. Кнопка скачивания теперь внутри popover.
    """
    with st.popover("⚙️ Настройка экспорта"):
        st.markdown("**Выберите, что включить в отчёт:**")
        
        include_income = st.checkbox("Итоговый доход по инструментам", value=True)
        include_burden_oin = st.checkbox("Нагрузка ОФЗ-ИН", value=True)
        include_burden_pd = st.checkbox("Нагрузка ОФЗ-ПД", value=True)
        include_params = st.checkbox("Параметры модели", value=True)
        include_user_params = st.checkbox("Ставки", value=True)
        
        st.divider()
        
        # ПРОВЕРКА: выбрано ли хоть что-то
        if not any([include_income, include_burden_oin, include_burden_pd, include_params, include_user_params]):
            st.warning("Выберите хотя бы один раздел для экспорта.")  
        else:
          
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                if include_income:
                    doxod_za_period.to_excel(writer, sheet_name='Доход', index=False)
                if include_burden_oin:
                    itog_ofz_in_l_gos.to_excel(writer, sheet_name='Нагрузка_ОФЗ_ИН', index=False)
                if include_burden_pd:
                    itog_ofz_pd_gos.to_excel(writer, sheet_name='Нагрузка_ОФЗ_ПД', index=False)
                if include_params:
                    pd.DataFrame(list(const.items()), columns=['Параметр', 'Значение']).to_excel(writer, sheet_name='Параметры', index=False)
                if include_user_params:
                    pd.DataFrame(list(user_params.items()), columns=['Параметр', 'Значение']).to_excel(writer, sheet_name='Ставки', index=False)
            
            output.seek(0)
            
            st.download_button(
                label="💾 Скачать отчёт",
                data=output,
                file_name=f"model_report_{datetime.now().strftime('%Y-%m-%d')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
# ===== ВАРИАНТ 4 СМТОРИМ ====
# export_utils.py
import io
import pandas as pd
from datetime import datetime

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
    """
    Генерирует Excel-файл в памяти с выбранными листами.
    Возвращает bytes для скачивания.
    """
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        if include_income:
            doxod_za_period.to_excel(writer, sheet_name='Доход', index=False)
        if include_burden_oin:
            itog_ofz_in_l_gos.to_excel(writer, sheet_name='Нагрузка_ОФЗ_ИН', index=False)
        if include_burden_pd:
            itog_ofz_pd_gos.to_excel(writer, sheet_name='Нагрузка_ОФЗ_ПД', index=False)
        if include_params:
            pd.DataFrame(list(const.items()), columns=['Параметр', 'Значение']).to_excel(writer, sheet_name='Параметры', index=False)
        if include_user_params:
            pd.DataFrame(list(user_params.items()), columns=['Параметр', 'Значение']).to_excel(writer, sheet_name='Пользовательские_параметры', index=False)
    output.seek(0)
    return output.getvalue()


# ===== продолжение варианта 4 в приложениии =====
# app.py (фрагмент)

# Импорты
from export_utils import generate_excel, get_default_filename

# ... весь остальной код ...

# --- Popover для экспорта ---
# with st.sidebar.popover("📤 Экспорт в Excel"):
#     st.markdown("**Выберите листы для экспорта:**")
    
#     include_income = st.checkbox("Итоговый доход", value=True)
#     include_burden_oin = st.checkbox("Нагрузка ОФЗ-ИН", value=True)
#     include_burden_pd = st.checkbox("Нагрузка ОФЗ-ПД", value=True)
#     include_params = st.checkbox("Параметры модели (const)", value=True)
#     include_user_params = st.checkbox("Пользовательские параметры", value=True)
    
#     st.divider()
    
#     if st.button("💾 Скачать"):
#         # Генерируем файл с учётом выбранных чекбоксов
#         excel_data = generate_excel(
#             doxod_za_period,
#             itog_ofz_in_l_gos,
#             itog_ofz_pd_gos,
#             const,
#             user_params,
#             include_income,
#             include_burden_oin,
#             include_burden_pd,
#             include_params,
#             include_user_params
#         )
        
#         # Кнопка скачивания появляется сразу после генерации
#         st.download_button(
#             label="📥 Скачать файл",
#             data=excel_data,
#             file_name=get_default_filename(),
#             mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
#             use_container_width=True
#         )
# Отсмотр варинатов 
with st.sidebar.popover("📤 Экспорт"):
    # чекбоксы...
    st.download_button(
        label="📥 Скачать отчёт",
        data=generate_excel(
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
    
# Вариант 5 раздельный
def generate_excel_bytes(
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
    """Чистая функция генерации байтов Excel. Не зависит от Streamlit."""
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        if include_income:
            doxod_za_period.to_excel(writer, sheet_name='Доход', index=False)
        if include_burden_oin:
            itog_ofz_in_l_gos.to_excel(writer, sheet_name='Нагрузка_ОФЗ_ИН', index=False)
        if include_burden_pd:
            itog_ofz_pd_gos.to_excel(writer, sheet_name='Нагрузка_ОФЗ_ПД', index=False)
        if include_params:
            pd.DataFrame(list(const.items()), columns=['Параметр', 'Значение']).to_excel(writer, sheet_name='Параметры', index=False)
        if include_user_params:
            pd.DataFrame(list(user_params.items()), columns=['Параметр', 'Значение']).to_excel(writer, sheet_name='Ставки', index=False)
    
    output.seek(0)
    return output.getvalue()

# Продолжение 5 варианта
with st.popover("📤 Экспорт отчёта", alignment="start"):
    st.subheader("Что включить в отчёт?")
    
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
            data=lambda: generate_excel_bytes(
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


