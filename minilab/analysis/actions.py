"""Deterministic action classification and error detection for mini-swe-agent turns.

Categories follow Table 1 of "Same Signal, Different Semantics" (Exploration, Modification, Test, Navigation,
Utility, Unknown). A command is split into its parts (`a && b; c | d`, here-document bodies kept with their part);
each part gets a category and the name of the rule that matched; the turn gets the highest-priority category of its
parts. Deviations from the paper are documented in minilab/README.md ("Behavior analysis").
"""

import re
import shlex
from dataclasses import dataclass, field
from pathlib import PurePosixPath

PRIORITY = ["Modification", "Test", "Exploration", "Utility", "Unknown", "Navigation"]
SUBMIT_MARKER = "COMPLETE_TASK_AND_SUBMIT_FINAL_OUTPUT"

NAVIGATION = {"cd", "pushd", "popd", "pwd"}
EXPLORATION = {
    "cat", "head", "tail", "less", "more", "grep", "egrep", "fgrep", "rg", "ag", "ack", "find", "fd", "locate", "ls",
    "tree", "wc", "nl", "file", "stat", "awk", "gawk", "cut", "sort", "uniq", "diff", "cmp", "xxd", "od", "strings",
    "readlink", "realpath", "basename", "dirname", "du", "column", "tr", "jq", "sed",
}  # fmt: skip
TEST_RUNNERS = {"pytest", "py.test", "tox", "nox", "unittest", "nosetests", "trial", "ctest", "jest", "mocha", "vitest"}
FILE_CHANGERS = {"cp", "mv", "rm", "touch", "truncate", "dd", "patch"}
UTILITY = {
    "git", "pip", "pip3", "uv", "conda", "mamba", "poetry", "apt", "apt-get", "echo", "printf", "export", "source", ".",
    "which", "command", "type", "id", "whoami", "true", "false", "sleep", "env", "printenv", "date", "set", "unset",
    "exit", "kill", "ps", "nproc", "uname", "hostname", "mkdir", "chmod", "chown", "tar", "curl", "wget", "ln", "wait",
    "test", "[", "nohup", "clear",
}  # fmt: skip
LINTERS = {"ruff", "flake8", "pylint", "mypy", "pyright", "black", "isort", "pycodestyle", "pyflakes", "eslint"}
SHELL_KEYWORDS = {"if", "then", "else", "elif", "do", "while", "until", "for", "!", "{"}
SHELL_END = {"fi", "done", "esac", "}"}
ERROR_TAIL_LINES = 20  # typed errors are looked for at the end of the output, where tracebacks and summaries are
WRAPPERS = {"timeout", "env", "sudo", "time", "nice", "nohup", "stdbuf"}
PYTHON = re.compile(r"^(python[\d.]*|pypy[\d.]*)$")
PY_WRITE = re.compile(r"\.write_text\(|\.write_bytes\(|\.write\(|open\([^)]*['\"][wa]b?\+?['\"]|shutil\.(copy|move)")
PATH_LITERAL = re.compile(r"""['"]([\w./-]+\.[A-Za-z]\w{0,5}|[\w.-]+(?:/[\w.-]+)+)['"]""")
HEREDOC = re.compile(r"<<-?\s*(['\"]?)(\w+)\1")

# Error types, checked in order on the output of a turn with a non-zero return code.
ERROR_TYPES = [
    ("command_not_found", re.compile(r"command not found|: not found\b|No such file or directory: '?(rg|ag|fd)\b")),
    ("timeout", re.compile(r"\btimed out after\b|TimeoutExpired")),
    ("syntax_error", re.compile(r"\bSyntaxError\b|IndentationError|syntax error")),
    ("import_error", re.compile(r"ModuleNotFoundError|ImportError")),
    ("test_failure", re.compile(r"\b\d+ (failed|error)s?\b|^FAILED |ERROR collecting|AssertionError", re.M)),
    ("file_not_found", re.compile(r"No such file or directory|FileNotFoundError|cannot access")),
    ("permission_denied", re.compile(r"Permission denied|PermissionError")),
    ("tool_error", re.compile(r"^(fatal|error): ", re.M)),
    ("traceback", re.compile(r"Traceback \(most recent call last\)|\b\w+Error: ")),
    ("usage_error", re.compile(r"^usage:|invalid option|unrecognized option|unknown option", re.I | re.M)),
]
STRONG_ERROR = re.compile(r"Traceback \(most recent|command not found|SyntaxError|ModuleNotFoundError|^fatal: ", re.M)
NO_MATCH_PROGRAMS = {"grep", "egrep", "fgrep", "rg", "ag", "ack", "diff", "cmp", "git"}


@dataclass
class Part:
    text: str
    program: str
    category: str
    rule: str
    paths: list[str] = field(default_factory=list)


def extract_heredocs(command: str) -> tuple[str, list[str]]:
    """Remove here-document bodies from the command; return the remaining text and the bodies in order."""
    lines, bodies, out, i = command.split("\n"), [], [], 0
    while i < len(lines):
        out.append(lines[i])
        for match in HEREDOC.finditer(lines[i]):
            body, i = [], i + 1
            while i < len(lines) and lines[i].strip() != match.group(2):
                body.append(lines[i])
                i += 1
            bodies.append("\n".join(body))
        i += 1
    return "\n".join(out), bodies


def split_command(command: str) -> list[str]:
    """Split on &&, ||, ;, |, & and newlines outside quotes, $(...) and backticks."""
    parts, buf, quote, depth, i = [], [], "", 0, 0
    while i < len(command):
        c, two = command[i], command[i : i + 2]
        if quote:
            buf.append(c)
            if c == "\\" and quote == '"':
                buf.append(command[i + 1 : i + 2])
                i += 1
            elif c == quote:
                quote = ""
        elif c in "'\"`":
            quote = c
            buf.append(c)
        elif c == "\\" and command[i + 1 : i + 2] == "\n":
            i += 1
        elif two == "$(":
            depth += 1
            buf.append(two)
            i += 1
        elif c == ")" and depth:
            depth -= 1
            buf.append(c)
        elif depth == 0 and (two in ("&&", "||") or c in ";|&\n"):
            if c == "&" and two != "&&" and (i > 0 and command[i - 1] in "<>" or command[i + 1 : i + 2] == ">"):
                buf.append(c)  # 2>&1, &>file: redirections, not separators
            else:
                parts.append("".join(buf))
                buf = []
                i += 1 if two in ("&&", "||") else 0
        else:
            buf.append(c)
        i += 1
    parts.append("".join(buf))
    return [p.strip().strip("()").strip() for p in parts if p.strip().strip("()").strip()]


def tokens_of(text: str) -> list[str]:
    try:
        return shlex.split(text, comments=False)
    except ValueError:
        return text.split()


def redirects(tokens: list[str]) -> tuple[list[str], list[str]]:
    """Split tokens into (arguments, stdout redirect targets); fd duplications and stdin are dropped."""
    args, targets, skip = [], [], False
    for k, tok in enumerate(tokens):
        if skip:
            skip = False
            continue
        if m := re.fullmatch(r"(\d?|&)(>>?)(.*)", tok):
            if m.group(1) == "2" or m.group(3).startswith("&"):
                skip = not m.group(3) and m.group(1) == "2"
                continue
            if m.group(3):
                targets.append(m.group(3))
            elif k + 1 < len(tokens):
                targets.append(tokens[k + 1])
                skip = True
        elif re.fullmatch(r"\d?<<?-?.*|<", tok):
            skip = tok in ("<", "<<")
        else:
            args.append(tok)
    return args, targets


def target_kind(path: str) -> str:
    if path in ("/dev/null", "/dev/stdout", "/dev/stderr"):
        return "null"
    if path.startswith("/tmp/") or path.startswith("$TMPDIR"):
        return "scratch"
    if PurePosixPath(path).name in ("patch.txt", "patch.diff") or path.endswith((".patch", ".diff")):
        return "patch"
    return "repo"


def write_category(targets: list[str], rule: str) -> tuple[str, str] | None:
    kinds = {target_kind(t) for t in targets} - {"null"}
    if "repo" in kinds:
        return "Modification", rule
    if "patch" in kinds:
        return "Utility", "make_patch"
    if "scratch" in kinds:
        return "Test", "scratch_script"
    return None


def python_write_targets(code: str) -> list[str]:
    """Paths a Python script writes to: Path('x').write_text(...), var.write_text(...), open(x, 'w')."""
    names = dict(re.findall(r"""(\w+)\s*=\s*(?:Path\()?['"]([^'"]+)['"]""", code))
    direct = re.findall(r"""Path\(\s*['"]([^'"]+)['"]\s*\)\.write_(?:text|bytes)\(""", code)
    via_name = [names.get(v, "") for v in re.findall(r"\b(\w+)\.write_(?:text|bytes)\(", code)]
    opened = re.findall(r"""open\(\s*(?:['"]([^'"]+)['"]|(\w+))\s*,\s*(?:mode\s*=\s*)?['"][wax]""", code)
    return [t for t in direct + via_name + [lit or names.get(var, "") for lit, var in opened] if t]


def python_code_category(code: str) -> tuple[str, str]:
    if not PY_WRITE.search(code):
        return "Test", "python_run"
    targets = python_write_targets(code)
    if targets:
        repo = any(target_kind(t) == "repo" for t in targets)
    else:
        repo = any(target_kind(p) == "repo" for p in PATH_LITERAL.findall(code)) and "TemporaryDirectory" not in code
    return ("Modification", "python_edit") if repo else ("Test", "python_scratch")


def strip_prefix(tokens: list[str]) -> list[str]:
    """Drop variable assignments (`A=1 cmd`) and wrappers (`timeout 60 cmd`)."""
    while tokens:
        if re.fullmatch(r"[A-Za-z_]\w*=.*", tokens[0]) or tokens[0] in SHELL_KEYWORDS:
            tokens = tokens[1:]
        elif PurePosixPath(tokens[0]).name in WRAPPERS and len(tokens) > 1:
            tokens = tokens[1:]
            while tokens and (tokens[0].startswith("-") or re.fullmatch(r"[\d.]+[smh]?", tokens[0])):
                tokens = tokens[1:]
        else:
            return tokens
    return tokens


def positional(args: list[str], skip_first: bool) -> list[str]:
    values = [a for a in args if not a.startswith("-")]
    return values[1:] if skip_first else values


def path_like(arg: str) -> bool:
    has_shape = re.search(r"/|\.[A-Za-z]\w{0,5}$", arg) and re.search(r"[A-Za-z]", arg)
    return bool(has_shape) and not re.search(r"[*|\\^$(){}\[\]=,:;'\"<>]", arg)


def classify_part(text: str, body: str = "") -> Part:
    if SUBMIT_MARKER in text:
        return Part(text, "echo", "Utility", "submit")
    args, targets = redirects(strip_prefix(tokens_of(text)))
    program = PurePosixPath(args[0]).name if args else ""
    rest = args[1:]
    category = None
    if not args or program in SHELL_END:
        category = ("Utility", "shell_syntax")
    elif program in NAVIGATION:
        category = ("Navigation", "navigation")
    elif rest and all(a in ("--version", "-V", "version", "--help", "-h") for a in rest):
        category = ("Utility", "version_or_help")
    elif program in ("bash", "sh") and "-c" in rest[:-1]:
        inner = classify_command(rest[rest.index("-c") + 1])
        return Part(text, program, turn_category(inner), "shell_c", [q for part in inner for q in part.paths])
    elif program == "xargs" and positional(rest, False):
        return classify_part(" ".join(rest[next(i for i, a in enumerate(rest) if not a.startswith("-")) :]), body)
    elif program == "tee":
        category = write_category(positional(rest, False), "redirect_write") or ("Utility", "tee")
    elif program in ("sed", "perl") and any(re.fullmatch(r"-\w*i\S*|--in-place\S*|-pi\w*", a) for a in rest):
        category = write_category(positional(rest, True) or ["?"], "in_place_edit") or ("Modification", "in_place_edit")
    elif program == "git" and rest[:1] == ["apply"]:
        category = ("Modification", "git_apply")
    elif program == "git" and rest[:1] == ["grep"]:
        category = ("Exploration", "git_grep")
    elif program in LINTERS or PYTHON.match(program) and "-m" in rest and set(rest) & LINTERS:
        category = ("Test", "lint")
    elif program in TEST_RUNNERS or program in ("runtests.py", "run_tests.py") or args[0].endswith("bin/test"):
        category = ("Test", "test_runner")
    elif PYTHON.match(program) or program == "uv" and rest[:2] == ["run", "python"]:
        if (
            any(m in rest for m in ("pytest", "unittest", "doctest"))
            and "-m" in rest
            or "runtests.py" in " ".join(rest)
        ):
            category = ("Test", "test_runner")
        elif "-c" in rest:
            category = python_code_category(rest[rest.index("-c") + 1] if rest.index("-c") + 1 < len(rest) else "")
        elif body:
            category = python_code_category(body)
        else:
            category = ("Test", "python_run")
    elif program in ("node", "deno", "ruby", "perl", "bash", "sh") and positional(rest, False):
        category = ("Test", "script_run")
    elif program in ("make", "npm", "yarn", "pnpm", "go", "cargo", "mvn", "gradle") and "test" in rest:
        category = ("Test", "test_runner")
    elif program in FILE_CHANGERS:
        changed = positional(rest, False)
        repo = any(target_kind(p) == "repo" for p in changed)
        category = ("Modification", "file_change") if repo or program == "patch" else ("Utility", "scratch_cleanup")
    if targets and (written := write_category(targets, "redirect_write")):
        if category is None or PRIORITY.index(written[0]) < PRIORITY.index(category[0]):
            category = written
    if category is None:
        if program in EXPLORATION:
            category = ("Exploration", "sed_print" if program == "sed" else "read_search")
        elif program in UTILITY:
            category = ("Utility", program)
        else:
            category = ("Unknown", "unknown")
    paths = []
    if category[0] == "Exploration" and program != "git":
        paths = [p for p in positional(rest, program in ("grep", "egrep", "fgrep", "rg", "ag", "ack", "sed", "awk"))
                 if path_like(p) and target_kind(p) == "repo"]  # fmt: skip
    return Part(text, program, *category, paths=paths)


def classify_command(command: str) -> list[Part]:
    text, bodies = extract_heredocs(command)
    parts = []
    for piece in split_command(text):
        body = bodies.pop(0) if HEREDOC.search(piece) and bodies else ""
        part = classify_part(piece, body)
        part.text = f"{piece}\n{body}" if body else piece
        parts.append(part)
    return parts or [Part(command, "", "Unknown", "empty")]


def turn_category(parts: list[Part]) -> str:
    if any(p.rule == "submit" for p in parts):
        return "Utility"
    return min((p.category for p in parts), key=PRIORITY.index)


def error_type(output: str, returncode: int | None, exception_info: str, parts: list[Part]) -> str:
    """Empty string for a clean turn, else the error type."""
    if returncode is None:
        return ""
    if exception_info or returncode in (-9, 124, 137):
        return (
            "timeout" if re.search(r"time", exception_info + output, re.I) or returncode in (124, 137) else "exception"
        )
    if returncode == 0:
        return "command_not_found" if ERROR_TYPES[0][1].search(output) else ""
    tail = "\n".join(output.rstrip().splitlines()[-ERROR_TAIL_LINES:])
    if returncode == 127:
        return "command_not_found"
    if returncode == 1 and any(p.program in NO_MATCH_PROGRAMS for p in parts) and not STRONG_ERROR.search(tail):
        return ""  # grep/rg/diff found nothing: not a failure
    if ERROR_TYPES[0][1].search(output):
        return "command_not_found"
    for name, pattern in ERROR_TYPES[1:]:
        if pattern.search(tail):
            return name
    return "nonzero_exit"
