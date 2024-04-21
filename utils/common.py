import backoff
import requests
import logging as logger
logger.getLogger('backoff').addHandler(logger.StreamHandler())


def dequote(s):
    """
    If a string has single or double quotes around it, remove them.
    Make sure the pair of quotes match.
    If a matching pair of quotes is not found,
    or there are less than 2 characters, return the string unchanged.
    """
    if (len(s) >= 2 and s[0] == s[-1]) and s.startswith(("'", '"')):
        return s[1:-1]
    return s


@backoff.on_exception(
    backoff.expo,
    requests.exceptions.RequestException,
    max_tries=5,
    giveup=lambda e: e.response is not None and e.response.status_code < 500
)
def request_data(url: str):
    return requests.get(url)


def parse_line_indent(line: str) -> str:
    n_spaces = 0
    for c in line.replace('\t', '    '):
        if c != " " and c != '\t':
            break
        n_spaces += 1

    return " " * n_spaces if n_spaces > 0 else " " * 4
