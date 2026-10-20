# S5.2, S5.3, S2.6: the v3.9 formula and planning calibration, read from config/formula.yml.
from scope import score

# v3.9 reference, as written in the PI-12 basis (cut-offs 6/24/60 -> 0/3/5/8; C 0/1-2/3+ -> 0/1/3; R 0-1/2/3+ -> 0/2/4; bands)
lvl = lambda b: sum(b > c for c in (6, 24, 60)); spts = (0, 3, 5, 8)
cpt = lambda n: 0 if n <= 0 else 1 if n <= 2 else 3
rpt = lambda n: 0 if n <= 1 else 2 if n == 2 else 4
band = lambda x: 1 if x <= 1 else 2 if x == 2 else 3 if x <= 4 else 5 if x <= 8 else 8 if x <= 12 else 13

def test_bands():
    assert [score.band(s) for s in range(21)] == [band(s) for s in range(21)]

def test_scope_cutoffs():
    assert [score.scope_pts(b) for b in (0, 6, 7, 24, 25, 60, 61, 500)] == [0, 0, 3, 3, 5, 5, 8, 8]

def test_planning_sp_matches_v39_with_calibration_on_a_grid():
    for br in range(0, 130, 3):
        for c in range(6):
            for r in range(6):
                p = score.planning(br, br + 10, c, r)
                assert p['planning_br'] == round(br * 1.4)
                assert p['planning_sp'] == band(spts[lvl(round(br * 1.4))] + cpt(c + 1) + rpt(r + 1))
                assert p['sp_as_measured'] == band(spts[lvl(br)] + cpt(c + 1) + rpt(r + 1))

def test_pert_points():
    p = score.planning(40, 80, 1, 1)['pert']
    assert (p['o_br'], p['m_br'], p['p_br']) == (40, 56, 112)
    assert p['expected_br'] == round((40 + 4 * 56 + 112) / 6)
    assert p['o_sp'] <= p['m_sp'] <= p['p_sp']
