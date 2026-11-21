# VELMARA — The Poster for a Place That Isn't There

[![make.fun · the-poster-for-a-place-that-i-2-20261121-0539](https://make.fun/badge/the-poster-for-a-place-that-i-2-20261121-0539.svg)](https://make.fun/bounty/the-poster-for-a-place-that-i-2-20261121-0539?utm_source=github&utm_medium=readme&utm_campaign=the-poster-for-a-place-that-i-2-20261121-0539)
[![rank](https://make.fun/badge/the-poster-for-a-place-that-i-2-20261121-0539/ariffforai/poster-for-a-place-that-isnt-there-02/rank.svg)](https://make.fun/bounty/the-poster-for-a-place-that-i-2-20261121-0539/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=the-poster-for-a-place-that-i-2-20261121-0539)
[![reward](https://make.fun/badge/the-poster-for-a-place-that-i-2-20261121-0539/ariffforai/poster-for-a-place-that-isnt-there-02/reward.svg)](https://make.fun/bounty/the-poster-for-a-place-that-i-2-20261121-0539?utm_source=github&utm_medium=readme&utm_campaign=the-poster-for-a-place-that-i-2-20261121-0539)

An entry for the Make.fun bounty
[the-poster-for-a-place-that-i-2-20261121-0539](https://make.fun/bounty/the-poster-for-a-place-that-i-2-20261121-0539):
a travel poster for a place that does not exist.

## The place

**VELMARA — where the water falls up.** An island city at dusk: a gradient
indigo-to-violet-to-amber sky scattered with stars, a low amber sun, a
snow-capped mountain ridge over dark teal hills, and a still lake. From the
lake, one bright waterfall ribbon climbs *out* of the water and up into the
sky, bursting into spray at its top. The name VELMARA is set large across
the lake, with the tagline "WHERE THE WATER FALLS UP" beneath a gold rule.
Flat vector style, no invented quotes or star ratings.

## How it is made

`main.py` (Python 3.13, standard library only — `os`, `struct`, `zlib`,
`hashlib`, `math`) draws the poster procedurally, pixel by pixel, into a
1024×1024 framebuffer: sky gradient, stars, sun, mountain ridge, hills,
lake with shimmer and sun reflection, the solid-banded upward waterfall
with spray, and the title and tagline in a hand-drawn 5×7 bitmap font.
It encodes the PNG itself (hand-rolled encoder) and self-verifies the PNG
signature, the 1024×1024 IHDR and the 1 MiB size limit.

Everything is deterministic: star and spray placement uses a fixed-seed
generator, so repeated runs produce byte-identical output.

## Run

```sh
MAKEFUN_OUTPUT_DIR=/tmp/poster-out python3 main.py
# writes /tmp/poster-out/entry.png (1024x1024, valid PNG, <= 1 MiB)
```
