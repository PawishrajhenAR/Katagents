import ssl

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from config import settings


def _connect_args(url: str) -> dict:
    if "supabase.co" in url:
        # Session pooler TLS fails strict CA verification on some Linux/pyenv installs.
        return {"ssl": "require"}
    if "localhost" in url or "127.0.0.1" in url:
        return {}
    return {"ssl": ssl.create_default_context()}


def _create_engine():
    kwargs: dict = {
        "echo": False,
        "pool_pre_ping": True,
        "pool_size": 5,
        "max_overflow": 10,
        "pool_recycle": 300,
        "pool_timeout": 30,
    }
    url = settings.database_url
    connect_args = _connect_args(url)
    if connect_args:
        kwargs["connect_args"] = connect_args
    return create_async_engine(url, **kwargs)


engine = _create_engine()
async_session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_db():
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
