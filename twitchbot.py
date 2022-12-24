from twitchio.ext import commands
import requests, os, json
from dotenv import load_dotenv

load_dotenv()

class Bot(commands.Bot):

    def __init__(self):
        super().__init__(token=os.getenv("TWITCH_TOKEN"), prefix='?', initial_channels=['segall'])

        self.rating_users = []
        self.rating_scores = []
        self.rating_running = False



    async def event_ready(self):
        print(f'Logged in as | {self.nick}')



    async def event_message(self, message):
        if message.echo:
            return

        if self.rating_running:
            if message.author.id not in self.rating_users:
                score = message.content.split(" ")[0].strip()
                if score.isdigit():
                    if int(score)>=0 and int(score)<=10:
                        self.rating_scores.append(int(score))
                        self.rating_users.append(message.author.id)

        await self.handle_commands(message)

        
        
    @commands.cooldown(rate=1, per=600, bucket=commands.Bucket.channel)
    @commands.command(name="нарисуй", aliases=["рисунок"])
    async def draw(self, ctx: commands.Context):
        emote = ctx.message.content.split(" ")[-1]
        url = "https://api.thefyrewire.com/twitch/pastebin/6itDyhwk?filter="+emote
        r = requests.get(url)

        if len(r.text)>=100:
            await ctx.send(r.text[0:500])
        else:
            await ctx.command._cooldowns[0].reset()



    @commands.command(name="rating", aliases=["рейтинг","оценка"])
    async def rating(self, ctx: commands.Context):

        if not ctx.author.is_mod and not ctx.author.is_vip and ctx.author.name!="declider":
            # ctx.command._cooldowns[0].reset()
            return

        if self.rating_running:
            self.rating_running = False
            if len(self.rating_scores)!=0:
                rating = sum(self.rating_scores)
                score = round(rating/len(self.rating_scores), 2)
                await ctx.send(f"/announce Чат поставил оценку {score}! Всего оценок: {len(self.rating_scores)}")
                self.rating_scores.clear()
                self.rating_users.clear()
            else:
                await ctx.send(f"Оценивание отключено.")
            

        else:
            self.rating_running = True
            await ctx.send("/announce Началось оценивание по шкале от 1 до 10! Пиши свою оценку в чат.")
    


    @commands.cooldown(rate=1, per=60, bucket=commands.Bucket.channel)
    @commands.command(name="emotecount", aliases=["countemote"])
    async def emotecount(self, ctx: commands.Context):

        targetId = os.getenv("DEFAULT_USER_ID")

        bttv = json.loads(requests.get("https://api.betterttv.net/3/cached/users/twitch/"+targetId).text)
        bttvCE = len(bttv['channelEmotes'])
        bttvSE = len(bttv['sharedEmotes'])

        ffz = json.loads(requests.get('https://api.betterttv.net/3/cached/frankerfacez/users/twitch/'+targetId).text)
        ffz = len(ffz)

        seventv = json.loads(requests.get('https://api.7tv.app/v2/users/'+targetId+'/emotes').text)
        seventv = len(seventv)

        emotesum = bttvCE + bttvSE + ffz + seventv

        await ctx.send(f"На канале segall всего {emotesum} смайлов: {bttvCE}/{bttvSE} личных/общих в BTTV, {ffz} в FFZ, {seventv} в 7TV.")



bot = Bot()
bot.run()
