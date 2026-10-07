from pathlib import Path
import re


def main():
    root = Path(__file__).resolve().parents[1]
    path = root / 'UPI-Payments.SemanticModel/definition/expressions.tmdl'
    value = (root / 'data/raw').as_posix().replace('"', '""')
    source, count = re.subn(r'^expression DataRoot = "(?:[^"]|"")*" meta',
        lambda _: 'expression DataRoot = "' + value + '" meta',
        path.read_text(encoding='utf-8'), flags=re.MULTILINE)
    if count != 1:
        raise ValueError(f'Expected one DataRoot expression; found {count}')
    path.write_text(source, encoding='utf-8')
    print('Configured DataRoot:', value)


if __name__ == '__main__':
    main()
