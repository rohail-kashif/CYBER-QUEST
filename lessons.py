"""Study cards: one short lesson per level, shown before the activities.

Each entry: level name -> (fact 1, fact 2, fact 3, golden rule).
Keep every line ASCII and short (about 90 characters) so it fits the card.
"""

LESSONS = {
    "Home Base": (
        "A password is a secret key to your accounts and your device.",
        "Strong passwords mix random words, numbers and symbols.",
        "Lock your screen when you walk away from a device.",
        "Your password is a secret. Only a trusted grown-up may know it."),
    "Message Meadow": (
        "Phishing messages pretend to be someone you trust to trick you.",
        "Warning signs: strange sender, big prizes, rush, odd links and files.",
        "Real companies never ask kids for passwords by message.",
        "Stop. Look for the tricks. Then tell a grown-up."),
    "Privacy Park": (
        "Private information tells strangers who you are or where to find you.",
        "Your address, school, phone number and passwords stay private.",
        "Once something is posted it can be copied and stay online forever.",
        "If it tells someone where to find me, keep it private."),
    "Tech Trail": (
        "Smart devices and AI helpers are useful, but they can make mistakes.",
        "The cloud is a computer far away that keeps your files.",
        "Devices and apps may collect information about you.",
        "Use smart tech with a grown-up and keep private things private."),
    "Download Dunes": (
        "A virus is a bad program that sneaks onto a device and causes harm.",
        "Free games and odd files from unknown sites often hide viruses.",
        "Updates and official app stores keep your device safer.",
        "Only download things a grown-up has checked."),
    "Wi-Fi Wharf": (
        "Public Wi-Fi in shops and airports is shared with strangers.",
        "Other people on the same network may be able to see what you do.",
        "Never log in or share private things on public Wi-Fi.",
        "On public Wi-Fi, look but do not log in."),
    "Kindness Kingdom": (
        "Words online can hurt as much as words in person.",
        "Cyberbullying means being mean on purpose using devices.",
        "If it happens, do not fight back. Save proof and tell a grown-up.",
        "Think before you send. Be kind, or say nothing."),
    "Game Galaxy": (
        "Online games let you talk to people you may not know.",
        "Use a nickname, not your real name, and never share where you live.",
        "Cheats and free-item offers can hide viruses or steal accounts.",
        "Game friends are strangers until a grown-up says otherwise."),
    "Social Square": (
        "Posts on social media can be seen, copied and shared by others.",
        "Privacy settings decide who can see what you share.",
        "Think about how a post could look to your family and teachers.",
        "Post only what you would be happy for everyone to see."),
    "Fact Forest": (
        "Not everything online is true. Some stories and pictures are fake.",
        "Check who made it, and see if other trusted places say the same.",
        "Shocking headlines are often made to get clicks.",
        "Check before you believe it. Check before you share it."),
    "Camera Cove": (
        "A photo or video can show your face, school, home and routine.",
        "Ask before taking or sharing a picture of another person.",
        "Photos you send can be saved and shared by anyone.",
        "Ask first. Share only photos that are safe and kind."),
    "Stranger Station": (
        "A stranger online is someone you have never met in real life.",
        "People can pretend to be kids. You cannot be sure who is there.",
        "Never share personal details or meet someone from online.",
        "If a stranger contacts you, stop, block and tell a grown-up."),
    "Footprint Fjord": (
        "Everything you do online leaves a trail called a digital footprint.",
        "Posts, comments, photos and searches can stay for a very long time.",
        "Your footprint shapes how others see you later on.",
        "Leave a footprint you will be proud of."),
    "Ad Alley": (
        "Ads and pop-ups try to get your attention and your clicks.",
        "Some ads are tricks. A close button may even be fake.",
        "In-app buys spend real money, so always ask first.",
        "Do not tap it. Ask a grown-up before you click or buy."),
    "Smart Home Street": (
        "Smart toys, cameras and speakers connect to the internet.",
        "They can listen and record, and a weak password lets others in.",
        "Change default passwords and keep devices updated.",
        "Smart things need strong passwords and grown-up setup."),
    "Two-Step Tower": (
        "Two-step login asks for your password and a second proof.",
        "The second proof can be a code sent to a grown-up's phone.",
        "Even if someone learns your password, they cannot get in.",
        "Never share a secret code with anyone, not even a friend."),
    "Backup Bay": (
        "A backup is a spare copy of your files kept in another place.",
        "Backups save your work if a device breaks, is lost or is locked.",
        "Some viruses lock your files and ask for money.",
        "Keep a backup, and never pay to get files back."),
    "Help Hub": (
        "Every problem online can be fixed faster with a helper.",
        "Block means stop that person. Report means tell the website.",
        "Trusted helpers are parents, teachers and kid helplines.",
        "If something feels wrong, tell a trusted grown-up right away."),
    "Email Express": (
        "Emails can hold tricks, fake prizes and dangerous attachments.",
        "Only open emails and files from people you know and expect.",
        "Never send passwords or private details by email.",
        "Know the sender. Expect the file. Otherwise ask first."),
    "Link Lagoon": (
        "A link can take you somewhere safe or somewhere tricky.",
        "Fake links copy real names with small changes, like paypa1.",
        "A QR code hides its link, so strangers' codes are risky.",
        "Check the link, then ask a grown-up before you click or scan."),
    "Cloud Cove": (
        "Cloud storage keeps your files online so you can reach them anywhere.",
        "Sharing a file is like giving someone a key to it.",
        "Pick private settings and share with only the people who need it.",
        "Share the smallest amount with the smallest group."),
    "AI Arcade": (
        "AI chatbots can answer questions, but they sometimes get things wrong.",
        "Chats may be saved, so never type private details or passwords.",
        "Use AI to help you think, not to do your thinking for you.",
        "Check the answer. Keep private things out of the chat."),
    "Market Mile": (
        "Online shops and games can take real money.",
        "Scam shops use rush timers and free offers to hurry you.",
        "Only a grown-up should enter card details.",
        "Never buy alone. Ask a grown-up first."),
    "School Street": (
        "Shared computers can keep your accounts open after you leave.",
        "The next person could read your files or use your name.",
        "Log out, close your tabs and never save passwords on shared devices.",
        "Leave a shared computer exactly as you found it."),
    "Chat Room Ranch": (
        "Messages in group chats can be copied and sent to anyone.",
        "Private photos or secrets of others should never be forwarded.",
        "If someone is being mean, be kind to them and tell a grown-up.",
        "Before you send, ask: is it kind, true and safe to share?"),
    "Copy Canyon": (
        "Pictures, songs and stories belong to the people who made them.",
        "Copying someone's work and saying it is yours is unfair.",
        "Use things you are allowed to use, and say who made them.",
        "Make your own, or ask and give credit."),
    "Oops Outpost": (
        "Everyone makes online mistakes, even grown-ups.",
        "The sooner a grown-up knows, the easier it is to fix.",
        "Stay calm, stop clicking, change your password and tell someone.",
        "Telling the truth fast is always the right move."),
    "Hero Academy": (
        "Cyber Heroes protect themselves and help others.",
        "They use strong passwords, think before they click and stay kind.",
        "They ask for help when something feels wrong.",
        "Stop, think, then click."),
    "Stream Studio": (
        "Live streams and videos can be seen by many people, even strangers.",
        "Some videos are not made for kids. You can close any video.",
        "Never show your home, school or private details on camera.",
        "Watch with a grown-up close by and never share where you are."),
    "Voice Valley": (
        "Smart speakers listen for their wake word and may save what you say.",
        "Never say passwords, codes or addresses near a speaker.",
        "Voice buying can spend real money, so ask a grown-up first.",
        "Ask fun questions, but keep secrets out of earshot."),
    "Update Utopia": (
        "Updates fix security holes that bad programs use to sneak in.",
        "Real updates come from your device settings or the app store.",
        "A pop-up that shouts 'You are infected!' is usually a trick.",
        "Let a grown-up install real updates. Ignore scary pop-ups."),
    "Bridge of Courage": (
        "An upstander helps in a safe way when someone is hurt online.",
        "You can be kind to the person, save proof and report the post.",
        "Joining in, laughing or sharing makes the hurt bigger.",
        "Be an upstander: kind, safe and with a grown-up's help."),
    "Screen Summit": (
        "Screens are fun, but your body and brain also need sleep and play.",
        "Apps use sounds and rewards to keep you playing longer.",
        "Set limits, take breaks and keep meals and bedtime screen-free.",
        "Balance your day: play, learn, rest and screen time."),
    "Fake Friend Creek": (
        "Fake profiles use made-up names and pictures to look like kids.",
        "Warning signs: no friends in common, photo requests and secrets.",
        "Never meet or share private details with someone from online.",
        "If you do not know them in real life, they are a stranger."),
    "Router Ridge": (
        "The router is the box that brings the internet into your home.",
        "Its Wi-Fi password should be long, strong and not the factory one.",
        "Only trusted people with permission should use your Wi-Fi.",
        "A strong Wi-Fi password protects every device at home."),
    "Phone Fort": (
        "Phones and tablets hold photos, chats and lots of private things.",
        "Use a strong lock such as a long PIN, face or fingerprint.",
        "If a device is lost, tell a grown-up right away so they can lock it.",
        "Lock it, hide your PIN and tell a grown-up if it is lost."),
    "Scam Swamp": (
        "Scam calls and texts pretend to be banks, delivery drivers or family.",
        "They rush you to pay money, click links or share codes.",
        "Real banks and shops never ask kids for codes or payments.",
        "Hang up, do not click and tell a grown-up."),
    "Safety Squad HQ": (
        "Your safety squad is the family, teachers and helpers you trust.",
        "Good family tech rules include asking first and sharing time.",
        "Telling the truth about a mistake lets your squad help you.",
        "Safety is a team sport. Never face online problems alone."),
    "Vault Valley": (
        "It is hard to remember many passwords, so grown-ups use password apps.",
        "Never write passwords on sticky notes or send them in chat.",
        "If you forget one, a grown-up can reset it on the real website.",
        "Keep your secrets in a safe place, not in plain sight."),
    "Photo Pier": (
        "A photo of another person is also their private information.",
        "Backgrounds can show where someone lives, learns or plays.",
        "Always ask before you post a picture of someone else.",
        "Ask first. Their face is their choice too."),
    "Hacker Hill": (
        "A hacker is someone who breaks into computer systems.",
        "Good hackers have permission and fix weak spots to protect people.",
        "Bad hackers steal, spread viruses and break the law.",
        "Use computer skills to help, never to harm."),
    "Cookie Cafe": (
        "Cookies are small files that websites save on your device.",
        "Some help sites remember you. Others track what you click for ads.",
        "You can choose fewer cookies with a grown-up's help.",
        "Ask a grown-up and choose only the cookies that are needed."),
    "Wearable Woods": (
        "Smartwatches and apps can share exactly where you are.",
        "Location sharing is for trusted family only, and only when needed.",
        "Allow apps to use your location only while you use them.",
        "Your location is private. Share it with trusted people only."),
    "Virus Lab": (
        "Malware is the name for viruses, worms and other bad programs.",
        "It spreads through odd files, links, pop-ups and unknown USB sticks.",
        "Updates, antivirus software and careful clicking keep it out.",
        "If a device acts strange, stop and tell a grown-up."),
    "Fair Play Field": (
        "Cheat tools for games often hide viruses or steal passwords.",
        "Buying, selling or trading accounts is often a scam.",
        "Honest play is safer and more fun for everyone.",
        "Play fair, and never share your game password."),
    "Search Shore": (
        "Search results can include pages that are not right for kids.",
        "Kid-safe search and trusted sites give better answers.",
        "If you see something upsetting, close it and tell a grown-up.",
        "Search with a plan. Close it and tell if it feels wrong."),
    "Detective Agency": (
        "Computers can make fake pictures and videos that look real.",
        "Clues: odd hands, shadows or words, and no trusted source.",
        "Check other trusted places before you believe or share.",
        "Be a detective. One clue is not enough."),
    "Report Rock": (
        "Block stops a person from contacting you.",
        "Report tells the website or app about a problem so it can act.",
        "Save a screenshot as proof, then tell a grown-up.",
        "Block it, report it and tell a grown-up."),
    "Cyber Champions": (
        "Strong passwords, careful clicking and kindness protect you.",
        "Keep private things private, and never trust strangers online.",
        "When anything feels wrong, tell a trusted grown-up.",
        "Stop, think, then click, and always ask for help."),
}
