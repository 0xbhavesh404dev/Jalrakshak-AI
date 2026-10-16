import pytest
from core.soils import *
def test_tables_and_conversion():
    assert awc("Loamy")==140 and efficiency("Drip")==.9 and litres(1,1)==4047
    with pytest.raises(ValueError): litres(-1,1)
