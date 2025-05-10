+++
title = 'DEFLATE a formaty zlib oraz gzip'
date = 2025-05-10T19:08:02+02:00
draft = true
+++
Istnieje wiele algorytmów kompresji, które w inteligenty sposób potrafią zmniejszyć ilość
bitów wymaganych do reprezentacji informacji, co jest bardzo przydatne w transmisji
a także przechowywaniu danych. W tym poście zgłębiam bibliotekę kompresji zlib, która
stała się de facto standardem.

# Poszukiwania biblioteki do kompresji
Jako użytkownik Linuxa, kiedy myślę o kompresji przychodzi mi na myśl program
`gzip`, to utility jest na tyle powszechne że jest od razu zainstalowane na
większości dystrybucji.  Ostatnio dla frajdy implementowałem swój serwer HTTP,
by usprawnić transmisję plików protoków definiuje nagłówek `Accept-Encoding`,
dzięki któremu klient może poprosić by serwer skompresował payload za pomocą
jakiegoś kodowania. (Wybrane kodowanie jest odpowiedzi w nagłówku
`Content-Encoding`).

Z moich testów wynika że firefox i chromium dołącza do każdego żądania poniższy nagłówek:
```
Accept-Encoding: gzip, deflate, br, zstd
```
Jak widać jednym z nich jest własnie gzip i uznałem że tym kodowaniem zajmę się
pierwszym. Następnym krokiem było znalezienie biblioteki która pozwoli mi w
łatwy sposób skompresować pliki bez wywoływania polecenia `gzip` z shella,
szybko znalazłem bibliotekę [zlib](https://zlib.net/)`. Biblioteka zlib została
napisana przez tych samych ludzi którzy stworzyli `gzipa` (Mark Adler i Jean
Loup). Panowie mają być z czego dumni, gdyż ich biblioteka jest jednym z
[najbardziej rozpowszechnionych kawałków kodu na
świecie](https://daniel.haxx.se/blog/2021/10/21/the-most-used-software-components-in-the-world/)

# Więcej o bibliotece zlib
Biblioteka pozwala nam na zakodowanie dowolnej sekwencji bajtów w krótszą
sekwencję (pomijając wyjątkowe przypadki jak bardzo małe pliki). Dostępne są
dwa wyjściowe formaty, `zlib` oraz `gzip`. W zasadzie nie różnią się one
znacznie, najważniejszy element, czyli algorytm kompresji bezstratnej jest taki
sam.

Zlib implementuje algorytm kompresji DEFLATE, który polega na połączeniu
algorytmu LZ77 oraz kodowania Huffmana. Jak pisałem wyżej Accept-Encoding
w HTTP przyjmuje też parameter `deflate`, jest to według mnie lekkie
niedopatrzenie, gdyż w rzeczywistości `gzip` też używa algorytmu DEFLATE,
lepszą nazwą byłoby `zlib` gdyż w rzeczywistości właśnie tego formatu
oczekuje klient gdy żąda kodowania `deflate`. Warto dodać też że algorytm
DEFLATE jest używany w formacie PNG, który też jest niezwykle popularny.
Różnice pomiędzy formatami zlib i gzip przedstawiam w tabeli poniżej:
,zlib,gzip
checksum,adler32,crc32
standard,[RFC1950](https://www.rfc-editor.org/rfc/rfc1950),[RFC1952](https://www.rfc-editor.org/rfc/rfc1952)
Powinienem dodać że aktualnie do HTTP dużo popularniejszy jest algorytm
[Brotli](https://github.com/google/brotli) stworzony przez inżynierów z Googla
lub [Zstandard](https://github.com/facebook/zstd) stworzony przez Facebooka. (Zdefiniowane jako Content-Encoding
`br` oraz `zstd`), zauważyłem że Cloudflare używa go do serwowania tego bloga :)

# Interfejs zlib.h
Interfejs zliba jest prosty, zawsze warto spojrzeć do nagłówka biblioteki (na
debianie 12 trzeba zainstalować pakiet: `zlib1g-dev1` a header znajdzie się w
/usr/include/zlib.h). Funkcja `deflate`, kompresuje bufor zaś `inflate`
dekompresuje go, na polski można o tym myśleć jak o spuszczaniu powietrza z
balona lub nadmuchiwanie go z powrotem, gdzie poziom kompresji odpowiada ilości
powietrza w balonie. Poniżej prosty przykład jak użyć bilbioteki w praktyce.

