# Installation

planta-filler is a Python command-line tool that drives Firefox through Selenium.
You need three things: Python, Firefox, and geckodriver.

## 1. Python 3.9 or newer

```bash
python3 --version
```

## 2. Firefox

Any current Firefox works, including Firefox ESR. Install it from
[mozilla.org](https://www.mozilla.org/firefox/) or your package manager:

```bash
# Debian / Ubuntu
sudo apt install firefox-esr
# Fedora
sudo dnf install firefox
# macOS (Homebrew)
brew install --cask firefox
```

## 3. geckodriver

geckodriver is the bridge between Selenium and Firefox. Download the release for your
platform from <https://github.com/mozilla/geckodriver/releases>, unpack it and put the
binary on your `PATH`:

```bash
# Linux x86_64 example
curl -fsSL https://github.com/mozilla/geckodriver/releases/download/v0.36.0/geckodriver-v0.36.0-linux64.tar.gz \
  | sudo tar -xz -C /usr/local/bin
geckodriver --version
```

```bash
# macOS (Homebrew)
brew install geckodriver
```

On Windows, unzip `geckodriver.exe` into a folder that is on your `PATH`
(for example the folder where Python's `Scripts` directory lives).

Selenium 4.6+ can also download a matching geckodriver automatically through
Selenium Manager if none is found on the `PATH`. That requires internet access on the
first run, so having geckodriver installed explicitly is the more predictable option.

## 4. planta-filler

### From PyPI (recommended)

```bash
pip3 install planta-filler
planta-filler --version
```

Using [pipx](https://pipx.pypa.io/) keeps the tool isolated from other Python packages:

```bash
pipx install planta-filler
```

### From source

```bash
git clone https://github.com/d-solve-de/planta-automation.git
cd planta-automation
pip3 install .            # or: pip3 install -e ".[dev]" for development
```

### Upgrade

```bash
pip3 install --upgrade planta-filler
```

## Docker or Podman

If you prefer not to install Firefox and geckodriver on your machine, use the
container image described in [docker.md](docker.md). It bundles Firefox ESR,
geckodriver and planta-filler.

## Check the installation

```bash
planta-filler --help
planta-filler --man
```

Continue with the [first-run tutorial](tutorial-first-run.md).
