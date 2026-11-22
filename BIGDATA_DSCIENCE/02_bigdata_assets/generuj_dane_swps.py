"""Generator SWPS, adaptacja kodu Marcina Albiniaka z AI_analiza_danych_tools_11.
Domyślnie 100 000 pozycji, wariant 5 mln przez --n 5000000.
Zachowano katalog, mapę miast, reguły cen w groszach, proporcje kolorów i zapis partiami.
Usunięto zależność Faker, która w oryginale sprawdzała dostępność nazw z jawnej mapy.
Dane syntetyczne, ceny stanowią założenie ćwiczenia, nie cennik rynkowy.
Jeden wiersz = pozycja syntetyczna. To nie tabela sesji ani unikalnych klientów.
CSV: UTF-8 z BOM, separator średnik, przecinek dziesiętny.
"""
import argparse
import csv
import random
import sys
import time
from pathlib import Path
N = 100000
KOLUMNY = ('id', 'nazwa', 'ilość sztuk', 'cena netto', 'kolor', 'miasto', 'województwo', 'kategoria', 'wartość netto')
KOLORY = ('czerwony', 'zielony', 'czarny', 'żółty', 'inne')
PROCENTY = (25, 25, 20, 10, 20)
PRODUKTY = (('Opaska kablowa pojedyncza', 'Akcesoria elektroniczne', 1, 5), ('Rezystor pojedynczy', 'Podzespoły elektroniczne', 1, 8), ('Przewód USB podstawowy', 'Akcesoria elektroniczne', 5, 35), ('Przewód USB-C premium', 'Akcesoria elektroniczne', 40, 180), ('Ładowarka USB-C 65 W', 'Akcesoria elektroniczne', 60, 250), ('Powerbank 20000 mAh', 'Akcesoria elektroniczne', 80, 350), ('Mysz przewodowa', 'Peryferia komputerowe', 15, 80), ('Mysz gamingowa premium', 'Peryferia komputerowe', 180, 750), ('Klawiatura biurowa', 'Peryferia komputerowe', 30, 180), ('Klawiatura mechaniczna premium', 'Peryferia komputerowe', 250, 1100), ('Dysk SSD 1 TB', 'Podzespoły komputerowe', 180, 550), ('Karta graficzna premium', 'Podzespoły komputerowe', 3500, 13000), ('Monitor biurowy 24 cale', 'Komputery i monitory', 300, 850), ('Monitor profesjonalny 32 cale', 'Komputery i monitory', 2200, 11000), ('Laptop podstawowy', 'Komputery i monitory', 1100, 2600), ('Laptop biznesowy', 'Komputery i monitory', 2800, 7500), ('Laptop gamingowy premium', 'Komputery i monitory', 6500, 22000), ('Stacja robocza profesjonalna', 'Komputery i monitory', 12000, 35000), ('Smartfon podstawowy', 'Urządzenia mobilne', 250, 850), ('Smartfon klasy średniej', 'Urządzenia mobilne', 900, 2300), ('Smartfon flagowy', 'Urządzenia mobilne', 2800, 7500), ('Tablet podstawowy', 'Urządzenia mobilne', 350, 1300), ('Tablet profesjonalny', 'Urządzenia mobilne', 2500, 8500), ('Smartwatch', 'Urządzenia mobilne', 150, 2400), ('Słuchawki przewodowe', 'Audio i RTV', 15, 200), ('Słuchawki bezprzewodowe premium', 'Audio i RTV', 450, 1800), ('Głośnik Bluetooth', 'Audio i RTV', 60, 1200), ('Soundbar premium', 'Audio i RTV', 1500, 6500), ('Telewizor LED 43 cale', 'Audio i RTV', 850, 2300), ('Telewizor OLED 65 cali', 'Audio i RTV', 3800, 14000), ('Projektor kina domowego premium', 'Audio i RTV', 7000, 30000), ('Router Wi-Fi', 'Sieci komputerowe', 70, 650), ('System Wi-Fi mesh premium', 'Sieci komputerowe', 800, 3500), ('Czajnik elektryczny podstawowy', 'Małe AGD', 35, 150), ('Czajnik elektryczny premium', 'Małe AGD', 180, 900), ('Toster', 'Małe AGD', 50, 450), ('Blender ręczny', 'Małe AGD', 60, 500), ('Robot kuchenny planetarny', 'Małe AGD', 350, 4500), ('Ekspres przelewowy', 'Małe AGD', 80, 650), ('Ekspres automatyczny premium', 'Małe AGD', 2500, 12000), ('Frytkownica beztłuszczowa', 'Małe AGD', 180, 1500), ('Żelazko parowe', 'Małe AGD', 60, 500), ('Odkurzacz tradycyjny', 'Małe AGD', 180, 1100), ('Robot sprzątający premium', 'Małe AGD', 1800, 6500), ('Pralka podstawowa', 'Duże AGD', 1000, 2000), ('Pralka premium', 'Duże AGD', 2800, 7500), ('Suszarka z pompą ciepła', 'Duże AGD', 1500, 5500), ('Lodówka z zamrażarką', 'Duże AGD', 1100, 3500), ('Lodówka side-by-side premium', 'Duże AGD', 4500, 16000), ('Zmywarka podstawowa', 'Duże AGD', 950, 2200), ('Zmywarka premium', 'Duże AGD', 2600, 6500), ('Piekarnik do zabudowy', 'Duże AGD', 900, 4500), ('Płyta indukcyjna premium', 'Duże AGD', 2200, 8500), ('Kuchenka mikrofalowa', 'Małe AGD', 200, 1500))
MIASTA_REGIONY = {'dolnośląskie': ('Wrocław', 'Legnica', 'Wałbrzych'), 'kujawsko-pomorskie': ('Bydgoszcz', 'Toruń', 'Włocławek'), 'lubelskie': ('Lublin', 'Chełm', 'Zamość'), 'lubuskie': ('Gorzów Wielkopolski', 'Zielona Góra', 'Nowa Sól'), 'łódzkie': ('Łódź', 'Piotrków Trybunalski', 'Pabianice'), 'małopolskie': ('Kraków', 'Tarnów', 'Nowy Sącz'), 'mazowieckie': ('Warszawa', 'Radom', 'Płock'), 'opolskie': ('Opole', 'Nysa', 'Brzeg'), 'podkarpackie': ('Rzeszów', 'Przemyśl', 'Krosno'), 'podlaskie': ('Białystok', 'Łomża', 'Suwałki'), 'pomorskie': ('Gdańsk', 'Gdynia', 'Słupsk'), 'śląskie': ('Katowice', 'Gliwice', 'Częstochowa'), 'świętokrzyskie': ('Kielce', 'Ostrowiec Świętokrzyski', 'Starachowice'), 'warmińsko-mazurskie': ('Olsztyn', 'Elbląg', 'Ełk'), 'wielkopolskie': ('Poznań', 'Kalisz', 'Konin'), 'zachodniopomorskie': ('Szczecin', 'Koszalin', 'Świnoujście')}

def pula_lokalizacji():
    return tuple(sorted(((miasto, woj) for woj, miasta in MIASTA_REGIONY.items() for miasto in miasta)))

def liczebnosci_kolorow(n):
    liczby = [n * procent // 100 for procent in PROCENTY]
    kolejnosc = sorted(range(len(PROCENTY)), key=lambda i: -(n * PROCENTY[i] % 100))
    for indeks in kolejnosc[:n - sum(liczby)]:
        liczby[indeks] += 1
    return liczby

def kwota(grosze):
    """Dokładny zapis do dwóch miejsc, bez błędów arytmetyki float."""
    return f'{grosze // 100},{grosze % 100:02d}'

def generuj(n=N, output=Path('dane_syntetyczne.csv'), seed=42, batch_size=50000):
    if n < 1 or batch_size < 1:
        raise ValueError('n i batch_size muszą być dodatnie')
    output = Path(output)
    if output.exists():
        raise FileExistsError(f'Plik już istnieje: {output}. Wybierz inną nazwę.')
    lokalizacje = pula_lokalizacji()
    rng = random.Random(seed)
    docelowe = liczebnosci_kolorow(n)
    pozostale = docelowe.copy()
    katalog = tuple(((nazwa, kategoria, dol * 100, gora * 100) for nazwa, kategoria, dol, gora in PRODUKTY))
    start = time.perf_counter()
    output.parent.mkdir(parents=True, exist_ok=True)
    print(f'Zapis {n:,} wierszy do: {output.resolve()}', flush=True)
    with output.open('x', encoding='utf-8-sig', newline='', buffering=1024 * 1024) as plik:
        writer = csv.writer(plik, delimiter=';', lineterminator='\n')
        writer.writerow(KOLUMNY)
        for poczatek in range(1, n + 1, batch_size):
            koniec = min(poczatek + batch_size, n + 1)
            partia = []
            for identyfikator in range(poczatek, koniec):
                nazwa, kategoria, minimum, maksimum = rng.choice(katalog)
                ilosc = rng.randint(1, 35)
                cena = rng.randint(minimum, maksimum)
                miasto, woj = rng.choice(lokalizacje)
                los = rng.randrange(n - identyfikator + 1)
                for indeks, liczba in enumerate(pozostale):
                    if los < liczba:
                        pozostale[indeks] -= 1
                        kolor = KOLORY[indeks]
                        break
                    los -= liczba
                partia.append((identyfikator, nazwa, ilosc, kwota(cena), kolor, miasto, woj, kategoria, kwota(ilosc * cena)))
            writer.writerows(partia)
            zapisano = koniec - 1
            if zapisano == n or (poczatek - 1) // 500000 < zapisano // 500000:
                czas = time.perf_counter() - start
                print(f'{zapisano:,}/{n:,} ({100 * zapisano / n:.1f}%) | {zapisano / max(czas, 0.001):,.0f} wierszy/s', flush=True)
    print(f'Gotowe. Rozmiar: {output.stat().st_size / 1024 ** 2:.1f} MiB')
    print('Liczebności kolorów: ' + ', '.join((f'{kolor}: {liczba:,}' for kolor, liczba in zip(KOLORY, docelowe))))
    return output

def dodatnia(text):
    wartosc = int(text)
    if wartosc < 1:
        raise argparse.ArgumentTypeError('Wartość musi być większa od zera')
    return wartosc

def main():
    parser = argparse.ArgumentParser(description='Generator syntetycznych danych elektroniki i AGD.')
    parser.add_argument('--n', type=dodatnia, default=N, help='Liczba wierszy (domyślnie 100000)')
    parser.add_argument('--output', type=Path, default=Path('dane_syntetyczne.csv'), help='Plik wyjściowy')
    parser.add_argument('--seed', type=int, default=42, help='Ziarno generatora (domyślnie 42)')
    parser.add_argument('--batch-size', type=dodatnia, default=50000, help='Liczba wierszy w partii')
    args = parser.parse_args()
    try:
        generuj(args.n, args.output, args.seed, args.batch_size)
    except (OSError, ValueError, RuntimeError) as blad:
        print(f'Błąd: {blad}', file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print('\nPrzerwano. Plik może zawierać tylko część danych.', file=sys.stderr)
        return 130
    return 0
if __name__ == '__main__':
    raise SystemExit(main())
