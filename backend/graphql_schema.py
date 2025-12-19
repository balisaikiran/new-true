"""
GraphQL schema for Nifty data
"""
import strawberry
from typing import List, Optional
from datetime import datetime
from strawberry.fastapi import GraphQLRouter


def get_db():
    """Get MongoDB database instance"""
    try:
        # Try importing from server module (works when server is running)
        import sys
        import importlib
        
        # Try multiple import paths
        if 'server' in sys.modules:
            server_module = sys.modules['server']
            return getattr(server_module, 'db', None)
        
        # Try direct import
        try:
            from server import db
            return db
        except ImportError:
            try:
                from backend.server import db
                return db
            except ImportError:
                # Last resort: import directly
                import server
                return getattr(server, 'db', None)
    except Exception as e:
        # Log error for debugging
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"Could not get database in GraphQL: {str(e)}")
        return None


@strawberry.type
class NiftyData:
    """Nifty OHLC data type"""
    name: Optional[str] = None
    date: str
    open: Optional[float] = None
    high: Optional[float] = None
    low: Optional[float] = None
    close: Optional[float] = None
    imported_at: Optional[str] = None


@strawberry.input
class NiftyDataInput:
    """Input type for creating/updating Nifty data"""
    name: Optional[str] = None
    date: str
    open: Optional[float] = None
    high: Optional[float] = None
    low: Optional[float] = None
    close: Optional[float] = None


@strawberry.input
class NiftyDataUpdateInput:
    """Input type for updating Nifty data (all fields optional except date)"""
    name: Optional[str] = None
    date: str
    open: Optional[float] = None
    high: Optional[float] = None
    low: Optional[float] = None
    close: Optional[float] = None


@strawberry.type
class NiftyDataResponse:
    """Response type for mutations"""
    success: bool
    message: str
    data: Optional[NiftyData] = None


@strawberry.type
class Query:
    """GraphQL queries for Nifty data"""
    
    @strawberry.field
    async def nifty_data(
        self,
        name: Optional[str] = None,
        date: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[NiftyData]:
        """
        Get Nifty data
        
        Args:
            date: Get data for a specific date (YYYY-MM-DD)
            start_date: Get data from this date onwards (YYYY-MM-DD)
            end_date: Get data up to this date (YYYY-MM-DD)
            limit: Maximum number of records to return
            offset: Number of records to skip
        """
        db = get_db()
        
        if db is None:
            return []
        
        collection = db.nifty_data
        query = {}
        
        if name:
            query["name"] = name
        
        if date:
            query["date"] = date
        else:
            if start_date:
                query["date"] = {"$gte": start_date}
            if end_date:
                if "date" in query:
                    query["date"]["$lte"] = end_date
                else:
                    query["date"] = {"$lte": end_date}
        
        cursor = collection.find(query).sort("date", -1).skip(offset).limit(limit)
        
        results = []
        async for doc in cursor:
            results.append(NiftyData(
                name=doc.get("name"),
                date=doc.get("date", ""),
                open=doc.get("open"),
                high=doc.get("high"),
                low=doc.get("low"),
                close=doc.get("close"),
                imported_at=doc.get("imported_at")
            ))
        
        return results
    
    @strawberry.field
    async def nifty_data_count(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> int:
        """Get count of Nifty data records"""
        db = get_db()
        
        if db is None:
            return 0
        
        collection = db.nifty_data
        query = {}
        
        if start_date:
            query["date"] = {"$gte": start_date}
        if end_date:
            if "date" in query:
                query["date"]["$lte"] = end_date
            else:
                query["date"] = {"$lte": end_date}
        
        return await collection.count_documents(query)
    
    @strawberry.field
    async def nifty_data_by_date(self, date: str) -> Optional[NiftyData]:
        """Get Nifty data for a specific date"""
        db = get_db()
        
        if db is None:
            return None
        
        collection = db.nifty_data
        doc = await collection.find_one({"date": date})
        
        if not doc:
            return None
        
        return NiftyData(
            date=doc.get("date", ""),
            open=doc.get("open"),
            high=doc.get("high"),
            low=doc.get("low"),
            close=doc.get("close"),
            imported_at=doc.get("imported_at")
        )


@strawberry.type
class Mutation:
    """GraphQL mutations for Nifty data"""
    
    @strawberry.mutation
    async def create_nifty_data(self, input: NiftyDataInput) -> NiftyDataResponse:
        """Create a new Nifty data record"""
        from datetime import datetime, timezone
        
        db = get_db()
        
        if db is None:
            return NiftyDataResponse(
                success=False,
                message="MongoDB not initialized"
            )
        
        collection = db.nifty_data
        
        # Check if record already exists (using both name and date)
        query = {"date": input.date}
        if input.name:
            query["name"] = input.name
        
        existing = await collection.find_one(query)
        if existing:
            return NiftyDataResponse(
                success=False,
                message=f"Record for {input.name or 'NIFTY 50'} on date {input.date} already exists. Use updateNiftyData instead."
            )
        
        document = {
            "name": input.name or "NIFTY 50",
            "date": input.date,
            "open": input.open,
            "high": input.high,
            "low": input.low,
            "close": input.close,
            "imported_at": datetime.now(timezone.utc).isoformat()
        }
        
        try:
            await collection.insert_one(document)
            
            return NiftyDataResponse(
                success=True,
                message=f"Created {document['name']} data for date {input.date}",
                data=NiftyData(
                    name=document["name"],
                    date=document["date"],
                    open=document["open"],
                    high=document["high"],
                    low=document["low"],
                    close=document["close"],
                    imported_at=document["imported_at"]
                )
            )
        except Exception as e:
            return NiftyDataResponse(
                success=False,
                message=f"Error creating record: {str(e)}"
            )
    
    @strawberry.mutation
    async def update_nifty_data(self, input: NiftyDataUpdateInput) -> NiftyDataResponse:
        """Update an existing Nifty data record"""
        from datetime import datetime, timezone
        
        db = get_db()
        
        if db is None:
            return NiftyDataResponse(
                success=False,
                message="MongoDB not initialized"
            )
        
        collection = db.nifty_data
        
        # Build query with name and date
        query = {"date": input.date}
        if input.name:
            query["name"] = input.name
        
        # Build update document with only provided fields
        update_doc = {}
        if input.name is not None:
            update_doc["name"] = input.name
        if input.open is not None:
            update_doc["open"] = input.open
        if input.high is not None:
            update_doc["high"] = input.high
        if input.low is not None:
            update_doc["low"] = input.low
        if input.close is not None:
            update_doc["close"] = input.close
        
        update_doc["imported_at"] = datetime.now(timezone.utc).isoformat()
        
        try:
            result = await collection.update_one(
                query,
                {"$set": update_doc},
                upsert=False
            )
            
            if result.matched_count == 0:
                return NiftyDataResponse(
                    success=False,
                    message=f"Record for {input.name or 'NIFTY 50'} on date {input.date} not found. Use createNiftyData to create a new record."
                )
            
            # Fetch updated document
            updated_doc = await collection.find_one(query)
            
            return NiftyDataResponse(
                success=True,
                message=f"Updated {updated_doc.get('name', 'NIFTY 50')} data for date {input.date}",
                data=NiftyData(
                    name=updated_doc.get("name"),
                    date=updated_doc.get("date", ""),
                    open=updated_doc.get("open"),
                    high=updated_doc.get("high"),
                    low=updated_doc.get("low"),
                    close=updated_doc.get("close"),
                    imported_at=updated_doc.get("imported_at")
                )
            )
        except Exception as e:
            return NiftyDataResponse(
                success=False,
                message=f"Error updating record: {str(e)}"
            )
    
    @strawberry.mutation
    async def upsert_nifty_data(self, input: NiftyDataInput) -> NiftyDataResponse:
        """Create or update a Nifty data record"""
        from datetime import datetime, timezone
        
        db = get_db()
        
        if db is None:
            return NiftyDataResponse(
                success=False,
                message="MongoDB not initialized"
            )
        
        collection = db.nifty_data
        
        document = {
            "name": input.name or "NIFTY 50",
            "date": input.date,
            "open": input.open,
            "high": input.high,
            "low": input.low,
            "close": input.close,
            "imported_at": datetime.now(timezone.utc).isoformat()
        }
        
        query = {
            "name": document["name"],
            "date": input.date
        }
        
        try:
            result = await collection.update_one(
                query,
                {"$set": document},
                upsert=True
            )
            
            action = "Updated" if result.matched_count > 0 else "Created"
            
            return NiftyDataResponse(
                success=True,
                message=f"{action} {document['name']} data for date {input.date}",
                data=NiftyData(
                    name=document["name"],
                    date=document["date"],
                    open=document["open"],
                    high=document["high"],
                    low=document["low"],
                    close=document["close"],
                    imported_at=document["imported_at"]
                )
            )
        except Exception as e:
            return NiftyDataResponse(
                success=False,
                message=f"Error upserting record: {str(e)}"
            )
    
    @strawberry.mutation
    async def delete_nifty_data(self, date: str, name: Optional[str] = None) -> NiftyDataResponse:
        """Delete a Nifty data record"""
        db = get_db()
        
        if db is None:
            return NiftyDataResponse(
                success=False,
                message="MongoDB not initialized"
            )
        
        collection = db.nifty_data
        
        query = {"date": date}
        if name:
            query["name"] = name
        
        try:
            result = await collection.delete_one(query)
            
            if result.deleted_count == 0:
                return NiftyDataResponse(
                    success=False,
                    message=f"Record for {name or 'NIFTY 50'} on date {date} not found"
                )
            
            return NiftyDataResponse(
                success=True,
                message=f"Deleted {name or 'NIFTY 50'} data for date {date}"
            )
        except Exception as e:
            return NiftyDataResponse(
                success=False,
                message=f"Error deleting record: {str(e)}"
            )


# Create GraphQL schema
schema = strawberry.Schema(query=Query, mutation=Mutation)

