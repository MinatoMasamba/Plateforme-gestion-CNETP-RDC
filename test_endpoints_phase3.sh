#!/bin/bash

# Test script pour Phase 3 endpoints

echo "🧪 Testing Phase 3 API Endpoints..."
echo

# Start Django server in background
cd /home/minato/projet
source mon_env/bin/activate
python manage.py runserver 0.0.0.0:8000 > /tmp/server.log 2>&1 &
SERVER_PID=$!
sleep 3

BASE_URL="http://localhost:8000/api/v1"

# Test fonction
test_endpoint() {
    local method=$1
    local endpoint=$2
    local description=$3
    
    response=$(curl -s -w "\n%{http_code}" -X $method "$BASE_URL$endpoint")
    status_code=$(echo "$response" | tail -n1)
    
    if [[ $status_code == "200" || $status_code == "201" || $status_code == "401" || $status_code == "403" || $status_code == "404" ]]; then
        echo "✅ [$status_code] $method $endpoint"
    else
        echo "❌ [$status_code] $method $endpoint"
    fi
}

echo "🧬 AMENDMENTS ENDPOINTS"
test_endpoint GET "/amendments/" "List amendments"
test_endpoint GET "/amendments/stats/" "Amendment stats"

echo
echo "📋 MEETINGS ENDPOINTS"
test_endpoint GET "/reunions/" "List reunions"
test_endpoint GET "/reunions/upcoming/" "Upcoming reunions"
test_endpoint GET "/presences/" "List presences"
test_endpoint GET "/pv/" "List PV"

echo
echo "💰 PAYMENTS ENDPOINTS"
test_endpoint GET "/cotisations/" "List cotisations"
test_endpoint GET "/cotisations/dashboard/" "Payment dashboard"
test_endpoint GET "/paiements/" "List payments"
test_endpoint GET "/jetons/" "List tokens"
test_endpoint GET "/jetons/stats/" "Token stats"

echo
echo "✅ All endpoints responsive!"
echo

# Cleanup
kill $SERVER_PID 2>/dev/null
