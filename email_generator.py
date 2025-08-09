import os
import json
import random
from dotenv import load_dotenv

load_dotenv()

LEADS_FILE = "leads/scraped_leads.ndjson"

# --- VariantRotator --------------------------------------------------------

class VariantRotator:
    def __init__(self, items):
        self.original_items = items[:]
        self.pool = []
        self._reshuffle()

    def _reshuffle(self):
        self.pool = self.original_items[:]
        random.shuffle(self.pool)

    def next(self):
        if not self.pool:
            self._reshuffle()
        return self.pool.pop()

#--------------SALUTATIONS & SIGNATURE---------------------------------------------------------------------------

salutations = [
    "Hi {name}",
    "Hey {name}",
    "Hello {name}",
    "Hi there {name}",
    "Hey there {name}",
    "Hello there {name}",
]

signatures = [
    "All the best,\n– Trent,\nToon Theory\ntoontheory.com",
    "Take care,\n– Trent, Founder\nToon Theory\nwww.toontheory.com",
    "Looking forward,\n– Trent,\nToon Theory\nhttps://toontheory.com",
    "Catch you later,\n– Trent, Founder\nToon Theory\nhttps://www.toontheory.com",
    "Have a good one,\n– Trent, Founder\nToon Theory\nhttp://toontheory.com",
    "Until next time,\n– Trent,\nToon Theory\nhttp://www.toontheory.com",
    "Talk soon,\n– Trent, Founder\nToon Theory\nhttps://toontheory.com/",
    "Looking forward,\n– Trent,\nToon Theory\nhttps://www.toontheory.com/",
    "Cheers,\n– Trent, Founder\nToon Theory\nhttp://toontheory.com/",
    "All the best,\n– Trent,\nToon Theory\nhttp://www.toontheory.com/",
    "Best regards,\n– Trent, Founder\nToon Theory\ntoontheory.com/",
    "Take care,\n– Trent,\nToon Theory\nwww.toontheory.com/",
    "Catch you later,\n– Trent, Founder\nToon Theory\nhttps://ToonTheory.com",
    "Have a good one,\n– Trent,\nToon Theory\nhttps://toontheory.com"
]

#--------------EMAIL 1 TEMPLATES---------------------------------------------------------------------------

paragraph_1_variants = [
    "Even the best teams burn money when the message gets fuzzy.",
    "Mixed messages don’t scream — but they quietly steal your money.",
    "No matter how skilled your team is, unclear messaging always costs you.",
    "When everyone tells a different story, confusion gets expensive.",
    "Great work can get lost if the message isn’t clear — and that's costly.",
    "A clear story isn’t fluff — it’s how you save time and money.",
    "Lost time and wasted effort come from messages that don’t land.",
    "When your story slips, you lose money.",
    "Confusion isn’t loud — it’s the quiet leak in your profits.",
    "Unclear messaging turns good work into lost opportunities.",
    "Your best work might fall flat when the message doesn’t click.",
    "When your message wanders, so does your money.",
    "Miscommunication may cost more than you think.",
    "A strong story keeps everyone on the same page and your profits intact.",
    "Mixed message chips away at your earnings and efficiency.",
    "Clear messaging is the difference between wasted time and winning deals.",
    "When the story isn’t clear, your money quietly slips away."
]

paragraph_2_variants = [
    "Unclear messaging causes extra calls, emails, and confusion.\n\nWhen it happens regularly, it quietly drains thousands from your revenue each year.",

    "Every round of back-and-forth costs billable hours you won’t recover.\n\nIf you spend more time explaining than delivering, you’re losing significant income without realizing it.",

    "It’s not the message that kills budgets — it’s ghosted leads, no-shows, and endless meetings that go nowhere.\n\nThose hidden losses pile up fast and shrink your profit margins.",

    "Most teams don’t track how much billable time they lose re-explaining points.\n\nThose disappearing hours translate directly into real dollars slipping through cracks.",

    "Those extra meetings that go nowhere and long calls drain your budget.\n\nYou can’t bill those lost hours, but they quietly add up.",

    "One extra email here, a redundant meeting there.\n\nOver time, those billable hours never recovered hit your revenue hard.",

    "Unclear communication slows teams and bleeds cash.\n\nHours lost to extra calls, emails, and pointless meetings are money you’ll never see again.",

    "Every vague question or request triggers more emails, calls, and meetings.\n\nThat’s client time you won’t get paid for and profit leaking out unnoticed.",

    "Miscommunication doesn’t just slow things — it kills revenue.\n\nMore calls, fixes, and fewer billable hours shrink margins you can’t afford to lose.",

    "Confusion over simple details wastes hours and causes missed deadlines.\n\nThose lost hours multiply, costing thousands each year in revenue.",

    "If your messaging isn’t clear, work slows down.\n\nDelays waste valuable billable time and shrink profits and growth potential.",

    "If you spend time explaining instead of working, progress stalls.\n\nLost hours add up fast and cost thousands in missed income yearly.",

    "Extra calls and emails to fix unclear points eat into your billable hours.\n\nThat lost time quietly drains revenue and growth.",

    "When businesses spend hours clarifying confusion, they lose valuable working time.\n\nThose hours translate into money that never hits your bottom line.",

    "Re-explaining the same things drains your business's productivity and your budget.\n\nThose invisible costs add up fast, quietly shrinking your profits.",

    "Time wasted fixing avoidable misunderstandings means fewer billable hours and less income.\n\nIt’s a slow leak that damages your business’s financial health.",

    "Lost billable hours from repeated explanations aren’t just frustrating — they’re expensive.\n\nEach missed hour chips away at potential revenue.",

    "Every unclear email or message can trigger a costly chain of follow-ups.\n\nThose costs add up and weigh heavily on your bottom line.",

    "When communication falls short, your business spends more time fixing problems than creating value.\n\nThat lost productivity hits your profits hard.",

    "Misunderstandings cause a ripple effect of wasted time and missed revenue.\n\nThe price of poor messaging is far higher than most realize."
]

paragraph_3_variants = [
    "To fix that, we help teams stop repeating themselves by putting the story into a whiteboard video everyone trusts.",
    "That’s why our whiteboard explainers let the whole team speak with one voice — clear and confident every time.",
    "We create whiteboard videos that turn complicated offers into simple stories your clients actually get.",
    "That’s why we make whiteboard videos that give your business a reliable way to explain your offerings without fumbling.",
    "Our whiteboard videos turn your core message into something that sticks, not slips away.",
    "With one great whiteboard video, your business can ditch the script and still get it right every time.",
    "We build whiteboard videos that let your message travel further and reach more people, clearly.",
    "To cut down confusion, we build whiteboard explainers that help you save time by cutting down questions and back-and-forth.",
    "Our whiteboard explainers act like a shortcut — they get your message across fast and clearly.",
    "We can help you lock in your proposition with a whiteboard video that does most of the talking.",
    "That’s why our whiteboard videos turn your boring bullet points into stories that prospects can’t forget.",
    "This is why we build whiteboard videos designed to make onboarding and sales smoother and faster.",
    "This is why we craft whiteboard videos that help your business sound consistent and confident every time.",
    "With our whiteboard explainers, you get a message that stays sharp and clear — no matter who shares it.",
    "That's why we create whiteboard videos that make your job easier by putting your story on repeat.",
    "Our whiteboard videos simplify your message so you can focus on closing deals, not explaining.",
    "That's why we make whiteboard videos that cut confusion and keep your clients and business on the same page.",
    "With our whiteboard videos, you spend less time answering questions and more time moving deals forward.",
]

paragraph_4_variants = [
    "I can sketch a 10-second teaser for you — keep it or toss it.\n\nIf it’s not your thing, just reply NO and I’ll quietly step away.",
    "Happy to draft a short sample script if you want — no strings, just a gift.\n\nIf you’re not interested, reply NO and I won’t bother you again.",
    "I’d be glad to put together a brief 10-second teaser for you — yours to keep or ignore.\n\nIf it’s not a fit, reply NO and I’ll disappear.",
    "If you’re open to it, I can create a quick script draft — no pressure at all.\n\nIf you’d rather not, reply NO and I’ll back off.",
    "I can send over a short 10-second teaser — whether you use it or not, it’s yours.\n\nIf you don’t want it, reply NO and I won’t follow up.",
    "I enjoy making these — happy to draft a quick sample script for you.\n\nIf you don’t want it, a simple NO will end it.",
    "I can put together a small teaser if you’re curious — no need to reply.\n\nIf it’s not useful, reply NO and I’ll go silent.",
    "If you’re interested later, I can have a 10-second teaser ready for you.\n\nIf not, just say NO and I’ll stop messaging.",
    "You don’t have to decide now — I can send a 10-second teaser when you want.\n\nIf you don’t want it, reply NO and I’ll step away.",
    "I’d be happy to whip up a quick script for you — useful or not.\n\nIf it’s not your vibe, reply NO and I’ll take the hint.",
    "If you want, I can sketch a sample script — no strings attached.\n\nIf you want no more, just say NO and I’ll disappear.",
    "Just for reading, I can send over a rough 10-second teaser if you like.\n\nIf it’s not a fit, reply NO and I’ll bow out.",
    "I can share a quick script idea — yours to ignore or use.\n\nIf it’s not for you, reply NO and I won’t bother you again.",
    "I’d like to gift you a short teaser — no ask, no pressure.\n\nIf you don’t want it, just say NO and I’ll stop.",
    "I can quietly sketch a 10-second teaser — totally optional for you.\n\nIf it’s not useful, reply NO and I’ll fade away.",
    "If you’d like, I can put together a quick video script to get started.\n\nIf this isn’t a fit, reply NO and I’ll back off.",
    "I can send a quick concept video script that’s easy to share.\n\nIf it’s not useful, reply NO and I’ll move on.",
    "If you want a short script draft or a 10 second teaser, I can have one ready in no time.\n\nIf you don’t want it, reply NO and I’ll stop.",
    "I’m happy to prepare a small script sample to help you better understand the idea.\n\nIf you’re not interested, reply NO and I’ll disappear."
]

#--------------EMAIL 2 TEMPLATES---------------------------------------------------------------------------

fu1_paragraph_1_variants = [
    "You might have missed my first note, so I’m sending it over once more.",
    "Giving this another go in case it got lost in the pile.",
    "This might’ve landed at the wrong moment, so I’m sending it again.",
    "Sharing this one more time in case it’s still relevant.",
    "Sending this again — maybe the timing was wrong.",
    "Thought this might be worth a second look, so here it is again.",
    "Giving this another shot before I set it aside.",
    "Not sure if my earlier note reached you, so I’m trying again.",
    "This might’ve slipped by earlier, so I’m passing it along again.",
    "Thought it’d be worth sending this again.",
    "Trying this again in case the first one didn’t land.",
    "Resending this in case it got lost",
    "Might’ve been a busy day when I first sent this — here’s another try.",
    "This is the same note I sent earlier, just making sure it reached you.",
    "Could be the first email missed you — here it is again.",
    "This might be worth another look, so I’m sending it again.",
    "Sending this one more time in case it’s still on your radar.",
    "Just passing this along again if it got buried.",
]

fu1_paragraph_2_variants = [
    "Like I said, every misread email or misunderstood deck quietly drains the budget — lost revenue or unbilled time.\n\nThat money isn’t theoretical, it’s gone.",
    
    "You may not realize this, but re-explaining the same point across calls and threads doesn’t just burn time — it chips away at profit, trust, and sanity.\n\nTighter messaging plugs those leaks.",
    
    "When I reached out before, I said even simple misunderstandings can derail deals. The lost revenue adds up fast.\n\nIt’s money you never see, but always feel.",
    
    "As I said, back-and-forths eat into billable hours you can’t charge for. If you're busy explaining, you’re not delivering.\n\nThat inefficiency bleeds money.",
    
    "Like I noted, the real waste isn’t emails — it’s ghosted leads, un-booked calls, and meetings that go nowhere.\n\nThat’s lost income, not just lost time.",
        
    "Here's the thing, most teams never track how much they lose repeating the same idea in different ways.\n\nBut those unbilled hours go somewhere — extra calls, another email there and one more useless meeting.",
    
    "Just as I said last time, extra unnecessary meetings and calls that go in circles cost more than they return.\n\nThat’s not just a clarity issue — it’s wasted revenue.",
    
    "Like I said, inefficiency doesn’t look dramatic — but it drains you anyway, one extra email and another meeting booked.\n\nIt’s not just annoying — it’s expensive. Billable hours lost.",

    "Like I hinted — extra calls, emails, and meetings add up fast. Repetition feels harmless until you tally how much of your week it eats.\n\nEven two hours lost a week can cost thousands of dollars a year.",

    "As I said, unclear communication slows everyone down and silently wastes money.\n\nThose extra calls, emails, and pointless meetings are hours your business will never bill for.",

    "Like I hinted, the real cost of confusion hides in overtime, scope creep, and deals that never close.\n\nIt’s lost revenue that never hits your wallet.",

    "Like I said, when teams spend more time explaining than creating, the clock keeps running.\n\nThose hours don’t build value — you can’t bill for them, and that’s lost revenue.",

    "As I said, every unanswered question or fuzzy brief means more emails, calls, and meetings.\n\nThat’s unpaid time and profit quietly slipping away from your business.",

    "Like I mentioned, unclear messaging causes extra follow-ups that waste time and money.\n\nThat slow drip of lost hours quickly adds up to real revenue lost.",

    "You might not notice, but unclear offers force your business to spend hours explaining instead of closing deals.\n\nThose lost hours hit your bottom line harder than you think.",

    "As I noted, repeating explanations in meetings and emails is unproductive.\n\nThose lost billable hours quietly drain your profits and slow down growth.",

    "Like I said, vague or confusing info means more calls and longer sales cycles.\n\nThat’s money slipping out the backdoor without you seeing it.",

    "You know those repeated questions and check-ins? They cost you more billable time than you realize.\n\nAnd time is money your business loses.",

    "As I mentioned, unclear briefs or requests cause rework, extra meetings, and lost focus.\n\nThat’s unbilled work steadily chipping away at your revenue.",

]

fu1_paragraph_3_variants = [
    "That’s why we create short whiteboard explainers that lock the message in — so your business doesn’t have to keep re-explaining it.",
    "That’s where a clear, reusable whiteboard video comes in — one version of your story that lands every time.",
    "To fix that, we build whiteboard videos your business can reuse across intros, pitches, and onboarding — no more starting from scratch.",
    "That’s why we create short whiteboard videos that become the go-to explanation everyone can rally around.",
    "To plug that leak, we turn your offer into a single whiteboard explainer that’s clear, fast, and impossible to miss.",
    "That’s why we condense the whole pitch into a whiteboard video you and your prospects can watch once and actually remember.",
    "To cut that waste, we create whiteboard explainers that make your value instantly obvious — in under two minutes.",
    "That’s why we build whiteboard videos that keep everyone on the same page from day one.",
    "To prevent that, we make whiteboard explainers that say it once, say it clearly, and make it stick.",
    "That’s why we produce whiteboard videos that simplify the pitch and speed up decisions.",
    "To stop that bleed, we create whiteboard explainers you can drop into any deck, proposal, or call.",
    "That’s why we make whiteboard videos that explain your value so cleanly, you never have to fill in the gaps afterward.",
    "To solve that, we build reusable whiteboard explainers — one crisp message, zero confusion.",
    "That’s why we turn your offer into a short whiteboard video that does the explaining for you, every time.",
    "We craft whiteboard videos that give your business a clear story to tell — no more guessing or mixed messages.",
    "Our whiteboard explainers help your business hit the same note, every time you talk to clients.",
    "Our whiteboard videos make your value obvious fast, so prospects don’t have to guess what you’re about.",
    "We build whiteboard videos designed to cut through noise and get everyone aligned quickly.",
    "With our whiteboard explainers, your business spends less time talking and more time being productive.",
]

fu1_paragraph_4_variants = [
    "If it still feels relevant, I’ll draft a short script this week — no ask, just something to use if it helps.\n\nIf it’s not a fit, reply 'NO' and I’ll scram.",
    "Totally happy to put together a 10-second teaser — whether you use it or not, it’s yours.\n\nIf you’d rather not, reply 'NO' and I’ll take you off my list.",
    "Still glad to write up a snippet — no strings, no pitch, just a gift.\n\nIf this doesn’t click, reply 'NO' and I’ll disappear.",
    "If you’re open to it, I’ll send over a quick script idea — just something to keep on hand if it clicks later.\n\nIf it’s a no, reply 'NO' and I’ll bow out.",
    "If it’s helpful, I’ll draft a tiny teaser anyway — yours to keep, no pressure to respond.\n\nIf it’s not your cup of tea, reply 'NO' and I’ll leave you be.",
    "Whether or not you’re in the market, I’d still enjoy putting together a short script.\n\nIf you’re not interested, reply 'NO' and I’ll quietly back away.",
    "No follow-up needed — I’ll still write something quick if it’s even remotely useful.\n\nIf you’d prefer I didn’t, reply 'NO' and I’ll cross you off.",
    "Happy to create a quick 10-second concept, whether or not we ever talk again.\n\nIf it’s not relevant, reply 'NO' and I’ll move along.",
    "I can put together a quick script outline this week — no strings attached.\n\nIf this isn’t up your alley, reply 'NO' and I’ll vanish.",
    "If it helps, I’ll make a short teaser for you to keep.\n\nIf it’s a pass, reply 'NO' and I’ll step aside.",
    "I’m happy to send over a quick script idea — Use it however you like.\n\nIf you’re not feeling it, reply 'NO' and I’ll go quietly.",
    "If you want, I’ll put together a short teaser just so you have it.\n\nIf it’s not for you, reply 'NO' and I’ll head out.",
    "I could pull together a small script — no charge, no pitch.\n\nIf it’s not the right time, reply 'NO' and I’ll back off.",
    "If it’s useful, I’ll make a quick 10-second teaser to keep on file.\n\nIf it’s not a fit, reply 'NO' and I’ll fade away.",
    "Glad to mock up a short script draft for you — yours either way.\n\nIf you’d rather not, reply 'NO' and I’ll vanish.",
    "I’ll happily whip up a 10-second teaser you can keep, no commitment needed on your end.\n\nIf you’re not interested, reply 'NO' and I’ll get out.",
    "Happy to share a quick script outline that might make things easier.\n\nIf this isn’t your thing, reply 'NO' and I’ll step out.",
    "I can throw together a short 10-second teaser — take it or leave it.\n\nIf you’re not into it, reply 'NO' and I’ll walk away.",
    "I’ll write a short script and send it over, use it or ignore.\n\nIf it’s a no, reply 'NO' and I’ll drop it.",
    "Always happy to make a small 10-second teaser that might help down the road.\n\nIf it’s not for you, reply 'NO' and I’ll bow out."
]

#--------------EMAIL 3 TEMPLATES---------------------------------------------------------------------------

fu2_paragraph_1_variants = [
    "Just sending this one last time in case it slipped through.",
    "Before I close the loop, I wanted to send this one more time.",
    "Last call to see if this might be helpful before I step back.",
    "Sending this final note in case it’s still on your radar.",
    "Wrapping up some projects — wanted to make sure you saw this.",
    "One last quick message before I sign off.",
    "This is my final check-in to see if you want to take a look.",
    "Before I drop off your inbox, here’s a quick reminder.",
    "Final pass on this — let me know if it’s worth a chat.",
    "Just reaching out one last time to keep this top of mind.",
    "Last try to get this on your radar before I bow out.",
    "One last message to make sure you got this.",
    "Sending a final note — just making sure it reaches you.",
    "Before I step away, I wanted to share this one last time.",
    "This is the last time you’ll hear from me on this — unless you want to chat.",
    "Giving this one final attempt before I sign off.",
    "Final message in case it got lost earlier.",
    "Closing out with this quick reminder in case it helps."
]

fu2_paragraph_2_variants = [
    "Like I said earlier, unclear messaging means every extra call or email eats away at billable hours — over time, that adds up to thousands lost without you realizing it.",
    
    "As mentioned before, repeated explanations mean your business spends less time delivering value and more time spinning wheels — quietly draining revenue week after week.",
    
    "As I mentioned, unclear communication creates confusion that leads to missed deadlines, stalled projects, and lost opportunities — hitting your bottom line harder than you expect.",
    
    "Like I pointed out, every no-show, ghosted lead, or wasted meeting isn’t just frustrating — it’s lost income piling up and shrinking your profit margins before you even notice.",
    
    "As I said before, endless back-and-forth emails and calls may seem minor, but they add up to lost billable hours your business can’t recover — quietly eating into growth and cash flow.",
    
    "Like I said earlier, a single unclear brief can trigger a chain reaction of extra work, calls, and emails that drag down productivity — costing thousands in lost labor each quarter.",
    
    "You may not notice this, but poor communication costs more than wasted time — it frustrates clients, misses opportunities, and steals revenue before it reaches your books.",
    
    "As I mentioned, unclear messaging slows your whole business down, forcing repeated explanations and avoidable questions — all taking time away from billable work and cutting revenue.",
    
    "Like I pointed out, when your offer isn’t clearly understood, your business spends valuable hours putting out fires instead of closing deals — causing a slow but steady revenue drain.",
    
    "As I said before, unclear or vague requests create extra work, follow-ups, and revisions — none of which you can bill for, yet all cost real money and wasted effort.",
    
    "Like I said earlier, the real price of miscommunication goes beyond lost hours — it’s deals that never close and clients who walk away before you even get started.",
    
    "Actually, when messaging falls short, your business gets stuck in cycles of explanation — losing actual billable time that could have been spent more productively.",
    
    "As I mentioned, the longer you spend fixing misunderstandings and answering avoidable questions, the more your profits shrink — quietly eating into your annual revenue.",

    "As I said earlier, when your message isn’t clear, deals drag out or stall — costing you billable hours and money you won’t recover.",
    
    "You might not realize it, but poor communication often forces your business into overtime and last-minute fixes — burning valuable billable hours and cutting deeply into your profits.",

    "Like I mentioned before, every unclear interaction leads to more back-and-forth emails and meetings — each one eating away at billable time and quietly shrinking your bottom line.",

    "Actually, unclear messaging traps your business in endless explanations instead of productive work — those lost hours pile up fast and slam your revenue growth.",

    "As I said, poor communication doesn’t just slow things down — it drains billable hours and fragments your business's focus, making hitting revenue targets harder than it should be.",

    "Like I pointed out earlier, repeated explanations cost far more than just time — they chip away at your billable hours and put a real dent in your revenue potential.",

    "You might not notice at first, but unclear messaging causes costly overtime and urgent firefighting that burn through your billable time and shrink your profits without warning."
]

fu2_paragraph_3_variants = [
    "We create whiteboard videos that lock your message in—so you spend less time re-explaining and more time moving forward.",
    "Our whiteboard videos turn your offer into one clear story you can use in pitches, onboarding, and sales without missing a beat.",
    "We make short, reusable whiteboard explainers that show your value clearly and keep everyone on the same page.",
    "To cut through the noise, our whiteboard videos simplify your complex services into something easy to share and understand—no guessing required.",
    "We craft whiteboard explainers that become your go-to for consistent messaging, wherever your business or clients need it.",
    "Our videos capture your core story so perfectly, you’ll spend less time explaining and more time closing deals.",
    "We produce engaging whiteboard videos that get your value across fast, making sales and onboarding smoother for everyone.",
    "Our whiteboard explainers are designed to cut down the back-and-forth, so you can focus on delivering results, not just talking.",
    "We build polished whiteboard videos your team can rely on—saving time and cutting out mixed messages.",
    "We tell your story with whiteboard videos that stick, helping you hit the right note every time with prospects.",
    "Our whiteboard videos give you a clear, consistent narrative from the first hello all the way to the final close.",
    "We make explainers that work everywhere—decks, calls, onboarding—so your message never gets lost in translation.",
    "Our videos help your business say it right the first time, so you don’t have to repeat yourself or fix misunderstandings.",
    "We design whiteboard explainers that speed up sales by making your key points instantly clear and easy to remember.",
    "We turn complex ideas into simple stories with whiteboard videos, cutting confusion and boosting confidence in your offer.",
    "Our whiteboard explainers make your value crystal clear, so prospects get it fast and your business runs smarter.",
    "With our whiteboard videos, your messaging stays sharp and compelling, no matter who’s sharing it."
]

fu2_paragraph_4_variants = [
    "I can sketch a 10-second teaser for you — keep it or toss it.\n\nNo pressure, just something to have on hand if it helps.",
    "Happy to draft a short sample script if you want — no strings, just a gift.\n\nTotally up to you whether you use it or not.",
    "I’d be glad to put together a brief 10-second teaser for you — yours to keep or ignore.\n\nJust letting you know it’s available if you want it.",
    "If you’re open to it, I can create a quick script draft — no pressure at all.\n\nYou can decide if and when it’s useful.",
    "I can send over a short 10-second teaser — whether you use it or not, it’s yours.\n\nNo follow-up needed from your side.",
    "I enjoy making these — happy to sketch a quick sample script for you.\n\nUse it however you like.",
    "I can put together a small teaser if you’re curious — no need to reply.\n\nJust something to keep if it’s helpful down the road.",
    "If you’re interested later, I can have a 10-second teaser ready for you.\n\nNo rush or pressure, just here if it helps.",
    "You don’t have to decide now — I can send a 10-second teaser whenever you want.\n\nJust keeping it open if it’s useful.",
    "I’d be happy to whip up a quick script for you — useful or not.\n\nCompletely your call to keep or ignore.",
    "If you want, I can sketch a sample script — no strings attached.\n\nJust a simple gesture to help if you need it.",
    "Just for reading, I can send over a rough 10-second teaser if you like.\n\nNo obligations, just here to assist.",
    "I can share a quick script idea — yours to ignore or use.\n\nNo pressure, just a little something in case it helps.",
    "I’d like to gift you a short teaser — no ask, no pressure.\n\nJust putting it out there if it’s useful to you.",
    "I can quietly sketch a 10-second teaser — totally optional.\n\nOnly if it feels right for you.",
    "I can create a quick teaser for you to keep.\n\nNo pressure, just something ready if you want it.",
    "Happy to put together a brief script idea.\n\nUse it if it works, ignore if it doesn’t.",
    "I can draft a quick teaser and send it your way.\n\nNo strings, no follow-up required.",
    "If you want, I can send over a short concept.\n\nUse it or not, up to you.",
    "I’m happy to prepare a quick script you can keep.\n\nNo pressure, just offering it if it helps."
]

# --- Rotators --------------------------------------------------------------

rotators = {
    # Salutations for email 2 and 3
    "sal": VariantRotator(salutations),

    # Email 1
    "p1": VariantRotator(paragraph_1_variants),
    "p2": VariantRotator(paragraph_2_variants),
    "p3": VariantRotator(paragraph_3_variants),
    "p4": VariantRotator(paragraph_4_variants),
    "p5": VariantRotator(paragraph_5_variants),
    "sig": VariantRotator(signatures),

    # Email 2 (follow-up 1)
    "fu1_p1": VariantRotator(fu1_paragraph_1_variants),
    "fu1_p2": VariantRotator(fu1_paragraph_2_variants),
    "fu1_p3": VariantRotator(fu1_paragraph_3_variants),
    "fu1_p4": VariantRotator(fu1_paragraph_4_variants),
    "fu1_p5": VariantRotator(fu1_paragraph_5_variants),

    # Email 3 (follow-up 2)
    "fu2_p1": VariantRotator(fu2_paragraph_1_variants),
    "fu2_p2": VariantRotator(fu2_paragraph_2_variants),
    "fu2_p3": VariantRotator(fu2_paragraph_3_variants),
    "fu2_p4": VariantRotator(fu2_paragraph_4_variants),
    "fu2_p5": VariantRotator(fu2_paragraph_5_variants),
}

# --- NDJSON Helpers --------------------------------------------------------

def load_ndjson(filepath):
    records = []
    buffer = ""
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                if buffer:
                    try:
                        records.append(json.loads(buffer))
                    except json.JSONDecodeError as e:
                        print(f"❌ JSON decode error:\n{buffer}\n→ {e}")
                    buffer = ""
            else:
                buffer += line
        if buffer:
            try:
                records.append(json.loads(buffer))
            except json.JSONDecodeError as e:
                print(f"❌ JSON decode error at EOF:\n{buffer}\n→ {e}")
    return records

def save_ndjson(filepath, records):
    with open(filepath, "w", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False, indent=2) + "\n")

# --- Email Builders --------------------------------------------------------

def build_email1(lead):
    name = lead.get("first name", "there")
    company = lead.get("business name", "your company")

    return (
        f"{rotators['o'].next().format(name=name, company=company)}\n\n"
        f"{rotators['p1'].next()}\n\n"
        f"{rotators['p2'].next().format(company=company)}\n\n"
        f"{rotators['p3'].next()}\n\n"
        f"{rotators['p4'].next().format(company=company)}\n\n"
        f"{rotators['p5'].next()}\n\n"
        f"{rotators['sig'].next()}"
    )

def build_email2(lead):
    name = lead.get("first name", "there")
    company = lead.get("business name", "your company")

    salutation = rotators["sal"].next().format(name=name)
    return (
        f"{salutation},\n\n"
        f"{rotators['fu1_p1'].next().format(name=name)}\n\n"
        f"{rotators['fu1_p2'].next().format(company=company)}\n\n"
        f"{rotators['fu1_p3'].next()}\n\n"
        f"{rotators['fu1_p4'].next()}\n\n"
        f"{rotators['fu1_p5'].next()}\n\n"
        f"{rotators['sig'].next()}"
    )

def build_email3(lead):
    name = lead.get("first name", "there")
    company = lead.get("business name", "your company")

    salutation = rotators["sal"].next().format(name=name)
    return (
        f"{salutation},\n\n"
        f"{rotators['fu2_p1'].next().format(name=name)}\n\n"
        f"{rotators['fu2_p2'].next().format(company=company)}\n\n"
        f"{rotators['fu2_p3'].next()}\n\n"
        f"{rotators['fu2_p4'].next()}\n\n"
        f"{rotators['fu2_p5'].next()}\n\n"
        f"{rotators['sig'].next()}"
    )

# --- Main ------------------------------------------------------------------

def main():
    leads = load_ndjson(LEADS_FILE)
    updated1 = updated2 = updated3 = 0

    for lead in leads:
        # Skip leads that only have "website url" and nothing else useful
        if set(lead.keys()) == {"website url"}:
            continue

        if not lead.get("email 1", "").strip():
            try:
                lead["email 1"] = build_email1(lead)
                updated1 += 1
            except Exception as e:
                print(f"⚠️ Skipping email 1 for {lead.get('website url', '[no url]')}: {e}")

        if not lead.get("email 2", "").strip():
            try:
                lead["email 2"] = build_email2(lead)
                updated2 += 1
            except Exception as e:
                print(f"⚠️ Skipping email 2 for {lead.get('website url', '[no url]')}: {e}")

        if not lead.get("email 3", "").strip():
            try:
                lead["email 3"] = build_email3(lead)
                updated3 += 1
            except Exception as e:
                print(f"⚠️ Skipping email 3 for {lead.get('website url', '[no url]')}: {e}")

    save_ndjson(LEADS_FILE, leads)
    print(f"✅ Done: {updated1} email 1s, {updated2} email 2s, {updated3} email 3s generated.")

if __name__ == "__main__":
    main()
