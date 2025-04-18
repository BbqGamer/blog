+++
title = 'Rozszerzenia w C do Pythona'
date = 2025-04-18T13:19:51+02:00
draft = false
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
// definiujemy docstringa
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

# Funkcja sort
Wreszcie możemy się wziąć za implementację quicksorta. Zacznijmy od implementacji
algorytmu na surowej liście liczb całkowitej bez przejmowania się typami Pythona.
```c
void swap(long *a, long* b) {
    long tmp = *a;
    *a = *b;
    *b = tmp;
}

Py_ssize_t partition(long *arr, Py_ssize_t lo, Py_ssize_t hi) {
    long mid = (lo + hi) / 2;
    if (arr[mid] < arr[lo]) {
        swap(&arr[mid], &arr[lo]);
    }
    if (arr[hi] < arr[lo]) {
        swap(&arr[hi], &arr[lo]);
    }
    if (arr[mid] < arr[hi]) {
        swap(&arr[mid], &arr[hi]);
    }
    
    long tmp, pivot = arr[hi];
    Py_ssize_t i, j; 
    for (i = lo, j = lo; j < hi; j++) {
        if(arr[j] <= pivot) {
            swap(&arr[j], &arr[i])
            i++;
        }
    }

    swap(&arr[hi], &arr[i]);
    return i;
}

void quicksort(long *arr, Py_ssize_t lo, Py_ssize_t hi) {
    if (lo >= hi)
        return;

    Py_ssize_t p = partition(arr, lo, hi);

    quicksort(arr, p + 1, hi);
    quicksort(arr, lo, p - 1);
}
```
Szczegóły na temat powyższej implementacji można znaleźć np na
[wikipedii](https://en.wikipedia.org/wiki/Quicksort).

Zajmijmy się teraz połączeniem tej funkcji z pythonem. Parsowanie argumentów
robimy podobnie jak w poprzedniej funkcji (`sum`). Alokujemy miejsce na macierz
*roboczą*, algorytm będzie działał dużo szybciej jeśli będziemy operować na
macierzach z C zamiast wykorzystywać operacje z `PyList`, typu `PyList_GetItem`
albo `PyList_SET_ITEM`, będą one nam tylko potrzebne do zczytania wartości w
liście wejściowej i wypisanie ich do listy wyjściowej.
```c
PyDoc_STRVAR(sort_doc,
"sort(list, /)\n--\n\n"
"Sorts in place a list of integers.");

static PyObject *sort(PyObject *self, PyObject *args) {

  PyObject *input_list;

  if (!PyArg_ParseTuple(args, "O!", &PyList_Type, &input_list)) {
    return NULL;
  }

  Py_ssize_t size = PyList_Size(input_list);
  long *sorted = malloc(sizeof(long) * size);

  for (Py_ssize_t i = 0; i < size; i++) {
      sorted[i] = PyLong_AsLong(PyList_GetItem(input_list, i));
  }

  quicksort(sorted, 0, size - 1);
    
  PyObject *output_list = PyList_New(size);
  if (output_list == NULL)
      return NULL;

  for (Py_ssize_t i = 0; i < size; i++) {
      PyObject *item = PyLong_FromLong(sorted[i]);
      if (item == NULL) {
          Py_DECREF(output_list);
          return NULL;
      }

      PyList_SET_ITEM(output_list, i, item);
  }
  return output_list;
}

static PyMethodDef qusort_methods[] = {
    {"sum", sum, METH_VARARGS, sum_doc},
    {"sort", sort, METH_VARARGS, sort_doc}, // dodajemy kolejną funkcję do listy
    {NULL, NULL, 0, NULL}};
```
# Benchmark
Funkcja sortująca działa, ale byłem ciekaw czy jest ona szybsza niż funkcja
wbudowana w Pythona (`sorted`), oczywiście porównanie to nie jest do końca fair
bo funkcja wbudowana działa niezależnie od tego jakie typy są w liście, a nasza
lista działa tylko na liczbach całkowitych. Tak czy inaczej warto sprawdzić jak
nam poszło, w tym celu napisałem krótki skrypt do benchmarku funkcji w pythonie.
```python
import random
import time
import qusort 
from statistics import mean


SIZES = [1000, 10_000, 100_000, 1_000_000, 5_000_000]
REPEATS = 10
for size in SIZES:
    qusorts = []
    sorteds = []
    for _ in range(REPEATS):
        arr = [random.randint(-10_000_000, 10_000_000) for _ in range(size)]

        start = time.perf_counter()
        A = qusort.sort(arr)
        qusorts.append(time.perf_counter() - start)

        start = time.perf_counter()
        B = sorted(arr)
        sorteds.append(time.perf_counter() - start)

        assert A == B
    print(f"Arr size: {size:8d}\tavg qsort = {mean(qusorts):.6f} s, avg sorted = {mean(sorteds):.6f} s")
```
Wyniki, były takie:
```bash
Arr size:     1000      avg qsort = 0.000078 s, avg sorted = 0.000070 s
Arr size:    10000      avg qsort = 0.000920 s, avg sorted = 0.000915 s
Arr size:   100000      avg qsort = 0.011651 s, avg sorted = 0.012594 s
Arr size:  1000000      avg qsort = 0.139018 s, avg sorted = 0.223437 s
Arr size:  5000000      avg qsort = 0.763253 s, avg sorted = 1.584413 s
```
Jak widać nasz algorytm był w stanie poprawić dość mocno czas sortowania dla większych
instancji problemu, czyli pokazuje to że czasami napisanie jakiegoś konkretnego 
rozwiązania pod nasz problem może być bardziej wydajne niż wbudowane rozwiązania.

