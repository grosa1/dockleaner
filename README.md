# Dockleaner

Rule-based refactoring tool for fixing Dockerfile smells detected by [hadolint](https://github.com/hadolint/hadolint).

A detailed description of the tool and its evaluation can be found in the [preprint of the original article](https://giovannirosa.com/assets/pdf/rosa2024fixingsmells.pdf).

## Setup

The first step is to install [hadolint](https://github.com/hadolint/hadolint/releases/tag/v2.12.0).
Next, clone the repository and install the requirements:
```
conda create -n dockleaner python=3.7
conda activate dockleaner

pip install -r requirements.txt
```

Dockleaner was tested on `macOS` and `Arch Linux` using `Python 3.7`.

## Usage

Run `python3 dockleaner.py --help` to see the following help message:

```
optional arguments:
  -h, --help            show this help message and exit
  --cache, -c           If selected, clears the cache of pulled image
  --overwrite, -o       Set TRUE to overwrite the target Dockerfile after the
                        fix
  --ignore rules_to_ignore [rules_to_ignore ...], -i rules_to_ignore [rules_to_ignore ...]
                        The rules that the solver must ignore
  --rule rules_to_fix [rules_to_fix ...]
                        Specify one or more specific rules to fix

required arguments:
  --path filepath, -p filepath
                        The path of the Dockerfile
  --last-edit dockerfile_date, -d dockerfile_date
                        Last edit date of the given Dockerfile. Format "YYYY-
                        MM-DD".
```

Thus, the command:
```
python3 -u dockleaner.py -p Dockerfile -d "2023-04-12" --rule "DL3008" --overwrite
```
will fix the Dockerfile `Dockerfile` by pinning versions for apt packages and overwriting the file.

## Supported Smells

- :calendar:         [DL3000](https://github.com/hadolint/hadolint/wiki/DL3000)
- :calendar:         [DL3002](https://github.com/hadolint/hadolint/wiki/DL3002)
- :white_check_mark: [DL3003](https://github.com/hadolint/hadolint/wiki/DL3003)
- :calendar:         [DL3004](https://github.com/hadolint/hadolint/wiki/DL3004)
- :calendar:         [DL3005](https://github.com/hadolint/hadolint/wiki/DL3005)
- :white_check_mark: [DL3006](https://github.com/hadolint/hadolint/wiki/DL3006)
- :white_check_mark: [DL3007](https://github.com/hadolint/hadolint/wiki/DL3007)
- :white_check_mark: [DL3008](https://github.com/hadolint/hadolint/wiki/DL3008)
- :white_check_mark: [DL3009](https://github.com/hadolint/hadolint/wiki/DL3009)
- :calendar:         [DL3013](https://github.com/hadolint/hadolint/wiki/DL3013)
- :ok:               [DL3014](https://github.com/hadolint/hadolint/wiki/DL3014)
- :white_check_mark: [DL3015](https://github.com/hadolint/hadolint/wiki/DL3015)
- :calendar:         [DL3016](https://github.com/hadolint/hadolint/wiki/DL3016)
- :white_check_mark: [DL3020](https://github.com/hadolint/hadolint/wiki/DL3020)
- :calendar:         [DL3022](https://github.com/hadolint/hadolint/wiki/DL3022)
- :calendar:         [DL3024](https://github.com/hadolint/hadolint/wiki/DL3024)
- :white_check_mark: [DL3025](https://github.com/hadolint/hadolint/wiki/DL3025)
- :calendar:         [DL3027](https://github.com/hadolint/hadolint/wiki/DL3027)
- :calendar:         [DL3028](https://github.com/hadolint/hadolint/wiki/DL3028)
- :calendar:         [DL3029](https://github.com/hadolint/hadolint/wiki/DL3029)
- :ok:               [DL3042](https://github.com/hadolint/hadolint/wiki/DL3042)
- :calendar:         [DL3045](https://github.com/hadolint/hadolint/wiki/DL3045)
- :ok:               [DL3047](https://github.com/hadolint/hadolint/wiki/DL3047)
- :white_check_mark: [DL3048](https://github.com/hadolint/hadolint/wiki/DL3048)
- :white_check_mark: [DL3059](https://github.com/hadolint/hadolint/wiki/DL3059)
- :white_check_mark: [DL4000](https://github.com/hadolint/hadolint/wiki/DL4000)
- :calendar:         [DL4001](https://github.com/hadolint/hadolint/wiki/DL4001)
- :calendar:         [DL4003](https://github.com/hadolint/hadolint/wiki/DL4003)
- :white_check_mark: [DL4006](https://github.com/hadolint/hadolint/wiki/DL4006)

**Legend:**

- :white_check_mark: Supported
- :ok: Supported, but not validated via pull requests
- :pushpin: To be implemented
- :calendar: For future implementation

## License

The project is licensed under the MIT License. See [LICENSE](LICENSE) for details.

## Acknowledgements

The first prototype of Dockleaner was developed by [Alessandro Giagnorio](https://github.com/Devy99). Withouth his work, this project would not have been possible.
The prototype has been extended and improved by [Simone Scalabrino](https://github.com/intersimone999) and [Giovanni Rosa](https://github.com/grosa1) which is currently the maintainer of the project.

## How to Cite

The proposal of the study, which includes the tool and its evaulation, was first presented at ICSME'22 - Registered Reports Track.
```
@article{rosa2022fixing,
  title={Fixing dockerfile smells: An empirical study},
  author={Rosa, Giovanni and Scalabrino, Simone and Oliveto, Rocco},
  journal={arXiv preprint arXiv:2208.09097},
  year={2022}
}
```

Next, the complete study has been accepted at Empirical Software Engineering (EMSE).
```
@article{rosa2024fixingsmells,
  author    = {Giovanni Rosa and
              Federico Zappone and
              Simone Scalabrino and
              Rocco Oliveto},
  title     = {Fixing Dockerfile Smells: An Empirical Study},
  journal   = {Empirical Software Engineering},
  year      = {2024},
  note      = {To appear}
}
```
