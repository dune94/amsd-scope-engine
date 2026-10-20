# v3.9 Score = Scope + Complexity + Risk -> SP band, planning calibration and PERT. All numbers from config/formula.yml.
from . import config
from .measure import scope_level

F = config.load('formula')


def _row(rows, n):
    return next(r for r in rows if r['max'] is None or n <= r['max'])


def complexity(n): return _row(F['complexity'], n)
def risk(n): return _row(F['risk'], n)
def band(score): return _row(F['bands'], score)['sp']
def scope_pts(br): return F['scope']['points'][scope_level(br)]


def sp(br, c_count, r_count):
    return band(scope_pts(br) + complexity(c_count)['points'] + risk(r_count)['points'])


def planning(base_br, upper_br, c_count, r_count):
    """Planning SP: Scope(BR x multiplier) + Complexity(drivers + extra) + Risk(drivers + extra); PERT over BASE / UPPER BR."""
    P = F['planning']; m = P['br_multiplier']
    c, r = c_count + P['complexity_extra'], r_count + P['risk_extra']
    o, ml, p = base_br, round(base_br * m), round(upper_br * m)
    w = F['pert']['weights']; expected = round((w[0] * o + w[1] * ml + w[2] * p) / sum(w))
    return dict(base_br=base_br, upper_br=upper_br, planning_br=ml, c_count=c_count, r_count=r_count,
                scope=F['scope']['levels'][scope_level(ml)], complexity=complexity(c)['level'], risk=risk(r)['level'],
                planning_sp=sp(ml, c, r), sp_as_measured=sp(base_br, c, r),
                pert=dict(o_br=o, m_br=ml, p_br=p, expected_br=expected, o_sp=sp(o, c, r), m_sp=sp(ml, c, r), p_sp=sp(p, c, r),
                          expected_sp=sp(expected, c, r)))
