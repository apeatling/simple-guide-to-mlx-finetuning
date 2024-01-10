import json
import requests
import sys
from pathlib import Path

def query_ollama(prompt, model='mistral', context=''):
    answer_marker = "Answer:"
    followup_marker = "Follow-up question:"
    full_prompt = f"{context}{prompt}\n{answer_marker}"
    url = 'http://localhost:11434/api/generate'
    data = {"model": model, "stream": False, "prompt": full_prompt}
    response = requests.post(url, json=data)
    response.raise_for_status()
    full_response = response.json()['response'].strip()
    parts = full_response.split(followup_marker)
    answer = parts[0].replace(answer_marker, '').strip()
    followup_question = parts[1].strip() if len(parts) > 1 else "No follow-up question provided."
    return answer, followup_question

def create_validation_file(train_file, valid_file, split_ratio):
    with open(train_file, 'r') as file:
        lines = file.readlines()
    valid_lines = lines[:int(len(lines) * split_ratio)]
    train_lines = lines[int(len(lines) * split_ratio):]
    with open(train_file, 'w') as file:
        file.writelines(train_lines)
    with open(valid_file, 'w') as file:
        file.writelines(valid_lines)

def main(instructions_file, train_file, valid_file, split_ratio):
    if not Path(instructions_file).is_file():
        sys.exit(f'{instructions_file} not found.')

    with open(instructions_file, 'r') as file:
        instructions = json.load(file)

    for i, instruction in enumerate(instructions, start=1):
        print(f"Processing ({i}/{len(instructions)}): {instruction}")
        answer, followup_question = query_ollama(instruction)
        result = json.dumps({
            'text': f'<s>[INST] {instruction}[/INST] {answer}</s>[INST]{followup_question}[/INST]'
        }) + "\n"
        with open(train_file, 'a') as file:
            file.write(result)
    
    create_validation_file(train_file, valid_file, split_ratio)
    print("Done! Training and validation JSONL files created.")

if __name__ == "__main__":
    if len(sys.argv) != 5:
        sys.exit("Usage: python script.py <instructions.json> <train.jsonl> <valid.jsonl> <split_ratio>")
    main(sys.argv[1], sys.argv[2], sys.argv[3], float(sys.argv[4]))