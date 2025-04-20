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
gcc qusort.c -O4 -fPIC -shared -o asort.so -I/usr/include/python3.11
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
Arr size:     1000      avg qsort = 0.000048 s, avg sorted = 0.000065 s
Arr size:    10000      avg qsort = 0.000568 s, avg sorted = 0.000891 s
Arr size:   100000      avg qsort = 0.008508 s, avg sorted = 0.014490 s
Arr size:  1000000      avg qsort = 0.089242 s, avg sorted = 0.240599 s
Arr size:  5000000      avg qsort = 0.485726 s, avg sorted = 1.543574 s
```
Jak widać nasz algorytm był w stanie poprawić dość mocno czas sortowania dla większych
instancji problemu, czyli pokazuje to że czasami napisanie jakiegoś konkretnego 
rozwiązania pod nasz problem może być bardziej wydajne niż wbudowane rozwiązania.

# Wielowątkowość
Quicksort jest algorytmem typu dziel i rządź i świetnie nadaje się do parallelizacji.
Chciałem zobaczyć jakie wyniki będę w stanie otrzymać na moim 16 wątkowym procesorze
i wyniki okazały się być bardzo fajne.

## Jak paralelizować quicksorta
Jest na to kilka sposobów, ja zdecydowałem się że w każdym wykonaniu quicksorta
rekurencyjne wywołanie quicksorta na części listy na lewo od pivota będzie odbywać się
w tym samym wątku, a prawa strona w nowym wątku, z tym że tworzymy nowy wątek tylko
jeśli nie istnieje już 16 wątków i lista jest wystarczająco długa żeby to miało sens.
```c
#include <pthread.h>
#include <semaphore.h>
...
// lekka zmiana implementacji swapa dla uproszczenia kodu
static inline void swap(long *arr, Py_ssize_t a, Py_ssize_t b) {
    long tmp = arr[a];
    arr[a] = arr[b];
    arr[b] = tmp;
}

// Dla uproszczenia zakładamy że lo zawsze jest 0 a n to indeks ostatniego elementu
// arr to tylko wskaźnik więc można nim manipulować w funkcji quicksort
Py_ssize_t partition(long *arr, Py_ssize_t n) {
    long mid = n / 2;
    if (arr[mid] < arr[0]) {
        swap(arr, mid, 0);
    }
    if (arr[n] < arr[0]) {
        swap(arr, n, 0);
    }
    if (arr[mid] < arr[n]) {
        swap(arr, mid, n);
    }

    long tmp, pivot = arr[n];
    Py_ssize_t i, j; 
    for (i = 0, j = 0; j < n; j++) {
        if(arr[j] <= pivot) {
            swap(arr, j, i);
            i++;
        }
    }

    swap(arr, n, i);
    return i;
}

// struktura do wrzucenia do funkcji quicksort (pthread tego wymaga)
typedef struct {
    long *arr;
    Py_ssize_t n;
    sem_t *sem;
} QSArgs;

#define PARALLEL_THRESHOLD 8196 // tylko twórz wątek jeśli macierz większa niż 8196
#define MAX_THREADS 16

void *quicksort(void* arg) {
    QSArgs *args = arg;

    if (args->n <= 0)
        return NULL;

    Py_ssize_t p = partition(args->arr, args->n);
    
    int s;
    pthread_t thread = 0;
    QSArgs rargs = { args->arr + p + 1, args->n - p - 1, args->sem };
    if (p - 1 >= PARALLEL_THRESHOLD && sem_trywait(args->sem) != -1) {
        s = pthread_create(&thread, NULL, quicksort, &rargs);
        if (s != 0)
            exit(1);
    } else {
        quicksort(&rargs);
    }

    QSArgs largs = { args->arr, p - 1, args->sem };
    quicksort(&largs);

    if (thread) {
        s = pthread_join(thread, NULL);
        if (s != 0)
            exit(1);
        sem_post(args->sem);
    }
}


static PyObject *sort(PyObject *self, PyObject *args) {
...
  sem_t sem;
  sem_init(&sem, 0, MAX_THREADS);
  QSArgs qsargs = { sorted, size - 1, &sem };
  quicksort(&qsargs);
...
}
```
Kompilujemy za pomocą:
```bash
gcc -Ofast -shared -fPIC \
    $(python3-config --includes) -pthread \
    qusort.c -o qusort.so 
```
W ten sposób byłem w stanie jeszcze bardziej przyśpieszyć quicksorta oto
wyniki, dla róznych rozmiarów listy, `qsort` to wersja z wielowątkowością,
możemy zauważyć dwukrotną poprawę dla dużych list:
| algo  |  n = 10000 | n = 100000 | n = 1000000 | n = 5000000 | n = 50000000 |
| ----  |  --------- | ---------- | ----------- | ----------- | ------------ |
|sorted |  0.000891  | 0.014490   | 0.240599    |  1.543574   | 25.132971    |
|qsort  |  0.000568  | 0.008508   | 0.089242    |  0.485726   |  4.911362     |
|qsortmt|  0.000582  | 0.007438   | 0.056366    |  0.240699   |  2.358893    |

**Tip** uruchom eksperyment z komendą nice żeby program miał dostęp do większej ilości
czasu procesora:
```bash
sudo nice --100 python3 benchmark.py
```
