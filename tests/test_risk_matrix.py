import pytest
from src.genetics_logic import calculate_risk

# Enumerate parent statuses and sexes
STATUSES = ["affected", "carrier", "unaffected", "unknown"]
SEXES = ["male", "female"]

# Priors must match implementation defaults
AR_CARRIER_PRIOR = 0.01
AR_AFFECTED_PRIOR = 0.0001
AD_AFFECTED_PRIOR = 0.001
X_MOTHER_CARRIER_PRIOR = 0.01
X_MOTHER_AFFECTED_PRIOR = 0.0001
X_FATHER_AFFECTED_PRIOR = 0.0005


def transmit_prob_ar(status, role):
    if status == 'affected':
        return 1.0
    if status == 'carrier':
        return 0.5
    if status == 'unaffected':
        return 0.0
    # unknown
    if role == 'mother':
        return X_MOTHER_CARRIER_PRIOR * 0.5 + AR_AFFECTED_PRIOR * 1.0
    return AR_CARRIER_PRIOR * 0.5 + AR_AFFECTED_PRIOR * 1.0


def transmit_prob_ad(status):
    if status in ('affected', 'carrier'):
        return 0.5
    if status == 'unaffected':
        return 0.0
    return AD_AFFECTED_PRIOR * 0.5


def mother_transmit_x(status):
    if status == 'affected':
        return 1.0
    if status == 'carrier':
        return 0.5
    if status == 'unaffected':
        return 0.0
    return X_MOTHER_CARRIER_PRIOR * 0.5 + X_MOTHER_AFFECTED_PRIOR * 1.0


def father_transmit_daughter_x(status):
    if status == 'affected':
        return 1.0
    if status == 'unaffected':
        return 0.0
    return X_FATHER_AFFECTED_PRIOR


@pytest.mark.parametrize("father_status", STATUSES)
@pytest.mark.parametrize("mother_status", STATUSES)
@pytest.mark.parametrize("child_sex", SEXES)
def test_risk_matrix_matches_expected(father_status, mother_status, child_sex):
    # Autosomal recessive expected
    ar_expected = None
    p_f = transmit_prob_ar(father_status, 'father')
    p_m = transmit_prob_ar(mother_status, 'mother')
    ar_expected = p_f * p_m

    res_ar = calculate_risk('autosomal_recessive', {'status': father_status}, {'status': mother_status}, child_sex)
    assert pytest.approx(res_ar['min'], rel=1e-6) == ar_expected
    assert pytest.approx(res_ar['max'], rel=1e-6) == ar_expected

    # Autosomal dominant expected
    p_f_ad = transmit_prob_ad(father_status)
    p_m_ad = transmit_prob_ad(mother_status)
    ad_expected = 1.0 - (1.0 - p_f_ad) * (1.0 - p_m_ad)
    res_ad = calculate_risk('autosomal_dominant', {'status': father_status}, {'status': mother_status}, child_sex)
    assert pytest.approx(res_ad['min'], rel=1e-6) == ad_expected
    assert pytest.approx(res_ad['max'], rel=1e-6) == ad_expected

    # X-linked recessive expected
    p_m_x = mother_transmit_x(mother_status)
    if child_sex == 'male':
        x_expected = p_m_x
    else:
        p_f_x = father_transmit_daughter_x(father_status)
        x_expected = p_m_x * p_f_x

    res_x = calculate_risk('x_linked', {'status': father_status}, {'status': mother_status}, child_sex)
    assert pytest.approx(res_x['min'], rel=1e-6) == x_expected
    assert pytest.approx(res_x['max'], rel=1e-6) == x_expected
*** End Patch