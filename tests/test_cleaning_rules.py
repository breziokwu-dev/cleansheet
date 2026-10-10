import pandas as pd
import pytest

from cleaning_rules import (
    apply_missing_value_rules,
    standardize_columns,
    trim_text_values,
)


def test_standardize_columns_makes_names_unique_even_with_collisions():
    assert standardize_columns([" A ", "A", "a_2", "!!!", "!!!"]) == [
        "a", "a_2", "a_2_2", "column", "column_2"
    ]


def test_trim_text_values_trims_strings_without_mutating_input():
    original = pd.DataFrame({"name": [" Ada ", None], "count": [1, 2]})
    cleaned = trim_text_values(original)

    assert cleaned["name"].tolist()[0] == "Ada"
    assert pd.isna(cleaned["name"].tolist()[1])
    assert cleaned["count"].tolist() == [1, 2]
    assert original["name"].tolist()[0] == " Ada "


def test_fill_numeric_column_with_median():
    original = pd.DataFrame({"score": [2.0, None, 10.0]})
    cleaned, changes = apply_missing_value_rules(
        original, [(0, "Fill with median")]
    )

    assert cleaned["score"].tolist() == [2.0, 6.0, 10.0]
    assert len(changes) == 1
    assert pd.isna(original.loc[1, "score"])


def test_fill_text_column_with_unknown():
    original = pd.DataFrame({"name": ["Ada", None]})
    cleaned, _ = apply_missing_value_rules(
        original, [(0, "Fill with 'Unknown'")]
    )

    assert cleaned["name"].tolist() == ["Ada", "Unknown"]


def test_mode_fill_uses_first_mode_for_ties():
    original = pd.DataFrame({"group": ["b", "a", None]})
    cleaned, _ = apply_missing_value_rules(
        original, [(0, "Fill with most frequent value")]
    )

    assert cleaned["group"].tolist() == ["b", "a", "a"]


def test_drop_rows_only_when_selected_column_is_missing():
    original = pd.DataFrame({
        "name": ["Ada", None, "Lin"],
        "score": [10, 20, None],
    })
    cleaned, changes = apply_missing_value_rules(
        original, [(0, "Drop rows where this column is missing")]
    )

    assert cleaned["name"].tolist() == ["Ada", "Lin"]
    assert len(cleaned) == 2
    assert pd.isna(cleaned.iloc[1]["score"])
    assert "removed 1 rows" in changes[0]


def test_all_missing_numeric_column_is_left_unchanged_for_median():
    # Explicit dtype matters: [None, None] alone is inferred as object, not numeric.
    original = pd.DataFrame({"score": pd.Series([None, None], dtype="float64")})
    cleaned, changes = apply_missing_value_rules(
        original, [(0, "Fill with median")]
    )

    assert cleaned["score"].isna().all()
    assert "no median available" in changes[0]


def test_invalid_fill_action_for_dtype_raises_helpful_error():
    with pytest.raises(TypeError, match="requires a numeric column"):
        apply_missing_value_rules(
            pd.DataFrame({"name": ["Ada", None]}),
            [(0, "Fill with median")],
        )


def test_duplicate_column_labels_are_handled_by_position():
    original = pd.DataFrame([[" Ada ", None]], columns=["name", "name"])
    cleaned = trim_text_values(original)
    filled, _ = apply_missing_value_rules(
        cleaned, [(1, "Fill with 'Unknown'")]
    )

    assert filled.iloc[0, 0] == "Ada"
    assert filled.iloc[0, 1] == "Unknown"
