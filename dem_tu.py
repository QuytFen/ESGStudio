"""Khớp nguyên từ và ưu tiên cụm dài trên toàn bộ ba nhóm."""
import re
from lam_sach import lam_sach
from tu_dien import GROUPS

def dem_tu(text, language, groups=None):
    groups = GROUPS if groups is None else groups
    text = lam_sach(text)
    counts = {(group, name): 0 for group, entries in groups.items() for name, _, _ in entries}
    candidates = []
    for group, entries in groups.items():
        for name, english, vietnamese in entries:
            patterns = [english] if language == 'en' else [re.escape(lam_sach(v)) for v in vietnamese]
            for pattern in patterns:
                for match in re.finditer(r'(?<!\w)(?:' + pattern + r')(?!\w)', text):
                    candidates.append((match.start(), match.end(), group, name))
    occupied = bytearray(len(text))
    for start, end, group, name in sorted(candidates, key=lambda x: (-(x[1]-x[0]), x[0])):
        if not any(occupied[start:end]):
            counts[group, name] += 1
            occupied[start:end] = b'\x01' * (end-start)
    return counts
