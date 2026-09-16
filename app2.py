import panel as pn

import function.cbr_inflation as cbr_inf
import model_2 as md  # твои классы
from function.api_in_function import get_deposit_rates

pn.extension(design='material')  # важно для работы виджетов

# ============================================
# 1. Логика и данные (отдельно от интерфейса)
# ============================================
    # твои функции получения инфляции и ставки
target_inf = cbr_inf.get_latest_target()
target_dep = get_deposit_rates()
target_dep = target_dep['rate'].iloc[-1]
deposit_decrement =  2.5
defaults = md.ModelConfig()
# return {
#         'attracted': 380_000_000_000,
#         'people': 2_000_000,
#         'coupon_oin': 2.5,
#         'coupon_pd': 13.74,
#         'nominal_oin': 10000,
#         'nominal_pd': 1000,
#         'ndfl': 13.0,
#         'inf_forecast': target_inf,
#         'deposit_rate': target_dep,
#         'deposit_decrement': 2.5
#     }
current_inflation = cbr_inf.get_latest_inflation()
# DEFAULTS = get_defaults()

# ============================================
# 2. Создаём виджеты (они НЕ привязаны к session_state)
# ============================================
number = pn.indicators.Number(
    label='Фактическая инфляция (ЦБ)',
    value=current_inflation,
    format='{value}%',
    font_size='20pt',
    title_size='15pt'
)

boxed_number = pn.Card(
    number,
    hide_header = True,
    styles={
        'background': 'var(--design-surface-color)',
        'border': '1px solid var(--panel-border-color)'
    },
    sizing_mode='stretch_width',
    margin=(10, 0, 10, 0),
)
inf_widget = pn.widgets.FloatInput(
    name='Прогноз инфляции на будущие годы, %',
    value= target_inf,
    step=0.1,
    format="0.00"
)

deposit_widget = pn.widgets.FloatInput(
    name='Текущая ставка депозита, %',
    value=target_dep,
    step=0.1,
    format="0.00"
)
deposit_decrements_widget = pn.widgets.NumberInput(
    name='Коэффициент снижения ставки, %',
    value= deposit_decrement,
    step=0.1,
    format='0.00'
)

# и так для всех параметров (привлекаемые средства, купоны и т.д.)
attracted_widget = pn.widgets.NumberInput(
    name='Привлекаемые средства, руб',
    value=defaults.attract_funds,
    step=10_000_000_000,
)
people_widget = pn.widgets.NumberInput(
    name="Количество человек, чел",
    value=defaults.people_count,
    step=100_000,
)
coupon_oin_widget = pn.widgets.FloatInput(
    name="Ставка купона ОФЗ-ИН (л),%", 
    value=defaults.coupon_ofz_in, 
    step=0.1, 
    format="0.00",
)
coupon_pd_widget = pn.widgets.FloatInput(
    name= "Ставка купона ОФЗ-ПД,%", 
    value=defaults.coupon_ofz_pd, 
    step=0.1, 
    format="0.00"
)

nominal_oin_widget = pn.widgets.NumberInput(
    name="Номинал ОФЗ-ИН, руб", 
    value=defaults.face_ofz_in, 
    step=1_000,
)
nominal_pd_widget = pn.widgets.NumberInput(
    name="Номинал ОФЗ-ПД, руб", 
    value=defaults.face_ofz_pd, 
    step=100,
)
ndfl_widget = pn.widgets.FloatInput(
    name="НДФЛ, %",
    value=defaults.ndfl,
    step=0.1,
    format="0.00",
)
# Кнопка сброса
reset_button = pn.widgets.Button(name='Сбросить все', button_type='warning', description='Сброс параметров модели')

# ============================================
# 3. Функция-конструктор модели (реактивная обёртка)
# ============================================
@pn.depends(
    inf = inf_widget.param.value,
    dep = deposit_widget.param.value,
    attracted = attracted_widget.param.value,
    dep_dec = deposit_decrements_widget.param.value,
    people = people_widget.param.value,
    cp_oin = coupon_oin_widget.param.value,
    cp_pd = coupon_pd_widget.param.value,
    nm_oin = nominal_oin_widget.param.value,
    nm_pd = nominal_pd_widget.param.value,
    ndfl_ = ndfl_widget.param.value
)

def create_model(inf,dep,attracted,dep_dec,people,cp_oin,cp_pd,nm_oin,nm_pd,ndfl_):
    # 1. Собираем конфиг
    config = md.ModelConfig(
        attract_funds=attracted,
        coupon_ofz_in=cp_oin,
        coupon_ofz_pd=cp_pd,
        face_ofz_in=nm_oin,
        face_ofz_pd=nm_pd,
        people_count=people,
        ndfl=ndfl_
    )
    # 2. Собираем препаратор
    preparer = md.InflationRatePreparer(
        inf_override=inf,
        deposit_rate=dep,
        deposit_decrement=dep_dec,
    )
    # 3. Создаём модель
    model = md.FinancialModel(config=config, preparer=preparer)
    return model  # возвращаем объект модели

# ============================================
# 4. Реактивный вывод таблиц
# ============================================
reactive_model = pn.bind(
    create_model,
    inf = inf_widget.param.value,
    dep = deposit_widget.param.value,
    attracted = attracted_widget.param.value,
    dep_dec = deposit_decrements_widget.param.value,
    people = people_widget.param.value,
    cp_oin = coupon_oin_widget.param.value,
    cp_pd = coupon_pd_widget.param.value,
    nm_oin = nominal_oin_widget.param.value,
    nm_pd = nominal_pd_widget.param.value,
    ndfl_ = ndfl_widget.param.value  
)

# ============================================
# 5. Реактивные панели для вывода (на основе reactive_model)
# ============================================

summary_pane = pn.bind(
    lambda model: pn.pane.DataFrame(
        model.summary, 
        width=800,
        formatters={
            'Доход': '{:.2f}'.format,
            'Итоговая сумма': '{:.2f}'.format,
            'Очистка инфляции': '{:.2f}'.format,
            'Реальный доход': '{:.2f}'.format
        }
    ) if model is not None else pn.pane.Markdown("Подождите, идёт расчёт..."),
    reactive_model
)

gov_in_pane = pn.bind(
    lambda model: pn.pane.DataFrame(
        model.government_ofz_in_l, 
        width=800,
        formatters={
            'Инфляция': '{:.2f}'.format,
            'Прибавка от инфляции': '{:.2f}'.format,
            'Тело долга': '{:.2f}'.format,
            'Расходы на купоны': '{:.2f}'.format,
            'Общие затраты': '{:.2f}'.format
            }) if model is not None else pn.pane.Markdown("Нет данных"),
    reactive_model
)

gov_pd_pane = pn.bind(
    lambda model: pn.pane.DataFrame(
        model.government_ofz_pd, 
        width=800,
        formatters={
            'Тело долга': '{:.2f}'.format,
            'Расходы на купоны': '{:.2f}'.format,
            'Сумма возврата,НДФЛ': '{:.2f}'.format,
            'Итого при учете возврата НДФЛ': '{:.2f}'.format, 
        }) if model is not None else pn.pane.Markdown("Нет данных"),
    reactive_model
)


# ============================================
# 5. Обработка кнопки сброса
# ============================================
def reset_values(event):
    # Меняем значения виджетов, а не session_state
    inf_widget.value = target_inf
    deposit_widget.value = target_dep 
    attracted_widget.value = defaults.attract_funds
    people_widget.value = defaults.people_count
    coupon_oin_widget.value = defaults.coupon_ofz_in
    coupon_pd_widget.value = defaults.coupon_ofz_pd
    nominal_oin_widget.value = defaults.face_ofz_in
    nominal_pd_widget.value = defaults.face_ofz_pd
    ndfl_widget.value = defaults.ndfl

reset_button.on_click(reset_values)

# ============================================
# 6. Сборка интерфейса
# ============================================
template = pn.template.FastListTemplate(
    title="Модель ОФЗ ИН (л)",
    sidebar=[
        boxed_number,
        pn.pane.Markdown('## Параметры модели'),
        inf_widget,
        deposit_widget,
        deposit_decrements_widget,
        attracted_widget,
        people_widget,
        coupon_oin_widget,
        coupon_pd_widget,
        nominal_oin_widget,
        nominal_pd_widget,
        ndfl_widget,
        reset_button
        ],
)

assert template.main is not None
template.main.append(
    pn.Column(
        pn.pane.Markdown('## Результаты'),
        pn.Card(
            summary_pane,
            title='Доходность',
            collapsed=True,
            width=800,
        ),
        pn.Card(
            gov_in_pane,
            title='Госдолг ОФЗ-ИН',
            collapsed=True,
            width=800,
        ),
        pn.Card(
            gov_pd_pane,
            title='Госдолг ОФЗ-ПД',
            collapsed=True,
            width=800,
        ),
    )
)
template.servable()