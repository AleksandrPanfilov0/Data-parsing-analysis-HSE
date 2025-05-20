import pandas as pd
import matplotlib.pyplot as plt


csv_file = "data/usd_2024-05-01_2025-05-01.csv"
currency_name = "USD"

df = pd.read_csv(csv_file, sep=";", encoding="utf-8-sig")
df["date"] = pd.to_datetime(df["date"], errors="coerce")
df["rate"] = pd.to_numeric(df["rate"], errors="coerce")
df = df.dropna(subset=["date", "rate"])

#скользящее среднее по 7 дням
df["rolling_avg"] = df["rate"].rolling(window=7).mean()

#визуализация
plt.figure(figsize=(12, 6))
plt.plot(df["date"], df["rate"], label="Курс " + currency_name, color="blue")
plt.plot(df["date"], df["rolling_avg"], label="Скользящее среднее (7 дней)", color="orange", linestyle="--")
plt.title(f"Курс {currency_name} с {df['date'].min().date()} по {df['date'].max().date()}")
plt.xlabel("Дата")
plt.ylabel("Курс")
plt.grid(True)
plt.legend()
plt.tight_layout()
plt.savefig(f"{currency_name}_trend.png", dpi=150)
plt.show()
