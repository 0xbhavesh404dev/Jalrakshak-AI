from core.i18n import STRINGS,t
def test_required_keys_translated():
    keys=set(STRINGS["en"]); assert all(set(v)==keys for v in STRINGS.values()); assert t("dashboard","te")
