import os
import requests
from sigma.collection import SigmaCollection
from sigma.backends.elasticsearch import ElasticsearchQueryBackend

def deploy_to_elastic(rules_dir="rules", elastic_url="", api_key=""):
    backend = ElasticsearchQueryBackend()
    headers = {
        "Authorization": f"ApiKey {api_key}",
        "Content-Type": "application/json"
    }
    
    for root, _, files in os.walk(rules_dir):
        for file in files:
            if file.endswith(".yml"):
                rule_path = os.path.join(root, file)
                try:
                    with open(rule_path, 'r') as f:
                        rule_content = f.read()
                    sigma_rule = SigmaCollection.from_yaml(rule_content)
                    query = backend.convert(sigma_rule)[0]
                    
                    payload = {
                        "name": sigma_rule.rules[0].title,
                        "rule_id": str(sigma_rule.rules[0].id),
                        "risk_score": 50,
                        "description": sigma_rule.rules[0].description or "No description",
                        "query": query,
                        "type": "query",
                        "interval": "5m",
                        "enabled": True
                    }
                    
                    response = requests.post(
                        f"{elastic_url}/_security/api/detection_engine/rules",
                        headers=headers,
                        json=payload
                    )
                    if response.status_code in [200, 201]:
                        print(f"Successfully deployed {rule_path}")
                    else:
                        print(f"Failed to deploy {rule_path}: {response.text}")
                        exit(1)
                except Exception as e:
                    print(f"Error deploying {rule_path}: {e}")
                    exit(1)

if __name__ == "__main__":
    elastic_url = os.getenv("ELASTIC_URL")
    api_key = os.getenv("ELASTIC_API_KEY")
    if not elastic_url or not api_key:
        print("Error: ELASTIC_URL or ELASTIC_API_KEY not set")
        exit(1)
    deploy_to_elastic(elastic_url=elastic_url, api_key=api_key)
