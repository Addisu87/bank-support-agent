"""
OBP (Open Bank Project) service to integrate real banking data
"""
import httpx
import logfire
from typing import List, Dict, Optional
from app.core.config import settings

class OBPService:
    """Service to interact with Open Bank Project sandbox data"""
    
    def __init__(self):
        self.base_url = "https://apisandbox.openbankproject.com"
        
    async def get_available_banks(self) -> List[Dict]:
        """Get list of available banks from OBP sandbox"""
        logfire.info("Fetching banks from OBP sandbox")
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.base_url}/obp/v5.0.0/banks")
                
                if response.status_code == 200:
                    data = response.json()
                    banks = data.get('banks', [])
                    logfire.info(f"Found {len(banks)} banks from OBP")
                    return banks
                else:
                    logfire.warning(f"Failed to fetch banks: {response.status_code}")
                    return []
                    
        except Exception as e:
            logfire.error(f"Error fetching banks: {str(e)}")
            return []
    
    async def get_bank_info(self, bank_id: str) -> Optional[Dict]:
        """Get information about a specific bank"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.base_url}/obp/v5.0.0/banks/{bank_id}")
                
                if response.status_code == 200:
                    return response.json()
                else:
                    return None
                    
        except Exception as e:
            logfire.error(f"Error fetching bank info: {str(e)}")
            return None
    
    async def get_public_accounts(self, bank_id: str) -> List[Dict]:
        """Get public accounts for a bank (for demo purposes)"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/obp/v5.0.0/banks/{bank_id}/accounts/public"
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return data.get('accounts', [])
                else:
                    return []
                    
        except Exception as e:
            logfire.error(f"Error fetching accounts: {str(e)}")
            return []
    
    async def get_demo_banking_scenario(self) -> Dict:
        """Get a demo banking scenario with real OBP data"""
        logfire.info("Creating demo banking scenario with OBP data")
        
        # Get a few banks
        banks = await self.get_available_banks()
        
        if not banks:
            return {"error": "No banks available"}
        
        # Use first available bank
        demo_bank = banks[0]
        bank_id = demo_bank.get('id')
        
        # Get accounts for demo
        accounts = await self.get_public_accounts(bank_id)
        
        scenario = {
            "bank": {
                "name": demo_bank.get('full_name', 'Demo Bank'),
                "short_name": demo_bank.get('short_name', 'DEMO'),
                "id": bank_id
            },
            "total_banks_available": len(banks),
            "demo_accounts": len(accounts),
            "message": f"Connected to {demo_bank.get('full_name')} with {len(accounts)} demo accounts"
        }
        
        return scenario

# Create singleton instance
obp_service = OBPService()
