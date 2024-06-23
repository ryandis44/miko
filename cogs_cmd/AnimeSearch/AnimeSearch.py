'''
Backend logic class for AnimeSearch
'''



import discord
import logging
import requests

from Database.MikoCore import MikoCore
from discord.ext import commands
LOGGER  = logging.getLogger()

class AnimeSearchView(discord.ui.View):
    
    def __init__(self, original_interaction: discord.Interaction, search: str) -> None:
        self.original_interaction: discord.Interaction = original_interaction
        self.__search: str = search
        self.mc: MikoCore = MikoCore()
        super().__init__(timeout=self.mc.tunables('GLOBAL_VIEW_TIMEOUT'))
        self.msg: discord.Message = None
    
    
    
    async def ainit(self) -> None:
        self.msg = await self.original_interaction.original_response()
        try: await self.search()
        except Exception as e: LOGGER.error(f"Error searching for anime: {e}")
    
    
    
    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return interaction.user.id == self.original_interaction.user.id

    
    
    async def on_timeout(self) -> None:
        try:
            await self.msg.edit(
                content=self.mc.tunables('GLOBAL_VIEW_TIMEOUT_MESSAGE'),
                view=None
            )
        except: pass
        
    
    
    async def search(self, interaction: discord.Interaction = None, srch: str = None) -> None:
        await self.mc.user_ainit(user=self.original_interaction.user if interaction is None else interaction.user, client=self.original_interaction.client)
        await self.mc.user.increment_statistic('ANIMES_SEARCHED')
        
        if srch is not None:
            self.__search = srch
            await self.msg.edit(
                content=self.mc.tunables('LOADING_EMOJI'),
                embed=None,
                view=None
            )
        
        data = self.__fetch_anime_results()
        self.clear_items()
        if data == 'Error' or len(data) == 0:
            self.add_item(SearchButton())
            await self.msg.edit(
                content="No results found. Please try again!",
                embed=None,
                view=self
            )
            return
        elif len(data) == 1:
            embed = self.display_result(data, 0)
        else:
            embed = self.__display_options(data)
            self.add_item(SelectAnime(data))
            
        self.add_item(SearchButton())
        await self.msg.edit(embed=embed, view=self, content=None)
        
    
    
    def display_result(self, data: dict, index: int) -> discord.Embed:
        temp = []

        
        if data[index]['title']['english'] == None: temp.append(f"**__{data[index]['title']['romaji']}__**:\n")
        else: temp.append(f"**__{data[index]['title']['english']}__**:\n")
        
        temp.append(
            f"> :100: **Average Score**: {data[index]['averageScore']}\n"
            f"> :chart_with_upwards_trend: **Popularity**: {int(data[index]['popularity']):,} fans\n"
            f"> :date: **Season Aired**: {data[index]['season']} {data[index]['seasonYear']}\n"
            f"> :telescope: **Genres**: {', '.join(data[index]['genres'])}\n"
            f"> :1234: **Episodes**: {data[index]['episodes']}\n"
            f"> :underage: **Adult Content**: {data[index]['isAdult']}\n"
        )
        
        if data[index]['nextAiringEpisode'] == None: temp.append(f"> :point_right: **Status**: {data[index]['status']}\n")
        else: temp.append(f"> :point_right: **Next Airing Episode**: Episode {data[index]['nextAiringEpisode']['episode']} <t:{data[index]['nextAiringEpisode']['airingAt']}:R>\n")
        
        embed = discord.Embed(
            color=self.mc.tunables('GLOBAL_EMBED_COLOR'),
            description=''.join(temp)
        )
        
        embed.set_author(
            icon_url=self.mc.user.miko_avatar,
            name="Anime Search"
        )

        embed.set_image(url=data[index]['coverImage']['extraLarge'])
        return embed

    
    
    def __display_options(self, data: dict) -> discord.Embed:
        temp = []
        
        for i in range(0, len(data)):
            if data[i]['title']['english'] == None: temp.append(f"**{i+1}.** {data[i]['title']['romaji']}")
            else: temp.append(f"**{i+1}.** {data[i]['title']['english']}")
        
        description_text = '[{}]'.format('\n'.join(temp))
        
        embed = discord.Embed(
            color = self.mc.tunables('GLOBAL_EMBED_COLOR'),
            description = description_text[1:-1]
        )
        
        embed.set_author(
            icon_url=self.mc.user.miko_avatar,
            name=f"Anime Search Results for {self.__search}"
        )
        
        return embed



    def get_index(self, data: dict, name: str) -> int:
        for index, anime in enumerate(data):
            if anime['title']['english'] == name or anime['title']['romaji'] == name:
                return index
        return -1

        
    
    # Function provided by AniList API
    def __fetch_anime_results(self) -> None:
        query = '''
        query ($search: String) {
            Page(page: 1, perPage: 10) {
                pageInfo {
                    total
                    currentPage
                    lastPage
                    hasNextPage
                }
                media(search: $search, type: ANIME, sort:[POPULARITY_DESC]) {
                    title {
                        romaji
                        english
                    }
                    averageScore
                    popularity
                    season
                    seasonYear
                    status
                    genres
                    coverImage {
                        extraLarge
                    }
                    episodes
                    isAdult
                    nextAiringEpisode {
                        airingAt
                        timeUntilAiring
                        episode
                    }
                }
            }
        }
        '''
        variables = {
            'search': self.__search
        }
        url = 'https://graphql.anilist.co'
        try:
            response = requests.post(url, json={'query': query, 'variables': variables})
            return response.json()['data']['Page']['media']
        except: return 'Error'



class SelectAnime(discord.ui.Select):
    def __init__(self, data: dict):
        self.data = data

        options = []
        for i in range(0, len(data)):
            if data[i]['title']['english'] == None:
                options.append(discord.SelectOption(label=f"{data[i]['title']['romaji']}"))
            else:
                options.append(discord.SelectOption(label=f"{data[i]['title']['english']}"))

        super().__init__(
            placeholder="Select an anime",
            min_values=1,
            max_values=1,
            options=options,
            row=1,
            custom_id="anime_selection",
            disabled=False
        )
    
    async def callback(self, interaction: discord.Interaction):
        await interaction.response.edit_message(
            embed=self.view.display_result(self.data, self.view.get_index(self.data, self.values[0])),
        )



class SearchButton(discord.ui.Button):

    def __init__(self):
        super().__init__(
            style=discord.ButtonStyle.gray,
            label=None,
            emoji="🔎",
            custom_id="asearch_button",
            row=2
        )
    
    async def callback(self, interaction: discord.Interaction) -> None:
        await interaction.response.send_modal(self.SearchModal(asearch=self.view))

    class SearchModal(discord.ui.Modal):

        def __init__(self, asearch: AnimeSearchView):
            super().__init__(title="Search for an anime", custom_id="asearch_modal")
            self.asearch = asearch

        anime = discord.ui.TextInput(
                label="Search for an anime:",
                placeholder="Attack on Titan",
                min_length=1,
                max_length=35
            )
        async def on_submit(self, interaction: discord.Interaction) -> None:
            await interaction.response.edit_message()
            await self.asearch.search(interaction=interaction, srch=self.anime.value)