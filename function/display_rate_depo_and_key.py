# %%
# Требуется, чтобы локаль поддерживала русский язык
import cbrapi as cb
import pandas as pd

from function.api_in_function import get_deposit_rates

# %%
key = cb.get_key_rate(first_date='2022-01-01',period='M').reset_index()

# %%
dep_rate = get_deposit_rates(start_years=2022)
dep_rate['date'] = dep_rate['date'].dt.to_period('M')

# %%
dep_rate['rate'] = dep_rate['rate'].shift(periods=-1)
dep_rate = dep_rate.dropna(subset=['rate']).reset_index(drop=True)

# %%
result = pd.merge(
    key,
    dep_rate,
    left_on='DATE',
    right_on='date',
    how= 'left',
)
# %%
result = result.iloc[1:].reset_index(drop=True)
result = result[[
    'DATE',
    'KEY_RATE',
    'rate'
]]

result['rate'] = result['rate'].ffill()
result['DATE'] = result['DATE'].dt.to_timestamp()

# %%
def avg_result () -> float:
    return result['KEY_RATE'].mean() - result['rate'].mean()

avg = avg_result()
# %%
import plotly.graph_objects as go

fig = go.Figure()
fig.add_trace(go.Scatter(
    x=result['DATE'], y=result['KEY_RATE'],
    mode='lines+markers',
    name='Ключевая ставка ЦБ, %',
))
fig.add_trace(go.Scatter(
    x=result['DATE'], y=result['rate'],
    mode='lines+markers',
    name='Ставка депозита, %',
))
fig.update_layout(
    title='Динамика ставок (2025–2026)',
    height=700,
    autosize=True,
    xaxis_title='Дата',
    yaxis_title='Ставка, %',
    hovermode='x unified',
    legend={'orientation': 'h', 'yanchor': 'bottom', 'y': 1.02, 'xanchor': 'right', 'x': 1},
)

fig.add_annotation(
    x=0.4, y=0.2,           # 2% от левого края, 98% от низа
    xref='paper', yref='paper',
    text=f"Средняя разница между ставками: {avg:.2f}%",
    showarrow=False,
    font={'size': 14},
    bgcolor='rgba(255,255,255,0.8)',
    bordercolor='gray',
    borderwidth=1,
    xanchor='left',
    yanchor='top',
)
fig.show()
