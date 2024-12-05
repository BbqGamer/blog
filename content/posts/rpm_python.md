+++
title = 'Creating RPM from Python script'
date = 2024-12-05T22:55:32+01:00
draft = true
+++
Let's inspect some RPM packages from the RHEL repository:

To download the RPM package:
```bash
dnf download python3.12-cryptography
```
We inspect the files included in the package with:
```bash
rpm -qpl python3.12-cryptography*.rpm
```
As we can see there are a lot of files included in the package, all 85 of the `.py` files 
will be installed in `/usr/lib/python3.12/site-packages/cryptography/...`, there are 
also 144 `.pyc` files containing Python bytecode, that will be installed in `__pycache__`
subfolders.

The package also includes a `*.so` file, which is a shared object file, a compiled library
in case of `cryptography` it was written in Rust.

## Installation of python libraries
It is very easy to globally install Python libraries, all that needs to happen is the
library files need to be copied into `/usr/lib/python3.12/site-packages/` directory.
