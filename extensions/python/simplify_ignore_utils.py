"""
simplify_ignore_utils.py
Shared helpers for the simplify-ignore Agent Zero extension.

Ported from simplify-ignore.sh (Claude Code hook) — preserves exact logic:
  - block_hash   : sha1[:8] of raw buf string (start line + content + end line)
  - filter_content: replace simplify-ignore-start/end blocks with BLOCK_<hash> placeholders
  - expand_content: replace BLOCK_<hash> placeholders back with original block content

Cache key and structure used by all three hook-point extensions:
  context.data[CACHE_KEY] = {
      file_path: {
          'original': str,       # real file content (updated after each model edit)
          'blocks': {
              hash8: {
                  'content': str,   # full block text incl. start+end marker lines
                  'reason':  str,   # optional reason label ('' if none)
                  'prefix':  str,   # text before 'simplify-ignore-start' on that line
                  'suffix':  str,   # ' */' | ' -->' | ''
              }
          }
      }
  }
"""
import hashlib
import re
import sys

CACHE_KEY = 'simplify_ignore_cache'


# ── Hashing ───────────────────────────────────────────────────────────────────

def _block_hash(content: str) -> str:
    """SHA-1 of content (encoded UTF-8), first 8 hex chars.
    Mirrors: block_hash() { printf '%s' "$1" | shasum | cut -c1-8; }
    """
    return hashlib.sha1(content.encode('utf-8', errors='replace')).hexdigest()[:8]


# ── Marker line parsing ───────────────────────────────────────────────────────

def _parse_start_line(line: str):
    """
    Parse a line that contains 'simplify-ignore-start'.

    Returns (prefix, suffix, reason):
      prefix  — everything before 'simplify-ignore-start' (the comment opener)
      suffix  — ' */'  if line contains '*/'
                ' -->' if line contains '-->'
                ''     otherwise
      reason  — text after 'simplify-ignore-start:' stripped of suffix/whitespace,
                or '' if no colon-reason is present

    Mirrors the prefix/suffix/reason extraction in bash filter_file().
    """
    idx = line.index('simplify-ignore-start')
    prefix = line[:idx]

    suffix = ''
    if '*/' in line:
        suffix = ' */'
    elif '-->' in line:
        suffix = ' -->'

    reason = ''
    marker = 'simplify-ignore-start:'
    if marker in line:
        after = line[line.index(marker) + len(marker):]
        after = after.strip()
        # Strip closing comment delimiter and trailing whitespace
        after = re.sub(r'\s*\*/.*$', '', after)
        after = re.sub(r'\s*-->.*$', '', after)
        reason = after.strip()

    return prefix, suffix, reason


# ── Filter: real code → placeholders ─────────────────────────────────────────

def filter_content(content: str, file_path: str = '<unknown>'):
    """
    Scan *content* for simplify-ignore-start/end blocks and replace each
    span (start line, interior, end line) with a single BLOCK_<hash> line.

    Faithfully mirrors bash filter_file():
      - buf starts with the start-marker line itself
      - interior lines are appended (newline-joined)
      - end-marker line is appended before hashing
      - single-line block (start+end on same line): the whole line is the buf
      - unclosed block: flushed verbatim to output with a stderr warning
      - trailing-newline status of *content* is preserved in filtered output

    Returns:
      filtered   (str)  — content with block spans replaced by placeholder lines
      blocks     (dict) — {hash8: {content, reason, prefix, suffix}}
      had_blocks (bool) — True when ≥1 block was replaced
    """
    source_ends_nl = content.endswith('\n')
    lines = content.splitlines()

    output_lines = []
    blocks: dict = {}
    in_block = False
    buf_lines: list = []
    reason = prefix = suffix = ''
    count = 0

    for line in lines:
        # ── Not currently inside a block ──────────────────────────────────────
        if not in_block:
            if 'simplify-ignore-start' not in line:
                output_lines.append(line)
                continue

            # Start marker found
            in_block = True
            buf_lines = [line]
            prefix, suffix, reason = _parse_start_line(line)

            # ── Single-line block: start and end on same line ─────────────────
            if 'simplify-ignore-end' in line:
                in_block = False
                buf = '\n'.join(buf_lines)
                h = _block_hash(buf)
                count += 1
                blocks[h] = {'content': buf, 'reason': reason,
                             'prefix': prefix, 'suffix': suffix}
                if reason:
                    output_lines.append(f'{prefix}BLOCK_{h}: {reason}{suffix}')
                else:
                    output_lines.append(f'{prefix}BLOCK_{h}{suffix}')
                buf_lines = []
                reason = prefix = suffix = ''
            # else: multi-line block opened — start line is NOT written to output
            continue

        # ── Inside a multi-line block: accumulate ─────────────────────────────
        buf_lines.append(line)

        if 'simplify-ignore-end' not in line:
            continue

        # End marker found: close block
        in_block = False
        buf = '\n'.join(buf_lines)
        h = _block_hash(buf)
        count += 1
        blocks[h] = {'content': buf, 'reason': reason,
                     'prefix': prefix, 'suffix': suffix}
        if reason:
            output_lines.append(f'{prefix}BLOCK_{h}: {reason}{suffix}')
        else:
            output_lines.append(f'{prefix}BLOCK_{h}{suffix}')
        buf_lines = []
        reason = prefix = suffix = ''

    # ── Unclosed block: flush verbatim with warning ───────────────────────────
    if in_block and buf_lines:
        print(
            f'Warning: unclosed simplify-ignore-start in {file_path} '
            '(block not hidden)',
            file=sys.stderr,
        )
        output_lines.extend(buf_lines)

    # ── Reconstruct, preserving trailing-newline status ───────────────────────
    filtered = '\n'.join(output_lines)
    if source_ends_nl:
        filtered += '\n'

    return filtered, blocks, count > 0


# ── Expand: placeholders → real code ─────────────────────────────────────────

def expand_content(content: str, blocks: dict, file_path: str = '<unknown>'):
    """
    Expand BLOCK_<hash> placeholders back to their original block content.

    Implements the same three-level progressive fallback as the bash hook:
      1. Full placeholder  : prefix + 'BLOCK_h: reason' + suffix
      2. No-reason match   : prefix + 'BLOCK_h' + suffix
      3. Hash-only fallback: 'BLOCK_h' anywhere in line

    A line containing a placeholder that spans multiple original lines will be
    expanded to multiple lines in the output.

    Also warns (stderr) if a protected block appears to have been deleted by
    the model (neither placeholder nor first line of block found after expansion).

    Returns expanded (str) — content with all placeholders replaced.
    """
    source_ends_nl = content.endswith('\n')
    lines = content.splitlines()
    output_lines: list = []

    for line in lines:
        if 'BLOCK_' not in line:
            output_lines.append(line)
            continue

        # Try to expand every known hash found on this line
        for h, info in blocks.items():
            if f'BLOCK_{h}' not in line:
                continue

            prefix      = info['prefix']
            suffix      = info['suffix']
            reason      = info['reason']
            block_text  = info['content']

            # ── Level 1: full placeholder (with reason) ───────────────────────
            if reason:
                placeholder = f'{prefix}BLOCK_{h}: {reason}{suffix}'
            else:
                placeholder = f'{prefix}BLOCK_{h}{suffix}'

            if placeholder in line:
                line = line.replace(placeholder, block_text)

            # ── Level 2 & 3: fallbacks if BLOCK_h still present ──────────────
            # (only if the block_text itself doesn't contain the hash token,
            #  to avoid infinite replacement)
            if f'BLOCK_{h}' in line and f'BLOCK_{h}' not in block_text:
                print(
                    f'Warning: placeholder BLOCK_{h} in {file_path} was '
                    'modified by model, using fuzzy match',
                    file=sys.stderr,
                )
                # Level 2: prefix+hash+suffix (no reason)
                fuzzy = f'{prefix}BLOCK_{h}{suffix}'
                if fuzzy in line:
                    line = line.replace(fuzzy, block_text)

                # Level 3: bare hash token
                if f'BLOCK_{h}' in line and f'BLOCK_{h}' not in block_text:
                    line = line.replace(f'BLOCK_{h}', block_text)

        # A replaced placeholder may expand to multiple lines
        output_lines.extend(line.split('\n'))

    # ── Warn about deleted blocks ─────────────────────────────────────────────
    expanded_joined = '\n'.join(output_lines)
    for h, info in blocks.items():
        if f'BLOCK_{h}' not in expanded_joined:
            first_line = info['content'].splitlines()[0] if info['content'] else ''
            if first_line and first_line not in expanded_joined:
                print(
                    f'Warning: protected block BLOCK_{h} was deleted by model '
                    f'in {file_path}',
                    file=sys.stderr,
                )

    result = '\n'.join(output_lines)
    if source_ends_nl:
        result += '\n'
    return result
