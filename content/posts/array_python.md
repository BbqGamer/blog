+++
title = 'Rozszerzenie w C do Pythona'
date = 2025-04-18T13:19:51+02:00
draft = true
+++
Python jest znany z bardzo słabej wydajności, nie ma się czego dziwić gdyż jest
on językiem interpretowalnym i jego celem nigdy nie było być najszybszym
językiem na świecie. Sam Python napisany jest w języku C, stąd nazwa
*oficjalnej* implementacji języka:
[cpython](https://github.com/python/cpython). Twórcy języka pozwolili na
relatywnie łatwe tworzenie rozszerzeń do języka, przez tworzenie modułów w C.
Celem tego posta jest nauczyć się podstaw tworzenia takiego rozszerzenia na
podstawie prostego przykładu, obiektu array mimikującego macierze z pakietu
numpy.

# Boilerplate
Na początek musimy dołączyć pliki nagłówkowe pythona, żeby móc korzystać z API w C. 
```c
#include <Python.h>
```
Warto się zapoznać z zawartością API przeglądając
[dokumentację](https://docs.python.org/3/c-api/index.html) i dostępne nagłówki,
w moim przypadku nagłówki znajdują się w folderze `/usr/include/python3.11/`.

Następnie zdefiniujemy sobie boilerplate wymagany do stworzenia importowalnego modułu.
```c
// Lista funkcji dostępnych w module (aktualnie pusta)
static PyMethodDef arr_methods[] = {{NULL, NULL, 0, NULL}};

// Definicja modułu (nazwa: arr, opis: A numpy clone)
static struct PyModuleDef arr = {
    PyModuleDef_HEAD_INIT, "arr", "A numpy clone", -1, arr_methods};

// Inicjalizacja modułu
PyMODINIT_FUNC PyInit_arr(void) { return PyModule_Create(&arr); }
```
Poniższa komenda pozwoli nam skompilować moduł:
```bash
gcc arr.c -fPIC -shared -o arr.so -I/usr/include/python3.11
```
Powinniśmy w efekcie otrzymać plik `arr.so` w formacie ELF, który jest naszym
skompilowanym modułem, możemy przetestować czy działa w interpreterze pythona
(ważne żebyśmy uruchamiali interpreter będąc w tym samym folderze co plik
`.so`).
```python
$ python3
>>> import arr
>>> help(arr)
>>> dir(arr)
```
Nasz modul powinien być importowalny, teraz zdefiniujemy nasz typ danych i funkcje.

# Definicja typu Array
Naszym głównym typem będzie macierz Array, która trzyma jakieś dane (`data`)
swój rozmiar (`size`) a także typ danych (`dtype`), w pythonie każdy obiekt
jest traktowany w taki sam sposób i może być castowany do typu `PyObject`,
dlatego musimy załączyć też makro `PyObject_HEAD`, które nam na to pozwoli.
```c
typedef enum {
  ARRAY_TYPE_LONG,
  ARRAY_TYPE_DOUBLE,
} ArrayDType;

typedef struct {
  PyObject_HEAD
  void *data;
  Py_ssize_t size;
  ArrayDType dtype;
} ArrayObject;

```



# Bibliografia
- [Poradnik z oficialnej strony Pythona]https://docs.python.org/3/extending/extending.html

