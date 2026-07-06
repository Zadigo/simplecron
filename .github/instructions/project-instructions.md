---
applyTo: "**/*"
description: "Use when editing any part of the project, including frontends, backends, services, and shared libraries."
---
# Project instructions

## Tech Stack

* Python 3.14

## Repository structure

```text
simplecron
|  |── simplecron/
|  |   |── base.py
|  |   |── exceptions.py
|  |   |── operators.py
|  |   |── runners.py
|  |   |── typings.py
|  |   └── utils.py
└── README.md
```

* **simplecron/** Contains the main code for the cron application

## Commands

- Testing: `pytest`
- Build application: `uv build`
- Build and upload to pypi test: `uv build && uv publish --index pypitest`
- Bump dev version: `uv version --bump dev`

## References

You can also check these files in order to understand what the project is about:

* Read me file: [README.md](../../README.md)
* Future implmentations: [TODO.md](../../TODO.md)
