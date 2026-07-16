from motor.motor_asyncio import AsyncIOMotorClient
from app.config.settings import settings

_client: AsyncIOMotorClient | None = None


def get_client() -> AsyncIOMotorClient:
    global _client
    if _client is None:
        _client = AsyncIOMotorClient(settings.MONGO_URI)
    return _client


def get_db():
    return get_client()[settings.MONGO_DB_NAME]


# Collection shortcuts
def traffic_logs():
    return get_db()["traffic_logs"]


def analysis_results():
    return get_db()["analysis_results"]


def ip_activity():
    return get_db()["ip_activity"]


def vulnerability_reports():
    return get_db()["vulnerability_reports"]


def alerts():
    return get_db()["alerts"]


def users():
    return get_db()["users"]


def blockchain_batches():
    return get_db()["blockchain_batches"]


async def ensure_indexes():
    await traffic_logs().create_index("timestamp")
    await traffic_logs().create_index("ip")
    await traffic_logs().create_index("risk_score")
    await analysis_results().create_index("traffic_id")
    await ip_activity().create_index("ip", unique=True)
    await alerts().create_index("timestamp")
