# Evidence rule for the Complexity / Risk drivers agent: a driver counts only with a quote found in the ticket text.
import re

_norm = lambda s: re.sub(r'\s+', ' ', (s or '')).strip().lower()


def validate(answer, text):
    """Returns (kept, dropped) per dimension. Kept: driver 1-5, first mention only, quote found in the ticket text."""
    t = _norm(text); kept, dropped = {}, []
    for dim in ('complexity', 'risk'):
        seen, kept[dim] = set(), []
        for d in (answer or {}).get(dim) or []:
            n, q = d.get('driver'), _norm(d.get('quote'))
            why = ('driver number not 1-5' if not isinstance(n, int) or not 1 <= n <= 5 else
                   'duplicate' if n in seen else
                   'no quote' if not q else
                   'quote not found in the ticket text' if q not in t else None)
            if why: dropped.append(dict(d, dimension=dim, reason=why)); continue
            seen.add(n); kept[dim].append(d)
    return kept, dropped
