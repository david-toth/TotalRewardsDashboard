from io import BytesIO
import pandas as pd

def excel_bytes(annual, segment, assumptions) -> bytes:
    buf = BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        annual.to_excel(writer, index=False, sheet_name="Annual Summary")
        segment.to_excel(writer, index=False, sheet_name="Segments")
        pd.json_normalize(assumptions, sep=".").T.rename(columns={0:"value"}).to_excel(writer, sheet_name="Assumptions")
    return buf.getvalue()
