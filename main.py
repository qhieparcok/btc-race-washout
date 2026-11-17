#!/usr/bin/env python3
"""Washout recovery bot for the cbBTC 24-hour race.

The idea is simple, and it is the one that has won these races before:
most days, Bitcoin shakes out weak hands once and then spends the rest
of the day climbing back. This bot waits for that shakeout, buys the
first green minute after it, and then holds to the end of the window.
It trades at most once a day, so fees never eat the move, and it carries
one hard stop so a day that keeps falling can only cost it about 1.5%.

Rules, in plain terms:
  - A washout is a close 1.5% or more below the highest high of the last
    six hours. Nothing happens until one shows up.
  - Once a washout is on, the bot watches for the turn: the first close
    above the previous close. That is the buy, for the full cash balance.
  - After buying it holds. The only exit is the stop: if the position
    is ever worth 1.5% less than it cost, sell everything and stop for
    the day. Otherwise the position is flattened by the harness at the
    last close, as the rules describe.
  - No trade in the first two hours (the six-hour high needs history
    to mean anything) and none in the last two (a late entry has no
    time to recover).

Why these numbers: a full-size round trip costs about 35 bps in fees,
slippage and pool impact, so a trade has to catch a move well above
that to be worth it. A 1.5% washout is deep enough to be a real shakeout
rather than noise — a 1% dip fires too early, on the first shallow pullback,
and leaves the recovery on the table — and a 1.5% stop is wide enough
that ordinary hourly noise (about 0.5% a side) does not trigger it, while
still capping the loss on a day that falls apart. On the published dev
window this bot makes money on a single trade; on the four falling days
before it, the stop is what keeps the loss to a bad day rather than a
disaster.

Standard library only. No network, no clock, no files, no randomness:
the same bars always give the same orders.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "vendor"))
import makefun_bars

SYMBOL = "CBBTC"

# A close this far below the six-hour high counts as a washout.
WASHOUT_NUM, WASHOUT_DEN = 197, 200          # 1.5% below the high
HIGH_BARS = 360                              # six hours of one-minute bars
# The position is sold if it is ever worth this much less than it cost.
STOP_NUM, STOP_DEN = 197, 200                # 1.5% below cost
# How much history the bot wants before it trusts the four-hour high,
# and the last bar on which it will still open a trade.
MIN_BARS = 120
LAST_ENTRY_BAR = 1320
# A fill more than this past the close the order was decided on is
# refused rather than chased (one-minute moves never came close).
MAX_SLIPPAGE_BPS = 300


class WashoutBot:
    """Keeps the closes and highs it has seen and decides one trade."""

    def __init__(self):
        self.closes = []
        self.highs = []
        self.washout_low = None
        self.entries = 0

    def on_batch(self, state, batch):
        for bar in batch["bars"]:
            if bar["symbol"] != SYMBOL:
                continue
            self.closes.append(int(bar["c"]))
            self.highs.append(int(bar["h"]))
        if not self.closes:
            return []
        close = self.closes[-1]

        held = state.positions.get(SYMBOL)
        if held is not None:
            # Holding: the only way out is the stop, checked against cost
            # with integers so the decision is exact.
            value = state.value(SYMBOL, held.qty)
            if value * STOP_DEN <= held.cost * STOP_NUM:
                self.washout_low = None
                return [{"side": "sell", "symbol": SYMBOL, "qty": held.qty,
                         "max_slippage_bps": MAX_SLIPPAGE_BPS}]
            return []

        # Flat: look for the washout, then for the turn.
        if self.entries > 0:
            return []
        if len(self.closes) < MIN_BARS or state.seq > LAST_ENTRY_BAR:
            return []
        high = max(self.highs[-HIGH_BARS:])
        if self.washout_low is None:
            if close * WASHOUT_DEN <= high * WASHOUT_NUM:
                self.washout_low = close
            return []
        if close < self.washout_low:
            self.washout_low = close
        if len(self.closes) >= 2 and close > self.closes[-2]:
            self.entries += 1
            self.washout_low = None
            return [{"side": "buy", "symbol": SYMBOL,
                     "notional_quote_units": state.cash,
                     "max_slippage_bps": MAX_SLIPPAGE_BPS}]
        return []


def main():
    bot = WashoutBot()
    makefun_bars.run(bot.on_batch)


if __name__ == "__main__":
    main()
