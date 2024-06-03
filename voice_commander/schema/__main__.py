# Not necessarily intended to be used by users.
# Used to regenerate schema.json file and as local pre-commit hook
from __future__ import annotations

from pathlib import Path


def main() -> None:
    from voice_commander.schema import ProfileSchema

    this_script = Path(__file__)
    schema_file = this_script.parent / 'schema.json'
    expected_schema = ProfileSchema.schema_json(indent=4) + '\n'
    with open(schema_file, encoding='utf-8') as f:
        actual_schema = f.read()

    if expected_schema != actual_schema:
        with open(schema_file, 'w', encoding='utf-8', newline='\n') as f:
            f.write(expected_schema)
        raise SystemExit(1)
    raise SystemExit(0)


if __name__ == '__main__':
    main()
