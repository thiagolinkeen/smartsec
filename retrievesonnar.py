import requests
from openai import OpenAI
import subprocess
import json
import os

SONARQUBE_URL = '<here>'
PROJECT_KEY = '<here>'
SONARQUBE_TOKEN = '<here>'

client = OpenAI(api_key='<here>')

GITHUB_TOKEN = 'YOUR_GITHUB_TOKEN'
REPO_OWNER = 'YOUR_GITHUB_USERNAME'
REPO_NAME = 'YOUR_REPO_NAME'

def list_issues():
    response = requests.get(
        f'{SONARQUBE_URL}/api/issues/search',
        params={
            'componentKeys': PROJECT_KEY,
            'types': 'VULNERABILITY',
            'statuses': 'OPEN'  # Filtrar apenas issues abertas
        },
        headers={'Authorization': f'Bearer {SONARQUBE_TOKEN}'}
    )
    issues = response.json().get('issues', [])
    return issues

def format_flows(flows):
    formatted_flows = ""
    for flow in flows:
        for location in flow['locations']:
            component = location['component']
            text_range = location['textRange']
            msg = location['msg']
            formatted_flows += (f"\nComponent: {component}\n"
                                f"Text Range: {text_range}\n"
                                f"Message: {msg}\n")
    return formatted_flows

def suggest_fix(issue_description, flows, source_code):
    formatted_flows = format_flows(flows)
    prompt = (f"Here is a security vulnerability found in JavaScript code: {issue_description}. "
              f"Here are the details of the vulnerability flow:\n{formatted_flows}\n"
              f"Here is the source code:\n\n{source_code}\n\n"
              "Suggest a code fix to address this issue in the provided code.")

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt}
        ]
    )
    return response.choices[0].message.content.strip()

def extract_code_from_fix(fix):
    start_marker = "```javascript"
    end_marker = "```"

    if start_marker in fix and end_marker in fix:
        code_block = fix.split(start_marker)[1].split(end_marker)[0].strip()
        return code_block
    return fix

def display_issue_details(issue):
    issue_message = issue['message']
    issue_key = issue['key']
    issue_severity = issue['severity']
    issue_component = issue['component']
    issue_file = issue_component.split(':')[-1]

    print(f"\nIssue Key: {issue_key}")
    print(f"Message: {issue_message}")
    print(f"Severity: {issue_severity}")
    print(f"File: {issue_file}")
    print("\n\n")

    return issue_file

def apply_fix_to_file(file_path, fix):
    print(f"Attempting to apply fix to file: {file_path}")

    if not os.path.isfile(file_path):
        print(f"File not found: {file_path}")
        return

    with open(file_path, 'r') as file:
        code = file.read()

    fixed_code = extract_code_from_fix(fix)

    with open(file_path, 'w') as file:
        file.write(fixed_code)

    print(f"Applied fix to {file_path}")

def commit_and_create_pr():
    subprocess.run(["git", "add", "."])
    subprocess.run(["git", "commit", "-m", "Autofix: Applied automatic fixes for vulnerabilities"])

    branch_name = "autofix-branch"
    subprocess.run(["git", "checkout", "-b", branch_name])
    # subprocess.run(["git", "push", "origin", branch_name])

    # # Create PR
    # pr_data = {
    #     "title": "Automatic Fixes for Vulnerabilities",
    #     "body": "This PR contains automatic fixes for vulnerabilities detected by SonarQube.",
    #     "head": branch_name,
    #     "base": "main"
    # }
    # response = requests.post(
    #     f'https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/pulls',
    #     headers={'Authorization': f'token {GITHUB_TOKEN}'},
    #     data=json.dumps(pr_data)
    # )
    # if response.status_code == 201:
    #     print("Pull request created successfully.")
    # else:
    #     print(f"Failed to create pull request: {response.content}")

    # # Exibe as alterações do último commit
    # subprocess.run(["git", "show"])

def review_and_feedback(issue):
    issue_file = issue['component'].split(':')[-1]
    with open(issue_file, 'r') as file:
        source_code = file.read()

    issue_description = issue['message']
    issue_flows = issue.get('flows', [])
    print("Processing your request .....:")
    print("\n\n")

    fix = suggest_fix(issue_description, issue_flows, source_code)
    print(f"Suggested fix: {fix}\n")

def autofix_and_pr(issue):
    issue_file = issue['component'].split(':')[-1]
    with open(issue_file, 'r') as file:
        source_code = file.read()

    issue_description = issue['message']
    issue_flows = issue.get('flows', [])
    fix = suggest_fix(issue_description, issue_flows, source_code)

    # Apply the fix to the code
    apply_fix_to_file(issue_file, fix)

    commit_and_create_pr()

def main():
    issues = list_issues()
    issue_files = set()

    for i, issue in enumerate(issues):
        issue_file = display_issue_details(issue)
        issue_files.add(issue_file)
        print(f"{i + 1}. Issue Key: {issue['key']} - File: {issue_file}")

    if not issues:
        print("No issues found.")
        return

    print("\n\n")
    issue_choice = input("Enter the number of the issue you want to address: ")
    try:
        issue_index = int(issue_choice) - 1
        if issue_index < 0 or issue_index >= len(issues):
            print("Invalid choice.")
            return
    except ValueError:
        print("Invalid choice.")
        return

    choice = input("Choose an action: (1) Review and Feedback (2) Autofix and PR\n")
    if choice == '1':
        review_and_feedback(issues[issue_index])
    elif choice == '2':
        autofix_and_pr(issues[issue_index])
    else:
        print("Invalid choice.")

if __name__ == "__main__":
    main()