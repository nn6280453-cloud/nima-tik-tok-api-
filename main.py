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
            title = info.get('title', 'TikTok Video')
            author = info.get('uploader', 'Unknown Author')
            description = info.get('description', 'No caption')

            if not video_url:
                raise HTTPException(status_code=404, detail="Could not extract video URL. It might be a photo slideshow.")

            # සිංහල අකුරු සහ emojis අයින් කරලා, ඉංග්‍රීසි අකුරු විතරක් තියාගන්නවා (Headers වලට දාන්න)
            safe_title = title.encode('ascii', 'ignore').decode('ascii').strip() or "tiktok_video"
            safe_author = author.encode('ascii', 'ignore').decode('ascii').strip() or "unknown_author"
            safe_desc = description.encode('ascii', 'ignore').decode('ascii').strip() or "No caption"

            # TikTok එකට යවන්න headers එකට User-Agent එකක් එකතු කරනවා (Block වෙන එක නවත්තන්න)
            headers['User-Agent'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'

            async def video_stream():
                async with httpx.AsyncClient() as client:
                    async with client.stream("GET", video_url, headers=headers) as response:
                        # TikTok එකෙන් error එකක් ආවොත් ඒක handle කරනවා
                        if response.status_code != 200:
                            raise HTTPException(status_code=response.status_code, detail="TikTok blocked the download")
                        async for chunk in response.aiter_bytes():
                            yield chunk

            # වීඩියෝ එකත් එක්කම Title, Author, Description ටිකත් Headers වලින් යවනවා
            custom_headers = {
                "Content-Disposition": f"attachment; filename={safe_title}.mp4",
                "X-Video-Title": safe_title,
                "X-Video-Author": safe_author,
                "X-Video-Description": safe_desc
            }

            return StreamingResponse(
                video_stream(), 
                media_type="video/mp4",
                headers=custom_headers
            )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")
