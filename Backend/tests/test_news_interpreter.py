from app.utils.helpers import news_interpreter
import time

news_text = """
(Bloomberg) -- Cathie Wood’s retail fans are tiptoeing back into her flagship product, potentially putting an end to a 14-month exodus.

Most Read from Bloomberg

Granted, it was just one day. But on Monday, amid a stock-market rout that drove the tech-heavy Nasdaq 100 Index to its lowest level since September, investors added nearly $300 million to the ARK Innovation ETF (ticker ARKK). It was the biggest daily inflow for the ETF in two years and it now leaves the fund up for both March and 2025 in terms of assets under management.

The ETF was hardly spared amid Monday’s equities slump. It tumbled about 9%, the worst session since 2022 for the $5 billion fund, which has seen its assets crater from a peak of $28 billion in 2021. The ETF is down roughly 15% this year, badly trailing the almost 6% drop in the S&P 500 Index. Stocks overall — and in particular the types of tech shares that Wood typically favors — have been clobbered by an intensifying trade war, signs of a softening economy and the Trump administration’s culling of the federal workforce.

Retail investors seem to be stepping back in after the tech sector’s slide this year, said Matt Maley, chief market strategist at Miller Tabak + Co. The “buy-the-dip” mentality of adding to investments on big down days is still strong for many, and that’s especially the case for those looking for exposure to Tesla Inc., which is ARKK’s largest holding, he said. The EV maker’s shares are down more than 40% this year amid concern around demand for its cars.

A spokesperson for Wood’s firm didn’t respond to a request for comment.

Her army of retail followers had consistently added to ARKK during the early pandemic years, with multi-billion-dollar monthly inflows not uncommon in 2021. But the enthusiasm around the fund has waned since her flagship strategy reached the pinnacle of its popularity in the cheap-money era. In fact, it hasn’t seen a monthly inflow since December 2023, data compiled by Bloomberg show.

Part of what catapulted Wood to fame was her bold calls on speculative tech firms, which comprise many of her holdings. An analysis by DataTrek Research LLC shows that a number of ARKK’s 10 largest positions in November 2021 remain at the top of her leaderboard — including Tesla, Roku Inc., Coinbase Global Inc. and Shopify Inc.
"""

start = time.time()
print(news_interpreter(news_text, 100))
end = time.time()

print(f"Execution time: {end - start} seconds")
