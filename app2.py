import pandas as pd
import panel as pn
import param
from panel_material_ui import Drawer, Page

import function.cbr_inflation as cbr_inf
import model_2 as md  # твои классы
from function.api_in_function import get_deposit_rates
from function.display_rate_depo_and_key import fig

pn.extension('plotly')  # важно для работы виджетов

# ============================================
# 1. Логика и данные (отдельно от интерфейса)
# ============================================
    # твои функции получения инфляции и ставки
target_inf = cbr_inf.get_latest_target()
target_dep = get_deposit_rates()
target_dep = target_dep['rate'].iloc[-1]
deposit_decrement =  2.5
defaults = md.ModelConfig()
current_inflation = cbr_inf.get_latest_inflation()
# виджет вывода ключевой метрики
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
# ============================================
# 2. Создаём виджеты (они НЕ привязаны к session_state)
# ============================================

class Scenario(param.Parameterized):
    inf = param.Number(default=target_inf,step=0.1)
    dep = param.Number(default=target_dep, step=0.1)
    dep_dec = param.Number(default=deposit_decrement, step=0.1)
    attracted = param.Number(default=defaults.attract_funds, step=10_000_000_000)
    people = param.Number(default=defaults.people_count,step=100_000)
    coupon_oin = param.Number(default=defaults.coupon_ofz_in,step=0.1)
    coupon_pd = param.Number(default=defaults.coupon_ofz_pd, step=0.1)
    nominal_oin = param.Number(default=defaults.face_ofz_in, step=1_000)
    nominal_pd = param.Number(default=defaults.face_ofz_pd, step=100)
    ndfl = param.Number(default=defaults.ndfl)

    _ALL_PARAMS = ['inf', 'dep', 'dep_dec', 'attracted', 'people',  # noqa: RUF012
                       'coupon_oin', 'coupon_pd', 'nominal_oin', 'nominal_pd', 'ndfl']
    
    @param.depends(*_ALL_PARAMS)
    def _get_model(self):
        config = md.ModelConfig(
            attract_funds=self.attracted,
            coupon_ofz_in=self.coupon_oin,
            coupon_ofz_pd=self.coupon_pd,
            face_ofz_in=self.nominal_oin,
            face_ofz_pd=self.nominal_pd,
            people_count=self.people,
            ndfl= self.ndfl
        )
        preparer = md.InflationRatePreparer(
            inf_override=self.inf,
            deposit_rate=self.dep,
            deposit_decrement=self.dep_dec
        )
        return md.FinancialModel(config=config,preparer=preparer)
    
    @staticmethod
    def _money_ru(x):
        if pd.isna(x):
            return ''
        return f'{x:_.2f}'.replace('_','\u00A0').replace('.',',')
    
    @param.depends(*_ALL_PARAMS)
    def summary_pane(self):
        return pn.pane.DataFrame(
            self._get_model().summary,
            formatters= {
               'Доход': self._money_ru,
               'Итоговая сумма': self._money_ru,
               'Очистка инфляции': self._money_ru,
               'Реальный доход': self._money_ru
            })
    @param.depends(*_ALL_PARAMS)
    def gov_in(self):
        return pn.pane.DataFrame(
            self._get_model().government_ofz_in_l,
            formatters={
              'Инфляция': '{:.3f}'.format,
              'Прибавка от инфляции': self._money_ru,
              'Тело долга': self._money_ru,
              'Расходы на купоны': self._money_ru,
              'Общие затраты': self._money_ru
            })
    @param.depends(*_ALL_PARAMS)
    def gov_pd(self):
        return pn.pane.DataFrame(
            self._get_model().government_ofz_pd,
            formatters={
              'Инфляция': '{:.3f}'.format,
               'Тело долга': self._money_ru,
               'Расходы на купоны': self._money_ru,
               'Сумма возврата,НДФЛ': self._money_ru,
               'Итого при учете возврата НДФЛ': self._money_ru
            })   

base_model = Scenario(name='Базовый') 
opt_model = Scenario(name = 'Оптимистичный', inf = 4, dep_dec = 1,dep=3)
pes_model = Scenario(name= 'Пессимистичный',inf=10,dep=25, dep_dec=3 )
print(base_model.name)
scenarios = {'Базовый': base_model, 'Оптимистичный': opt_model, 'Пессимистичный': pes_model}    
selector = pn.widgets.RadioButtonGroup(
    name='Сценарий',
    options=list(scenarios.keys()),
    value='Базовый',
    button_type='primary',
)
def switch_tab(event):
    # event.new — новое значение selector.value (например, 'Оптимистичный')
    idx = list(scenarios.keys()).index(event.new)
    tabs.active = idx

selector.param.watch(switch_tab, 'value')
@pn.depends(selector) # type: ignore
def get_widgets(name):
    return pn.Param(
        scenarios[name].param,
        widgets={
            'inf': {
                'widget_type':pn.widgets.FloatInput,
                'name':'Прогноз инфляции, %',
                'format': '0.00'
            },
            'dep': {
                'widget_type': pn.widgets.FloatInput,
                'name': 'Ставка депозита, %',
                'format': '0.00'
            },
            'dep_dec': {
                'widget_type':pn.widgets.FloatInput,
                'name': 'Снижение ставки депозита, %',
                'format': '0.00'
            },
            'attracted': {
                'widget_type':pn.widgets.FloatInput,
                'name': 'Привлекаемые средства, руб',
            },
            'people': {
                'widget_type':pn.widgets.FloatInput,
                'name': 'Количество человек',
            },
            'coupon_oin': {
                'widget_type':pn.widgets.FloatInput,
                'name': 'Купон ОФЗ-ИН, %',
                'format': '0.00'
            },
            'coupon_pd': {
                'widget_type':pn.widgets.FloatInput,
                'name': 'Купон ОФЗ-ПД, %',
                'format': '0.00'
            },
            'nominal_oin': {
                'widget_type':pn.widgets.FloatInput,
                'name': 'Номинал ОФЗ-ИН,руб'
            },
            'nominal_pd': {
                'widget_type':pn.widgets.FloatInput,
                'name': 'Номинал ОФЗ-ПД, руб'
            },
            'ndfl': {
                'widget_type':pn.widgets.FloatInput,
                'name': 'НДФЛ, %',
                'format': '0.00'
            },
    },

    show_labels=True,
    )
drawer = Drawer(
    pn.pane.Plotly(
                    fig,
                    sizing_mode='stretch_both',
                    margin=0
                    ), # ваш график
                    anchor="right",   # выезжает слева
                    size=750,        # ширина панели в пикселях
                    variant="docked",
                    dock_position="middle",
                    sizing_mode='stretch_both',
                    margin=0
)

# reset_button = pn.widgets.Button(name='Сбросить все', button_type='warning', description='Сброс параметров модели')


# ============================================
# 5. Обработка кнопки сброса
# ============================================
# def reset_values(event):
#     # Меняем значения виджетов, а не session_state
#     inf_widget.value = target_inf
#     deposit_widget.value = target_dep 
#     attracted_widget.value = defaults.attract_funds
#     people_widget.value = defaults.people_count
#     coupon_oin_widget.value = defaults.coupon_ofz_in
#     coupon_pd_widget.value = defaults.coupon_ofz_pd
#     nominal_oin_widget.value = defaults.face_ofz_in
#     nominal_pd_widget.value = defaults.face_ofz_pd
#     ndfl_widget.value = defaults.ndfl

# reset_button.on_click(reset_values)
tabs = pn.Tabs(
    ('Базовый', pn.Column(
        pn.pane.Markdown('### Доходность'),
        base_model.summary_pane,
        pn.pane.Markdown('### Госдолг ОФЗ-ИН'),
        base_model.gov_in,
        pn.pane.Markdown('### Госдолг ОФЗ-ПД'),
        base_model.gov_pd,
    )),
    ('Оптимистичный', pn.Column(
        pn.pane.Markdown('### Доходность'),
        opt_model.summary_pane,
        pn.pane.Markdown('### Госдолг ОФЗ-ИН'),
        opt_model.gov_in,
        pn.pane.Markdown('### Госдолг ОФЗ-ПД'),
        opt_model.gov_pd,
    )),
    ('Пессимистичный', pn.Column(
        pn.pane.Markdown('### Доходность'),
        pes_model.summary_pane,
        pn.pane.Markdown('### Госдолг ОФЗ-ИН'),
        pes_model.gov_in,
        pn.pane.Markdown('### Госдолг ОФЗ-ПД'),
        pes_model.gov_pd,
    )),
)

page= Page(
    title="Модель ОФЗ ИН (л)",
    sidebar_width=450,
    sidebar=[
        pn.pane.Markdown('## Параметры'),
        boxed_number,
        selector,
        get_widgets,
    ],
    main=[
        tabs,
        drawer],
    sizing_mode='stretch_width',
    margin=0 
)
page.servable()
