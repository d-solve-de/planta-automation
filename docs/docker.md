# Running in Docker or Podman

The repository ships a `Dockerfile` that bundles Python, Firefox ESR, geckodriver and
planta-filler, plus a `docker-compose.yml` for the two commands you need. Every
`docker` command below works with `podman` as well.

## Build the image

```bash
docker build -t planta-filler:local .
# or
make docker-build
# Podman
podman build -t planta-filler:local .
```

The build downloads geckodriver from GitHub. To pin a different version:
`docker build --build-arg GECKODRIVER_VERSION=0.36.0 -t planta-filler:local .`

The container runs as the unprivileged user `planta` (UID 1000). The Firefox profile
lives in `/home/planta/.selenium_profiles`; mount a volume there so the login survives
between runs.

## The login problem, and three ways to solve it

Inside a container there is no screen, so nobody can type your password into
Firefox. You have to get a logged-in profile into the volume once. Afterwards all
runs are headless.

### Option A: share your X11 display (Linux)

```bash
xhost +local:            # allow local containers to use your display
docker run --rm -it \
  -e DISPLAY -v /tmp/.X11-unix:/tmp/.X11-unix:ro \
  -v planta-profile:/home/planta/.selenium_profiles \
  planta-filler:local --url https://planta.example.com/ --login-only --close-delay 0
```

A Firefox window appears on your desktop. Log in, press ENTER in the terminal, done.
`make docker-login PLANTA_URL=https://planta.example.com/` runs the same command.
On Wayland desktops XWayland usually provides `/tmp/.X11-unix`; if not, use option B.

With Podman, add `--userns=keep-id` if the socket is not accessible, or run it
rootless as your own user, which is the default.

### Option B: copy a profile you created on the host

Log in once on the host with the normal installation
(`planta-filler --url URL --login-only`), then copy the profile into the volume:

```bash
docker run --rm -v planta-profile:/dest -v ~/.selenium_profiles/planta_firefox:/src:ro \
  alpine sh -c 'rm -rf /dest/planta_firefox && cp -a /src /dest/planta_firefox && chown -R 1000:1000 /dest'
```

Firefox refuses to open a profile that was last used by a *newer* Firefox. If the
host runs a newer Firefox than the ESR in the image, add `-e MOZ_ALLOW_DOWNGRADE=1`
to the run command, or use option A.

### Option C: bind-mount a host directory instead of a volume

```bash
mkdir -p ~/planta-profile
docker run --rm -it -e DISPLAY -v /tmp/.X11-unix:/tmp/.X11-unix:ro \
  -v ~/planta-profile:/home/planta/.selenium_profiles \
  planta-filler:local --url https://planta.example.com/ --login-only
```

Make sure UID 1000 can write to the directory (`chown 1000:1000 ~/planta-profile`
or `podman unshare chown 1000:1000 ~/planta-profile` for rootless Podman).

## Headless runs

```bash
docker run --rm -it -v planta-profile:/home/planta/.selenium_profiles \
  planta-filler:local --url https://planta.example.com/ --headless --close-delay 0
```

Add any other option after the image name, for example
`--week=-1 --strategy random`. `make docker-run PLANTA_URL=... ARGS="--week=-1"` is a shortcut.

Reference files live on the host; mount them read-only:

```bash
docker run --rm -it -v planta-profile:/home/planta/.selenium_profiles \
  -v ~/planta:/data/reference:ro \
  planta-filler:local --url https://planta.example.com/ --headless --close-delay 0 \
  --strategy copy_reference --reference-file /data/reference/my_week.csv
```

To export a reference file, mount the directory writable and export to it:
`-v ~/planta:/data/reference ... --export-reference /data/reference/my_week.csv`.

## docker compose

```bash
cp .env.example .env         # set PLANTA_URL (and REFERENCE_DIR)
docker compose run --rm login            # once, option A above
docker compose run --rm fill             # headless fill of the current week
docker compose run --rm fill --week=-1 --strategy random   # extra options are appended
```

`REFERENCE_DIR` (default `./examples/reference-files`) is mounted at
`/data/reference`. Podman users can use `podman compose` (with the docker-compose
provider) or `podman-compose`.

## Scheduled runs with the container

A cron entry that fills the current week every weekday evening:

```cron
30 17 * * 1-5 docker run --rm -v planta-profile:/home/planta/.selenium_profiles planta-filler:local --url https://planta.example.com/ --headless --close-delay 0 >> ~/planta-filler.log 2>&1
```

Drop `-it` in non-interactive contexts. When the log says "The timesheet did not
appear", the session expired: repeat the login step.

## Troubleshooting

| Symptom | Fix |
|---|---|
| `Could not start Firefox` | The image is broken or out of memory; rebuild, give the container at least 1 GB RAM (`--memory 1g`, `--shm-size 512m` helps on some hosts). |
| `The timesheet did not appear` in headless mode | Not logged in: repeat the login step. |
| Firefox window does not show with option A | `xhost +local:` not run, `DISPLAY` not set, or no X11 socket (Wayland without XWayland). |
| `Permission denied` on the profile directory | The directory is not writable by UID 1000; see option C. |
| Profile "was last used with a newer version" | Set `MOZ_ALLOW_DOWNGRADE=1` or recreate the profile in the container. |
