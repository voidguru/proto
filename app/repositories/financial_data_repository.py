import boto3
import requests
from datetime import datetime, timedelta
from typing import List, Type, Optional, Any


class FinancialDataRepository:
    """
    Universal DynamoDB cache manager for financial statement datasets.
    Uses:
        PK: symbol (e.g., "AAPL")
        SK: dataset (e.g., "key-metrics", "balance-sheet-statement", etc.)
    """

    def __init__(
        self,
        table_name: str,
        api_key: str,
        base_url: str = "https://financialmodelingprep.com/stable",
        max_cache_age_hours: int = 24,
        aws_region: str = "us-east-1",
    ):
        self.dynamodb = boto3.resource("dynamodb", region_name=aws_region)
        self.table = self.dynamodb.Table(table_name)
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.max_age = timedelta(hours=max_cache_age_hours)

    # -------------------------------------------------------
    # Internal Helpers
    # -------------------------------------------------------
    def _is_fresh(self, updated_at: str) -> bool:
        """Return True if data is newer than the allowed max cache age."""
        updated = datetime.fromisoformat(updated_at)
        return (datetime.utcnow() - updated) < self.max_age

    def _build_url(self, endpoint: str, symbol: str, extra: str = "") -> str:
        """Create full API endpoint URL."""
        extra = ("&" + extra.lstrip("&")) if extra else ""
        return f"{self.base_url}/{endpoint}?symbol={symbol}&apikey={self.api_key}{extra}"

    # -------------------------------------------------------
    # Main Loader
    # -------------------------------------------------------
    def load(
        self,
        symbol: str,
        endpoint: str,
        model: Type[Any],
        limit: Optional[int] = None,
        extra_params: str = "",
        ttl_days: int = 3,
    ) -> List[Any]:
        """
        Load a dataset for a symbol:
        - Check DynamoDB cache
        - If stale or missing → call API
        - Parse with Pydantic
        - Return list of model instances
        """

        # --------------------------
        # Build extra API params
        # --------------------------
        if limit:
            extra_params += f"&limit={limit}"

        # --------------------------
        # 1. Try DynamoDB cache
        # --------------------------
        response = self.table.get_item(
            Key={
                "symbol": symbol,      # PK
                "dataset": endpoint,   # SK
            }
        )

        item = response.get("Item")

        if item and self._is_fresh(item["updated_at"]):
            print(f"[CACHE HIT] {symbol}/{endpoint}")

            return [model(**entry) for entry in item["data"]]

        print(f"[CACHE MISS] Fetching {symbol}/{endpoint} from FMP API…")

        # --------------------------
        # 2. Call external API
        # --------------------------
        url = self._build_url(endpoint, symbol, extra_params)
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        json_data = r.json()

        # --------------------------
        # 3. Convert to Pydantic models
        # --------------------------
        records = [model(**row) for row in json_data]
        print(f"[RECORDS] Returned from FMP API…")

        # --------------------------
        # 4. Store in DynamoDB
        # --------------------------
        ttl_value = int((datetime.utcnow() + timedelta(days=ttl_days)).timestamp())

        self.table.put_item(
            Item={
                "symbol": symbol,
                "dataset": endpoint,
                "updated_at": datetime.utcnow().isoformat(),
                "data": [rec.dict() for rec in records],
                "ttl": ttl_value,
            }
        )

        return records
