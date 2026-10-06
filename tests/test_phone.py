import pytest
from lagosdata.normalise import clean_phone

@pytest.mark.parametrize(('value','expected'),[
 ('0803 123 4567','+2348031234567'),
 ('+234 803 123 4567','+2348031234567'),
 ('234 1 234 5678','+23412345678'),
 ('08031234567','+2348031234567'),
 ('01 2345678','+23412345678'),
 ('+23412454213789',''),
 ('0803-123-456',''),
 ('0803 123 4567 / 0805 987 6543','+2348031234567'),
 ('WhatsApp: 0803 123 4567','+2348031234567')])
def test_phone_examples(value,expected):assert clean_phone(value)==expected
