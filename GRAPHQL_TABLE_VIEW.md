# 📊 GraphQL Table View Guide

You now have **two ways** to view GraphQL results in table format!

## 🎯 Option 1: GraphiQL (Built-in IDE)

**URL**: http://localhost:8000/graphql

GraphiQL is now enabled and provides:
- ✅ Interactive query editor
- ✅ Table-like view of results
- ✅ Query history
- ✅ Schema explorer
- ✅ Auto-completion

### How to Use:
1. Open http://localhost:8000/graphql in your browser
2. Enter your query in the left panel
3. Click the "Play" button or press `Ctrl+Enter`
4. Results appear in the right panel with table-like formatting

## 🎯 Option 2: Custom HTML Viewer

**URL**: http://localhost:8000/graphql-viewer

A beautiful custom viewer with:
- ✅ Clean table format
- ✅ Query presets (quick buttons)
- ✅ Statistics display
- ✅ Formatted numbers
- ✅ Responsive design

### How to Use:
1. Open http://localhost:8000/graphql-viewer in your browser
2. Use preset buttons or enter your own query
3. Click "Execute Query"
4. Results display in a formatted table

## 📋 Example Queries

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

### Get Data by Date Range
```graphql
query {
  niftyData(startDate: "2025-12-01", endDate: "2025-12-04") {
    date
    open
    high
    low
    close
  }
}
```

### Get Count
```graphql
query {
  niftyDataCount
}
```

### Get Single Date
```graphql
query {
  niftyDataByDate(date: "2025-12-04") {
    date
    open
    high
    low
    close
  }
}
```

## 🎨 Features

### GraphiQL Features:
- Syntax highlighting
- Query validation
- Schema documentation
- Variable support
- Query history

### Custom Viewer Features:
- Beautiful UI
- Quick preset buttons
- Statistics cards
- Formatted numbers
- Responsive tables
- Error handling

## 🚀 Quick Start

1. **Start the server** (if not running):
   ```bash
   cd backend
   python3 -m uvicorn server:app --host 0.0.0.0 --port 8000 --reload
   ```

2. **Open GraphiQL**:
   - Visit: http://localhost:8000/graphql
   - Start querying!

3. **Or use Custom Viewer**:
   - Visit: http://localhost:8000/graphql-viewer
   - Use preset buttons or write custom queries

## 💡 Tips

- In GraphiQL, you can toggle between JSON and table views
- The custom viewer automatically formats numbers
- Use query presets for quick access to common queries
- Both viewers support all GraphQL queries and mutations

Enjoy viewing your data in beautiful table format! 🎉








