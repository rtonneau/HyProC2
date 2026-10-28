import pandas as pd
import pytest

from hyproc import file_io

COLUMNS = {"energy": "Energy", "yield": "Yield", "yield_err": "Error"}


@pytest.mark.parametrize(
    "extension,text",
    [
        ("csv", "Energy,Yield,Error\n2,20,2\n1,10,1\n"),
        ("txt", "# comment\n2\t20\t2\n1 10 1\n"),
    ],
)
def test_curve_import_sorting(tmp_path, extension, text):
    path = tmp_path / f"curve.{extension}"
    path.write_text(text)
    assert file_io.read_text_curve(path, COLUMNS) == ([1, 2], [10, 20], [1, 2])


def test_excel_without_optional_uncertainty(tmp_path):
    path = tmp_path / "curve.xlsx"
    pd.DataFrame({"Energy": [2, 1], "Yield": [20, 10]}).to_excel(path, index=False)
    sheets = file_io.excel_tables(path, COLUMNS)
    frame = sheets["Sheet1"]
    assert file_io.header_rows(frame, ["Energy", "Yield"]) == [0]
    assert file_io.count_datapoints(frame, 0) == 2
    table = frame.iloc[1:].copy()
    table.columns = frame.iloc[0]
    assert file_io.curve_from_table(table, COLUMNS) == ([1, 2], [10, 20], [0, 0])


def test_text_export_precision(tmp_path):
    path = tmp_path / "curve.txt"
    file_io.save_curve(path, [1.23456], [5.678])
    assert path.read_text() == "1.235\t5.7\n"


def test_excel_duplicate_headers_keep_first_curve(tmp_path):
    path = tmp_path / "two-curves.xlsx"
    frame = pd.DataFrame([[1, 10, 1, 20], [2, 11, 2, 21]], columns=["Energy", "Yield", "Energy", "Yield"])
    frame.to_excel(path, index=False)
    assert file_io.read_excel_curve(path, "Sheet1", 0, 2, COLUMNS) == ([1, 2], [10, 11], [0, 0])
