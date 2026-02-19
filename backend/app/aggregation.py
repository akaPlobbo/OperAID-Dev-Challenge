"""Live aggregation with Polars."""
from datetime import datetime, timedelta, timezone
from typing import Any

import polars as pl


class Aggregator:
    """Real-time aggregation per machine ID and scrap index."""

    def __init__(self, window_seconds: int = 60) -> None:
        """Initialize aggregator with time window in seconds."""
        self.window_seconds = window_seconds
        self.rows: list[dict[str, Any]] = []

    def add(self, payload: dict[str, Any]) -> None:
        """Add incoming message to aggregation buffer.
        
        Args:
            payload: Message payload containing machine data
        """
       
        machine_id = payload.get("machineId") or payload.get("maschinenId")
        scrap_index = payload.get("scrapIndex") or payload.get("scrapeIndex")
        value = payload.get("value")
        timestamp = payload.get("timestamp") or payload.get("zeitstempel")

        if machine_id is None or scrap_index is None or value is None:
            return

       
        if isinstance(timestamp, datetime):
            parsed_timestamp = timestamp if timestamp.tzinfo else timestamp.replace(tzinfo=timezone.utc)
        elif isinstance(timestamp, str):
            parsed_timestamp = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        else:
            parsed_timestamp = datetime.now(timezone.utc)

        self.rows.append({
            "maschinenId": machine_id,
            "scrapIndex": scrap_index,
            "value": float(value),
            "zeitstempel": parsed_timestamp
        })

    def aggregate(self) -> pl.DataFrame:
        """Calculate sum and average for last N seconds.
        
        Returns:
            DataFrame with aggregated results per machine/index combination
        """
        if not self.rows:
            return pl.DataFrame()

        now = datetime.now(timezone.utc)
        cutoff = now - timedelta(seconds=self.window_seconds)

        df = pl.DataFrame(self.rows)
        recent = df.filter(pl.col("zeitstempel") >= cutoff)

        self.rows = recent.to_dicts()

        if recent.height == 0:
            return pl.DataFrame()

        return (
            recent.group_by(["maschinenId", "scrapIndex"])
            .agg([
                pl.col("value").sum().alias("sumLast60s"),
                pl.col("value").mean().alias("avgLast60s"),
                pl.col("value").count().alias("messageCount")
            ])
            .sort(["maschinenId", "scrapIndex"])
        )
