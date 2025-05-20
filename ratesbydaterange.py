import requests
import xml.etree.ElementTree as ET
import pandas as pd
from datetime import datetime, timedelta
import os

def rates_date(date_str: str, iso_code: str) -> dict:
    """
        возвращает DataFrame с колонками
        date,iso,amount,rate,difference
    """
    envelope = f"""<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope 
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" 
    xmlns:xsd="http://www.w3.org/2001/XMLSchema" 
    xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
  <soap:Body>
    <ExchangeRatesByDateByISO xmlns="http://www.cba.am/">
      <date>{date_str}T00:00:00</date>
      <ISO>{iso_code}</ISO>
    </ExchangeRatesByDateByISO>
  </soap:Body>
</soap:Envelope>"""
    headers = {
        "Content-Type": "text/xml; charset=utf-8",
        "SOAPAction":   "http://www.cba.am/ExchangeRatesByDateByISO"
    }

    resp = requests.post("http://api.cba.am/exchangerates.asmx",
                         data=envelope.encode("utf-8"),
                         headers=headers,
                         timeout=300)
    #если 500 ошибка — данных нет
    if resp.status_code == 500:
        return {"date": date_str, "currency": iso_code, "amount": "", "rate": ""}

    resp.raise_for_status()
    root = ET.fromstring(resp.content)
    ns = {"cba": "http://www.cba.am/"}

    #cначала проверка <CurrentDate>
    current_date = root.findtext(".//cba:CurrentDate", namespaces=ns) or ""
    if not current_date.startswith(date_str):
        #данных за date_str нет
        return {"date": date_str, "currency": iso_code, "amount": "", "rate": ""}

    #узел ExchangeRate
    rate_node = root.find(".//cba:ExchangeRate", ns)
    if rate_node is None:
        return {"date": date_str, "currency": iso_code, "amount": "", "rate": ""}

    # Извлекаем поля
    def txt(tag):
        return rate_node.findtext(f"cba:{tag}", namespaces=ns) or ""

    try:
        return {
            "date":     date_str,
            "currency": txt("ISO"),
            "amount":   float(txt("Amount")),
            "rate":     float(txt("Rate")),
            "difference": float(txt("Difference")),
        }
    except ValueError:
        # Если не получилось сконвертировать — оставляем пустые поля
        return {"date": date_str, "currency": iso_code, "amount": "", "rate": ""}


def rates_datelist(start_date: str, end_date: str, iso_list: list) -> pd.DataFrame:
    """
    проходит по датам от start_date до end_date
    и для каждой валюты из iso_list собирает данные,
    заполняя пустыми значениями, если курс за день отсутствует
    """
    start = datetime.fromisoformat(start_date)
    end   = datetime.fromisoformat(end_date)
    delta = timedelta(days=1)
    rows = []
    cur = start
    while cur <= end:
        ds = cur.strftime("%Y-%m-%d")
        for iso in iso_list:
            rec = rates_date(ds, iso)
            rows.append(rec)
            status = "+" if rec["amount"] != "" else "-"
            print(f"{status} {ds} {iso}")
        cur += delta

    return pd.DataFrame(rows)


if __name__ == "__main__":
    start    = "2024-05-01"
    end      = "2025-05-01"
    iso_list = ["USD"]
    df = rates_datelist(start, end, iso_list)
    #оставляем только нужные колонки и в нужном порядке
    df = df[["date","currency","amount","rate","difference"]]
    os.makedirs("data", exist_ok=True)
    filename = f"{'_'.join(iso_list).lower()}_{start}_{end}.csv"
    path = os.path.join("data", filename)
    df.to_csv(path,
              index=False,
              sep=';',
              decimal=',',
              encoding='utf-8-sig')
    print(f"\nфайл готов")
