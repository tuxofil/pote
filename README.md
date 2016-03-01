# Python Online Test Executor

## Summary

Pote is acronym for Python Online Test Executor. It provides Web interface
to enqueue and launch Python tests in a separate environments.

## Directory layout

* bin/ - scripts vital for Pote start/stop etc.;
* debian/ - Debian specs needed to build DEB package with Pote;
* doc/ - project documentation and pictures;
* etc/ - config files to adjacent programs;
* pote/ - core Python library;
* test/ - Pote unit and functional tests;
* tests/ - not to be confused with "test/"! Directory with test sets
 available for online testing;
* www/ - static files for the web clients.

## Requirements

Developed and tested in Debian 7 Wheezy.

See Build-Depends and Depends definitions in the debian/control file.

## Testing

```
make test
```

## Linting

```
make lint
```

## Building DEB package from scratch

Required software:

* git;
* dpkg-dev;
* pbuilder.

```
git clone https://github.com/tuxofil/pote.git pote
dpkg-source -b pote
sudo pbuilder --build pote_*.dsc
```
