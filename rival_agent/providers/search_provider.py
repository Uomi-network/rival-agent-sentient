from tavily import AsyncTavilyClient

class SearchProvider:
    def __init__(
            self,
            api_key: str
    ):
        """Initialize the search provider with Tavily API key."""
        self.client = AsyncTavilyClient(api_key=api_key)

    async def search(
            self,
            query: str
    ) -> dict:
        """Search the internet for information using Tavily API."""
        results = await self.client.search(query)
        return results
