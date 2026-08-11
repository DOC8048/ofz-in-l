
# Только ставки по депозитам физических лиц, довостребования до 1 года
def get_deposit_rates():
    """
    Получает ставки по депозитам физических лиц, довостребования до 1 года
    
    Возвращает:
        pd.DataFreme:
            - date
            - rate
            - period_name
    """
    import requests
    import pandas as pd
    from datetime import datetime
    BASE_URL = "http://www.cbr.ru/dataservice"
    PUBLICATION_ID = 18
    DATASET_ID = 37
    end_date = datetime.now().strftime('%Y')
    params = {
        "publicationId": PUBLICATION_ID,
        "y1": 2020,
        "y2": end_date,
        "i_ids": [DATASET_ID],
        "m1_ids": [2], # разрез в рублях
        "m2_ids": [7]  # разрез до востребования 1 год
    }
    response = requests.get(f"{BASE_URL}/dataEx", params=params)
    data = response.json()
    raw = data.get("RawData", [])
    df = pd.DataFrame(raw)
    df.rename(columns={
        'period': 'period_name',
        'date': 'date_str',
        'value': 'rate',
        'measure_1_id': 'currency_id',
        'measure_2_id': 'term_id',
        'period_id': 'period_id',
        'rowId': 'row_id'
    }, inplace=True)
    df['date'] = pd.to_datetime(df['date_str'], format='%d.%m.%Y')
    df = df.sort_values('date').reset_index(drop=True)
    df = df[['date', 'rate', 'period_name']]
    return df

# Позволяет работать с API, но заранее нужно знать праметры: publication_id, dataset_id
def get_cbr_data(
        publication_id: int, 
        dataset_id: int, 
        m1_ids: list[int] | None=None, 
        m2_ids: list[int] | None=None, 
        year_from:int = 2020, 
        year_to: int=None):
    """
    Получает данные из API ЦБ (сервис /dataEx).`
    
    Параметры:
        publication_id (int): ID публикации (категории)
        dataset_id (int): ID показателя
        m1_ids (list[int]): ID первого разреза (например, валюта). По умолчанию None.
        m2_ids (list[int]): ID второго разреза (например, срок). По умолчанию None.
        year_from (int): начальный год. По умолчанию 2020
        year_to (int): текущий год
    
    Возвращает:
        pandas.DataFrame с колонками: date, rate, currency_id, term_id, period_name
    """
    import requests
    import pandas as pd
    from datetime import datetime
    BASE_URL = "http://www.cbr.ru/dataservice"
    if year_to is None:
            year_to = datetime.now().strftime('%Y')
    params = {
        "publicationId": publication_id,
        "y1": year_from,
        "y2": year_to,
        "i_ids": [dataset_id]
    }
    if m1_ids is not None:
        params["m1_ids"] = m1_ids if isinstance(m1_ids, list) else [m1_ids]
    if m2_ids is not None:
        params["m2_ids"] = m2_ids if isinstance(m2_ids, list) else [m2_ids]
    
    response = requests.get(f"{BASE_URL}/dataEx", params=params)
    response.raise_for_status()  # если статус не 200, выбросит исключение
    data = response.json()
    raw = data.get("RawData", [])
    if not raw:
        print("Нет данных для указанных параметров.")
        return pd.DataFrame()
    
    df = pd.DataFrame(raw)
    df.rename(columns={
        'period': 'period_name',
        'date': 'date_str',
        'value': 'rate',
        'measure_1_id': 'currency_id',
        'measure_2_id': 'term_id',
        'period_id': 'period_id',
        'rowId': 'row_id'
    }, inplace=True)
    df['date'] = pd.to_datetime(df['date_str'], format='%d.%m.%Y')
    df = df.sort_values('date').reset_index(drop=True)
    df = df[['date', 'rate', 'currency_id', 'term_id', 'period_name']]
    return df
