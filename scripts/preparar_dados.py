"""Gera as bases do app em data/ a partir dos CSV originais do Kaggle em data/raw/.

Uso:  python scripts/preparar_dados.py

- telco_churn.csv     -> cópia integral do original.
- hotel_bookings.csv  -> amostra de 30.000 linhas (seed 42), sem limpar nada.
                         As poucas linhas com defeitos raros (children vazio, adr negativa,
                         adr > 1000) entram sempre na amostra; o restante vem de
                         sample(random_state=42). Ver DECISOES.md.
- noshow_consultas.csv -> df.sample(n=30000, random_state=42), sem limpar nada.

No fim, confere se os "defeitos" que o app ensina a tratar continuam presentes.
Se algum sumir, o script falha com uma mensagem clara.
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parent.parent
RAW = RAIZ / "data" / "raw"
DATA = RAIZ / "data"

N_AMOSTRA = 30_000
SEED = 42

ORIGINAIS = {
    "telco": RAW / "WA_Fn-UseC_-Telco-Customer-Churn.csv",
    "hotel": RAW / "hotel_bookings.csv",
    "noshow": RAW / "KaggleV2-May-2016.csv",
}


def amostra_hotel(df: pd.DataFrame) -> pd.DataFrame:
    raros = df["children"].isna() | (df["adr"] < 0) | (df["adr"] > 1000)
    resto = df[~raros].sample(n=N_AMOSTRA - int(raros.sum()), random_state=SEED)
    return pd.concat([resto, df[raros]])


def resumo(nome: str, df: pd.DataFrame) -> None:
    pct_nulos = df.isna().sum().sum() / df.size * 100
    print(
        f"{nome}: {len(df):,} linhas, {df.shape[1]} colunas, "
        f"{pct_nulos:.2f}% células nulas, {int(df.duplicated().sum()):,} linhas duplicadas"
    )


def conferir(nome: str, df: pd.DataFrame, defeitos: dict[str, bool]) -> list[str]:
    faltando = [d for d, presente in defeitos.items() if not presente]
    for d, presente in defeitos.items():
        print(f"   {'ok   ' if presente else 'FALTA'} {d}")
    return [f"{nome}: {d}" for d in faltando]


def main() -> int:
    ausentes = [str(p) for p in ORIGINAIS.values() if not p.exists()]
    if ausentes:
        print("Arquivos originais não encontrados em data/raw/:")
        for p in ausentes:
            print(f"  - {p}")
        print("Baixe as três bases do Kaggle (ver README.md) e rode de novo.")
        return 1

    problemas: list[str] = []

    # Telco: cópia integral, byte a byte.
    destino = DATA / "telco_churn.csv"
    shutil.copyfile(ORIGINAIS["telco"], destino)
    telco = pd.read_csv(destino)
    resumo("telco_churn.csv", telco)
    problemas += conferir(
        "telco",
        telco,
        {
            "TotalCharges com espaços em branco (texto)": telco["TotalCharges"]
            .astype(str)
            .str.strip()
            .eq("")
            .any(),
            "SeniorCitizen como 0/1": set(telco["SeniorCitizen"].unique()) == {0, 1},
            "categorias 'No internet service'": telco["OnlineSecurity"].eq("No internet service").any(),
        },
    )

    # Hotel: amostra.
    hotel = amostra_hotel(pd.read_csv(ORIGINAIS["hotel"]))
    hotel.to_csv(DATA / "hotel_bookings.csv", index=False)
    hotel = pd.read_csv(DATA / "hotel_bookings.csv")
    resumo("hotel_bookings.csv", hotel)
    problemas += conferir(
        "hotel",
        hotel,
        {
            "company com > 80% nulos": hotel["company"].isna().mean() > 0.8,
            "reservation_status presente": "reservation_status" in hotel.columns,
            "reservation_status_date presente": "reservation_status_date" in hotel.columns,
            "children com nulos": hotel["children"].isna().any(),
            "adr negativa": (hotel["adr"] < 0).any(),
            "adr acima de 1000": (hotel["adr"] > 1000).any(),
            "adr igual a 0": (hotel["adr"] == 0).any(),
            "meal 'Undefined'": hotel["meal"].eq("Undefined").any(),
            "reservas sem hóspedes": ((hotel["adults"] + hotel["children"].fillna(0) + hotel["babies"]) == 0).any(),
            "linhas duplicadas": hotel.duplicated().any(),
        },
    )

    # No-show: amostra simples.
    noshow = pd.read_csv(ORIGINAIS["noshow"]).sample(n=N_AMOSTRA, random_state=SEED)
    noshow.to_csv(DATA / "noshow_consultas.csv", index=False)
    noshow = pd.read_csv(DATA / "noshow_consultas.csv")
    resumo("noshow_consultas.csv", noshow)
    mesmo_dia = noshow["ScheduledDay"].str[:10] == noshow["AppointmentDay"].str[:10]
    problemas += conferir(
        "noshow",
        noshow,
        {
            "Age com valores <= 0": (noshow["Age"] <= 0).any(),
            "Age negativa": (noshow["Age"] < 0).any(),
            "Handcap acima de 1": (noshow["Handcap"] > 1).any(),
            "consultas marcadas no mesmo dia": mesmo_dia.any(),
            "pacientes com várias consultas": noshow["PatientId"].duplicated().any(),
        },
    )

    if problemas:
        print("\nERRO: defeitos esperados sumiram das bases geradas:")
        for p in problemas:
            print(f"  - {p}")
        print("Os blocos de tratamento dependem desses defeitos. Revise a amostragem.")
        return 1

    print("\nBases geradas em data/ e defeitos conferidos.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
