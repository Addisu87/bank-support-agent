from fastapi import APIRouter, Depends, HTTPException, status
from app.services.bank_service import create_bank, list_banks
from app.models.bank import CreateBankRequest, BankInfo
from app.core.deps import get_current_user

router = APIRouter()

@router.post("/banks", response_model=BankInfo, status_code=status.HTTP_201_CREATED)
async def create_bank_endpoint(request: CreateBankRequest, current_user: Depends(get_current_user)):
    """
    Create a new bank.
    """
    try:
        bank = await create_bank(name=request.name, bic=request.bic, country=request.country)
        return BankInfo.model_validate(bank)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating bank: {str(e)}")

@router.get("/banks", response_model=list[BankInfo])
async def list_banks_endpoint(current_user: Depends(get_current_user)):
    """
    List all banks.
    """
    try:
        banks = await list_banks()
        return [BankInfo.model_validate(bank) for bank in banks]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing banks: {str(e)}")