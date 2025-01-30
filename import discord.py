import os

# FFmpeg 실행 파일 경로 설정 (실제 설치 경로에 맞게 변경)
FFMPEG_PATH = r"C:\Users\eahnb\Downloads\ffmpeg-7.1-essentials_build (1)\ffmpeg-7.1-essentials_build\bin\ffmpeg.exe"

# Python 환경 변수(PATH)에 FFmpeg 경로 추가
os.environ["PATH"] += os.pathsep + os.path.dirname(FFMPEG_PATH)


import discord
from discord.ext import commands
import yt_dlp
import asyncio
import os

intents = discord.Intents.default()
intents.message_content = True  # 메시지 읽기 허용
intents.voice_states = True  # 음성 관련 이벤트 허용
intents.guilds = True  # 서버 관련 이벤트 허용

bot = commands.Bot(command_prefix="!", intents=intents)

# 각 서버별 음악 대기열 저장
music_queue = {}

@bot.event
async def on_ready():
    print(f'✅ {bot.user} 노래봇이 준비되었습니다!')

# ✅ 유튜브에서 노래를 검색하고 다운로드
def search_youtube(query):
    ydl_opts = {
        'format': 'bestaudio/best',
        'noplaylist': True,
        'quiet': True,
        'default_search': 'ytsearch1',
        'extract_flat': False
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(query, download=False)
            if 'entries' in info and len(info['entries']) > 0:
                return info['entries'][0]['url']
            elif 'url' in info:
                return info['url']
            else:
                print("❌ 유튜브 검색 결과가 없습니다.")
                return None
        except Exception as e:
            print(f"❌ 유튜브 검색 오류: {e}")
            return None

# ✅ 음악 재생 기능
@bot.command()
async def 재생(ctx, *, query: str):
    voice_channel = ctx.author.voice
    if not voice_channel:
        await ctx.send("❌ 먼저 음성 채널에 접속하세요!")
        return

    guild_id = ctx.guild.id
    voice_client = discord.utils.get(bot.voice_clients, guild=ctx.guild)

    if guild_id not in music_queue:
        music_queue[guild_id] = []

    url = search_youtube(query)
    if not url:
        await ctx.send("❌ 유튜브에서 노래를 찾을 수 없습니다.")
        return

    music_queue[guild_id].append(url)

    if not voice_client or not voice_client.is_connected():
        voice_client = await voice_channel.channel.connect()

    if not voice_client.is_playing():
        await play_next(ctx, voice_client)

import discord

async def play_next(ctx, voice_client):
    guild_id = ctx.guild.id
    if len(music_queue[guild_id]) > 0:
        url = music_queue[guild_id].pop(0)

        ffmpeg_options = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn'}


        ydl_opts = {
            'format': 'bestaudio/best',
            'quiet': True
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                audio_url = info.get('url')

                if not audio_url:
                    await ctx.send("❌ 유튜브에서 오디오 스트림을 찾을 수 없습니다.")
                    return

                # ✅ 유튜브 영상 정보 가져오기
                title = info.get('title', '알 수 없는 제목')
                uploader = info.get('uploader', '알 수 없는 채널')
                thumbnail = info.get('thumbnail', '')  # 썸네일 URL
                video_url = info.get('webpage_url', url)  # 원본 영상 URL

                voice_client.stop()
                voice_client.play(discord.FFmpegPCMAudio(audio_url, **ffmpeg_options), after=lambda e: asyncio.run_coroutine_threadsafe(play_next(ctx, voice_client), bot.loop))

                # ✅ "선욱은 탈모"를 강조하는 메시지 (세 줄 반복)
                bold_text = "**# 선욱은 탈모 #**\n" * 3  # ✅ 3번 반복하여 강조

                # ✅ 임베드(embed) 메시지 생성
                embed = discord.Embed(
                    title=f"🎵 현재 재생 중: {title}",
                    url=video_url,
                    description=f"📺 **채널:** {uploader}\n\n{bold_text}",
                    color=discord.Color.blue()
                )
                embed.set_thumbnail(url=thumbnail)  # ✅ 썸네일 추가
                embed.set_footer(text="디스코드 노래봇 🎶")

                await ctx.send(embed=embed)  # ✅ 임베드 메시지 전송

        except Exception as e:
            await ctx.send(f"❌ 음악을 재생하는 중 오류가 발생했습니다: `{str(e)}`")
            print(f"❌ 음악 재생 오류: {e}")



# ✅ 일시정지 기능
@bot.command()
async def 일시정지(ctx):
    voice_client = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    if voice_client and voice_client.is_playing():
        voice_client.pause()
        await ctx.send("⏸ 음악을 일시정지했습니다.")

# ✅ 다시재생 기능
@bot.command()
async def 다시재생(ctx):
    voice_client = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    if voice_client and voice_client.is_paused():
        voice_client.resume()
        await ctx.send("▶ 음악을 다시 재생합니다.")

# ✅ 건너뛰기 기능
@bot.command()
async def 건너뛰기(ctx):
    voice_client = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    if voice_client and voice_client.is_playing():
        voice_client.stop()
        await ctx.send("⏩ 음악을 건너뛰었습니다!")
        await play_next(ctx, voice_client)

# ✅ 정지 기능
@bot.command()
async def 정지(ctx):
    voice_client = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    if voice_client:
        await voice_client.disconnect()
        music_queue.pop(ctx.guild.id, None)
        await ctx.send("🛑 노래를 정지하고 음성 채널에서 나갑니다.")

# ✅ 대기열 확인 기능
@bot.command()
async def 대기열(ctx):
    guild_id = ctx.guild.id
    if guild_id not in music_queue or len(music_queue[guild_id]) == 0:
        await ctx.send("📭 현재 대기 중인 노래가 없습니다.")
    else:
        queue_message = "\n".join([f"{idx + 1}. {url}" for idx, url in enumerate(music_queue[guild_id])])
        await ctx.send(f"🎶 현재 대기열:\n{queue_message}")
@bot.command()
async def 도움말(ctx):
    help_message = """
    **🎵 노래봇 명령어 안내 🎵**
    
    🔹 `!재생 (노래 제목 또는 유튜브 링크)` → 유튜브에서 노래 검색 후 재생
    🔹 `!일시정지` → 현재 노래를 일시정지
    🔹 `!다시재생` → 일시정지된 노래 다시 재생
    🔹 `!건너뛰기` → 현재 노래 건너뛰기
    🔹 `!정지` → 모든 노래를 정지하고 음성 채널에서 나감
    🔹 `!대기열` → 현재 대기열 목록 확인

    🔥 노래를 틀 때마다 "선욱은 탈모"가 자동으로 출력됩니다.
    """
    await ctx.send(help_message)

# ✅ 봇 실행 (async 버전)
import asyncio

async def main():
    async with bot:
        await bot.start("MTMzNDU0NTk3NjM0MTQzMDM4Mw.GvLF5l.OrDaCYMcQgMcTwAtg4yDVkgjwA6o18u73SMy6g")

asyncio.run(main())
