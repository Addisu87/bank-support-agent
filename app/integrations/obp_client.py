import httpx
from app.core.config import settings

class OBPClient: 
    def __init__(self,
                 base_url=settings.OBP_BASE_URL,
                 token=settings.OBP_ACCESS_TOKEN):
        self.base_url = base_url.rstrip("/") # type: ignore
        self.token = token
        
    def _headers(self):
        return {
            "Authorization": f"DirectLogin token={self.token}",
            "Content-Type": "application/json"
        }
        
    async def get_banks(self):
        async with httpx.AsyncClient() as client: 
            # Try with auth first, fallback to public if auth fails
            try:
                if self.token:
                    resp = await client.get(f"{self.base_url}/obp/v5.0.0/banks",
                                            headers=self._headers())
                else:
                    raise Exception("No token, using public endpoint")
            except:
                # Fallback to public endpoint
                resp = await client.get(f"{self.base_url}/obp/v5.0.0/banks")
            
            resp.raise_for_status()
            return resp.json().get('banks', [])
        
    async def get_transactions(self, bank_id, account_id):
        async with httpx.AsyncClient() as client: 
            resp = await client.get(
                f"{self.base_url}/obp/v5.0.0/banks/{bank_id}/accounts/{account_id}/transactions",
                headers = self._headers()
            )
            resp.raise_for_status()
            return resp.json().get("transactions", [])
        