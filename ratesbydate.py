import requests
import xml.etree.ElementTree as ET
import pandas as pd
import os

def rates_date(date_str: str, iso_code: str) -> pd.DataFrame:
    """
    возвращает DataFrame с колонками
    date,iso,amount,rate,difference
    """
    envelope = f"""<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
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
    resp = requests.post(
        "http://api.cba.am/exchangerates.asmx",
        data=envelope.encode("utf-8"),
        headers=headers
    )
    resp.raise_for_status()
    #разбор xml
    root = ET.fromstring(resp.content)
    ns   = {"cba": "http://www.cba.am/"}
    rates = root.findall(".//cba:ExchangeRate", ns)
    rows = []
    for r in rates:
        rows.append({
            "requested_iso": iso_code,
            "date":          date_str,
            "iso":           r.findtext("cba:ISO",        namespaces=ns),
            "amount":        float(r.findtext("cba:Amount", namespaces=ns)),
            "rate":          float(r.findtext("cba:Rate",   namespaces=ns)),
            "difference":    float(r.findtext("cba:Difference", namespaces=ns)),
        })
    return pd.DataFrame(rows)

if __name__ == "__main__":
    date = "2025-05-01"
    iso  = "USD"
    #полный DataFrame
    df = rates_date(date, iso)
    #del ненужный дублирующий столбец requested_iso
    df = df.drop(columns=["requested_iso"])
    df = df.rename(columns={"iso": "currency"})
    #папка для данных
    os.makedirs("data", exist_ok=True)
    output_path = os.path.join("data", "rates.csv")
    #сохраняем в CSV
    df.to_csv(
        output_path,
        index=False,
        sep=';',
        decimal=',',
        encoding='utf-8-sig'
    )
    print(f"файл готов {output_path}")
