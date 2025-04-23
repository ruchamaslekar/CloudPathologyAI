from concurrent.futures import ThreadPoolExecutor
import asyncio

class QueryRunner:
    def __init__(self, connection):
        self.connection = connection
        self.thread_pool = ThreadPoolExecutor(max_workers=10)
        
    def run_query(self, query, parameters=None):
        try:
            session = self.connection.session
            result = session.execute(query, parameters)
            print(f"Query executed: {query}")
            
            # SELECT 
            if query.strip().upper().startswith("SELECT"):
                rows = list(result) 
                print(f"Rows fetched: {len(rows)}")
                return [dict(row._asdict()) for row in rows]
            
            # INSERT, UPDATE, DELETE
            else:
                return True  
        except Exception as e:
            print(f"Error executing query: {str(e)}")
            raise e

    async def run_query_async(self, query, parameters=None):
        loop = asyncio.get_event_loop()
        try:
            return await loop.run_in_executor(
                self.thread_pool, 
                self.run_query,
                query,
                parameters
            )
        except Exception as e:
            print(f"Error executing async query: {str(e)}")
            raise e
    
    def close(self):
        self.thread_pool.shutdown(wait=True)
        self.connection.close()
        print("Connection closed")