# Russian chess notation reference

Many older instructional chess books are in Russian. The board diagrams
themselves use international piece glyphs, but the surrounding text uses
Cyrillic abbreviations and Russian idiom. This guide covers what you need to
correctly read prompts, captions, and move text.

## Piece letters (in text, not on the board)

| Russian | Translit | English | FEN char |
|---------|----------|---------|----------|
| Кр      | Kr       | King    | K / k    |
| Ф       | F        | Queen   | Q / q    |
| Л       | L        | Rook    | R / r    |
| С       | S        | Bishop  | B / b    |
| К       | K        | Knight  | N / n    |
| п       | p        | Pawn    | P / p    |

Note: a single capital `К` is the **knight** (Конь), not the king. The king
is two letters: `Кр` (Король).

## Side to move

| Russian phrase     | Meaning                       |
|--------------------|-------------------------------|
| Ход белых          | White to move                 |
| Ход чёрных         | Black to move                 |
| Белые начинают     | White begins (= White to move)|
| Чёрные начинают    | Black begins (= Black to move)|

## Task types

| Russian            | Meaning                                                  |
|--------------------|----------------------------------------------------------|
| Мат в N ходов      | Mate in N moves                                          |
| Мат в N хода       | (genitive form for 2/3/4 — same meaning)                 |
| Найти выигрыш      | Find the win                                             |
| Найти N решений    | Find N solutions                                         |
| Дать мат           | Deliver mate / give mate                                 |
| Заматовать         | (verb) to deliver mate                                   |
| 2 способа          | Two methods / two solutions                              |

## Common annotations

| Russian              | Meaning                                  |
|----------------------|------------------------------------------|
| диаграмма N          | Diagram N                                |
| см. диаграмму N      | See diagram N                            |
| Реши сам!            | Solve it yourself! (puzzles section)     |
| оппозиция            | Opposition                               |
| выжидательный ход    | Waiting move                             |
| обход                | Detour / walk-around                     |
| сторож               | Sentinel / guard (rook on a file)        |
| охотник              | Hunter (attacking rook)                  |
| отрезает             | Cuts off                                 |
| оттеснить            | To push back / drive                     |
| передача очереди хода| Passing the move (zugzwang-like idea)    |
| пат                  | Stalemate                                |
| патовая позиция      | Stalemate position                       |

## Move-text quirks

In move sequences like `1.Лh3` you'll see Cyrillic piece letters mixed with
Latin file letters and digits (the international algebraic notation files
a-h are universal). When transcribing into English-format PGN, convert the
piece prefix:

- `Лh3` → `Rh3`
- `Крс2` → `Kc2`
- `Фd5+` → `Qd5+`
- `Кb7` → `Nb7`  (not Kb7 — single К is knight)

Check vs mate symbols:
- `+` = check (universal)
- `х` (Cyrillic kh, looks like Latin x) = mate. Often written `Лa6х` for
  "Ra6#".
- Sometimes `#` is used in modern editions; older books prefer `х`.

## Useful idioms in puzzle prompts

- *король оттесняется к краю доски* = the king is driven to the edge of
  the board.
- *король стоит напротив белого короля* = the king stands opposite the
  white king (i.e., direct opposition).
- *на расстоянии хода коня* = at a knight's-move distance (a key concept in
  K+Q vs K technique — the queen stays a knight's move from the enemy king
  to avoid stalemate).
- *задача-шутка* = joke problem / humorous puzzle (often a position with
  an unusual or surprising solution).
