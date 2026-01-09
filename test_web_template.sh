#!/bin/bash

# Test fetching web template from EHRBase 2.26.0

TEMPLATE_ID="IDCR - Vital Signs Encounter.v1"
TEMPLATE_ID_ENCODED="IDCR%20-%20Vital%20Signs%20Encounter.v1"
BASE_URL="http://localhost:8080/ehrbase"
USER="ehrbase-user"
PASS="SuperSecretPassword"

echo "=== Attempt 1: Standard openEHR REST API with JSON ==="
curl -s -X GET \
  "${BASE_URL}/rest/openehr/v1/definition/template/adl1.4/${TEMPLATE_ID_ENCODED}" \
  -H "Accept: application/json" \
  -u "${USER}:${PASS}" \
  > /tmp/web_template_test1.json
STATUS_1=$?

echo "Status: $STATUS_1"
echo "Response:"
cat /tmp/web_template_test1.json | head -50
echo ""

echo "=== Attempt 2: Web Template specific accept header ==="
curl -s -X GET \
  "${BASE_URL}/rest/openehr/v1/definition/template/adl1.4/${TEMPLATE_ID_ENCODED}" \
  -H "Accept: application/openehr.wt+json" \
  -u "${USER}:${PASS}" \
  > /tmp/web_template_test2.json
STATUS_2=$?

echo "Status: $STATUS_2"
echo "Response:"
cat /tmp/web_template_test2.json | head -50
echo ""

echo "=== Attempt 3: /webtemplate suffix ==="
curl -s -X GET \
  "${BASE_URL}/rest/openehr/v1/definition/template/adl1.4/${TEMPLATE_ID_ENCODED}/webtemplate" \
  -H "Accept: application/json" \
  -u "${USER}:${PASS}" \
  > /tmp/web_template_test3.json
STATUS_3=$?

echo "Status: $STATUS_3"
echo "Response:"
cat /tmp/web_template_test3.json | head -50
echo ""

echo "=== Checking which one worked ==="
for file in /tmp/web_template_test*.json; do
    echo "File: $file"
    if grep -q '"tree"' "$file" 2>/dev/null; then
        echo "✓ Found 'tree' key - this is a Web Template!"
        cp "$file" web_template.json
        echo "Saved to web_template.json"
    elif grep -q 'error' "$file" 2>/dev/null; then
        echo "✗ Error response"
    else
        echo "? Unknown response"
    fi
done
