from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import yt_dlp
import httpx
from fastapi.responses import StreamingResponse

app = FastAPI()

class TikTokRequest(BaseModel):
    url: str

@app.get("/")
def read_root():
    return {
        "status": "ok",
        "message": "TikTok Video Downloader API is running (Proxy Mode)",
        "usage": "POST /download with JSON body: {\"url\": \"<tiktok_url>\"} to download the video directly."
    }

@app.post("/download")
async def download_tiktok(request: TikTokRequest):
    url = request.url
    if "tiktok.com" not in url:
        raise HTTPException(status_code=400, detail="Please provide a valid TikTok URL")

    ydl_opts = {
        'format': 'best',
        'quiet': True,
        'no_warnings': True,
        'noplaylist': True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            if 'entries' in info:
                info = info['entries'][0]

            video_url = info.get('url')
            headers = info.get('http_headers', {})
            title = info.get('title', 'tiktok_video')

            if not video_url:
                raise HTTPException(status_code=404, detail="Could not extract video URL. It might be a photo slideshow.")

            async def video_stream():
                async with httpx.AsyncClient() as client:
                    async with client.stream("GET", video_url, headers=headers) as response:
                        async for chunk in response.aiter_bytes():
                            yield chunk

            safe_title = "".join([c for c in title if c.isalpha() or c.isdigit() or c==' ' or c=='.']).rstrip()
            
            return StreamingResponse(
                video_stream(), 
                media_type="video/mp4",
                headers={"Content-Disposition": f"attachment; filename={safe_title}.mp4"}
            )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")
