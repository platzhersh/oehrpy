#!/bin/bash
# Helper script to fetch web template from a CI run
# Usage: ./fetch_webtemplate_from_ci.sh

set -e

echo "This script will create a temporary commit that fetches the web template in CI"
echo ""
echo "Steps:"
echo "1. Creates a test file that runs curl to fetch web template"
echo "2. Commits and pushes"
echo "3. You download the artifact from CI"
echo "4. We revert the commit"
echo ""
read -p "Press Enter to continue or Ctrl+C to cancel..."

# Create a GitHub Actions workflow that fetches web template
mkdir -p .github/workflows-temp
cat > .github/workflows-temp/fetch-webtemplate.yml << 'EOF'
name: Fetch Web Template

on:
  push:
    branches:
      - feat/integration-testing-with-ehrbase

jobs:
  fetch:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: ehrbase/ehrbase-v2-postgres:16.2
        env:
          POSTGRES_DB: ehrbase
          POSTGRES_USER: postgres
          POSTGRES_PASSWORD: postgres
          EHRBASE_USER: ehrbase
          EHRBASE_PASSWORD: ehrbase
        options: >-
          --health-cmd "pg_isready -U postgres"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
      - name: Start EHRBase
        run: |
          docker run -d --name ehrbase --network host \
            -e DB_URL=jdbc:postgresql://localhost:5432/ehrbase \
            -e DB_USER=ehrbase \
            -e DB_PASS=ehrbase \
            -e DB_USER_ADMIN=ehrbase \
            -e DB_PASS_ADMIN=ehrbase \
            -e SECURITY_AUTHTYPE=BASIC \
            -e SECURITY_AUTHUSER=ehrbase-user \
            -e SECURITY_AUTHPASSWORD=SuperSecretPassword \
            -e SECURITY_AUTHADMINUSER=ehrbase-admin \
            -e SECURITY_AUTHADMINPASSWORD=EvenMoreSecretPassword \
            ehrbase/ehrbase:2.0.0

      - name: Wait for EHRBase
        run: |
          for i in {1..30}; do
            sleep 3
            curl -sf -u ehrbase-user:SuperSecretPassword \
              http://localhost:8080/ehrbase/rest/status && break || echo "Waiting..."
          done

      - name: Upload template
        run: |
          curl -X POST -u ehrbase-user:SuperSecretPassword \
            -H "Content-Type: application/xml" \
            -H "Accept: */*" \
            --data @tests/fixtures/vital_signs.opt \
            http://localhost:8080/ehrbase/rest/openehr/v1/definition/template/adl1.4 || true

      - name: Fetch Web Template
        run: |
          curl -u ehrbase-user:SuperSecretPassword \
            "http://localhost:8080/ehrbase/rest/openehr/v1/definition/template/adl1.4/IDCR%20-%20Vital%20Signs%20Encounter.v1" \
            | python3 -m json.tool > web_template.json

      - name: Upload artifact
        uses: actions/upload-artifact@v3
        with:
          name: web-template
          path: web_template.json
EOF

echo "Created workflow file. Commit and push? (y/n)"
read -r response
if [[ "$response" == "y" ]]; then
    git add .github/workflows-temp/fetch-webtemplate.yml
    git commit -m "temp: Add workflow to fetch web template"
    git push
    echo ""
    echo "✓ Pushed! Check GitHub Actions and download the web_template.json artifact"
    echo "  Then run: ./analyze_webtemplate.sh web_template.json"
fi
