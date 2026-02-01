def format_git_output(raw_output):
    lines = raw_output.splitlines()
    summary = []
    files = []
    changes = []

    for line in lines:
        if line.startswith("Fast-forward") or line.startswith("Updating") or line.startswith("From "):
            summary.append(line)
        elif "|" in line:
            parts = line.split("|")
            filename = parts[0].strip()
            stats = parts[1].strip()
            plus_count = stats.count("+")
            minus_count = stats.count("-")
            numbers = [int(s) for s in stats.split() if s.isdigit()]
            files.append(f"{filename}\n+ {plus_count}\n- {minus_count}")
        elif "changed" in line and ("insertion" in line or "deletion" in line):
            changes.append(line)
        else:
            summary.append(line)

    summary_block = "```shell\n" + "\n".join(summary) + "\n```" if summary else ""
    files_block = "```diff\n" + "\n".join(files) + "\n```" if files else ""
    changes_block = "```diff\n" + "\n".join(changes) + "\n```" if changes else ""
    return summary_block + files_block + changes_block


def format_git_output_ansi(raw_output):
    """Return ANSI-colored git output for Discord ```ansi blocks."""
    GREY = "\x1b[90m"
    GREEN = "\x1b[32m"
    RED = "\x1b[31m"
    YELLOW = "\x1b[33m"
    CYAN = "\x1b[36m"
    RESET = "\x1b[0m"

    colored = []
    for line in raw_output.splitlines():
        stripped = line.strip()

        if stripped.startswith("Already up to date"):
            colored.append(f"{GREEN}{line}{RESET}")
        elif stripped.startswith(("Fast-forward", "Updating", "From ")):
            colored.append(f"{GREY}{line}{RESET}")
        elif stripped.startswith("fatal") or "fatal:" in stripped or stripped.startswith("error") or "error:" in stripped:
            colored.append(f"{RED}{line}{RESET}")
        elif "|" in line:
            parts = line.split("|", 1)
            file_part = parts[0].strip()
            stats_part = parts[1].strip()

            stats_colored = stats_part
            stats_colored = stats_colored.replace("+", f"{GREEN}+{RESET}{YELLOW}")
            stats_colored = stats_colored.replace("-", f"{RED}-{RESET}{YELLOW}")

            colored.append(f"{CYAN}{file_part}{RESET} {YELLOW}{stats_colored}{RESET}")
        elif stripped.startswith("+"):
            colored.append(f"{GREEN}{line}{RESET}")
        elif stripped.startswith("-"):
            colored.append(f"{RED}{line}{RESET}")
        else:
            colored.append(line)

    return "\n".join(colored)
