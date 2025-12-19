# GraphQL API Documentation

GraphQL endpoints for viewing and updating Nifty data in MongoDB.

## 🚀 Endpoint

**GraphQL Endpoint**: `http://localhost:8000/graphql`

For production: `https://your-domain.com/graphql`

## 📋 Available Queries

### 1. Get Nifty Data (with filters)

Get Nifty OHLC data with optional filters.

**Query:**
```graphql
query {
  niftyData(
    date: "2025-12-04"          # Optional: specific date
    startDate: "2025-12-01"     # Optional: start date
    endDate: "2025-12-04"        # Optional: end date
    limit: 100                   # Optional: max records (default: 100)
    offset: 0                    # Optional: skip records (default: 0)
  ) {
    date
    open
    high
    low
    close
    importedAt
  }
}
```

**Example Response:**
```json
{
  "data": {
    "niftyData": [
      {
        "date": "2025-12-04",
        "open": 25981.85,
        "high": 26098.25,
        "low": 25938.95,
        "close": 26033.75,
        "importedAt": "2025-12-05T12:14:24.168000"
      }
    ]
  }
}
```

### 2. Get Nifty Data by Date

Get data for a specific date.

**Query:**
```graphql
query {
  niftyDataByDate(date: "2025-12-04") {
    date
    open
    high
    low
    close
    importedAt
  }
}
```

### 3. Get Count

Get total count of records (optionally filtered by date range).

**Query:**
```graphql
query {
  niftyDataCount(
    startDate: "2025-12-01"
    endDate: "2025-12-04"
  )
}
```

**Example Response:**
```json
{
  "data": {
    "niftyDataCount": 3785
  }
}
```

## ✏️ Available Mutations

### 1. Create Nifty Data

Create a new Nifty data record. Fails if record already exists.

**Mutation:**
```graphql
mutation {
  createNiftyData(input: {
    date: "2025-12-06"
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
```

### 2. Update Nifty Data

Update an existing Nifty data record. Only updates provided fields.

**Mutation:**
```graphql
mutation {
  updateNiftyData(input: {
    date: "2025-12-06"
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
```

### 3. Upsert Nifty Data

Create or update a Nifty data record. Creates if doesn't exist, updates if exists.

**Mutation:**
```graphql
mutation {
  upsertNiftyData(input: {
    date: "2025-12-06"
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
```

### 4. Delete Nifty Data

Delete a Nifty data record.

**Mutation:**
```graphql
mutation {
  deleteNiftyData(date: "2025-12-06") {
    success
    message
  }
}
```

## 🧪 Testing

### Using curl

**Query Example:**
```bash
curl -X POST http://localhost:8000/graphql \
  -H "Content-Type: application/json" \
  -d '{
    "query": "query { niftyData(limit: 5) { date open high low close } }"
  }'
```

**Mutation Example:**
```bash
curl -X POST http://localhost:8000/graphql \
  -H "Content-Type: application/json" \
  -d '{
    "query": "mutation { upsertNiftyData(input: { date: \"2025-12-06\" open: 26000.0 high: 26100.0 low: 25900.0 close: 26050.0 }) { success message data { date open high low close } } }"
  }'
```

### Using Python

```python
import httpx

response = httpx.post(
    "http://localhost:8000/graphql",
    json={
        "query": """
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
    }
)
print(response.json())
```

### Using GraphQL Playground

Visit `http://localhost:8000/graphql` in your browser to use the interactive GraphQL playground (if enabled).

## 📝 Examples

### Get Latest 10 Records

```graphql
query {
  niftyData(limit: 10) {
    date
    open
    high
    low
    close
  }
}
```

### Get Data for Last Week

```graphql
query {
  niftyData(
    startDate: "2025-11-28"
    endDate: "2025-12-04"
  ) {
    date
    open
    close
  }
}
```

### Update Only Close Price

```graphql
mutation {
  updateNiftyData(input: {
    date: "2025-12-04"
    close: 26040.0
  }) {
    success
    message
    data {
      date
      close
    }
  }
}
```

### Bulk Upsert Multiple Dates

```graphql
mutation {
  day1: upsertNiftyData(input: {
    date: "2025-12-06"
    open: 26000.0
    high: 26100.0
    low: 25900.0
    close: 26050.0
  }) {
    success
    message
  }
  
  day2: upsertNiftyData(input: {
    date: "2025-12-07"
    open: 26050.0
    high: 26150.0
    low: 26000.0
    close: 26100.0
  }) {
    success
    message
  }
}
```

## 🔧 Error Handling

All mutations return a response with `success` and `message` fields:

```json
{
  "data": {
    "updateNiftyData": {
      "success": false,
      "message": "Record for date 2025-12-06 not found. Use createNiftyData to create a new record.",
      "data": null
    }
  }
}
```

## 📊 Field Types

- **date**: String (format: YYYY-MM-DD)
- **open**: Float (optional)
- **high**: Float (optional)
- **low**: Float (optional)
- **close**: Float (optional)
- **importedAt**: String (ISO 8601 timestamp)

## 🚨 Notes

1. Date format must be `YYYY-MM-DD` (e.g., "2025-12-04")
2. All OHLC values are optional in mutations
3. `upsertNiftyData` is recommended for most use cases as it handles both create and update
4. Queries are read-only and don't modify data
5. Mutations require MongoDB to be initialized








