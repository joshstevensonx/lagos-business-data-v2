"""Optional targeted Places enrichment, disabled unless explicitly enabled."""
import json,os
from datetime import datetime
from pathlib import Path
import httpx

ALLOWANCES={'essentials':10000,'pro':5000,'enterprise':1000}
ENTERPRISE_MASK='places.id,places.displayName,places.formattedAddress,places.location,places.nationalPhoneNumber,places.websiteUri,places.rating,places.userRatingCount,places.regularOpeningHours'
class PlacesAPI:
    def __init__(self,usage_path='~/.lagosdata/places_usage.json',ceiling_pct=80):
        self.path=Path(usage_path).expanduser();self.pct=ceiling_pct
    def _usage(self):
        try:return json.loads(self.path.read_text())
        except (OSError,json.JSONDecodeError):return {}
    async def enrich(self,place_id,enabled=False):
        if not enabled:raise RuntimeError('Google Places API is disabled in configuration')
        key=os.environ.get('GOOGLE_PLACES_API_KEY')
        if not key:raise RuntimeError('GOOGLE_PLACES_API_KEY is required when optional Places enrichment is enabled')
        sku='enterprise'; month=datetime.now().strftime('%Y-%m'); usage=self._usage(); bucket=usage.setdefault(month,{}).setdefault(sku,0); ceiling=int(ALLOWANCES[sku]*self.pct/100)
        if bucket>=ceiling:raise RuntimeError(f'Local {sku} Places API ceiling reached ({bucket}/{ceiling})')
        mask=ENTERPRISE_MASK
        if '*' in mask:raise AssertionError('wildcard Places field mask forbidden')
        async with httpx.AsyncClient(timeout=10) as client:
            response=await client.get(f'https://places.googleapis.com/v1/places/{place_id}',headers={'X-Goog-Api-Key':key,'X-Goog-FieldMask':mask})
            response.raise_for_status(); data=response.json()
        usage[month][sku]+=1;self.path.parent.mkdir(parents=True,exist_ok=True);self.path.write_text(json.dumps(usage,indent=2))
        return data
