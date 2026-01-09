#!/bin/bash

# Test submitting a minimal FLAT composition to EHRBase
# to understand the expected path structure

BASE_URL="http://localhost:8080/ehrbase"
USER="ehrbase-user"
PASS="SuperSecretPassword"
TEMPLATE_ID="IDCR - Vital Signs Encounter.v1"

echo "=== Creating test EHR ==="
EHR_JSON=$(curl -s -X POST "${BASE_URL}/rest/openehr/v1/ehr" \
  -H "Prefer: return=representation" \
  -u "${USER}:${PASS}")

if echo "$EHR_JSON" | grep -q "ehr_id"; then
  EHR_ID=$(echo "$EHR_JSON" | python3 -c "import sys, json; print(json.load(sys.stdin)['ehr_id']['value'])")
  echo "Created EHR: $EHR_ID"
else
  echo "Failed to create EHR:"
  echo "$EHR_JSON" | python3 -m json.tool
  exit 1
fi

echo ""
echo "=== Testing FLAT composition submission ==="

# Try blood pressure with all required fields from web template
FLAT_DATA='{
  "ctx/language": "en",
  "ctx/territory": "US",
  "ctx/composer_name": "Test",
  "vital_signs/blood_pressure:0/systolic|magnitude": 120,
  "vital_signs/blood_pressure:0/systolic|unit": "mm[Hg]",
  "vital_signs/blood_pressure:0/diastolic|magnitude": 80,
  "vital_signs/blood_pressure:0/diastolic|unit": "mm[Hg]",
  "vital_signs/blood_pressure:0/time": "2026-01-09T12:00:00Z",
  "vital_signs/blood_pressure:0/language|code": "en",
  "vital_signs/blood_pressure:0/language|terminology": "ISO_639-1",
  "vital_signs/blood_pressure:0/encoding|code": "UTF-8",
  "vital_signs/blood_pressure:0/encoding|terminology": "IANA_character-sets"
}'

echo "Attempting submission with paths:"
echo "$FLAT_DATA" | python3 -m json.tool

RESPONSE=$(curl -s -w "\nHTTP_STATUS:%{http_code}" -X POST \
  "${BASE_URL}/rest/openehr/v1/ehr/${EHR_ID}/composition?format=FLAT&templateId=${TEMPLATE_ID// /%20}" \
  -H "Content-Type: application/json" \
  -u "${USER}:${PASS}" \
  -d "$FLAT_DATA")

HTTP_STATUS=$(echo "$RESPONSE" | grep "HTTP_STATUS" | cut -d: -f2)
BODY=$(echo "$RESPONSE" | sed '/HTTP_STATUS/d')

echo ""
echo "Response status: $HTTP_STATUS"
echo "Response body:"
echo "$BODY" | python3 -m json.tool 2>/dev/null || echo "$BODY"
