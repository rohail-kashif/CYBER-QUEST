# CyberQuest Kids

A cyber-safety adventure game for ages 6-11, built with Python and pygame.
Kids travel through 49 levels (five map worlds) and learn about passwords, phishing, privacy,
smart tech, downloads and viruses, public Wi-Fi, cyberbullying, safe gaming, social media,
fake news, cameras, online strangers, digital footprints, ads, smart homes, two-step logins,
backups, email and links, cloud sharing, AI chatbots, online shopping, shared computers, group chats, copyright, fixing mistakes, live streams, voice speakers, updates, standing up to bullying, screen time, fake profiles, home Wi-Fi, phone locks, scam calls, family tech rules, password helpers, photo sharing, good and bad hackers, cookies, location sharing, malware, fair play, safe searching, fake images and blocking and reporting:

World 1: 1 Home Base, 2 Message Meadow, 3 Privacy Park, 4 Tech Trail, 5 Download Dunes,
6 Wi-Fi Wharf, 7 Kindness Kingdom, 8 Game Galaxy, 9 Social Square, 10 Fact Forest

World 2: 11 Camera Cove, 12 Stranger Station, 13 Footprint Fjord, 14 Ad Alley,
15 Smart Home Street, 16 Two-Step Tower, 17 Backup Bay, 18 Help Hub, 19 Email Express, 20 Link Lagoon

World 3: 21 Cloud Cove, 22 AI Arcade, 23 Market Mile, 24 School Street, 25 Chat Room Ranch,
26 Copy Canyon, 27 Oops Outpost, 28 Hero Academy

World 4: 29 Stream Studio, 30 Voice Valley, 31 Update Utopia, 32 Bridge of Courage, 33 Screen Summit,
34 Fake Friend Creek, 35 Router Ridge, 36 Phone Fort, 37 Scam Swamp, 38 Safety Squad HQ

World 5: 39 Vault Valley, 40 Photo Pier, 41 Hacker Hill, 42 Cookie Cafe, 43 Wearable Woods,
44 Virus Lab, 45 Fair Play Field, 46 Search Shore, 47 Detective Agency, 48 Report Rock, 49 Cyber Champions (finale)

## Run

```
pip install pygame
python main.py
```

Needs Python 3.8+. Works on Windows, macOS and Linux. No internet, accounts or servers.
Progress is saved in a tiny file at `~/.cyberquest_kids.json` (use "Reset" on the title screen to clear it).

## Controls

| Input | Action |
|---|---|
| Mouse / touch | Click, drag and drop |
| 1-9 | Pick quiz answers |
| Enter / Space | Main button (Check / Next) |
| Esc | Back to the map |
| M | Mute / unmute |
| F11 | Fullscreen |

## What is inside

- **Study Time cards**: every level starts with a short lesson (3 key facts and a golden rule) before the questions, so kids learn first and then practise. Lessons live in `lessons.py`.
- **Level map** with locked levels, stars and a guide character per level.
- **Mini-games**
  - Password Builder: tile-based strength meter
  - Sorter: drag-and-drop cards into boxes (tap a card, then tap a box, also works)
  - Phish Hunt: tap the warning signs in a fake message
  - Quizzes: single choice and "pick all that apply"
- **Reward loop**: 3/2/1 points per activity by first-try accuracy, 1-3 stars per level, confetti, checkpoints, a final Champion screen with accuracy and time played.
- **Sound** is generated in code, so there are no asset files.

## Files

- `main.py` - engine, scenes, mini-games, drawing
- `content.py` - all learning content (plain data, no pygame needed)
- `lessons.py` - the Study Time card for each level (3 facts and a golden rule)

## Adding content

Edit `content.py`. Each level has a list of `activities`; the kinds
(`story`, `quiz`, `sort`, `hunt`, `builder`) are documented at the top of that file.
To add a level, copy an existing level block, add its Study Time entry in `lessons.py` (keyed by the level name), and insert it before the finale (the last
level). Pick a `guide` (owl, fox, bear, robot, dino, penguin, cat, alien, bunny, turtle, panda, lion, frog, elephant)
and an `art` (house, meadow, park, trail, dunes, wifi, kind, galaxy, social, forest, camera,
station, fjord, alley, smarthome, tower, bay, hub, mail, lagoon, cloud, ai, market, school, chat, canyon, outpost, academy, stream, voice, update, bridge, summit, creek, router, fort, swamp, hq, vault, pier, hill, cafe, woods, lab, field, shore, agency, rock, castle). The map (10 levels per page, use the
< > buttons or PageUp/PageDown), colors, stars, save file and final screen adjust automatically.
Older 5-, 9-, 19-, 29- and 39-level save files are migrated automatically.
Keep sorter cards to 6 or fewer and quiz options to 4 or fewer so everything fits on screen.
