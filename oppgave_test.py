"""Automatisk retting av FY1-01-bevegelse-fra-maledata.

Hver sjekk i SJEKKER er én deltest, og poengene fordeles likt på dem.
De samme sjekkene ligger i "Test løsningen din"-cellen nederst i notebooken.
"""
import pytest

from notebook_loader import last_notebook

def naer(a, b, rel=1e-3):
    """Sant hvis tallet a er innenfor rel (relativt) av b."""
    try:
        a, b = float(a), float(b)
    except (TypeError, ValueError):
        return False
    if b == 0:
        return abs(a) < 1e-9
    return abs(a - b) <= rel * abs(b)


def S(tekst):
    """Gjør tekst om til et sympy-uttrykk, f.eks. S("x**2 - 1")."""
    import sympy
    return sympy.sympify(tekst, locals={n: sympy.Symbol(n) for n in ("N", "O", "Q", "S")})


def lik(a, b):
    """Sant hvis a og b er matematisk like.

    Lister og mengder sammenlignes uten hensyn til rekkefølge, tupler (koordinater) i rekkefølge.
    """
    import sympy
    if a is None:
        return False
    if isinstance(b, tuple):
        if not isinstance(a, (tuple, list, sympy.Tuple)) or len(a) != len(b):
            return False
        return all(lik(x, y) for x, y in zip(a, b))
    if isinstance(b, (list, set)):
        if isinstance(a, sympy.FiniteSet):
            a = list(a)
        if not isinstance(a, (list, tuple, set)) or len(a) != len(b):
            return False
        rest = list(a)
        for y in b:
            for i, x in enumerate(rest):
                if lik(x, y):
                    del rest[i]
                    break
            else:
                return False
        return True
    if isinstance(b, dict):
        if not isinstance(a, dict) or len(a) != len(b):
            return False
        a = {str(k): v for k, v in a.items()}
        return all(str(k) in a and lik(a[str(k)], v) for k, v in b.items())
    try:
        a, b = sympy.sympify(a), sympy.sympify(b)
    except (sympy.SympifyError, TypeError):
        return False
    vanlige = lambda u: u.subs({s: sympy.Symbol(s.name) for s in u.free_symbols})
    a, b = vanlige(a), vanlige(b)
    if isinstance(a, sympy.Set) or isinstance(b, sympy.Set):
        return a == b
    if getattr(b, "is_Relational", False):
        return a == b
    try:
        return sympy.simplify(a - b) == 0
    except TypeError:
        return a == b

oppgave = last_notebook("oppgave")

SJEKKER = [
    ('1_fart', 'fart([0, 1, 3], [0, 2, 8]) skal gi [2, 3]', 'len(fart([0, 1, 3], [0, 2, 8])) == 2 and all(naer(a, b) for a, b in zip(fart([0, 1, 3], [0, 2, 8]), [2, 3]))'),
    ('1_midt', 'midtpunkter([0, 1, 3]) skal gi [0.5, 2]', 'len(midtpunkter([0, 1, 3])) == 2 and all(naer(a, b) for a, b in zip(midtpunkter([0, 1, 3]), [0.5, 2]))'),
    ('2', 'akselerasjon_fra_fart([0, 1, 2, 3], [2, 5, 8, 11]) skal gi 3', 'naer(akselerasjon_fra_fart([0, 1, 2, 3], [2, 5, 8, 11]), 3)'),
    ('3', 'akselerasjon_fra_posisjon skal gi a = 4 når s = 1 + 2t + 2t²', 'naer(akselerasjon_fra_posisjon([0, 0.5, 1, 1.5, 2], [1 + 2*t + 2*t**2 for t in [0, 0.5, 1, 1.5, 2]]), 4)'),
    ('3_data', 'akselerasjon_fra_posisjon på vogndataene skal gi ca. 0.85 m/s²', "naer(akselerasjon_fra_posisjon(*__import__('numpy').loadtxt('vogn.csv', delimiter=',', skiprows=1, unpack=True)), 0.85, rel=0.05)"),
]


@pytest.mark.parametrize(
    "beskrivelse,uttrykk", [s[1:] for s in SJEKKER], ids=[s[0] for s in SJEKKER]
)
def test_sjekk(beskrivelse, uttrykk):
    navnerom = {**vars(oppgave), "naer": naer, "lik": lik, "S": S}
    assert eval(uttrykk, navnerom), beskrivelse
