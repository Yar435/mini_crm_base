'''

Коротко о логике усечения (константы ниже):

DISPLAY_MODE = "FULL" — всё показывать.

DISPLAY_MODE = "TRUNCATE" — если число элементов
(папок+файлов) в папке > X_LIMIT, то:

показываем все папки;

считаем files_to_show = X_LIMIT - num_dirs.

если files_to_show > 0 — показываем столько файлов (альфавитно);

если files_to_show <= 0 — показываем ровно FALLBACK_SHOW_FILES (Z),
заданное в константе.

Папки из IGNORE_DIR_PATTERNS отображаются, но в них не заходим (как просил).

Поддержка шаблонов: обычный glob (*.js) и regex — для regex
добавляй префикс re: (пример re:^test_\\d+$).

'''

import fnmatch
import io
import re
import sys
from pathlib import Path

#
# ========== Конфигурация (редактируй здесь) ==========
#
# Если BASE_PATH пустая строка -> стартуем от места где лежит этот файл.
# BASE_PATH = "C:\\Users\\Yar43\\OneDrive\\Документы\\Obsidian Vault"
# пример: "/home/user/projects" или "" для текущей папки скрипта
BASE_PATH = ""
# Режим отображения: "FULL" или "TRUNCATE"
DISPLAY_MODE = "TRUNCATE"  # "FULL" or "TRUNCATE"

# Ограничение X из описания: если (files+dirs) > X_LIMIT — применяем усечение
X_LIMIT = 20 # X

# Если X_LIMIT - num_dirs <= 0 -> показываем FALLBACK_SHOW_FILES (Z)
FALLBACK_SHOW_FILES = 2  # Z

# Игнорируем скрытые файлы/папки (начинающиеся с точки)
IGNORE_HIDDEN = True

# Списки шаблонов для исключения входа в папки и отображения файлов.
# Поддержка:
#  - glob patterns: "*.git", "node_modules"
#  - regex: prefix "re:" then raw regex, например r"re:^test_\\d+$"
IGNORE_DIR_PATTERNS = [
    "node_modules",
    "*.git",
    "venv",
    # "re:^__pycache__$",
]

# Аналогично для файлов (если нужно исключить
# конкретные файлы из вывода и подсчёта)
IGNORE_FILE_PATTERNS = [
    "*.pyc",
    "*.log",
]

# ======== Поддержка Unicode в Windows-консолях ========
# Это решает проблемы с кириллицей при выводе
if sys.stdout.encoding.lower() != "utf-8":
    sys.stdout = io.TextIOWrapper(
        sys.stdout.buffer,
        encoding="utf-8",
        errors="replace",
    )
    sys.stderr = io.TextIOWrapper(
        sys.stderr.buffer,
        encoding="utf-8",
        errors="replace",
    )
# ======================================================


def is_regex_pattern(pat: str) -> bool:
    return pat.startswith("re:")


def matches_any(name: str, patterns: list) -> bool:
    """Поддерживает glob и regex (префикс re:)."""
    for pat in patterns:
        if is_regex_pattern(pat):
            try:
                r = re.compile(pat[3:])
            except re.error:
                # некорректный regex — игнорируем этот паттерн
                continue
            if r.search(name):
                return True
        else:
            if fnmatch.fnmatch(name, pat):
                return True
    return False


def should_ignore_name(name: str, is_dir: bool) -> bool:
    if IGNORE_HIDDEN and name.startswith("."):
        return True
    if is_dir:
        return matches_any(name, IGNORE_DIR_PATTERNS)
    else:
        return matches_any(name, IGNORE_FILE_PATTERNS)


def get_sorted_entries(path: Path):
    """
    Возвращает два списка: dirs, files — оба отсортированы алфавитно,
    исключая скрытые/паттерны по конфигу, но НЕ исключая папки,
    в которые нельзя заходить:
    (мы хотим их отображать, но не заходить в них).
    """
    try:
        entries = list(path.iterdir())
    except PermissionError:
        return [], []
    dirs = []
    files = []
    for p in entries:
        name = p.name
        if p.is_dir():
            # NOTE: мы НЕ убираем папку из списка,
            # если она совпадает с IGNORE_DIR_PATTERNS,
            # при этом в printing/recursing мы будем не заходить в неё.
            if IGNORE_HIDDEN and name.startswith("."):
                continue
            dirs.append(p)
        else:
            if IGNORE_HIDDEN and name.startswith("."):
                continue
            if matches_any(name, IGNORE_FILE_PATTERNS):
                continue
            files.append(p)
    dirs.sort(key=lambda p: p.name.lower())
    files.sort(key=lambda p: p.name.lower())
    return dirs, files


def limited_file_list(files, num_to_show):
    """
    Возвращает первые num_to_show файлов и число скрытых.
    """
    total = len(files)
    if num_to_show >= total:
        return files, 0
    shown = files[:num_to_show]
    hidden_count = total - num_to_show
    return shown, hidden_count


def print_tree(root: Path):
    """
    Публичная функция: печатает дерево от root.
    Использует DISPLAY_MODE и X_LIMIT и т.д.
    """
    # Normalize root
    root = root.resolve()
    print(root.name)

    def _recurse(path: Path, prefix: str = ""):
        dirs, files = get_sorted_entries(path)
        total_entries = len(dirs) + len(files)

        files_to_display = files
        hidden_files_count = 0
        if DISPLAY_MODE == "TRUNCATE" and total_entries > X_LIMIT:
            # показываем все папки + (X_LIMIT - num_dirs) файлов (если >0),
            # иначе показываем FALLBACK_SHOW_FILES файлов
            num_dirs = len(dirs)
            allowed_files_count = X_LIMIT - num_dirs
            if allowed_files_count > 0:
                files_to_display, hidden_files_count = limited_file_list(
                    files,
                    allowed_files_count,
                )
            else:
                # X_LIMIT < num_dirs
                files_to_display, hidden_files_count = limited_file_list(
                    files,
                    FALLBACK_SHOW_FILES,
                )

        combined = []
        for d in dirs:
            combined.append((d, True))
        for f in files_to_display:
            combined.append((f, False))

        for idx, (entry, is_dir) in enumerate(combined):
            name = entry.name
            is_last = (idx == len(combined) - 1) and (hidden_files_count == 0)
            branch = "└── " if is_last else "├── "
            print(prefix + branch + name)

            if is_dir:
                if matches_any(name, IGNORE_DIR_PATTERNS):
                    continue
                new_prefix = prefix + ("    " if is_last else "│   ")
                _recurse(entry, new_prefix)

        if hidden_files_count > 0:
            # place this as the last line under current directory
            more_line = f"... ({hidden_files_count} file(s) hidden)"
            # the 'more' line should be last child
            branch = "└── "
            print(prefix + branch + more_line)

    _recurse(root, "")


def main():
    if BASE_PATH:
        start = Path(BASE_PATH)
    else:
        try:
            start = Path(__file__).parent.resolve()
        except NameError:
            start = Path.cwd().resolve()

    if not start.exists():
        print(f"ERROR: start path does not exist: {start}", file=sys.stderr)
        sys.exit(1)
    if not start.is_dir():
        print(
            f"ERROR: start path is not a directory: {start}",
            file=sys.stderr,
        )
        sys.exit(1)

    try:
        print_tree(start)
    except KeyboardInterrupt:
        print("\nInterrupted.", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
