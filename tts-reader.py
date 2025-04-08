import asyncio

from openai import AsyncOpenAI
from openai.helpers import LocalAudioPlayer

openai = AsyncOpenAI()

input = """Alright, alright, folks, welcome to the grandest online jewelry auction
this side of the internet—let's get you bidding!
Lookin' for dazzling diamonds, shimmering gold, or rare vintage pieces? Click
\"Browse Auctions\", and feast your eyes on the finest treasures up for grabs!
Spotted somethin' you fancy? Hit \"Place Bid\", enter your number—do I hear one
hundred, do I hear two? Keep your eye on that \"Current Bid\" 'cause competition's
heating up!\n\nWant it now? Click \"Buy It Now\", skip the wait, and make it
yours in a flash! When you win, just glide on over to \"Checkout\",
seal the deal, and that beauty's on its way!\n\nDon't blink, don't hesitate—these
gems move fast! Bid bold, bid smart, and may fortune shine on you! SOLD!"""

instructions = """Voice: Staccato, fast-paced, energetic, and rhythmic, with the
classic charm of a seasoned auctioneer.\n\nTone: Exciting, high-energy,
and persuasive, creating urgency and anticipation.\n\nDelivery: Rapid-fire
yet clear, with dynamic inflections to keep engagement high and momentum strong.
Pronunciation: Crisp and precise, with emphasis on key action words like bid, buy,
checkout, and sold to drive urgency."""


async def main() -> None:

    async with openai.audio.speech.with_streaming_response.create(
        model="gpt-4o-mini-tts",
        voice="verse",
        input=input,
        instructions=instructions,
        response_format="pcm",
    ) as response:
        await LocalAudioPlayer().play(response)


if __name__ == "__main__":
    asyncio.run(main())
