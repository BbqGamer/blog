+++
title = 'Dodawanie nowych typów w C do Pythona'
date = 2025-04-19T13:53:21+02:00
draft = true
+++
Ten post jest kontynuacją mojego [poprzedniego
posta](/posts/python_c_extensions/) w którym pisałem jak pisać rozszerzenia do
Pythona korzystając z API w C. W tamtym poście skupiłem się jedynie na
implementacji funkcji w module, operowały one na obiektach które były dość
mocno ograniczone przez Pythona, np. żeby operować na listach musimy wywoływać
funkcje z przedrostkiem PyList które zakładają że lista jest typem dynamicznym.

Przydałoby się móc stworzyć typy które będą trzymać dane w odpowiednich do tego
strukturach w C zoptymalizowanych pod nasz problem. Postaramy się
zaimplementować nasz typ `Array`, który będzie wspierał podobne funckjonalności
jak macierze z `numpy`.

# Boilerplate
Zaczniemy od przedstawienia minimalnego kodu który musi się znaleźć żeby zacząć
tworzyć swój typ. Polecam [oficjalną
dokumentację](https://docs.python.org/3/extending/newtypes_tutorial.html) jeśli
chcesz się dowiedzieć czegoś więcej.
```c
#include <Python.h>

// defninicja struktury dla obiektów z naszego typu Array
typedef struct {
  PyObject_HEAD    // wymagany header, który pozwoli traktować Array jako PyObject
  double *data;    // wskaźnik do listy z liczbami zmiennoprzecinkowymi
  Py_ssize_t size; // ilość liczb w naszej macierzy
} ArrayObject;

// boilerplate by zadeklarować nasz typ w Pythonie
static PyTypeObject ArrayType = {
    .ob_base = PyVarObject_HEAD_INIT(NULL, 0)
    .tp_name = "myarr.Array",  // nazwa typu widoczna w dokumentacji
    .tp_doc = PyDoc_STR("Array object"), // opis do dokumentacji
    .tp_basicsize = sizeof(ArrayObject), // rozmiar struktury obiektu
    .tp_itemsize = 0,
    .tp_flags = Py_TPFLAGS_DEFAULT,
    .tp_new = PyType_GenericNew,  // Domyślna implementacja __new__
};

// definicja modułu myarr
static PyModuleDef myarr_module = {
    .m_base = PyModuleDef_HEAD_INIT,
    .m_name = "myarr",
    .m_doc = "My array implementation",
    .m_size = -1,
};

// inicjalizacja modułu myarr
PyMODINIT_FUNC PyInit_myarr(void) {
    if (PyType_Ready(&ArrayType) < 0)
        return NULL;

    PyObject *m = PyModule_Create(&myarr_module);
    if (m == NULL)
        return NULL;

    // dodajemy nasz typ (Array) do modułu (myarr)
    if(PyModule_AddObjectRef(m, "Array", (PyObject *) &ArrayType) < 0) {
        Py_DECREF(m);
        return NULL;
    }

    return m;
}
```
Dodatkowo zdefiniujemy sobie makefile do prostego kompilowania modułu.
```Makefile
myarr.so: myarr.c
	gcc $< -fPIC -shared -o $@ -I/usr/include/python3.11
```
Możemy przetestować że nasz moduł działa, w natępujący sposób:
```bash
$ make    # zbudowanie modułu
$ python3 # otwarcie interpretera pythona
>>> import myarr
>>> help(myarr)
>>> a = myarr.Array()
>>> a
```

# Dodanie podstawowych metod
Jesteśmy w stanie zaimportować nasz typ i tworzyć obiekty, świetnie, tylko na
razie na tym się kończy funkcjonalność, przyda się kilka funkcji które pozwolą
nam robić coś więcej z obiektami `Array`.

## \_\_init\_\_
Żeby móc tworzyć nasze macierze przyda się inicjalizator przekopiuje elementy z
listy do naszego obiektu `Array`.
```c
static int Array_init(ArrayObject *self, PyObject *args) {
    PyObject *input_list;
    
    // parsowanie argumentu (powinien być jeden argument typu `list`)
    if (!PyArg_ParseTuple(args, "O!", &PyList_Type, &input_list)) {
        return -1;
    }

    Py_ssize_t list_size = PyList_Size(input_list);
    // alokacja pamięci na macierz
    self->data = malloc(list_size * sizeof(double));
    self->size = list_size;
    if (!self->data) {
        PyErr_NoMemory();
        return -1;
    }

    // przekopiowanie liczb zmiennoprzecinkowych z listy do macierzy
    for(Py_ssize_t i = 0; i < list_size; i++) {
        PyObject *item = PyList_GetItem(input_list, i);
        self->data[i] = PyFloat_AsDouble(item);
    }

    return 0;
}

static PyTypeObject ArrayType = {
    ... // to co wcześniej tu było zostaje
    .tp_init = (initproc)Array_init, // dodajemy init do zbioru metod
};
```

## \_\_repr\_\_
Funkcja repr jest stringiem który pozwala nam wyświetlić w zrozumiały dla
człowieka sposób dane zawarte w obiekcie. Funkcja ta się wyświetla jeśli
użyjemy funkcji `repr(obiekt)` lub po prostu kiedy REPL próbuje wyświetlić stan
obiektu. 

Nie chciało mi się analizować wszystkich przypadków i pisać własnego sposobu na
formatowanie listy liczb zmiennoprzecinkowych więc ukradłem repra z `PyList`,
nie jest to najoptymalniejsze rozwiązanie gdyż musimy zbudować listę zanim ją
wyświetlimy ale chyba jest to najprostsze rozwiązanie.
```c
static PyObject *Array_repr(ArrayObject *self) {
  PyObject *str_list = PyList_New(self->size);
  if (!str_list)
    return NULL;

  for (Py_ssize_t i = 0; i < self->size; ++i) {
    PyObject *item = PyFloat_FromDouble(self->data[i]);
    if (!item) {
      Py_DECREF(str_list);
      return NULL;
    }
    PyList_SET_ITEM(str_list, i, item); // Steals ref
  }

  PyObject *list_str = PyObject_Repr(str_list); // Gets repr like "[1, 2, 3]"
  Py_DECREF(str_list);

  if (!list_str)
    return NULL;

  PyObject *final_str = PyUnicode_FromFormat("Array(%U)", list_str);
  Py_DECREF(list_str);
  return final_str;
}

```
