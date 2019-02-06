# Subtitles

[![Build Status](https://travis-ci.org/philipbel/Subtitles.svg?branch=master)](https://travis-ci.org/philipbel/Subtitles)

# Dependencies

## Linux

### Debian-Based Distros (Ubuntu, etc.)

### Development Packages

```
sudo apt install make git zip
```

#### Install pipenv

```
sudo pip3 install --upgrade pipenv
```

#### Install python3.7

```
sudo apt install python3.7 python3.7-dev
```

#### Install Python Packages

```
make depends-force
```

#### Install packpack

(Optional) Install packpack
```
curl -s https://packagecloud.io/install/repositories/packpack/packpack/script.deb.sh | sudo bash
```

# Build

```
make
```
