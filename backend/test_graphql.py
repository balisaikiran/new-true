#!/usr/bin/env python3
"""
Test script for GraphQL endpoints
"""

import httpx
import json

BASE_URL = "http://localhost:8000/graphql"


def test_query(query: str, variables: dict = None):
    """Execute a GraphQL query"""
    payload = {"query": query}
    if variables:
        payload["variables"] = variables
    
    response = httpx.post(BASE_URL, json=payload)
    return response.json()


def main():
    print("🧪 Testing GraphQL Endpoints\n")
    
    # Test 1: Query all Nifty data (limited)
    print("1️⃣ Query: Get first 5 Nifty records")
    query1 = """
    query {
        niftyData(limit: 5) {
            date
            open
            high
            low
            close
        }
    }
    """
    result1 = test_query(query1)
    print(json.dumps(result1, indent=2))
    print()
    
    # Test 2: Query by date range
    print("2️⃣ Query: Get data from 2025-12-01 to 2025-12-04")
    query2 = """
    query {
        niftyData(startDate: "2025-12-01", endDate: "2025-12-04") {
            date
            open
            high
            low
            close
        }
    }
    """
    result2 = test_query(query2)
    print(json.dumps(result2, indent=2))
    print()
    
    # Test 3: Query single date
    print("3️⃣ Query: Get data for specific date")
    query3 = """
    query {
        niftyDataByDate(date: "2025-12-04") {
            date
            open
            high
            low
            close
        }
    }
    """
    result3 = test_query(query3)
    print(json.dumps(result3, indent=2))
    print()
    
    # Test 4: Get count
    print("4️⃣ Query: Get total count")
    query4 = """
    query {
        niftyDataCount
    }
    """
    result4 = test_query(query4)
    print(json.dumps(result4, indent=2))
    print()
    
    # Test 5: Upsert mutation
    print("5️⃣ Mutation: Upsert Nifty data")
    mutation1 = """
    mutation {
        upsertNiftyData(input: {
            date: "2025-12-05"
            open: 26000.0
            high: 26100.0
            low: 25900.0
            close: 26050.0
        }) {
            success
            message
            data {
                date
                open
                high
                low
                close
            }
        }
    }
    """
    result5 = test_query(mutation1)
    print(json.dumps(result5, indent=2))
    print()
    
    # Test 6: Update mutation
    print("6️⃣ Mutation: Update Nifty data")
    mutation2 = """
    mutation {
        updateNiftyData(input: {
            date: "2025-12-05"
            close: 26075.5
        }) {
            success
            message
            data {
                date
                open
                high
                low
                close
            }
        }
    }
    """
    result6 = test_query(mutation2)
    print(json.dumps(result6, indent=2))
    print()
    
    # Test 7: Query updated data
    print("7️⃣ Query: Verify updated data")
    query7 = """
    query {
        niftyDataByDate(date: "2025-12-05") {
            date
            open
            high
            low
            close
        }
    }
    """
    result7 = test_query(query7)
    print(json.dumps(result7, indent=2))
    print()
    
    print("✅ GraphQL tests completed!")


if __name__ == "__main__":
    try:
        main()
    except httpx.ConnectError:
        print("❌ Error: Could not connect to server. Make sure the backend is running on http://localhost:8000")
    except Exception as e:
        print(f"❌ Error: {str(e)}")

