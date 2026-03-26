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
- In the live match, use `Ctrl-B`, `Ctrl-F`, `Ctrl-P`, and `Ctrl-N` for left, right, up, and down.
- Do not use arrow keys in automated sessions.
- Avoid sending bare `Esc` unless you intentionally want to clear selection or close an in-game panel.
- Use `Tab` to cycle owned units and buildings, but do not spam it blindly.
- `Tab` cycles all owned units and buildings in top-to-bottom, then left-to-right map order.
- `Tab` also moves the cursor to the selected entity, so the camera state changes with it.
- Treat the action log as the most reliable confirmation channel after movement, attack, build, and production inputs.

## Stateful Control Semantics

- `Tab` is a high-value but high-risk shortcut because villagers, scout, infantry, and buildings share the same cycle.
- In the build menu, pressing `1` / `2` / `3` / `4` places the foundation immediately on the current cursor tile.
- Do not press `a` after choosing a build key unless you want to issue a new command.
- For military units, `a` attacks only when the cursor is exactly on an enemy unit or building tile.
- If the cursor is not exactly on an enemy tile, `a` becomes a move order.
- Do not rely on attack-move or strong auto-acquire behavior. Re-target visible enemies explicitly.
- After `Tab`, selection changes, or cursor travel, confirm the resulting state from the log or the selected-entity panel before sending more inputs.

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

## Agent Tactics / Failure Modes

- Once the match starts, prefer short input bursts plus confirmation instead of long blind macros.
- Re-acquire exact enemy tiles during combat. General movement toward an enemy is not enough to guarantee attacks.
- Watch the log for confirmations such as `moving to x,y`, `ordered to attack ...`, `Started ... foundation.`, and production queue messages.
- Do not assume fixed spawn orientation or a seat-based corner assignment.
- Scout early instead of assuming the enemy direction from your starting position.

## Control Shortlist

- `Ctrl-B` / `Ctrl-F` / `Ctrl-P` / `Ctrl-N`: move left / right / up / down
- `Space` or `Enter`: select
- `Tab`: cycle owned units and buildings in map order; moves cursor to the selected entity
- `a`: context command; attacks only on an exact enemy tile, otherwise moves
- `b`: build menu from a selected `Villager`
- `1` / `2` / `3` / `4` in build menu: place `House` / `Lumber Camp` / `Mill` / `Barracks` immediately at cursor
- `v`: queue `Villager` at a selected `Town Center`
- `s`: queue military at a selected `Barracks`
- `n`: advance age at a selected `Town Center`
- `t`: research at a selected `Mill` or `Barracks`
- `x` or `Esc`: clear selection
