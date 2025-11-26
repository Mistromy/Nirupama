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
