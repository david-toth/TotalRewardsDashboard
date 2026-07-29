import pandas as pd
from utils.data_validation import validate

def test_validation_warnings():
    df = pd.DataFrame({"employee_id":["A","A"], "age":[10,40], "service":[12,2], "annual_base_pay":[-1,2]})
    warnings = validate(df)
    assert any("Duplicate" in w for w in warnings)
    assert any("Negative" in w for w in warnings)
    assert any("Implausible" in w for w in warnings)
