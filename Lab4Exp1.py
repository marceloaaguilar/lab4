import csv
import requests
from datetime import datetime
import matplotlib.pyplot as plt
import os

GITHUB_API_URL = "https://api.github.com/graphql"
GITHUB_TOKEN = "" 

REPO_QUERY = """
query ($owner: String!, $name: String!) {
  repository(owner: $owner, name: $name) {
    name
    owner {
      login
    }
    createdAt
    updatedAt
    primaryLanguage {
      name
    }
    releases {
      totalCount
    }
    pullRequests(states: MERGED) {
      totalCount
    }
    issues(states: CLOSED) {
      totalCount
    }
    totalIssues: issues {
      totalCount
    }
    stargazerCount
  }
}
"""

def fetch_repository_data(owner, name):
    headers = {"Authorization": f"Bearer {GITHUB_TOKEN}"}
    variables = {"owner": owner, "name": name}

    response = requests.post(GITHUB_API_URL, json={"query": REPO_QUERY, "variables": variables}, headers=headers)
    
    if response.status_code != 200:
        print(f"Erro ao buscar {owner}/{name}: {response.status_code} - {response.text}")
        return None

    data = response.json().get("data", {}).get("repository", None)
    return data

def process_repository(repo):
    if not repo:
        return None

    created_at = datetime.strptime(repo["createdAt"], "%Y-%m-%dT%H:%M:%SZ")
    updated_at = datetime.strptime(repo["updatedAt"], "%Y-%m-%dT%H:%M:%SZ")

    return {
        "name": repo["name"],
        "owner": repo["owner"]["login"],
        "age_years": (datetime.utcnow() - created_at).days // 365,
        "time_since_last_update": (datetime.utcnow() - updated_at).days,
        "language": repo["primaryLanguage"]["name"] if repo["primaryLanguage"] else "Unknown",
        "releases": repo["releases"]["totalCount"],
        "pull_requests": repo["pullRequests"]["totalCount"],
        "closed_issues": repo["issues"]["totalCount"],
        "total_issues": repo["totalIssues"]["totalCount"],
        "issue_closure_rate": repo["issues"]["totalCount"] / repo["totalIssues"]["totalCount"] if repo["totalIssues"]["totalCount"] > 0 else 0,
        "stars": repo["stargazerCount"]
    }

def read_repository_list(file_path):
  with open(file_path, newline='', encoding="utf-8") as csvfile:
    reader = csv.DictReader(csvfile)
    return [(row["Dono"], row["Nome"]) for row in reader]

if __name__ == "__main__":
    repo_list = read_repository_list("data/repositories.csv")
    repos_data = []
    indice = 0
    for owner, name in repo_list:
        repo = fetch_repository_data(owner, name)
        processed = process_repository(repo)
        if processed:
            indice+=1
            print(f"Processando repositório: {indice}")
            repos_data.append(processed)

    with open("github_repos_data.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Nome", "Dono", "Idade (anos)", "Dias desde última atualização",
                         "Linguagem", "Releases", "Pull Requests", "Issues Fechadas",
                         "Total Issues", "Taxa de Fechamento de Issues", "Stars"])
        for repo in repos_data:
            writer.writerow([
                repo["name"], repo["owner"], repo["age_years"],
                repo["time_since_last_update"], repo["language"],
                repo["releases"], repo["pull_requests"], repo["closed_issues"],
                repo["total_issues"], repo["issue_closure_rate"], repo["stars"],
            ])
    print("Dados salvos em github_repos_data.csv")
