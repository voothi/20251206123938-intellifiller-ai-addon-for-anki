import os
import csv
import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from IntelliFiller.config_manager import ConfigManager
from IntelliFiller.headless_entrypoint import main as headless_main
import install as install_module

def test_headless_fill_tsv(tmp_path, monkeypatch):
    # 1. Set up simulated user settings and credentials
    ConfigManager.save_settings({"emulate": "yes"})
    
    # Save a test prompt
    test_prompt_config = {
        "promptName": "English Vocabulary Analysis and Translation (JSON)",
        "prompt": "Analyze {{{WordSource}}}. Context: {{{SentenceSource}}}",
        "responseFormat": "json",
        "fieldMapping": {
            "ru": "WordDestination",
            "ipa": "WordSourceIPA"
        },
        "overwriteField": True
    }
    ConfigManager.save_prompt(test_prompt_config)

    # 2. Create a test TSV file
    tsv_path = tmp_path / "test_vocab.tsv"
    header = ["WordSource", "SentenceSource", "WordDestination", "WordSourceIPA"]
    rows = [
        ["apple", "I like apple.", "", ""],
        ["banana", "I like banana.", "", ""]
    ]
    with open(tsv_path, "w", newline="", encoding="utf-8") as f:
        f.write("# language=en\n")
        f.write("# target_lang=ru\n")
        writer = csv.writer(f, delimiter="\t")
        writer.writerow(header)
        writer.writerows(rows)

    # Mock send_prompt_to_llm to return simulated JSON
    mock_responses = [
        '{"ru": "яблоко", "ipa": "æpl"}',
        '{"ru": "банан", "ipa": "bəˈnɑːnə"}'
    ]
    response_idx = 0

    def mock_send(prompt):
        nonlocal response_idx
        res = mock_responses[response_idx]
        response_idx += 1
        return res

    monkeypatch.setattr("IntelliFiller.headless_entrypoint.send_prompt_to_llm", mock_send)

    # Mock sys.argv
    test_args = [
        "headless_entrypoint.py",
        "--tsv", str(tsv_path),
        "--prompt", "English Vocabulary Analysis and Translation (JSON)"
    ]
    monkeypatch.setattr("sys.argv", test_args)

    # Run headless entrypoint
    headless_main()

    # Read back TSV and verify columns were filled
    with open(tsv_path, "r", encoding="utf-8") as f:
        reader = csv.reader(f, delimiter="\t")
        res_rows = list(reader)

    assert res_rows[0] == ["# language=en"]
    assert res_rows[1] == ["# target_lang=ru"]
    assert res_rows[2] == header
    assert res_rows[3] == ["apple", "I like apple.", "яблоко", "æpl"]
    assert res_rows[4] == ["banana", "I like banana.", "банан", "bəˈnɑːnə"]


def test_headless_skips_fully_filled_rows(tmp_path, monkeypatch):
    ConfigManager.save_settings({"emulate": "yes"})
    test_prompt_config = {
        "promptName": "English Vocabulary Analysis and Translation (JSON)",
        "prompt": "Analyze {{{WordSource}}}. Context: {{{SentenceSource}}}",
        "responseFormat": "json",
        "fieldMapping": {
            "ru": "WordDestination",
            "ipa": "WordSourceIPA"
        },
        "overwriteField": True
    }
    ConfigManager.save_prompt(test_prompt_config)

    tsv_path = tmp_path / "test_skip.tsv"
    header = ["WordSource", "SentenceSource", "WordDestination", "WordSourceIPA"]
    rows = [
        ["apple", "I like apple.", "яблоко_original", "æpl_original"],
        ["banana", "I like banana.", "", ""]
    ]
    with open(tsv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, delimiter="\t")
        writer.writerow(header)
        writer.writerows(rows)

    mock_responses = [
        '{"ru": "банан", "ipa": "bəˈnɑːnə"}'
    ]
    response_idx = 0

    def mock_send(prompt):
        nonlocal response_idx
        if response_idx >= len(mock_responses):
            pytest.fail("send_prompt_to_llm called too many times (should have skipped fully filled row!)")
        res = mock_responses[response_idx]
        response_idx += 1
        return res

    monkeypatch.setattr("IntelliFiller.headless_entrypoint.send_prompt_to_llm", mock_send)

    test_args = [
        "headless_entrypoint.py",
        "--tsv", str(tsv_path),
        "--prompt", "English Vocabulary Analysis and Translation (JSON)"
    ]
    monkeypatch.setattr("sys.argv", test_args)

    headless_main()

    with open(tsv_path, "r", encoding="utf-8") as f:
        reader = csv.reader(f, delimiter="\t")
        res_rows = list(reader)

    assert res_rows[0] == header
    assert res_rows[1] == ["apple", "I like apple.", "яблоко_original", "æpl_original"]
    assert res_rows[2] == ["banana", "I like banana.", "банан", "bəˈnɑːnə"]
    assert response_idx == 1


def test_headless_skips_partially_filled_rows_with_translation(tmp_path, monkeypatch):
    ConfigManager.save_settings({"emulate": "yes"})
    test_prompt_config = {
        "promptName": "English Vocabulary Analysis and Translation (JSON)",
        "prompt": "Analyze {{{WordSource}}}. Context: {{{SentenceSource}}}",
        "responseFormat": "json",
        "fieldMapping": {
            "ru": "WordDestination",
            "ipa": "WordSourceIPA"
        },
        "overwriteField": True
    }
    ConfigManager.save_prompt(test_prompt_config)

    tsv_path = tmp_path / "test_skip_part.tsv"
    header = ["WordSource", "SentenceSource", "WordDestination", "WordSourceIPA"]
    rows = [
        ["apple", "I like apple.", "яблоко_original", ""],  # Has translation but empty IPA
        ["banana", "I like banana.", "", ""]
    ]
    with open(tsv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, delimiter="\t")
        writer.writerow(header)
        writer.writerows(rows)

    mock_responses = [
        '{"ru": "банан", "ipa": "bəˈnɑːnə"}'
    ]
    response_idx = 0

    def mock_send(prompt):
        nonlocal response_idx
        if response_idx >= len(mock_responses):
            pytest.fail("send_prompt_to_llm called too many times (should have skipped row with translation!)")
        res = mock_responses[response_idx]
        response_idx += 1
        return res

    monkeypatch.setattr("IntelliFiller.headless_entrypoint.send_prompt_to_llm", mock_send)

    test_args = [
        "headless_entrypoint.py",
        "--tsv", str(tsv_path),
        "--prompt", "English Vocabulary Analysis and Translation (JSON)"
    ]
    monkeypatch.setattr("sys.argv", test_args)

    headless_main()

    with open(tsv_path, "r", encoding="utf-8") as f:
        reader = csv.reader(f, delimiter="\t")
        res_rows = list(reader)

    assert res_rows[1] == ["apple", "I like apple.", "яблоко_original", ""]
    assert res_rows[2] == ["banana", "I like banana.", "банан", "bəˈnɑːnə"]
    assert response_idx == 1


def test_headless_reprocess_does_not_skip_rows_with_translation(tmp_path, monkeypatch):
    ConfigManager.save_settings({"emulate": "yes"})
    test_prompt_config = {
        "promptName": "English Vocabulary Analysis and Translation (JSON)",
        "prompt": "Analyze {{{WordSource}}}. Context: {{{SentenceSource}}}",
        "responseFormat": "json",
        "fieldMapping": {
            "ru": "WordDestination",
            "ipa": "WordSourceIPA"
        },
        "overwriteField": True
    }
    ConfigManager.save_prompt(test_prompt_config)

    tsv_path = tmp_path / "test_reprocess.tsv"
    header = ["WordSource", "SentenceSource", "WordDestination", "WordSourceIPA"]
    rows = [
        ["apple", "I like apple.", "яблоко_original", ""],  # Has translation but empty IPA
        ["banana", "I like banana.", "", ""]
    ]
    with open(tsv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, delimiter="\t")
        writer.writerow(header)
        writer.writerows(rows)

    mock_responses = [
        '{"ru": "яблоко_new", "ipa": "æpl_new"}',
        '{"ru": "банан", "ipa": "bəˈnɑːnə"}'
    ]
    response_idx = 0

    def mock_send(prompt):
        nonlocal response_idx
        res = mock_responses[response_idx]
        response_idx += 1
        return res

    monkeypatch.setattr("IntelliFiller.headless_entrypoint.send_prompt_to_llm", mock_send)

    test_args = [
        "headless_entrypoint.py",
        "--tsv", str(tsv_path),
        "--prompt", "English Vocabulary Analysis and Translation (JSON)",
        "--reprocess"
    ]
    monkeypatch.setattr("sys.argv", test_args)

    headless_main()

    with open(tsv_path, "r", encoding="utf-8") as f:
        reader = csv.reader(f, delimiter="\t")
        res_rows = list(reader)

    assert res_rows[1] == ["apple", "I like apple.", "яблоко_new", "æpl_new"]
    assert res_rows[2] == ["banana", "I like banana.", "банан", "bəˈnɑːnə"]
    assert response_idx == 2


def test_headless_target_field(tmp_path, monkeypatch):
    ConfigManager.save_settings({"emulate": "yes"})
    test_prompt_config = {
        "promptName": "English Vocabulary Analysis and Translation (JSON)",
        "prompt": "Analyze {{{WordSource}}}. Context: {{{SentenceSource}}}",
        "responseFormat": "json",
        "fieldMapping": {
            "ru": "WordDestination",
            "en": "WordEnglish",
            "ipa": "WordSourceIPA"
        },
        "overwriteField": True
    }
    ConfigManager.save_prompt(test_prompt_config)

    tsv_path = tmp_path / "test_target_field.tsv"
    header = ["WordSource", "SentenceSource", "WordDestination", "WordEnglish", "WordSourceIPA"]
    rows = [
        ["apple", "I like apple.", "", "apple_en", ""],  # WordDestination is empty, WordEnglish has translation
        ["banana", "I like banana.", "", "", ""]
    ]
    with open(tsv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, delimiter="\t")
        writer.writerow(header)
        writer.writerows(rows)

    mock_responses = [
        '{"ru": "яблоко_new", "en": "apple_new", "ipa": "æpl_new"}',
        '{"ru": "банан", "en": "banana_new", "ipa": "bəˈnɑːnə"}'
    ]
    response_idx = 0

    def mock_send(prompt):
        nonlocal response_idx
        res = mock_responses[response_idx]
        response_idx += 1
        return res

    monkeypatch.setattr("IntelliFiller.headless_entrypoint.send_prompt_to_llm", mock_send)

    # 1. Run with --target-field WordDestination. Should NOT skip row 1 because WordDestination is empty.
    test_args = [
        "headless_entrypoint.py",
        "--tsv", str(tsv_path),
        "--prompt", "English Vocabulary Analysis and Translation (JSON)",
        "--target-field", "WordDestination"
    ]
    monkeypatch.setattr("sys.argv", test_args)

    headless_main()

    with open(tsv_path, "r", encoding="utf-8") as f:
        reader = csv.reader(f, delimiter="\t")
        res_rows = list(reader)

    assert res_rows[1] == ["apple", "I like apple.", "яблоко_new", "apple_new", "æpl_new"]
    assert response_idx == 2


def test_install_script_list(capsys, monkeypatch):
    test_args = ["install.py", "--list"]
    monkeypatch.setattr("sys.argv", test_args)
    
    install_module.main()
    
    captured = capsys.readouterr()
    assert "IntelliFiller Fill" in captured.out
