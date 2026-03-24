---
name: play-ssh-of-empires
description: Play SSH of Empires as a live multiplayer participant over SSH. Use when a user wants Codex to join their SSH of Empires room, coordinate multiplayer setup, ready up in the lobby, and play the match to win. Trigger on requests about SSH of Empires, room codes, multiplayer rooms, live terminal gameplay, or joining a hosted match.
---

# Play SSH Of Empires

## Overview

Play SSH of Empires as the non-host player. Read the game's `llms.txt`, let the human create and administer the room, join their room code, wait for their ready/start instructions, and pursue victory once the match begins.

## Read The Game Docs First

- Read [website/public/llms.txt](/Users/juan/Documents/code/age_of_empires/website/public/llms.txt) before connecting.
- If the workspace copy is unavailable, read [llms.txt](https://ssh-of-empires.juanmartinez.xyz/llms.txt).
- Treat `llms.txt` as the source of truth for controls, buildings, resources, and win condition.

## Multiplayer Protocol

- Require the human to be the multiplayer admin.
- Do not create the room when playing with a human unless they explicitly ask you to host for testing.
- Ask the human to create the room, remain host, provide the room code, and tell you when to use `/ready`.
- Join only through `Multiplayer -> Join Room`.
- After joining, wait in the lobby until the host tells you to use `/ready`.
- After using `/ready`, wait for the host to start the match.
- Assume rejoining a live match may be blocked if you leave or disconnect.

## SSH Session Setup

- Use a real PTY.
- Prefer `TERM=xterm-256color ssh -p 2222 -t player@ssh-of-empires.juanmartinez.xyz`.
- If outbound SSH or DNS resolution fails inside a sandbox, retry with the required network approval instead of assuming the server is unavailable.
- If the remote curses app fails on startup with a terminal or cursor error, reconnect with `TERM=xterm-256color`.
- Keep the terminal at least `90x22`. `120x30` is safer.
- If the match screen says the terminal is too small, resize the PTY before continuing.

## Input Reliability

- In menu screens, prefer `j` and `k` with `Enter` when the menu supports them.
- In the live match, arrow keys are required for cursor movement.
- When sending arrow keys programmatically, send the full escape sequence in one write. Do not split `Esc` from the rest of the sequence.
- Avoid sending bare `Esc` unless you intentionally want to back out or quit. It can close menus, leave rooms, or exit the match.
- Use `Tab` to cycle owned units and buildings and reduce fragile cursor travel.

## Lobby Commands

- `/ready`
- `/unready`
- `/name <new_name>`
- `/leave`
- `/help`
- Treat `/start` as host-only.

## Match Objective

- Aim for victory and nothing else.
- Do not optimize for roleplay, sightseeing, or passive spectating unless the user explicitly changes the goal.
- Win by being the last civilization with surviving units or buildings.

## Opening Priorities

1. Build a `House` quickly because the starting population cap is `4`.
2. Queue additional `Villagers` from the `Town Center` as soon as population allows.
3. Put early workers on `food` and `wood`.
4. Build a `Mill` near berries and a `Lumber Camp` near trees when it reduces walking time.
5. Build a `Barracks` once the economy can sustain military production.
6. Keep exploring with the `Scout`.
7. Keep producing units while pressuring the opponent.

## Tactical Guidance

- Protect villager production and avoid idle Town Center time.
- Attack exposed enemy `Villagers` first when that does not throw away your army.
- Deny enemy economy before committing to a base race.
- Do not stay population capped.
- Advance ages when the economy can support it.
- Keep producing units during fights.

## Control Shortlist

- `Space` or `Enter`: select
- `Tab`: cycle owned units and buildings
- `a`: context command
- `b`: build menu from a selected `Villager`
- `v`: queue `Villager` at a selected `Town Center`
- `s`: queue military at a selected `Barracks`
- `n`: advance age at a selected `Town Center`
- `t`: research at a selected `Mill` or `Barracks`
- `x`: clear selection
