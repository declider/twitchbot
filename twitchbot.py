from twitchio.ext import commands
import requests, os, json, time
from dotenv import load_dotenv
from datetime import timedelta
from keep_alive import keep_alive

load_dotenv()


class Bot(commands.Bot):

    def __init__(self):
        super().__init__(token=os.getenv("TWITCH_TOKEN"),
                         prefix='!',
                         initial_channels=['segall', "roadhouse", "declider"])

        self.data = {}

    async def event_ready(self):
        print(f'Logged in as | {self.nick}')
        for channel in self.connected_channels:
            self.data[channel.name] = {
                "rating": {
                    "status": False,
                    "users": [],
                    "scores": []
                }
            }
        self.start = time.time()

    async def event_message(self, message):
        ch = message.channel.name
        if message.echo:
            return

        if self.data[ch]["rating"]["status"]:
            if message.author.id not in self.data[ch]["rating"]["users"]:
                score = message.content.split(" ")[0].strip()
                if score.isdigit():
                    if int(score) >= 0 and int(score) <= 10:
                        self.data[ch]["rating"]["scores"].append(int(score))
                        self.data[ch]["rating"]["users"].append(
                            message.author.id)

        await self.handle_commands(message)

    @commands.cooldown(rate=1, per=600, bucket=commands.Bucket.channel)
    @commands.command(name="нарисуй", aliases=["рисунок"])
    async def draw(self, ctx: commands.Context):
        emote = ctx.message.content.split(" ")[-1]
        url = "https://api.thefyrewire.com/twitch/pastebin/6itDyhwk?filter=" + emote
        r = requests.get(url)

        if len(r.text) >= 100:
            await ctx.send(r.text[0:499])
        else:
            await ctx.command._cooldowns[0].reset()

    @commands.command(name="rating", aliases=["рейтинг", "оценка"])
    async def rating(self, ctx: commands.Context):

        ch = ctx.channel.name

        if not ctx.author.is_mod and ctx.author.name != "declider":
            return

        if self.data[ch]["rating"]["status"]:
            self.data[ch]["rating"]["status"] = False
            if len(self.data[ch]["rating"]["scores"]) != 0:
                rating = sum(self.data[ch]["rating"]["scores"])
                length = len(self.data[ch]["rating"]["scores"])
                score = round(rating / length, 2)
                await ctx.send(
                    f"/announce Чат поставил оценку {score}! Всего оценок: {length}"
                )
                self.data[ch]["rating"]["scores"].clear()
                self.data[ch]["rating"]["users"].clear()
            else:
                await ctx.send("Оценивание отключено.")

        else:
            self.data[ch]["rating"]["status"] = True
            await ctx.send(
                "/announce Началось оценивание по шкале от 1 до 10! Пиши свою оценку в чат."
            )

    @commands.cooldown(rate=1, per=60, bucket=commands.Bucket.channel)
    @commands.command(name="emotecount", aliases=["countemote"])
    async def emotecount(self, ctx: commands.Context):

        user = await ctx.channel.user()
        ch = ctx.channel.name

        bttv = json.loads(
            requests.get(
                f"https://api.betterttv.net/3/cached/users/twitch/{user.id}").
            text)
        bttv = len(bttv['channelEmotes']) + len(bttv['sharedEmotes'])

        ffz = json.loads(
            requests.get(
                f'https://api.betterttv.net/3/cached/frankerfacez/users/twitch/{user.id}'
            ).text)
        ffz = len(ffz)

        seventv = json.loads(
            requests.get(
                f'https://api.7tv.app/v2/users/{user.id}/emotes').text)
        seventv = len(seventv)

        emotesum = bttv + ffz + seventv

        await ctx.send(
            f"На канале {ch} всего {emotesum} смайлов: {bttv} в BTTV, {ffz} в FFZ, {seventv} в 7TV."
        )

    @commands.command(name="ping")
    async def ping(self, ctx: commands.Context):
        end = round(time.time() - self.start)
        await ctx.send(f"Бот работает {timedelta(seconds=end)}")


bot = Bot()
keep_alive()
bot.run()
