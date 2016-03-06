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

First, install all required software:

```
sudo apt-get install -y git dpkg-dev pbuilder
```

Second stage. Create a base tarball with Debian Wheezy build environment:

```
sudo pbuilder --create --distribution wheezy
```

And now we are ready to clone and build a DEB package:

```
git clone https://github.com/tuxofil/pote.git pote
dpkg-source -b pote
sudo pbuilder --build pote_*.dsc
```

Built DEB package you can find in ``/var/cache/pbuilder/result/`` directory.

## Install DEB package to target system

You can add pote package to one of your APT repositories (if you have) and then
install it with simple:

```
sudo apt-get install pote
```

If this is not the case, install the package manually:

```
sudo dpkg -i /path/to/pote_*.deb
sudo apt-get install -y -f
```

Second line is required to satisfy all software dependencies of the package.

## Usage

After the package was successfully installed and all software dependencies were
satisfied, just point your web browser to the host where Pote is installed:

```
http://$hostname/pote/
```
