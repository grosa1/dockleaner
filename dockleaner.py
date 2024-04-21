from __future__ import annotations

import argparse
import datetime
import difflib
import logging
from pyclbr import Class
from typing import List

import docker

from logic.dockerfile_obj import Dockerfile
from smell_solvers.smell_solver import SmellSolver
from utils.cache_handler import clear_cache

logging.basicConfig(level=logging.INFO, format='%(asctime)s :: %(levelname)s :: %(message)s')
logger = logging.getLogger(__name__.split('.')[0])
logger.setLevel(logging.DEBUG)


def get_argparser() -> argparse.ArgumentParser:
    """
    Get the configured argument parser
    """

    parser = argparse.ArgumentParser(description='Fix Dockerfile smells')
     # todo: check cache
    parser.add_argument('--cache', '-c',
                        action='store_true',
                        dest='cache',
                        required=False,
                        help='If selected, clears the cache of pulled image')
    parser.add_argument('--overwrite', '-o',
                        action='store_true',
                        dest='overwrite',
                        required=False,
                        help='Set TRUE to overwrite the target Dockerfile after the fix')
    parser.add_argument('--ignore', '-i',
                        metavar='rules_to_ignore',
                        dest='ignored',
                        nargs='+',
                        required=False,
                        help='The rules that the solver must ignore')
    parser.add_argument('--rule',
                        metavar='rules_to_fix',
                        dest='to_fix',
                        nargs='+',
                        required=False,
                        help='Specify one or more specific rules to fix')

    required = parser.add_argument_group('required arguments')
    required.add_argument('--path', '-p',
                          metavar='filepath',
                          dest='path',
                          required=True,
                          help='The path of the Dockerfile')
# todo: if not date provided, use current as default
    required.add_argument('--last-edit', '-d',
                          metavar='dockerfile_date',
                          dest='date',
                          required=True,
                          type=date_string,
                          help='Last edit date of the given Dockerfile. Format "YYYY-MM-DD".')

    return parser


def date_string(s: str) -> datetime:
    """
    Get date from given date string
    :param s: date string in the format 'YYYY-MM-DD'
    :return: datetime.datetime(YYYY, MM, DD, 0, 0, 0)
    """

    try:
        return datetime.datetime.strptime(s, "%Y-%m-%d")
    except ValueError:
        msg = f"Not a valid date (Expected format, 'YYYY-MM-DD'): '{s}'."
        raise argparse.ArgumentTypeError(msg)


def get_class(kls: str) -> Class:
    """
    Retrieve the instance of a specific class
    :param kls: class filepath
    :return: a Class object
    """
    parts = kls.split('.')
    module = ".".join(parts[:-1])
    m = __import__(module)
    for comp in parts[1:]:
        m = getattr(m, comp)
    return m


def fix_dockerfile(dockerfile: Dockerfile, ignored_rules: List) -> None:
    """
    Fix the given Dockerfile
    :param dockerfile: Dockerfile to fix
    :param ignored_rules: list of rules to not fix
    """
    RULES_PATH = 'smell_solvers.rules.'
    solver = SmellSolver()

    keys = list(dockerfile.smells_dict.keys())
    fixed_lines = []
    dict_changed = True
    while dict_changed:
        dict_changed = False

        for pos in keys:
            smells = dockerfile.smells_dict[pos]
            for smell in smells:
                if solver.strategy_exists(smell.code) and smell.code not in ignored_rules:
                    logger.info(f'Fixing smell {smell.code} on line {smell.line}')
                    # Dynamically choose the strategy
                    solver.strategy = get_class(RULES_PATH + smell.code + '.' + smell.code)()
                    solver.fix_smell(dockerfile, pos)
                    fixed_lines.append(smell.line)

            # Check if dictionary line position changed after fix
            if dockerfile.lines_changed:
                keys = list(set(dockerfile.smells_dict.keys()) - set(fixed_lines))
                dict_changed = True
                dockerfile.lines_changed = False
                break

            if dict_changed:
                break


def produce_dockerfile(dockerfile: Dockerfile, overwrite: bool) -> None:
    """
    Generate the fixed Dockerfile
    :param dockerfile: Dockerfile to produce
    :param overwrite: boolean that represent the need to overwrite or not the original file
    """
    filepath = dockerfile.filepath + '-fixed' if not overwrite else dockerfile.filepath

    with open(filepath, 'w') as file:
        file.writelines(dockerfile.lines)

        if not overwrite:
            logger.info(f'You can find the resulting Dockerfile at: {filepath}')


def produce_log(filepath) -> None:
    """
    Generate the log of Dockerfile fixes
    :param filepath: path of the original Dockerfile
    """
    original_dockerfile = open(filepath).readlines()
    fixed_dockerfile = open(filepath + '-fixed').readlines()

    diff = difflib.HtmlDiff().make_file(original_dockerfile, fixed_dockerfile, filepath, filepath + '-fixed', charset='utf-8')
    with open(filepath + '-log.html', 'w', encoding='utf8') as file:
        file.write(diff)


if __name__ == '__main__':
    try:
        docker.from_env().info()
    except:
        logger.error("Docker daemon is not available. Please install and start Docker before running the tool.")

    parser = get_argparser()
    args = parser.parse_args()

    if args.cache:
        clear_cache()

    fix_and_overwrite = True if args.overwrite else False

    ignored_rules = list()
    if args.to_fix:
        logger.info("Fixing only: %s", args.to_fix)
        ignored_rules = [r for r in SmellSolver()._available_strategies if r not in args.to_fix]
    elif args.ignored:
        logger.info("Ignoring rules: %s", args.ignored)
        ignored_rules = args.ignored

    dockerfile = Dockerfile(args.path, args.date)

    if dockerfile.smells_dict:
        fix_dockerfile(dockerfile, ignored_rules)
        produce_dockerfile(dockerfile, fix_and_overwrite)

        if not fix_and_overwrite:
            produce_log(args.path)
    else:
        logger.info(f'Your Dockerfile has no smells.')
