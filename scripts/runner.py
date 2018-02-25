import subprocess
import os
import sys


def main():
    venv_dir = os.path.dirname(sys.argv[0])
    flake8 = os.path.join(venv_dir, 'flake8')
    mypy = os.path.join(venv_dir, 'mypy')
    python = os.path.join(venv_dir, 'python')

    print('Running Flake8...', flush=True)
    pytest_args = ' '.join([f"'{arg}'" for arg in sys.argv[1:]])
    result = subprocess.call(
        f'{flake8} --import-order-style=google '
        '--application-import-names=typebarrier typebarrier',
        shell=True)
    if result:
        return result

    print('Running MyPy...', flush=True)
    result_2 = subprocess.call(
        f'{mypy} --strict-optional '
        '--ignore-missing-imports '
        '--disallow-untyped-calls '
        '--disallow-untyped-defs '
        'typebarrier',
        shell=True)
    if result_2:
        return result_2

    print('Running PyTest...', flush=True)
    result_3 = subprocess.call(
        f'{python} -m pytest -vv -x --benchmark-group-by=func '
        f'{pytest_args}'.strip(),
        shell=True)

    if result_3:
        return result_3

    print('Running PyTest Benchmarks...', flush=True)
    os.environ['TYPIFY_BENCHMARK'] = 'true'
    return subprocess.call(
        f'{python} -m pytest -x --benchmark-group-by=func '
        f'{pytest_args}'.strip(),
        shell=True)
