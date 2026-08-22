import os
import sys
import csv
import json
import argparse

# Add the parent directory of IntelliFiller to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import re
import configparser
from pathlib import Path

from IntelliFiller.config_manager import ConfigManager
from IntelliFiller.data_request import create_prompt, send_prompt_to_llm

BUILTIN_PROMPTS = {
    "morphology_and_ipa": {
        "promptName": "morphology_and_ipa",
        "prompt": "Analyze the word \"{{{WordSource}}}\" in the context: \"{{{SentenceSource}}}\".\n"
                  "Return valid JSON only with keys:\n"
                  "- \"lemma\": base dictionary form\n"
                  "- \"ipa\": IPA phonetic transcription\n"
                  "- \"pos\": part of speech\n"
                  "- \"morphology\": grammatical form details (tense, person, gender, case, etc.)\n"
                  "- \"translation\": accurate translation to destination language\n"
                  "Do not include markdown codeblocks if possible, or format as ```json ... ```.",
        "responseFormat": "json",
        "fieldMapping": {
            "lemma": "WordSource",
            "ipa": "WordSourceIPA",
            "pos": "PartOfSpeech",
            "morphology": "Grammar",
            "translation": "WordDestination"
        },
        "overwriteField": True
    },
    "lemma_extraction": {
        "promptName": "lemma_extraction",
        "prompt": "Extract the base lemma and grammatical part of speech for the word \"{{{WordSource}}}\" in context: \"{{{SentenceSource}}}\".\n"
                  "Return valid JSON only with keys: \"lemma\", \"pos\".",
        "responseFormat": "json",
        "fieldMapping": {
            "lemma": "WordSource",
            "pos": "PartOfSpeech"
        },
        "overwriteField": True
    },
    "ipa_extraction": {
        "promptName": "ipa_extraction",
        "prompt": "Provide the IPA phonetic transcription for the word \"{{{WordSource}}}\".\n"
                  "Return valid JSON only with key: \"ipa\".",
        "responseFormat": "json",
        "fieldMapping": {
            "ipa": "WordSourceIPA"
        },
        "overwriteField": True
    },
    "english_vocabulary_analysis_and_translation": {
        "promptName": "English Vocabulary Analysis and Translation (JSON)",
        "prompt": "Analyze the English word \"{{{WordSource}}}\" in the context \"{{{SentenceSource}}}\".\n"
                  "Provide the Russian translation and IPA transcription.\n"
                  "Return valid JSON only with keys: \"ru\", \"ipa\", \"lemma\".",
        "responseFormat": "json",
        "fieldMapping": {
            "ru": "WordDestination",
            "ipa": "WordSourceIPA",
            "lemma": "WordSource"
        },
        "overwriteField": True
    },
    "german_vocabulary_analysis_and_translation": {
        "promptName": "German Vocabulary Analysis and Translation (JSON)",
        "prompt": "Analyze the German word \"{{{WordSource}}}\" in the context \"{{{SentenceSource}}}\".\n"
                  "Provide base lemma with article for nouns (der/die/das), IPA, and Russian translation.\n"
                  "Return valid JSON only with keys: \"ru\", \"ipa\", \"lemma\", \"pos\".",
        "responseFormat": "json",
        "fieldMapping": {
            "ru": "WordDestination",
            "ipa": "WordSourceIPA",
            "lemma": "WordSource",
            "pos": "PartOfSpeech"
        },
        "overwriteField": True
    }
}


def resolve_headless_config(args=None):
    """
    Resolves effective LLM and runtime configuration following hierarchy:
    CLI arguments > config.ini ([intellifiller] section) > Anki user_files/ fallback.
    """
    # 1. Fallback to Anki user_files
    effective = {}
    try:
        settings = ConfigManager.load_settings()
        encryption_key = settings.get("encryptionKey", "")
        credentials = ConfigManager.load_credentials(key=encryption_key)
        effective = {**settings, **credentials}
    except Exception:
        effective = {}

    # 2. config.ini hierarchy
    ini_candidates = []
    if getattr(args, 'config', None):
        ini_candidates.append(Path(args.config))
    ini_candidates.extend([
        Path.cwd() / "config.ini",
        Path(__file__).resolve().parent.parent / "config.ini",
        Path(__file__).resolve().parent.parent.parent / "20260629183335-kardenwort-desk" / "config.ini"
    ])

    for candidate in ini_candidates:
        if candidate and candidate.exists() and candidate.is_file():
            try:
                cp = configparser.ConfigParser()
                cp.read(str(candidate), encoding="utf-8")
                if cp.has_section("intellifiller"):
                    if cp.has_option("intellifiller", "model"):
                        effective["model"] = cp.get("intellifiller", "model")
                    if cp.has_option("intellifiller", "base_url"):
                        effective["base_url"] = cp.get("intellifiller", "base_url")
                    if cp.has_option("intellifiller", "api_key"):
                        effective["api_key"] = cp.get("intellifiller", "api_key")
                    if cp.has_option("intellifiller", "temperature"):
                        try:
                            effective["temperature"] = cp.getfloat("intellifiller", "temperature")
                        except (ValueError, TypeError):
                            pass
                    if cp.has_option("intellifiller", "prompt_template"):
                        effective["prompt_template"] = cp.get("intellifiller", "prompt_template")
                    if cp.has_option("intellifiller", "timeout"):
                        try:
                            effective["netTimeout"] = cp.getfloat("intellifiller", "timeout")
                        except (ValueError, TypeError):
                            pass
                if cp.has_section("timeouts") and cp.has_option("timeouts", "intellifiller_timeout"):
                    try:
                        effective["netTimeout"] = cp.getfloat("timeouts", "intellifiller_timeout")
                    except (ValueError, TypeError):
                        pass
                break
            except Exception:
                pass

    # 3. CLI arguments (highest priority)
    if getattr(args, 'model', None):
        effective["model"] = args.model
    if getattr(args, 'base_url', None):
        effective["base_url"] = args.base_url
    if getattr(args, 'api_key', None) is not None:
        effective["api_key"] = args.api_key
    if getattr(args, 'temperature', None) is not None:
        effective["temperature"] = args.temperature
    if getattr(args, 'prompt_template', None):
        effective["prompt_template"] = args.prompt_template
    if getattr(args, 'timeout', None) is not None:
        effective["netTimeout"] = args.timeout

    # 4. Map effective settings into provider connection format
    if effective.get("base_url"):
        effective["selectedApi"] = "custom"
        b_url = str(effective["base_url"]).strip()
        if not (b_url.endswith("/chat/completions") or b_url.endswith("/generate")):
            if b_url.endswith("/v1"):
                b_url = b_url + "/chat/completions"
            elif "/v1" not in b_url and not b_url.endswith("/generate"):
                b_url = b_url.rstrip("/") + "/v1/chat/completions"
        effective["customUrl"] = b_url
        effective["customModel"] = effective.get("model") or "qwen2.5:3b"
        effective["customKey"] = effective.get("api_key") or ""
    elif effective.get("model"):
        selected = effective.get("selectedApi", "openai")
        effective[f"{selected}Model"] = effective["model"]
        if effective.get("api_key") is not None:
            effective[f"{selected}Key"] = effective["api_key"]
            effective["apiKey"] = effective["api_key"]

    return effective


def resolve_prompt_config(prompt_name, prompt_template_arg=None, field_mapping_arg=None, effective_config=None):
    """
    Resolves prompt configuration from explicit template, Anki user_files, or built-in schemas.
    """
    if prompt_template_arg:
        mapping = {}
        if field_mapping_arg:
            try:
                mapping = json.loads(field_mapping_arg) if isinstance(field_mapping_arg, str) else field_mapping_arg
            except Exception:
                mapping = {}
        if not mapping:
            mapping = {
                "ru": "WordDestination",
                "translation": "WordDestination",
                "ipa": "WordSourceIPA",
                "lemma": "WordSource",
                "pos": "PartOfSpeech",
                "morphology": "Grammar"
            }
        return {
            "promptName": prompt_name or "custom_prompt",
            "prompt": prompt_template_arg,
            "responseFormat": "json" if ("json" in prompt_template_arg.lower() or "{" in prompt_template_arg) else "text",
            "fieldMapping": mapping,
            "overwriteField": True
        }

    # 1. Search user prompts from Anki user_files
    try:
        prompts = ConfigManager.list_prompts()
        for p in prompts:
            if p.get("promptName") == prompt_name:
                return dict(p)
    except Exception:
        pass

    # 2. Search built-in prompt schemas
    if prompt_name:
        norm_key = prompt_name.strip().lower().replace(" ", "_").replace("-", "_")
        for key, p in BUILTIN_PROMPTS.items():
            if key == norm_key or p.get("promptName", "").lower() == prompt_name.strip().lower():
                return dict(p)

    return None

def _is_translation_field(json_key, column_name):
    if json_key in ("ru", "ua", "en", "de", "translation", "dest", "word_translation"):
        return True
    col_lower = str(column_name).lower()
    if "destination" in col_lower:
        return True
    if col_lower in ("wordrussian", "wordukrainian", "wordenglish", "wordgerman"):
        return True
    return False

def _is_source_field(json_key, column_name):
    if json_key in ("lemma", "word", "source", "word_source"):
        return True
    if str(column_name) in ("WordSource", "Quotation"):
        return True
    return False

def parse_llm_json(response_text):
    """
    Parses JSON from LLM response, handling markdown code blocks.
    Returns dict or None if parsing fails.
    """
    if not response_text:
        return None
        
    pattern = r"```(?:json)?\s*(.*?)\s*```"
    match = re.search(pattern, response_text, re.DOTALL)
    if match:
        json_str = match.group(1)
    else:
        json_str = response_text
        
    try:
        return json.loads(json_str)
    except json.JSONDecodeError:
        start = json_str.find('{')
        end = json_str.rfind('}')
        if start != -1 and end != -1:
             try:
                 return json.loads(json_str[start:end+1])
             except:
                 pass
        return None


def classify_error(err, response_text=None):
    err_str = str(err).lower()
    if isinstance(err, (json.JSONDecodeError, ValueError)) and ("json" in err_str or "parse" in err_str):
        return {
            "code": "ERR_LLM_PARSE",
            "message": str(err),
            "retryable": False,
            "details": {"raw_response": (response_text[:200] if response_text else "")}
        }
    if "429" in err_str or "rate limit" in err_str or "quota" in err_str or "too many requests" in err_str:
        return {
            "code": "ERR_LLM_RATE_LIMIT",
            "message": str(err),
            "retryable": True,
            "details": {"http_status": 429}
        }
    if "401" in err_str or "403" in err_str or "auth" in err_str or "api key" in err_str or "unauthorized" in err_str:
        status_code = 401 if "401" in err_str else (403 if "403" in err_str else 401)
        return {
            "code": "ERR_LLM_AUTH",
            "message": str(err),
            "retryable": False,
            "details": {"http_status": status_code}
        }
    if "timed out" in err_str or "timeout" in err_str:
        return {
            "code": "ERR_LLM_TIMEOUT",
            "message": str(err),
            "retryable": True,
            "details": {}
        }
    if "network" in err_str or "urlerror" in err_str or "connection" in err_str or "getaddrinfo" in err_str:
        return {
            "code": "ERR_LLM_NETWORK",
            "message": str(err),
            "retryable": True,
            "details": {}
        }
    return {
        "code": "ERR_LLM_REQUEST",
        "message": str(err),
        "retryable": False,
        "details": {}
    }


def emit_error(code, message, zid=None, trace_id=None, row_id=None, retryable=False, details=None):
    envelope = {
        "status": "error",
        "zid": zid or "",
        "trace_id": trace_id or "",
        "code": code,
        "message": message,
        "row_id": row_id,
        "retryable": retryable,
        "details": details if details is not None else {}
    }
    print(json.dumps(envelope, ensure_ascii=False), file=sys.stderr)


def write_tsv_atomically(path, comments, header, rows):
    tmp_path = path + ".tmp"
    try:
        with open(tmp_path, "w", newline="", encoding="utf-8") as f:
            for comment in comments:
                f.write(comment + '\n')
            writer = csv.writer(f, delimiter="\t", lineterminator="\n")
            writer.writerow(header)
            for row in rows:
                writer.writerow([row.get(h, "") for h in header])
        if os.path.exists(path):
            os.replace(tmp_path, path)
        else:
            os.rename(tmp_path, path)
    except Exception as e:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        raise e


def main():
    parser = argparse.ArgumentParser(description="Headless IntelliFiller CLI Entrypoint")
    parser.add_argument("--serve", action="store_true", help="Start IntelliFiller as a persistent HTTP microservice")
    parser.add_argument("--port", type=int, default=8083, help="Port for HTTP microservice (default: 8083)")
    parser.add_argument("--host", default="127.0.0.1", help="Host interface for HTTP microservice (default: 127.0.0.1)")
    parser.add_argument("--tsv", required=False, help="Path to vocabulary TSV file")
    parser.add_argument("--prompt", required=False, help="Prompt name or built-in schema to apply")
    parser.add_argument("--prompt-template", required=False, help="Custom prompt template string")
    parser.add_argument("--model", help="LLM model identifier override (e.g. qwen2.5:3b, gpt-4o-mini)")
    parser.add_argument("--base-url", help="OpenAI-compatible LLM endpoint override (e.g. http://127.0.0.1:11434/v1)")
    parser.add_argument("--api-key", help="LLM API key override")
    parser.add_argument("--temperature", type=float, help="Sampling temperature override")
    parser.add_argument("--timeout", type=float, help="Network timeout in seconds")
    parser.add_argument("--config", help="Path to config.ini file")
    parser.add_argument("--field-mapping", help="Optional JSON string overriding field mapping")
    parser.add_argument("--selected-rows", help="Comma-separated list of 0-based row indices to process. If omitted, all rows are processed.")
    parser.add_argument("--reprocess", action="store_true", help="Allow processing rows even if they already have translations")
    parser.add_argument("--target-field", help="Specify target translation field to check for existing translations")
    parser.add_argument("--zid", help="Session ZID timestamp")
    parser.add_argument("--trace-id", help="Correlation trace ID")
    args = parser.parse_args()

    if args.serve:
        from IntelliFiller.server import start_server
        start_server(host=args.host, port=args.port)
        return

    if not args.tsv or (not args.prompt and not args.prompt_template):
        parser.error("--tsv and either --prompt or --prompt-template are required when not running with --serve")

    selected_indices = None
    if args.selected_rows:
        try:
            selected_indices = set(int(x.strip()) for x in args.selected_rows.split(",") if x.strip())
        except ValueError:
            emit_error("ERR_INVALID_ARGS", "--selected-rows must be a comma-separated list of integers.", zid=args.zid, trace_id=args.trace_id)
            sys.exit(1)

    if not os.path.exists(args.tsv):
        emit_error("ERR_FILE_NOT_FOUND", f"TSV file not found at {args.tsv}", zid=args.zid, trace_id=args.trace_id)
        sys.exit(1)

    # 1. Resolve effective runtime LLM config
    effective_config = resolve_headless_config(args)

    # 2. Resolve prompt configuration (CLI template > user prompts > built-in schemas)
    prompt_config = resolve_prompt_config(
        prompt_name=args.prompt,
        prompt_template_arg=args.prompt_template or effective_config.get("prompt_template"),
        field_mapping_arg=args.field_mapping,
        effective_config=effective_config
    )

    if not prompt_config:
        emit_error("ERR_PROMPT_NOT_FOUND", f"Prompt '{args.prompt}' not found in user prompts or built-in schemas.", zid=args.zid, trace_id=args.trace_id)
        sys.exit(1)

    # 3. Get field mapping
    mapping = dict(prompt_config.get("fieldMapping", {}))
    if args.field_mapping:
        try:
            mapping.update(json.loads(args.field_mapping))
        except Exception as e:
            emit_error("ERR_MAPPING_INVALID", f"Error parsing --field-mapping JSON: {e}", zid=args.zid, trace_id=args.trace_id)
            sys.exit(1)

    # 4. Read TSV
    comments = []
    headers = []
    lines_to_parse = []
    try:
        with open(args.tsv, "r", encoding="utf-8") as f:
            for line in f:
                if not headers and not lines_to_parse and line.startswith('#'):
                    comments.append(line.rstrip('\r\n'))
                else:
                    lines_to_parse.append(line)
    except Exception as e:
        emit_error("ERR_TSV_READ", f"Error reading TSV: {e}", zid=args.zid, trace_id=args.trace_id)
        sys.exit(1)

    if not lines_to_parse:
        emit_error("ERR_TSV_EMPTY", "Empty TSV file.", zid=args.zid, trace_id=args.trace_id)
        sys.exit(1)

    try:
        reader = csv.reader(lines_to_parse, delimiter="\t")
        rows = list(reader)
    except Exception as e:
        emit_error("ERR_TSV_PARSE", f"Error parsing TSV rows: {e}", zid=args.zid, trace_id=args.trace_id)
        sys.exit(1)

    if not rows:
        emit_error("ERR_TSV_EMPTY", "Empty TSV file.", zid=args.zid, trace_id=args.trace_id)
        sys.exit(1)

    header = rows[0]
    data_rows = [dict(zip(header, row)) for row in rows[1:]]

    # Ensure all target fields exist in the header
    all_output_fields = list(mapping.values())
    if prompt_config.get("targetField"):
        all_output_fields.append(prompt_config.get("targetField"))

    for f in all_output_fields:
        if f and f not in header:
            header.append(f)

    # 5. Fill rows
    updated_rows = []
    overwrite_global = effective_config.get("overwriteField", False)
    overwrite = prompt_config.get("overwriteField", overwrite_global)
    fmt = prompt_config.get("responseFormat", "text")

    translation_fields = []
    other_enrichment_fields = []
    
    if args.target_field:
        translation_fields.append(args.target_field)
        for json_key, field in mapping.items():
            if field != args.target_field and not _is_source_field(json_key, field):
                other_enrichment_fields.append(field)
    else:
        target_field = prompt_config.get("targetField")
        if target_field:
            translation_fields.append(target_field)
            
        for json_key, field in mapping.items():
            if _is_translation_field(json_key, field):
                translation_fields.append(field)
                
        for json_key, field in mapping.items():
            if not _is_translation_field(json_key, field) and not _is_source_field(json_key, field):
                other_enrichment_fields.append(field)

    prompt_display_name = prompt_config.get("promptName", args.prompt or "custom")
    print(f"Running prompt '{prompt_display_name}' on {len(data_rows)} rows...")

    for i, row in enumerate(data_rows):
        row_dict = dict(row)
        
        if selected_indices is not None and i not in selected_indices:
            updated_rows.append(row_dict)
            continue
            
        has_translation = any(row.get(f, "").strip() for f in translation_fields if f)
        if has_translation and not args.reprocess:
            print(f"Row {i+1} already has translation, skipping.")
            updated_rows.append(row_dict)
            continue
            
        # Ensure fallback aliases for common prompt placeholders
        if "WordSource" not in row_dict:
            row_dict["WordSource"] = row_dict.get("word", row_dict.get("Word", ""))
        if "SentenceSource" not in row_dict:
            row_dict["SentenceSource"] = row_dict.get("Quotation", row_dict.get("sentence", row_dict.get("Sentence", "")))

        print(f"Processing row {i+1}/{len(data_rows)}: {row_dict.get('WordSource', row_dict.get('Quotation', ''))}")
        response = None
        try:
            prompt_str = create_prompt(row_dict, prompt_config)
            try:
                response = send_prompt_to_llm(prompt_str, config=effective_config)
            except TypeError:
                response = send_prompt_to_llm(prompt_str)

            if fmt == "json":
                data = parse_llm_json(response)
                if not data:
                    raise ValueError(f"Failed to parse JSON response from LLM: {response[:100] if response else ''}")
                
                for json_key, target_field in mapping.items():
                    if json_key in data:
                        val = data[json_key]
                        if isinstance(val, (dict, list)):
                            val = json.dumps(val, ensure_ascii=False)
                        val = str(val)
                        formatted = val.replace("\n", "<br>")
                        
                        existing = row_dict.get(target_field, "")
                        if existing.strip() and not overwrite:
                            row_dict[target_field] = existing + "<hr>" + formatted
                        else:
                            row_dict[target_field] = formatted
            else:
                target_field = prompt_config.get("targetField")
                if target_field:
                    formatted = response.replace("\n", "<br>")
                    existing = row_dict.get(target_field, "")
                    if existing.strip() and not overwrite:
                        row_dict[target_field] = existing + "<hr>" + formatted
                    else:
                        row_dict[target_field] = formatted

        except Exception as e:
            err_info = classify_error(e, response_text=response)
            emit_error(
                code=err_info["code"],
                message=err_info["message"],
                zid=args.zid,
                trace_id=args.trace_id,
                row_id=i,
                retryable=err_info["retryable"],
                details=err_info["details"]
            )
            # Write back any already processed rows before exiting so work is not lost
            try:
                full_updated = updated_rows + [dict(r) for r in data_rows[len(updated_rows):]]
                write_tsv_atomically(args.tsv, comments, header, full_updated)
            except Exception:
                pass
            sys.exit(1)

        updated_rows.append(row_dict)

    # 6. Write updated TSV back atomically
    try:
        write_tsv_atomically(args.tsv, comments, header, updated_rows)
        print(f"Successfully processed and updated {args.tsv}")
    except Exception as e:
        emit_error("ERR_TSV_SAVE", f"Error saving TSV atomically: {e}", zid=args.zid, trace_id=args.trace_id)
        sys.exit(1)

if __name__ == "__main__":
    main()
