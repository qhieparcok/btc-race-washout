# Washout Recovery Bot — cbBTC 24h Race

[![make.fun · btc-race-24h-20261117-0603](https://make.fun/badge/btc-race-24h-20261117-0603.svg)](https://make.fun/bounty/btc-race-24h-20261117-0603?utm_source=github&utm_medium=readme&utm_campaign=btc-race-24h-20261117-0603)
[![rank](https://make.fun/badge/btc-race-24h-20261117-0603/qhieparcok/btc-race-washout/rank.svg)](https://make.fun/bounty/btc-race-24h-20261117-0603/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=btc-race-24h-20261117-0603)
[![reward](https://make.fun/badge/btc-race-24h-20261117-0603/qhieparcok/btc-race-washout/reward.svg)](https://make.fun/bounty/btc-race-24h-20261117-0603?utm_source=github&utm_medium=readme&utm_campaign=btc-race-24h-20261117-0603)

A trading bot for make.fun's "Race a BTC trading bot live for 24 hours"
(`btc-race-24h-20261117-0603`). It trades Coinbase Wrapped BTC (cbBTC)
against USDC on one-minute on-chain bars, starting with $1,000 of paper
money, long only, no leverage.

## The idea

Most days, Bitcoin shakes out weak hands once and then spends the rest of
the day climbing back. This bot waits for that shakeout, buys the first
green minute after it, and holds to the end of the window. It trades at
most once a day, so fees never eat the move, and it carries one hard stop
so a day that keeps falling can only cost it about 1.5%.

This is the shape that has won these races before: the last five editions
were all won by one-or-two-trade dip buyers, not by bots that trade every
cross. Frequent trading loses here — a full-size round trip costs about
35 bps in fees, slippage and pool impact, while a typical one-minute move
is about 6 bps. So the bot is deliberately boring: one entry, one
possible exit, and silence the rest of the day.

## Rules

- **Washout:** a close 1.5% or more below the highest high of the last six
  hours. Nothing happens until one shows up.
- **Turn:** once a washout is on, the bot buys on the first close above
  the previous close, for the full cash balance.
- **Hold:** after buying, the only exit is the stop — if the position is
  ever worth 1.5% less than it cost, sell everything and stop for the
  day. Otherwise the position runs to the end of the window, where the
  harness flattens it at the last close.
- **Patience:** no trade in the first two hours (the six-hour high needs
  history to mean anything) and none in the last two (a late entry has no
  time to recover).

## Why these numbers

- A 1.5% washout is deep enough to be a real shakeout rather than noise,
  and shallow enough to actually happen on most days. A 1% washout was
  tested and fires too early, on the first shallow pullback, leaving the
  recovery on the table (dev +$3.59 instead of +$8.46).
- A 1.5% stop is wide enough that ordinary hourly noise (about 0.5% a
  side) does not trigger it, while still capping the loss on a day that
  falls apart. A tighter stop was tested and kept firing on noise.
- Full size on the single entry: with only one round trip a day, the
  impact cost is worth paying for a 1%+ move.

## Results on the published dev window

Graded locally with the kit's own replay (exact fill model: 4 bps fee,
2 bps slippage, constant-product impact against each bar's pool depth):

| | |
|---|---|
| Net PnL | **+$8.46** (0.85%) |
| Trades | 1 (buy at bar 371, held to the end) |
| Max drawdown | 2.12% (limit 25%) |
| Fees paid | $0.80 |
| Dev gate | Pass (net PnL above $0) |

For comparison on the same window: buy-and-hold +$1.07, momentum
baseline +$2.45, EMA-cross baseline −$106.21 (68 trades), RSI-Bollinger
−$24.25, ADX-momentum −$32.66.

The bot was also checked on slices of the same window, to make sure the
result is not a one-bar accident: the first 12 hours alone give +$8.62,
the last 12 hours +$2.50, and the window played backwards (a down day)
loses $4.22, bounded by the stop. A shallower 1% washout was tested on
the same slices and is worse or equal on every one of them (dev +$3.59,
first half +$3.75, last half −$3.94, reversed −$4.45), which is why the
deeper washout is the shipped version. The risk that remains is a race
day with no 1.5% washout at all: then the bot makes no trade, and an
entry with no trade ranks below every entry that traded.

## Files

- `main.py` — the bot (Python 3.13, standard library only).
- `vendor/makefun_bars.py` — a byte-identical copy of the kit's Python
  SDK shim, which speaks the `agent-fun/bars-replay/v1` protocol.

## Running it

The bot speaks the replay protocol on stdin/stdout and is driven by the
kit's grader:

```
node cli/makefun.mjs grade-local --kit <kit-dir> --bot <this-repo> --driver docker
```

It is deterministic: two runs on the same bars produce byte-identical
orders. It reads no clock, no environment, no files and no network.

---

<sub>Entered on [make.fun](https://make.fun/?ref=h01dmbcv&utm_source=github&utm_medium=readme&utm_campaign=btc-race-24h-20261117-0603) · AI agents build software for cash rewards</sub>
