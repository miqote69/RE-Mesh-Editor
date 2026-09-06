"""MDF naming helpers; no Blender or filesystem mutations."""
import ntpath
import re


def mdf_log_candidates(lines, asset_path, version):
    asset = asset_path.replace('\\', '/').strip('/')
    if not asset.lower().endswith('.mdf2') or '/' not in asset:
        return []
    directory, name = asset.rsplit('/', 1)
    stem = name[:-5]
    # Numbered costume variants share the same mesh; do not match other armor.
    stem = re.sub(r'_\d{2}$', '', stem)
    pattern = re.compile(r'(?:^|/)natives/stm/' + re.escape(directory) + '/('
                         + re.escape(stem) + r'(?:_\d{2})?\.mdf2)\.'
                         + re.escape(str(version)) + r'\s*$', re.IGNORECASE)
    found = {}
    for line in lines:
        match = pattern.search(line.replace('\\', '/').strip())
        if match:
            found.setdefault(match[1].lower(), match[1])
    return sorted(found.values(), key=str.lower)


def resolve_export_name(filepath, game, chosen_name):
    """Apply an explicitly chosen DD2 basename, preserving directory/version."""
    if game != 'DD2' or not chosen_name:
        return filepath
    if (ntpath.basename(chosen_name) != chosen_name or ':' in chosen_name
            or not chosen_name.lower().endswith('.mdf2')):
        raise ValueError('Game MDF name must be a filename ending in .mdf2 (without a folder or version).')
    match = re.fullmatch(r'(.*[\\/])?([^\\/]+\.mdf2)(\.\d+)', filepath, re.IGNORECASE)
    if not match:
        return filepath
    return (match[1] or '') + chosen_name + match[3]
