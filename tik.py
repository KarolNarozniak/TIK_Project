import struct

def oblicz_crc32(dane):
    """
    Implementacja CRC32 z wielomianem 0xEDB88320.
    Każdy bajt jest przetwarzany bit po bicie.
    """
    crc = 0xFFFFFFFF
    for bajt in dane:
        temp = crc ^ bajt
        for _ in range(8):
            if temp & 1:
                temp = (temp >> 1) ^ 0xEDB88320
            else:
                temp >>= 1
        crc = (crc >> 8) ^ temp
    return crc ^ 0xFFFFFFFF

def znajdz_najdluzsze_dopasowanie(dane, pozycja, okno):
    """
    Szuka najdłuższej sekwencji w oknie (domyślnie 4096 bajtów) 
    przed obecną pozycją. Zwraca (offset, length).
    """
    koniec = len(dane)
    naj_offset = 0
    naj_dl = 0
    
    start_bufora = max(0, pozycja - okno)
    
    for p in range(pozycja - 1, start_bufora - 1, -1):
        dl = 0
        while (p + dl < pozycja and 
               pozycja + dl < koniec and 
               dane[p + dl] == dane[pozycja + dl]):
            dl += 1
        if dl > naj_dl:
            naj_dl = dl
            naj_offset = pozycja - p
    
    return naj_offset, naj_dl

def lz77_koduj(dane, okno=4096):
    """
    Kompresuje dane metodą LZ77:
    Zwraca listę tokenów (offset, length, symbol).
    Jeśli offset=0 i length=0 => symbol literalny.
    """
    pozycja = 0
    n = len(dane)
    tokens = []
    
    while pozycja < n:
        offset, dl = znajdz_najdluzsze_dopasowanie(dane, pozycja, okno)
        
        if dl > 0 and pozycja + dl < n:
            symbol = dane[pozycja + dl]
            tokens.append((offset, dl, symbol))
            pozycja += (dl + 1)
        else:
            tokens.append((0, 0, dane[pozycja]))
            pozycja += 1
    
    return tokens

def lz77_dekoduj(tokens):
    """
    Dekoduje listę tokenów (offset, length, symbol) do oryginalnych bajtów.
    """
    wyjscie = bytearray()
    for offset, dl, symbol in tokens:
        if offset == 0 and dl == 0:
            wyjscie.append(symbol)
        else:
            start = len(wyjscie) - offset
            for i in range(dl):
                wyjscie.append(wyjscie[start + i])
            wyjscie.append(symbol)
    return wyjscie

def zapisz_skompresowane(path_wyjscie, tokens):
    """
    Zapisuje tokeny w formacie binarnym:
      - offset (2 bajty, little-endian)
      - length (2 bajty)
      - symbol (1 bajt)
    Na koniec dopisuje 4 bajty CRC32.
    """
    dane_skompresowane = bytearray()
    for offset, dl, symbol in tokens:
        dane_skompresowane.extend(struct.pack("<HHB", offset, dl, symbol))
    
    crc = oblicz_crc32(dane_skompresowane)
    dane_skompresowane.extend(struct.pack("<I", crc))
    
    with open(path_wyjscie, "wb") as f:
        f.write(dane_skompresowane)

def wczytaj_skompresowane(path_wejscie):
    """
    Wczytuje binarnie zapisane tokeny, weryfikuje CRC.
    Zwraca listę tokenów (offset, length, symbol).
    """
    with open(path_wejscie, "rb") as f:
        dane = f.read()
    
    if len(dane) < 4:
        raise ValueError("Plik skompresowany jest za krótki (brak CRC).")
    
    zapisany_crc = struct.unpack("<I", dane[-4:])[0]
    dane_tokens = dane[:-4]
    
    policzony_crc = oblicz_crc32(dane_tokens)
    if policzony_crc != zapisany_crc:
        raise ValueError("Błąd CRC – plik może być uszkodzony.")
    
    if len(dane_tokens) % 5 != 0:
        raise ValueError("Błąd formatu – dane tokenów nie są wielokrotnością 5.")
    
    tokens = []
    for i in range(0, len(dane_tokens), 5):
        offset, dl, symbol = struct.unpack("<HHB", dane_tokens[i:i+5])
        tokens.append((offset, dl, symbol))
    
    return tokens

def porownaj_pliki(oryginal, zdekompresowany):
    """
    Proste porównanie bajt-po-bajcie. Zwraca True/False.
    """
    if len(oryginal) != len(zdekompresowany):
        return False
    return oryginal == zdekompresowany

def menu():
    print("Witaj w kompresorze LZ77 z CRC32!")
    while True:
        print("\n===== MENU =====")
        print("1. Kompresuj plik")
        print("2. Dekompresuj plik")
        print("3. Wyjście")
        print("4. Pełny test (kompresja, dekompresja, porównanie)")
        
        wybor = input("Wybierz opcję (1-4): ").strip()
        
        if wybor == '1':
            sciezka_in = input("Podaj ścieżkę do pliku do kompresji: ")
            sciezka_out = input("Podaj ścieżkę wyjściową (np. skompresowane.bin): ")
            try:
                print("Wczytuję plik źródłowy...")
                with open(sciezka_in, "rb") as f:
                    dane = f.read()
                print("Kompresuję dane...")
                tokens = lz77_koduj(dane)
                print(f"Powstało {len(tokens)} tokenów. Zapisuję do pliku...")
                zapisz_skompresowane(sciezka_out, tokens)
                print("Kompresja zakończona sukcesem!")
            except Exception as e:
                print("Błąd podczas kompresji:", e)
        
        elif wybor == '2':
            sciezka_in = input("Podaj ścieżkę do pliku skompresowanego: ")
            sciezka_out = input("Podaj ścieżkę wyjściową (zdekompresowany plik): ")
            try:
                print("Wczytuję plik skompresowany...")
                tokens = wczytaj_skompresowane(sciezka_in)
                print(f"Odczytano {len(tokens)} tokenów. Dekompresuję dane...")
                dane_odkodowane = lz77_dekoduj(tokens)
                print(f"Zapisuję {len(dane_odkodowane)} bajtów do pliku wynikowego...")
                with open(sciezka_out, "wb") as f:
                    f.write(dane_odkodowane)
                print("Dekompresja zakończona sukcesem!")
            except Exception as e:
                print("Błąd podczas dekompresji:", e)
        
        elif wybor == '3':
            print("Koniec programu.")
            break
        
        elif wybor == '4':
            sciezka_in = input("Podaj ścieżkę do pliku źródłowego: ")
            
            # Proponujemy automatyczne nazwy dla skompresowanego i zdekompresowanego
            sciezka_skompresowane = sciezka_in + ".lz77"
            sciezka_rozpakowane = sciezka_in + ".dec"
            
            try:
                print("Wczytuję oryginalny plik...")
                with open(sciezka_in, "rb") as f:
                    dane_oryginal = f.read()
                
                print("Kompresuję...")
                tokens = lz77_koduj(dane_oryginal)
                zapisz_skompresowane(sciezka_skompresowane, tokens)
                print(f"Kompresja zakończona. Plik: {sciezka_skompresowane}")
                
                print("Dekompresuję...")
                tokens_wczytane = wczytaj_skompresowane(sciezka_skompresowane)
                dane_odkodowane = lz77_dekoduj(tokens_wczytane)
                with open(sciezka_rozpakowane, "wb") as f:
                    f.write(dane_odkodowane)
                print(f"Dane zdekompresowane. Plik: {sciezka_rozpakowane}")
                
                print("Porównuję pliki...")
                if porownaj_pliki(dane_oryginal, dane_odkodowane):
                    print("Sukces! Plik zdekompresowany jest identyczny z oryginałem.")
                else:
                    print("Błąd! Dane nie są takie same.")
            except Exception as e:
                print("Błąd testu:", e)
        
        else:
            print("Nieprawidłowy wybór, spróbuj ponownie.")

if __name__ == "__main__":
    menu()
