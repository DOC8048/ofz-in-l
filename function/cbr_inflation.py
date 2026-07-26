import pandas as pd
import requests
from xml.etree import ElementTree as ET
from datetime import datetime

def get_inflation(start_date='2013-01-01', end_date=None):
    """
    Получает данные по инфляции (индекс потребительских цен) с сайта ЦБ РФ.
    Возвращает pandas Series с индексом из дат и значениями инфляции (в процентах).
    """
    if end_date is None:
        end_date = datetime.now().strftime('%Y-%m-%d')
    
    url = "https://cbr.ru/secinfo/secinfo.asmx"
    headers = {
        "Content-Type": "text/xml; charset=utf-8",
        "SOAPAction": "http://web.cbr.ru/InflationXML"
    }
    
    body = f'''<?xml version="1.0" encoding="utf-8"?>
    <soap:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                   xmlns:xsd="http://www.w3.org/2001/XMLSchema"
                   xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
      <soap:Body>
        <InflationXML xmlns="http://web.cbr.ru/">
          <DateFrom>{start_date}</DateFrom>
          <DateTo>{end_date}</DateTo>
        </InflationXML>
      </soap:Body>
    </soap:Envelope>'''
    
    response = requests.post(url, data=body, headers=headers)
    
    if response.status_code != 200:
        raise Exception(f"Ошибка HTTP: {response.status_code}")
    
    root = ET.fromstring(response.content)
    
    # Данные лежат в тегах <RI>
    data = []
    for item in root.findall('.//RI'):
        dts_elem = item.find('DTS')
        inf_elem = item.find('infVal')
        target_elem = item.find('AimVal')
        if dts_elem is not None and inf_elem is not None and target_elem is not None:
            # Дата в формате MM.YYYY, превратим в datetime (первый день месяца)
            month, year = dts_elem.text.split('.')
            date_str = f"{year}-{month}-01"
            date = pd.to_datetime(date_str)
            inf_val = float(inf_elem.text.replace(',','.'))
            target_val = float(target_elem.text.replace(',','.'))
            data.append({'date': date, 'inflation': inf_val, 'target': target_val})
    
    # Если не нашли, попробуем с пространством имён (на случай, если потребуется)
    if not data:
        ns = {'cbr': 'http://web.cbr.ru/'}
        for item in root.findall('.//cbr:RI', ns):
            dts_elem = item.find('cbr:DTS', ns)
            inf_elem = item.find('cbr:infVal', ns)
            target_elem = item.find('cbr:AimVal', ns)
            if dts_elem is not None and inf_elem is not None and target_elem is not None:
                month, year = dts_elem.text.split('.')
                date_str = f"{year}-{month}-01"
                date = pd.to_datetime(date_str)
                inf_val = float(inf_elem.text.replace(',','.'))
                target_val = float(target_elem.text.replace(',','.'))
                data.append({'date': date, 'inflation': inf_val, 'target': target_val})
    
    if not data:
        raise ValueError("Не удалось извлечь данные из ответа.")
    
    df = pd.DataFrame(data)
    df = df.sort_values('date').reset_index(drop=True)
    return df

def get_latest_inflation():
    df = get_inflation()
    return df['inflation'].iloc[-1]
    
def get_latest_target():
    df = get_inflation()
    return df['target'].iloc[-1]