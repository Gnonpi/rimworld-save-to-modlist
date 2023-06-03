# rimworld-save-to-modlist

This project allow you to extract your modlist from a Rimworld save file.

## How to run it

To make it easier,
this script won't have any runtime requirements.

You just need to have **Python 3.10** installed.
You can install Python from [python.org](https://www.python.org/downloads/)
if it's not preinstalled in your system.

Then locate your save file.
It should be a `.rws` (weighting some MBs).
[This RimWorld wiki page](https://www.rimworldwiki.com/wiki/Save_file) might help finding it.
It might be a good idea to back it up.
Note the path to it.

Then locate your save file and run:
```
python3 generate_modlist_from_save.py \
    --input <location-to-your-save-file> \
    --output <desired-output-location>
```

It will read the content of your save file,
find the modlist used in it
and write both a `.rml` file and a `.csv` file.
The `.rml` can be used to load mods in Rimworld mod menu.
The `.csv` is there to make it easier for you to read the modlist.

## Contributing & testing

While I took the decision to not use libraries to run the script
(so that it's easy for people to use it),
I think it's better to use some when developing.

### Installing dependencies

The dependency configuration is done with [Poetry](https://python-poetry.org/).

Install the dependencies with it:
```commandline
$ poetry install
```

### Testing

Use poetry to run the tests.
They're written with [pytest](https://docs.pytest.org/)
and located in the `tests/` folder.

```commandline
$ poetry run pytest
```

### Hooks

In order to maintain good code quality,
use [pre-commit](https://pre-commit.com/)
to run checks before committing your changes.

Install and run the hooks with:
```commandline
$ poetry run pre-commit install
$ poetry run pre-commit run --all-files
```
