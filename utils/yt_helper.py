from yt_dlp import YoutubeDL
import asyncio
import logging

# Set up logging for debugging and error tracking
logger = logging.getLogger(__name__)

# Options for YoutubeDL to extract the best available audio
YDL_OPTIONS = {
    'format': 'bestaudio[ext=webm]/bestaudio/best', 
    'noplaylist': True, 
    'force-ipv4': True, 
    'extractor_args': {
        'youtube': {
            'skip': ['hls', 'dash', 'translated_subs'],  
            'player_skip': ['configs'],
        }
    },
    'postprocessors': [{
        'key': 'FFmpegExtractAudio', 
        'preferredcodec': 'opus',  
    }],
    'socket_timeout': 15,  
    'verbose': True  
}

"""Helper class to extract audio stream URLs from YouTube using yt-dlp."""
class YTDLHelper:
    
    """
        Extracts and processes audio information from a YouTube video URL.

        Args:
            url (str): The URL of the YouTube video.

        Returns:
            dict | None: A dictionary containing extracted info, or None if extraction fails.
    """
    @staticmethod
    async def extract_info(url):        
        try:
            with YoutubeDL(YDL_OPTIONS) as ydl:
                # Run extraction in a separate thread to avoid blocking the event loop
                info = await asyncio.to_thread(
                    ydl.extract_info, 
                    url, 
                    download=False  
                )
                
                logger.debug(f"Extracted Info: {info}")
                
                # If the extracted info is a playlist, return None (not supported in this version)
                if info.get('_type') == 'playlist':
                    logger.warning("Playlists are not supported.")
                    return None                    
                
                if not info or 'url' not in info:
                    logger.error("No valid URL found in extracted info.")
                    return None
                    
                return info
        except Exception as e:
            logger.error(f"YTDL Error: {str(e)}", exc_info=True) 
            return None