from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import yt_dlp

app = FastAPI()

class TikTokRequest(BaseModel):
    url: str

@app.get("/")
def read_root():
    return {
        "status": "ok",
        "message": "TikTok Video Downloader API is running",
        "usage": "POST /download with JSON body: {\"url\": \"<tiktok_url>\"}"
    }

@app.post("/download")
async def download_tiktok(request: TikTokRequest):
    url = request.url
    
    # ලින්ක් එක TikTok එකක්ද කියලා චෙක් කරනවා
    if "tiktok.com" not in url:
        raise HTTPException(status_code=400, detail="Please provide a valid TikTok URL")

    ydl_opts = {
        'format': 'best',
        'quiet': True,
        'no_warnings': True,
        'noplaylist': True,
        # 'cookiefile': 'cookies.txt', # TikTok එකෙන් block කරොත් මේක අයින් කරන්න
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)

            if 'entries' in info:
                info = info['entries'][0]

            video_url = info.get('url')
            title = info.get('title', 'TikTok Video')

            if not video_url:
                raise HTTPException(status_code=404, detail="Could not extract video URL. It might be a photo slideshow.")

            return {
                "status": "success",
                "title": title,
                "download_url": video_url
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")
