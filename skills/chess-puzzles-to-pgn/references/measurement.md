# Measurement reference

Why `detect_occupancy.py` exists, how it works, and how to use it well.

## The problem it solves

Chess diagrams in scanned books are deceptively hard to read. Pieces near a
file boundary — is this rook on g4 or h4? — are systematically misread when
you eyeball them, especially on grayscale scans from books printed before
2000. The error rate on a first visual pass through a Soviet-era puzzle book
is roughly 30-50%. That's not because anyone is being careless; the visual
system genuinely cannot reliably tell apart pieces that are 5-10mm apart on a
noisy scan.

Measurement fixes this. The board has a fixed grid. Each square is the same
size. You can count dark pixels per square, threshold, and get an unambiguous
"piece here / no piece here" map.

## How the script works

1. **Find the board borders.** Chess diagrams are framed by a thick black
   line. Scan rows/columns of the image for high concentrations of dark
   pixels; the outermost dark rows/columns are the borders.

2. **Subdivide into 64 squares.** Once we know the four corners, each
   square is `(right - left) / 8` wide and `(bottom - top) / 8` tall.

3. **Sample the inner portion of each square.** We don't want to count
   border lines (which are very dark) or the edge of the shading texture
   (which can also be dark). The default samples the central 60% of each
   square.

4. **Count "ink" pixels** — pixels darker than 60/255. This threshold is
   chosen so that piece glyph strokes (close to pure black, < 30) count
   reliably, while board shading texture (typically 130-180 grayscale)
   does not.

5. **Threshold to occupancy.** Default threshold is 350 ink pixels.
   Empty squares typically score 100-400 (from shading texture);
   piece-occupied squares score 600-2500.

## Reading the output

```
Ink density per square (inner sample):
    a    b    c    d    e    f    g    h
8:    0  246 1671  314    0  309    0  702
7:  213    0  320    0  303    0  698    0
6:    0  367    0  359    0  357    0  244
...

Occupancy (# = piece, ink > 350):
    a b c d e f g h
8:  . . # . . . . #
7:  . . . . . . # .
6:  . # . # . # . .
...
```

Squares with very high ink (1000+) are almost always pieces. Squares in the
200-400 range are usually empty squares with shading. The borderline cases
(400-700) need a visual sanity check, which you should do anyway.

The script does **not** identify which piece is on which square — only that
*something* is there. Identifying the piece (king vs queen vs rook) is still
your job, but you do it knowing exactly which square to look at.

## Calibration

Different scans need different parameters. Use these rules of thumb:

- **If real pieces show as `.` (false negatives):** lower `--threshold`
  (try 250 or 200), or check that the crop actually shows the full board
  with no margin issues. Sometimes the auto-border-detection picks up a
  rank label as the border, shrinking the sampled area.

- **If empty squares show as `#` (false positives):** raise `--threshold`
  (try 500 or 700), or shrink `--inner` (try 0.5 or 0.4) to sample
  closer to the square's center and avoid shaded edges.

- **If everything is the same density:** the crop is probably wrong.
  Check that the borders printed by the script make sense and that you
  don't have the wrong image.

## When to use measurement

Always, eventually. Specifically:

- **Always before finalizing a FEN.** Even if you're sure, run it.
- **Mandatory for pieces near file boundaries** (a/b, g/h files).
- **Mandatory for pieces on the same rank close together** (e.g., King and
  Queen both on rank 1).
- **Mandatory for crowded clusters** (more than 3 pieces on adjacent squares).
- **Skip only for trivially simple positions** (one king at a corner, one
  rook at the opposite corner, nothing else) — and even then, why skip?

## What it can't do

- It can't tell colors. A black rook and a white rook produce the same
  ink count.
- It can't tell piece types. King and queen ink counts overlap.
- It can't recover from a bad crop. If the crop cuts off rank 1, the
  borders detected will be wrong and the whole grid will be shifted.

For all these limitations, your eyes still matter. The script tells you
*where* the pieces are; you tell it *what* they are.
