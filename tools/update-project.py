#!/usr/bin/env python3
"""Update the portfolio's current project and push it. Python standard library only."""
import argparse
from datetime import date, datetime
import html
import json
from pathlib import Path
import re
import subprocess
import sys
from zoneinfo import ZoneInfo

DEFAULT_REPO = Path.home() / 'Documents/Codex/2026-09-30/create-a-new-site-with-sites/work/github-pages'
EXPECTED_ORIGINS = {'https://github.com/anaqvi02/anaqvi02.github.io', 'git@github.com:anaqvi02/anaqvi02.github.io', 'ssh://git@github.com/anaqvi02/anaqvi02.github.io'}
FILES = ['status.json', 'index.html']


def git(repo, *args, capture=True):
    result = subprocess.run(['git', '-C', str(repo), *args], text=True,
                            capture_output=capture, check=True)
    return result.stdout.strip() if capture else ''


def today():
    return datetime.now(ZoneInfo('America/Toronto')).date()


def eta(deadline):
    if deadline is None:
        return 'TBD'
    days = (date.fromisoformat(deadline) - today()).days
    if days <= 0:
        return 'ASAP'
    if days < 7:
        return f'{days} DAY' + ('S' if days != 1 else '')
    weeks = (days + 6) // 7
    return f'{weeks} WEEK' + ('S' if weeks != 1 else '')


def replace_once(pattern, replacement, text):
    result, count = re.subn(pattern, lambda _: replacement, text)
    if count != 1:
        raise ValueError('Homepage markup has changed; refusing a partial update.')
    return result


def build_update(status, markup, project, completion, deadline):
    project = project.strip()
    if not project or len(project) > 80 or any(ord(c) < 32 or ord(c) == 127 for c in project):
        raise ValueError('Project name must be 1–80 characters with no control characters.')
    if not 0 <= completion <= 100:
        raise ValueError('Completion must be a whole number from 0 to 100.')
    if deadline is not None:
        deadline = date.fromisoformat(deadline).isoformat()
    updated = dict(status)
    updated.update(project=project, completion=completion, deadline=deadline, updated=today().isoformat())
    old_option = f"Working away on {status['project'].upper()}..."
    new_option = f'Working away on {project.upper()}...'
    options = [new_option if value == old_option else value for value in status.get('status_options', [])]
    if new_option not in options:
        options.append(new_option)
    updated['status_options'] = options
    label = html.escape(project.upper())
    markup = replace_once(r'<span class="mono" data-current-project>[^<]*</span>',
                          f'<span class="mono" data-current-project>CURRENT PROJECT / {label}</span>', markup)
    markup = replace_once(r'<span class="proof-measure" data-progress-value>.*?</span></span>',
                          f'<span class="proof-measure" data-progress-value>{completion}<span>%</span></span>', markup)
    meter = (f'<div class="status-meter" aria-label="{html.escape(project, quote=True)} completion" '
             f'role="progressbar" aria-valuemin="0" aria-valuemax="100" aria-valuenow="{completion}">'
             f'<span style="width:{completion}%"></span></div>')
    markup = replace_once(r'<div class="status-meter"[^>]*><span[^>]*></span></div>', meter, markup)
    attr = f' data-deadline="{deadline}"' if deadline else ''
    markup = replace_once(r'<small class="progress-eta mono" data-progress-eta[^>]*>[^<]*</small>',
                          f'<small class="progress-eta mono" data-progress-eta{attr}>ETA / {eta(deadline)}</small>', markup)
    return updated, markup


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, epilog='No arguments: prompts for project, completion, and deadline. Blank keeps the current value.')
    parser.add_argument('--project', help='Current project name')
    parser.add_argument('--completion', type=int, help='Whole-number percentage, 0–100')
    parser.add_argument('--deadline', help='YYYY-MM-DD; use none or - to clear the ETA')
    parser.add_argument('--repo', type=Path, default=DEFAULT_REPO, help='Website checkout path')
    parser.add_argument('--dry-run', action='store_true', help='Preview without changing files, committing, or pushing')
    parser.add_argument('--push-only', action='store_true', help='Retry a failed push without making another edit')
    args = parser.parse_args(argv)
    repo = args.repo.expanduser().resolve()
    origin = git(repo, 'remote', 'get-url', '--push', 'origin').removesuffix('.git')
    if origin not in EXPECTED_ORIGINS or git(repo, 'branch', '--show-current') != 'main':
        raise ValueError('Use the anaqvi02 GitHub Pages repository on branch main.')
    if args.push_only:
        if args.dry_run:
            print('Would push main to origin; no files changed.')
        else:
            git(repo, 'push', 'origin', 'main', capture=False)
        return
    if not args.dry_run and git(repo, 'status', '--porcelain'):
        raise ValueError('The website has uncommitted edits. Commit or stash those first; no files changed.')
    interactive = all(value is None for value in (args.project, args.completion, args.deadline))
    if not args.dry_run:
        print('Syncing the website checkout…', flush=True)
        git(repo, 'fetch', 'origin', 'main', capture=False)
        if git(repo, 'rev-list', '--count', 'origin/main..HEAD') != '0':
            raise ValueError('Local commits are waiting to be pushed. Run with --push-only first.')
        git(repo, 'merge', '--ff-only', 'origin/main', capture=False)
    status_path, page_path = (repo / name for name in FILES)
    status = json.loads(status_path.read_text())
    project = args.project if args.project is not None else status['project']
    completion = args.completion if args.completion is not None else status['completion']
    deadline = args.deadline if args.deadline is not None else status.get('deadline')
    if interactive:
        project = input(f"Project [{project}]: ").strip() or project
        value = input(f"Completion % [{completion}]: ").strip()
        completion = int(value) if value else completion
        value = input(f"Deadline [{deadline or 'none'}] (YYYY-MM-DD, - to clear): ").strip()
        deadline = value if value else deadline
    if deadline is not None and deadline.lower() in ('none', '-'):
        deadline = None
    new_status, new_page = build_update(status, page_path.read_text(), project, completion, deadline)
    print(f"Current project: {new_status['project']} | {completion}% | ETA / {eta(deadline)}")
    if args.dry_run:
        print('Dry run: no files changed or pushed.')
        return
    # Build and validate both outputs before writing either one.
    old_status, old_page = status_path.read_bytes(), page_path.read_bytes()
    try:
        status_path.write_text(json.dumps(new_status, indent=2, ensure_ascii=False) + '\n')
        page_path.write_text(new_page)
    except OSError:
        status_path.write_bytes(old_status)
        page_path.write_bytes(old_page)
        raise
    if not git(repo, 'diff', '--', *FILES):
        print('Already up to date; nothing to push.')
        return
    git(repo, 'diff', '--check', '--', *FILES)
    git(repo, 'add', '--', *FILES)
    git(repo, 'commit', '-m', f"Update current project: {project} ({completion}%)", '--', *FILES, capture=False)
    try:
        git(repo, 'push', 'origin', 'main', capture=False)
    except subprocess.CalledProcessError:
        print('Saved and committed locally, but push failed. Retry with --push-only.', file=sys.stderr)
        raise
    print('Pushed! GitHub Pages will publish it shortly: https://anaqvi02.github.io/')


if __name__ == '__main__':
    try:
        main()
    except (ValueError, OSError, subprocess.CalledProcessError) as error:
        print(f'Error: {error}', file=sys.stderr)
        sys.exit(1)
    except (KeyboardInterrupt, EOFError):
        print('\nCancelled.', file=sys.stderr)
        sys.exit(130)
