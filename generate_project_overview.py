#!/usr/bin/env python3
"""
generate_project_overview.py

Usage:
  python generate_project_overview.py
     -> Generates 'project_overview.txt' with the full code for text files,
        except for skipping listing files inside data/ directories.

  python generate_project_overview.py --short
     -> Generates 'project_overview.txt' with only function/ class signatures and
        docstrings for Python files, no full code included.

  python generate_project_overview.py --short path/to/exclude1.py path/to/exclude2.txt
     -> When using the --short flag, the additional file paths passed as arguments
        will be excluded from shortening and will be output in full.

  python generate_project_overview.py --skip path/to/skipDir path/to/skipFile.txt
     -> Skips the specified directories or files entirely. This flag can be used with
        or without the other flags.

Additionally, this script parses Python files to extract third-party imports
and writes them to 'requirements_autogenerated.txt'.
"""

import os
import sys
import ast
import argparse
from pathlib import Path

# A naive list of known standard library modules we skip from "requirements".
STANDARD_LIBS = {
    "abc", "argparse", "ast", "asyncio", "base64", "binascii", "bisect", "builtins", "calendar",
    "collections", "concurrent", "contextlib", "copy", "csv", "ctypes", "datetime", "decimal",
    "difflib", "dis", "distutils", "email", "enum", "errno", "faulthandler", "filecmp", "fileinput",
    "fnmatch", "fractions", "functools", "gc", "getopt", "getpass", "gettext", "glob", "gzip", "hashlib",
    "heapq", "hmac", "http", "imaplib", "imp", "importlib", "inspect", "io", "ipaddress", "itertools",
    "json", "logging", "lzma", "math", "multiprocessing", "numbers", "operator", "os", "pathlib",
    "pickle", "platform", "plistlib", "pprint", "queue", "random", "re", "runpy", "sched", "secrets",
    "select", "shlex", "shell", "shutil", "signal", "site", "smtp", "smtplib", "socket", "socketserver",
    "sqlite3", "ssl", "stat", "statistics", "string", "struct", "subprocess", "sys", "tempfile", "termios",
    "textwrap", "threading", "time", "timeit", "tkinter", "traceback", "types", "typing", "unittest",
    "urllib", "uuid", "venv", "warnings", "wave", "weakref", "webbrowser", "xml", "xmlrpc", "zipfile", "zipimport"
}

PROMPT_TEXT = """PROMPT FOR AI MODEL:

You are about to read a detailed overview of a software project. Please read 
everything in the following text and act as a helpful software engineering assistant. This overview itself is generated by one of the files which will be described below.

At the end of the overview, there will be a list of next steps for implementation. Please tailor your response for these steps. Generally, if more than one step is listed, focus on the first one only in your first response. The user will probably request the subsequent steps later.

If you can't find any next steps for the project listed at the bottom of the file, please do your best to look for mistakes, errors, discrepancies, or ways to clean up and refine the project, and decide yourself what should be considered high priority, and include that in your first response.

--------------------------------------------------------------------------------
"""

def is_text_file(file_path):
    """
    Check if a file is a text file based on its extension.
    """
    text_extensions = {
        '.txt', '.md', '.rst', '.py', '.java', '.js', '.ts', '.cpp', '.c',
        '.cs', '.html', '.css', '.xml', '.yaml', '.yml', '.sh', '.bat',
        '.go', '.rb', '.php', '.swift', '.kt', '.scala', '.pl', '.sql'
    }
    return file_path.suffix.lower() in text_extensions

def get_file_type(file_path):
    """
    Determine the file type based on its extension.
    """
    return file_path.suffix.lower() if file_path.suffix else 'No Extension'

def extract_functions_and_docstrings(file_content):
    """
    Parse Python code with AST, returning a string with
    module-level docstring, class names, function names,
    and any docstrings. Used for the --short flag.
    """
    try:
        tree = ast.parse(file_content)
    except SyntaxError:
        return ""

    lines = []
    module_docstring = ast.get_docstring(tree)
    if module_docstring:
        lines.append(f'Module Docstring:\n"""{module_docstring}"""\n')

    for node in tree.body:
        if isinstance(node, ast.FunctionDef):
            lines.append(f"def {node.name}(...):")
            func_doc = ast.get_docstring(node)
            if func_doc:
                lines.append(f'    """{func_doc}"""')
            lines.append("")

        elif isinstance(node, ast.ClassDef):
            lines.append(f"class {node.name}(...):")
            class_doc = ast.get_docstring(node)
            if class_doc:
                lines.append(f'    """{class_doc}"""')
            for subnode in node.body:
                if isinstance(subnode, ast.FunctionDef):
                    lines.append(f"    def {subnode.name}(...):")
                    method_doc = ast.get_docstring(subnode)
                    if method_doc:
                        lines.append(f'        """{method_doc}"""')
            lines.append("")

    return "\n".join(lines)

def parse_imports_from_python(file_content):
    """
    Parse Python imports using AST, returning a set of top-level modules
    that might be external dependencies.
    """
    try:
        tree = ast.parse(file_content)
    except SyntaxError:
        return set()

    imported_modules = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imported_modules.add(alias.name.split('.')[0])
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imported_modules.add(node.module.split('.')[0])
    return imported_modules

def is_standard_library(module_name):
    """
    Very naive check if a module name is in our known standard libraries set.
    """
    return module_name in STANDARD_LIBS

def traverse_directory(root_path, short_version=False, exclude_files=None, skip_paths=None):
    """
    Traverse the directory and collect:
      - directory structure (skipping file listings under data/ and any paths specified in skip_paths),
      - file contents (full or short version),
      - third-party imports from Python files.
    """
    directory_structure = []
    relevant_contents = []
    third_party_libraries = set()

    readme_extensions = {'.md', '.markdown', '.txt'}
    code_extensions = {
        '.py', '.java', '.js', '.ts', '.cpp', '.c', '.cs', '.html', '.css',
        '.xml', '.yaml', '.yml', '.sh', '.bat', '.go', '.rb',
        '.php', '.swift', '.kt', '.scala', '.pl', '.sql'
    }
    documentation_extensions = {'.md', '.markdown', '.txt', '.rst'}

    if exclude_files is None:
        exclude_files = []
    if skip_paths is None:
        skip_paths = []

    # Normalize exclude and skip paths to posix-style strings for reliable comparison.
    normalized_exclude = {Path(f).as_posix() for f in exclude_files}
    normalized_skip = {Path(f).as_posix() for f in skip_paths}

    for dirpath, dirnames, filenames in os.walk(root_path):
        # Skip hidden directories.
        dirnames[:] = [d for d in dirnames if not d.startswith('.')]

        relative_dir = os.path.relpath(dirpath, root_path)
        relative_dir_posix = Path(relative_dir).as_posix()

        # Skip this directory if it or any parent directory is in the skip list.
        if any(relative_dir_posix == skip_item or relative_dir_posix.startswith(skip_item + "/") for skip_item in normalized_skip):
            continue

        directory_structure.append(f"Directory: {relative_dir}")

        # Skip listing files if under data/
        if relative_dir.startswith('data'):
            continue

        # Optionally, modify dirnames in-place to skip subdirectories matching skip paths.
        dirnames[:] = [d for d in dirnames if not any(
            (Path(relative_dir, d).as_posix() == skip_item or Path(relative_dir, d).as_posix().startswith(skip_item + "/"))
            for skip_item in normalized_skip
        )]

        for filename in filenames:
            file_path = Path(dirpath) / filename
            if file_path.name.startswith('.'):
                continue

            # Build a relative file identifier (e.g., "src/file.py")
            relative_file = Path(relative_dir) / filename
            relative_file_posix = relative_file.as_posix()

            # Skip this file entirely if it is in the skip list.
            if any(relative_file_posix == skip_item or relative_file_posix.startswith(skip_item + "/")
                   for skip_item in normalized_skip):
                continue

            file_type = get_file_type(file_path)
            directory_structure.append(f"  File: {filename} | Type: {file_type}")

            # Determine if the file should be shortened.
            should_shorten = short_version and (relative_file_posix not in normalized_exclude)

            # If it's a recognized text file, try reading it.
            if (is_text_file(file_path)
                and (file_path.suffix.lower() in readme_extensions
                     or file_path.suffix.lower() in code_extensions
                     or file_path.suffix.lower() in documentation_extensions)):
                try:
                    content = file_path.read_text(encoding='utf-8')

                    # If it's a Python file, parse imports.
                    if file_path.suffix.lower() == '.py':
                        imports_in_file = parse_imports_from_python(content)
                        for lib in imports_in_file:
                            if not is_standard_library(lib):
                                third_party_libraries.add(lib)

                    # For Python files, if short_version is True and file is not excluded, shorten its content.
                    if file_path.suffix.lower() == '.py' and should_shorten:
                        extracted = extract_functions_and_docstrings(content)
                        if extracted.strip():
                            header = f"\n=== Functions & Docstrings in {relative_dir}/{filename} ===\n"
                            relevant_contents.append(header + extracted)
                    else:
                        header = f"\n=== Content of {relative_dir}/{filename} ===\n"
                        relevant_contents.append(header + content)

                except Exception as e:
                    print(f"Warning: Could not read {file_path}: {e}", file=sys.stderr)

    return directory_structure, relevant_contents, third_party_libraries

def main():
    parser = argparse.ArgumentParser(description="Generate a project overview.")
    parser.add_argument(
        "--short",
        action="store_true",
        default=False,
        help="Include only function names/docstrings for Python files."
    )
    # Positional arguments for file paths to exclude from shortening when using --short.
    parser.add_argument(
        "exclude_files",
        nargs="*",
        default=[],
        help="List of file paths (relative to the project root) to exclude from shortening when using --short."
    )
    parser.add_argument(
        "--skip",
        nargs="*",
        default=[],
        help="List of directories or file paths (relative to the project root) to skip entirely."
    )
    args = parser.parse_args()

    if not args.short and args.exclude_files:
        print("Warning: Exclude file arguments are ignored when not using --short.")

    root_path = Path(__file__).parent.resolve()
    print(f"Traversing directory: {root_path}")

    directory_structure, relevant_contents, third_party_libraries = traverse_directory(
        root_path,
        short_version=args.short,
        exclude_files=args.exclude_files,
        skip_paths=args.skip
    )

    # Write overview to project_overview.txt.
    output_file = root_path / "project_overview.txt"
    with output_file.open('w', encoding='utf-8') as f:
        # Write the prompt text.
        f.write(PROMPT_TEXT)
        f.write("\n=== Directory Structure ===\n")
        f.write("\n".join(directory_structure))
        f.write("\n\n=== Consolidated Documentation ===\n")
        f.write("\n".join(relevant_contents))

    print(f"Overview has been written to {output_file}")

    # Write discovered third-party libraries to requirements_autogenerated.txt.
    sorted_libs = sorted(third_party_libraries)
    req_file = root_path / "requirements_autogenerated.txt"
    with req_file.open('w', encoding='utf-8') as f:
        for lib in sorted_libs:
            f.write(lib.lower() + "\n")

    print(f"Auto-generated requirements saved to {req_file}")

if __name__ == "__main__":
    main()
