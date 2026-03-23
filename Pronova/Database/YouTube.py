import aiohttp
import time

from .Core import db


_session = None


async def get_session():
    global _session
    if _session is None or _session.closed:
        timeout = aiohttp.ClientTimeout(total=8)
        _session = aiohttp.ClientSession(timeout=timeout)
    return _session


async def is_stream_valid(url):
    try:
        session = await get_session()

        # ✅ Try HEAD first
        try:
            async with session.head(url, allow_redirects=True) as resp:
                if resp.status == 200:
                    return True
        except:
            pass

        headers = {
            "Range": "bytes=0-512",
            "User-Agent": "Mozilla/5.0"
        }

        async with session.get(url, headers=headers, allow_redirects=True) as resp:

            if resp.status not in (200, 206):
                return False

            content_type = resp.headers.get("Content-Type", "")

            if "audio" not in content_type and "video" not in content_type:
                return False

            # REAL DATA CHECK
            chunk = await resp.content.read(512)
            if not chunk:
                return False

            return True

    except Exception as e:
        print("Stream check error:", e)
        return False


async def get_stream_cache(key):
    try:
        data = await db.yt_stream_cache.find_one({"_id": key})
        if not data:
            return None
        return data.get("stream")
    except Exception:
        return None


async def set_stream_cache(key, stream):
    try:
        await db.yt_stream_cache.update_one(
            {"_id": key},
            {
                "$set": {
                    "stream": stream,
                    "created_at": time.time()
                }
            },
            upsert=True
        )
    except Exception:
        pass


async def get_search_cache(key):
    try:
        data = await db.yt_search_cache.find_one({"_id": key})
        if not data:
            return None
        return data.get("data")
    except Exception:
        return None


async def set_search_cache(key, data):
    try:
        await db.yt_search_cache.update_one(
            {"_id": key},
            {
                "$set": {
                    "data": data,
                    "created_at": time.time()
                }
            },
            upsert=True
        )
    except Exception:
        pass



async def close_session():
    global _session
    if _session and not _session.closed:
        await _session.close()
