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
podstawie prostego przykładu, implementacji szybkiego algorytmu sortowania.

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
static PyMethodDef qusort_methods[] = {
    {NULL, NULL, 0, NULL} // element wskazujący koniec listy (sentinel - strażnik)
};

// Definicja modułu (nazwa: qusort, opis: Quicksort implementation in C)
static struct PyModuleDef qusort = {
    PyModuleDef_HEAD_INIT, "qusort", "Quicksort implementation in C", -1, qusort_methods};

// Inicjalizacja modułu
PyMODINIT_FUNC PyInit_qusort(void) { return PyModule_Create(&qusort_methods); }
```
Poniższa komenda pozwoli nam skompilować moduł:
```bash
gcc qusort.c -fPIC -shared -o asort.so -I/usr/include/python3.11
```
Powinniśmy w efekcie otrzymać plik `qusort.so` w formacie ELF, który jest naszym
skompilowanym modułem, możemy przetestować czy działa w interpreterze pythona
(ważne żebyśmy uruchamiali interpreter będąc w tym samym folderze co plik
`.so`).
```python
$ python3
>>> import qusort
>>> help(qusort)
>>> dir(qusort)
```
Nasz modul powinien być importowalny, teraz zdefiniujemy nasz typ danych i funkcje.

# Definicja funkcji operującej na liście
W pythonie praktycznie wszystko jest obiektem, włączając w to funkcje. 
Funkcja przyjmuje jako argumenty inne obiekty a także zwraca inne obiekty.

Python jest językiem dynamicznie typowanym, gdzie każdy typ jest traktowany w
ten sam sposób i by otrzymać w C konkretne typy musimy używać parsowania
obiektów podanych w `args` do każdej funkcji. Jendym ze sposobów jest użycie
`PyArg_ParseTuple`, tajemniczo wyglądający argument `O` wskazuje na to że
funkcja przyjmuje jeden argument który jest obiektem `!` zaś wymaga by typ
obiektu był zweryfikowany. W naszym przypadku oczekujemy że obiekt będzie typu
`PyList_Type` (czyli po prostu `list` z Pythona) i że w wyniku przeniesiony
będzie do zmiennej `input_list`. [dokumentacja parsowania
argumentów](https://docs.python.org/3/c-api/arg.html)

Funkcja `PyList_Size(list)` pozwala nam wyciągnąć ilość elementów z listy
(równoważne z `len(list)`) Funkcja `PyList_GetItem(list, index)` pozwala nam
wyciągnąć poszczególne elementy z listy `list[index]`.

Oczywiście elementy w liście także są wskaźnikami do `PyObject` więc musimy je 
przekonwertować do liczy całkowitej za pomocą `PyLong_AsLong`

Na końcu programu musimy także zwrocić wskaźnik do `PyObject` z wynikiem, użyjemy do
tego celu funkcję `PyLong_FromLong`.
```c
static PyObject *sum(PyObject *self, PyObject *args) {
  PyObject *input_list;

  if (!PyArg_ParseTuple(args, "O!", &PyList_Type, &input_list)) {
    return NULL;
  }

  int res = 0;
  for (Py_ssize_t i = 0; i < PyList_Size(input_list); i++) {
    PyObject *item = PyList_GetItem(input_list, i);
    res += PyLong_AsLong(item);
  }

  return PyLong_FromLong(res);
}
```
W wyniku otrzymaliśmy funkcję która sumuje wszystkie elementy w liście. By móc jej
używać w Pythonie musimy zadeklarować że jest ona częścią modułu, przyda się także
docstring który będzie widoczny gdy ktoś będzie przeglądał dokumentację.
```c
PyDoc_STRVAR(sum_doc,
"sum(list, /)\n--\n\n"
"Return sum of a list"
);

static PyMethodDef qusort_methods[] = {
    {"sum", sum, METH_VARARGS, sum_doc}, // rozszerzamy listę metod qusort o sum
    {NULL, NULL, 0, NULL}};
```
Kompilujemy nasz plik i możemy sprawdzić naszą funkcję w akcji:
```python3
$ python3
import qusort
print(qusort.sum([1,2,3])) # 6
```
By otrzymać dokumentację możemy w terminalu wpisać
```bash
python3 -m pydoc qusort
```
Lub po prostu `help(...)` w interpreterze.

