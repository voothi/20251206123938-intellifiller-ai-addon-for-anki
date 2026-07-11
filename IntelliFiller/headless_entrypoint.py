import os
import sys
import csv
import json
import argparse

# Add the parent directory of IntelliFiller to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import re
from IntelliFiller.config_manager import ConfigManager
from IntelliFiller.data_request import create_prompt, send_prompt_to_llm

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
    parser.add_argument("--tsv", required=True, help="Path to vocabulary TSV file")
    parser.add_argument("--prompt", required=True, help="Prompt name to apply")
    parser.add_argument("--field-mapping", help="Optional JSON string overriding field mapping")
    parser.add_argument("--selected-rows", help="Comma-separated list of 0-based row indices to process. If omitted, all rows are processed.")
    parser.add_argument("--reprocess", action="store_true", help="Allow processing rows even if they already have translations")
    parser.add_argument("--target-field", help="Specify target translation field to check for existing translations")
    args = parser.parse_args()

    selected_indices = None
    if args.selected_rows:
        try:
            selected_indices = set(int(x.strip()) for x in args.selected_rows.split(",") if x.strip())
        except ValueError:
            print("Error: --selected-rows must be a comma-separated list of integers.", file=sys.stderr)
            sys.exit(1)

    if not os.path.exists(args.tsv):
        print(f"Error: TSV file not found at {args.tsv}", file=sys.stderr)
        sys.exit(1)

    # 1. Load prompts and find target prompt
    prompts = ConfigManager.list_prompts()
    prompt_config = None
    for p in prompts:
        if p.get("promptName") == args.prompt:
            prompt_config = p
            break

    if not prompt_config:
        print(f"Error: Prompt '{args.prompt}' not found in user prompts.", file=sys.stderr)
        sys.exit(1)

    # 2. Get field mapping
    mapping = dict(prompt_config.get("fieldMapping", {}))
    if args.field_mapping:
        try:
            mapping.update(json.loads(args.field_mapping))
        except Exception as e:
            print(f"Error parsing --field-mapping JSON: {e}", file=sys.stderr)
            sys.exit(1)

    # 3. Read TSV
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
        print(f"Error reading TSV: {e}", file=sys.stderr)
        sys.exit(1)

    if not lines_to_parse:
        print("Error: Empty TSV file.", file=sys.stderr)
        sys.exit(1)

    try:
        reader = csv.reader(lines_to_parse, delimiter="\t")
        rows = list(reader)
    except Exception as e:
        print(f"Error parsing TSV rows: {e}", file=sys.stderr)
        sys.exit(1)

    if not rows:
        print("Error: Empty TSV file.", file=sys.stderr)
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

    # 4. Fill rows
    updated_rows = []
    settings = ConfigManager.load_settings()
    overwrite_global = settings.get("overwriteField", False)
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

    print(f"Running prompt '{args.prompt}' on {len(data_rows)} rows...")

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
            
        print(f"Processing row {i+1}/{len(data_rows)}: {row.get('WordSource', row.get('Quotation', ''))}")
        try:
            prompt_str = create_prompt(row_dict, prompt_config)
            response = send_prompt_to_llm(prompt_str)

            if fmt == "json":
                data = parse_llm_json(response)
                if not data:
                    raise ValueError("Failed to parse JSON response from LLM")
                
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
            print(f"Warning: Failed to process row {i+1}: {e}", file=sys.stderr)
            # Keep original values on failure

        updated_rows.append(row_dict)

    # 5. Write updated TSV back atomically
    try:
        write_tsv_atomically(args.tsv, comments, header, updated_rows)
        print(f"Successfully processed and updated {args.tsv}")
    except Exception as e:
        print(f"Error saving TSV atomically: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
