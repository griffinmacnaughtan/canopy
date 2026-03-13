from pydantic import BaseModel, Field
from typing import List, Optional, Dict

class Asset(BaseModel):
    id: str
    name: str
    sector: str
    region: str
    revenue_usd_m: float = Field(..., gt=0)
    scope1_tco2e: float = Field(..., ge=0)
    scope2_tco2e: float = Field(..., ge=0)
    green_revenue_pct: float = Field(..., ge=0, le=100)
    controversies: int = Field(0, ge=0, le=5)

class Portfolio(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    assets: List[Asset]


class PortfolioSummary(BaseModel):
    """Summary of a portfolio without asset details."""
    id: str
    name: str
    description: str
    asset_count: int


class PortfolioListResponse(BaseModel):
    """Response listing all available portfolios."""
    portfolios: List[PortfolioSummary]

class ScoreResponse(BaseModel):
    portfolio_id: str
    overall_score: float
    climate_risk: float
    transition_risk: float
    physical_risk: float
    opportunity_score: float
    top_risks: List[str]
    quick_wins: List[str]
    sector_breakdown: Dict[str, float]

class ScenarioRequest(BaseModel):
    portfolio_id: Optional[str] = None
    scenario: str
    carbon_price_usd: Optional[float] = None
    revenue_shock_pct: Optional[float] = None

class ScenarioResponse(BaseModel):
    portfolio_id: str
    scenario: str
    impact_summary: str
    est_ebitda_impact_pct: float
    emissions_delta_pct: float
    hotspots: List[str]

class CopilotRequest(BaseModel):
    portfolio_id: Optional[str] = None
    question: str

class CopilotResponse(BaseModel):
    portfolio_id: str
    answer: str
    citations: List[str]
    confidence: Optional[float] = Field(None, ge=0, le=1, description="Response confidence score (0-1)")


class CopilotStreamRequest(BaseModel):
    """Request for streaming copilot endpoint."""
    question: str
    portfolio_id: Optional[str] = None


class DocumentInfo(BaseModel):
    """Information about an uploaded document."""
    filename: str
    char_count: int


class UploadResponse(BaseModel):
    """Response from document upload."""
    success: bool
    document: DocumentInfo
    message: str


class DocumentListResponse(BaseModel):
    """Response listing all uploaded documents."""
    documents: List[DocumentInfo]
    total_chars: int


class CreatePortfolioRequest(BaseModel):
    """Request to create a custom portfolio."""
    name: str
    description: Optional[str] = None
    assets: List[Asset]


class CreatePortfolioResponse(BaseModel):
    """Response after creating a portfolio."""
    success: bool
    portfolio: PortfolioSummary
    message: str
