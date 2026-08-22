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


def test_headless_rate_limit_error_emits_structured_envelope(tmp_path, monkeypatch, capsys):
    ConfigManager.save_settings({"emulate": "no"})
    test_prompt_config = {
        "promptName": "RateLimitTest",
        "prompt": "Analyze {{{WordSource}}}",
        "responseFormat": "json",
        "fieldMapping": {"ru": "WordDestination"},
        "overwriteField": True
    }
    ConfigManager.save_prompt(test_prompt_config)

    tsv_path = tmp_path / "test_ratelimit.tsv"
    with open(tsv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, delimiter="\t")
        writer.writerow(["WordSource", "WordDestination"])
        writer.writerow(["apple", ""])

    def mock_send_ratelimit(prompt):
        raise Exception("HTTP 429 Too Many Requests - Rate limit exceeded")

    monkeypatch.setattr("IntelliFiller.headless_entrypoint.send_prompt_to_llm", mock_send_ratelimit)

    test_args = [
        "headless_entrypoint.py",
        "--tsv", str(tsv_path),
        "--prompt", "RateLimitTest",
        "--zid", "20260818190200",
        "--trace-id", "20260818190200:reword:row_0"
    ]
    monkeypatch.setattr("sys.argv", test_args)

    with pytest.raises(SystemExit) as excinfo:
        headless_main()

    assert excinfo.value.code == 1
    captured = capsys.readouterr()
    stderr_lines = [line.strip() for line in captured.err.splitlines() if line.strip()]
    envelope = json.loads(stderr_lines[-1])
    assert envelope["status"] == "error"
    assert envelope["code"] == "ERR_LLM_RATE_LIMIT"
    assert envelope["zid"] == "20260818190200"
    assert envelope["trace_id"] == "20260818190200:reword:row_0"
    assert envelope["retryable"] is True
    assert envelope["row_id"] == 0
    assert envelope["details"]["http_status"] == 429


def test_headless_malformed_json_emits_parse_error(tmp_path, monkeypatch, capsys):
    ConfigManager.save_settings({"emulate": "no"})
    test_prompt_config = {
        "promptName": "ParseErrorTest",
        "prompt": "Analyze {{{WordSource}}}",
        "responseFormat": "json",
        "fieldMapping": {"ru": "WordDestination"},
        "overwriteField": True
    }
    ConfigManager.save_prompt(test_prompt_config)

    tsv_path = tmp_path / "test_parse.tsv"
    with open(tsv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, delimiter="\t")
        writer.writerow(["WordSource", "WordDestination"])
        writer.writerow(["banana", ""])

    def mock_send_malformed(prompt):
        return "Not a valid json response at all <<<"

    monkeypatch.setattr("IntelliFiller.headless_entrypoint.send_prompt_to_llm", mock_send_malformed)

    test_args = [
        "headless_entrypoint.py",
        "--tsv", str(tsv_path),
        "--prompt", "ParseErrorTest",
        "--zid", "20260818190200",
        "--trace-id", "20260818190200:reword:row_0"
    ]
    monkeypatch.setattr("sys.argv", test_args)

    with pytest.raises(SystemExit) as excinfo:
        headless_main()

    assert excinfo.value.code == 1
    captured = capsys.readouterr()
    stderr_lines = [line.strip() for line in captured.err.splitlines() if line.strip()]
    envelope = json.loads(stderr_lines[-1])
    assert envelope["status"] == "error"
    assert envelope["code"] == "ERR_LLM_PARSE"
    assert envelope["retryable"] is False
    assert "Not a valid json" in envelope["details"]["raw_response"]


def test_headless_standalone_builtin_prompt_without_anki(tmp_path, monkeypatch):
    # Ensure no prompts in Anki user_files
    monkeypatch.setattr(ConfigManager, "list_prompts", lambda: [])

    tsv_path = tmp_path / "test_builtin.tsv"
    with open(tsv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, delimiter="\t")
        writer.writerow(["WordSource", "SentenceSource", "WordDestination", "WordSourceIPA", "Grammar"])
        writer.writerow(["gehen", "Ich gehe nach Hause.", "", "", ""])

    passed_config = {}

    def mock_send(prompt, config=None):
        nonlocal passed_config
        passed_config = config or {}
        return '{"lemma": "gehen", "ipa": "ˈɡeːən", "pos": "verb", "morphology": "1st person sg present", "translation": "идти"}'

    monkeypatch.setattr("IntelliFiller.headless_entrypoint.send_prompt_to_llm", mock_send)

    test_args = [
        "headless_entrypoint.py",
        "--tsv", str(tsv_path),
        "--prompt", "morphology_and_ipa",
        "--model", "qwen2.5:3b",
        "--base-url", "http://127.0.0.1:11434/v1",
        "--temperature", "0.0"
    ]
    monkeypatch.setattr("sys.argv", test_args)

    headless_main()

    with open(tsv_path, "r", encoding="utf-8") as f:
        reader = csv.reader(f, delimiter="\t")
        rows = list(reader)

    assert rows[0] == ["WordSource", "SentenceSource", "WordDestination", "WordSourceIPA", "Grammar", "PartOfSpeech"]
    assert rows[1] == ["gehen", "Ich gehe nach Hause.", "идти", "ˈɡeːən", "1st person sg present", "verb"]
    assert passed_config.get("customModel") == "qwen2.5:3b"
    assert passed_config.get("customUrl") == "http://127.0.0.1:11434/v1/chat/completions"
    assert passed_config.get("temperature") == 0.0


def test_headless_config_hierarchy(tmp_path, monkeypatch):
    # 1. Base user_files settings
    monkeypatch.setattr(ConfigManager, "load_settings", lambda: {"selectedApi": "openai", "openaiModel": "gpt-4o-mini"})
    monkeypatch.setattr(ConfigManager, "load_credentials", lambda key=None: {"apiKey": "base_key"})
    monkeypatch.setattr(ConfigManager, "list_prompts", lambda: [])

    # 2. Mock config.ini
    ini_path = tmp_path / "config.ini"
    with open(ini_path, "w", encoding="utf-8") as f:
        f.write("[intellifiller]\nmodel = llama3.2:3b\nbase_url = http://localhost:11434/v1\ntemperature = 0.1\n")

    tsv_path = tmp_path / "test_hierarchy.tsv"
    with open(tsv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, delimiter="\t")
        writer.writerow(["WordSource", "WordDestination"])
        writer.writerow(["haus", ""])

    passed_config = {}

    def mock_send(prompt, config=None):
        nonlocal passed_config
        passed_config = config or {}
        return '{"ru": "дом", "lemma": "Haus"}'

    monkeypatch.setattr("IntelliFiller.headless_entrypoint.send_prompt_to_llm", mock_send)

    # A) Test hierarchy: config.ini overrides user_files
    test_args_ini = [
        "headless_entrypoint.py",
        "--tsv", str(tsv_path),
        "--prompt", "lemma_extraction",
        "--config", str(ini_path)
    ]
    monkeypatch.setattr("sys.argv", test_args_ini)
    headless_main()
    assert passed_config.get("customModel") == "llama3.2:3b"
    assert passed_config.get("temperature") == 0.1

    # B) Test hierarchy: CLI flag overrides config.ini
    test_args_cli = [
        "headless_entrypoint.py",
        "--tsv", str(tsv_path),
        "--prompt", "lemma_extraction",
        "--config", str(ini_path),
        "--model", "qwen2.5:3b",
        "--temperature", "0.0",
        "--reprocess"
    ]
    monkeypatch.setattr("sys.argv", test_args_cli)
    headless_main()
    assert passed_config.get("customModel") == "qwen2.5:3b"
    assert passed_config.get("temperature") == 0.0


def test_headless_custom_prompt_template(tmp_path, monkeypatch):
    tsv_path = tmp_path / "test_template.tsv"
    with open(tsv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, delimiter="\t")
        writer.writerow(["WordSource", "WordDestination"])
        writer.writerow(["sun", ""])

    captured_prompt = ""

    def mock_send(prompt, config=None):
        nonlocal captured_prompt
        captured_prompt = prompt
        return '{"ru": "солнце"}'

    monkeypatch.setattr("IntelliFiller.headless_entrypoint.send_prompt_to_llm", mock_send)

    test_args = [
        "headless_entrypoint.py",
        "--tsv", str(tsv_path),
        "--prompt-template", "Translate word: {{{WordSource}}} into JSON",
        "--field-mapping", json.dumps({"ru": "WordDestination"})
    ]
    monkeypatch.setattr("sys.argv", test_args)
    headless_main()

    assert "Translate word: sun into JSON" in captured_prompt
    with open(tsv_path, "r", encoding="utf-8") as f:
        reader = csv.reader(f, delimiter="\t")
        rows = list(reader)
    assert rows[1] == ["sun", "солнце"]


