---
title: Freebox planner
emoji: ⚡
colorFrom: purple
colorTo: yellow
sdk: docker
pinned: false
short_description: Small app cheecking the freebox wifi config
---

Check out the configuration reference at https://huggingface.co/docs/hub/spaces-config-reference

# freebox-planner
Small app ensuring the Freebox wifi stays up, even when someone daily activates the planification.
It is based on [the previous work of Clément Caillaud.](https://domotique.blog.zastron.fr/pilotage-de-la-freebox-revolution-en-python/)

## Requirements
The app is containerized and intended to run on Huggingface.
Thus, it requires to [enable external access to the freebox.](https://assistance.free.fr/articles/329)

Moreover, the authentification needs the app to be registered first.

## App registration
Launch the following command to start the registation process:
```bash
python -m src.registration
```
A physical access to the server is mandatory.

This multi-steps process is undocumented but the current implementation found [useful insights here](https://dev.freebox.fr/bugs/task/13811)

## Wifi check
The main process perform a continuous check of the wifi status and the presence of a wifi planning.
Every half hour, the check is done, eventually leading to wifi activation and/or planning deactivation.

### Local launch
From the root folder:
```bash
python -m uvicorn src.api:app --host 0.0.0.0 --port 7860
```

### Containerized launch
```bash
docker run --rm --mount type=bind,src=./.env,target=/app/.env freebox-planner
```

### Huggingface launch
Create a space on Huggingface.
Set the environment variables (as secrets) in the space settings.
Push the current repository code into the space repository.
The container will automatically be built and deployed.

