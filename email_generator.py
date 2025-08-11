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
    "You might not notice it right away, but unclear messaging can quietly turn good work into lost opportunities.",
    "You may not realize this, but mixed messages often add up to wasted time and missed revenue.",
    "It’s easy to miss, but when your story slips, your work can lose its impact.",
    "Have you noticed how small messaging gaps can turn good projects into missed chances?",
    "You might not see it at first, but inconsistent messaging tends to cost time and money.",
    "It’s easy to overlook; but unclear messages often mean more work and less revenue.",
    "You may not feel it daily, but those little messaging gaps add up over time.",
    "You may not be tracking this, but unclear messaging often chips away at productivity.",
    "You might not spot it in a meeting, but mixed messages quietly slow down progress.",
    "You may not notice immediately, but unclear messaging costs your business more time and money.",
    "It’s easy to miss, but inconsistent messaging makes good work harder to sell.",
    "You may not think about it much, but small communication gaps cost real money.",
    "You might not see the impact at first, but messy messaging often leads to missed opportunities.",
    "You may not feel it now, but unclear messaging quietly chips away at productivity and profit."
]

paragraph_2_variants = [
    "Those extra check-in calls can eat up billable hours.\n\nAnd since none of that time shows up on invoices, it might quietly drain your revenue.",
    
    "Pointless meetings that don’t go anywhere can eat into your week and leave less time to bill.\n\nOver time, that unpaid work may pile up and slow your whole business down.",
    
    "Follow-up calls that loop in circles can leave everyone worn out and cost billable time.\n\nIt’s the kind of work that might burn energy without bringing any return.",
    
    "Every pointless meeting is unpaid work that can take time away from doing chargeable work.\n\nThat might mean less money in the bank and more frustration for everyone.",
    
    "Unnecessary calls and check-ins can pile up into unpaid hours that add up quickly.\n\nIt may wear down everyone involved and shrink the hours you can actually invoice.",
    
    "All those small follow-ups can eventually turn into hours you might not bill and money you may not see.\n\nThe real cost can be how it drags everyone's energy and time.",
    
    "Those long status calls and repeat explanations can drag out in circles leave everyone tired.\n\nThose lost hours might not get paid, but they can cut into your profits.",
    
    "Those ‘quick’ calls can end up taking real, unbilled time out of your schedule.\n\nThat’s time you might spend on work that actually pays the bills.",
    
    "Clarification calls can keep coming back around and quietly cut into the hours you may bill.\n\nIt’s unpaid work that slowly eats into your profits.",
    
    "Each extra meeting usually means more emails and more unpaid follow-ups afterward.\n\nTogether, they can eat into your time and your revenue.",
    
    "That back-and-forth of calls and emails can take up time you might otherwise bill for.\n\nIt’s time lost that no one sees on the books but everyone feels.",
    
    "One unclear brief might start several unpaid follow-ups that eat into the quarter.\n\nBefore you know it, those hours may add up and shrink your margins.",
    
    "Repeated explanations can take small chunks out of the workweek; time you might not get paid for.\n\nThat slow leak may leave everyone worn out and cut down revenue.",
        
    "Those recurring check-ins can wear everyone down and turn billable time into lost hours.\n\nIt’s a hidden cost that might quietly waste time and profits.",
                    
    "All the back-and-forth around small details can quietly reduce the time you might actually bill.\n\nIt may wear down everyone involved and even shrink your revenue."
]

paragraph_3_variants = [
    "To cut the churn, we make clear whiteboard explainers that say your message once and say it well.",

    "To fix the mess, we create crisp whiteboard explainers that help everyone grasp your offer faster and easier.",

    "To stop the cycle, we build whiteboard videos that turn those boring bullet points into visuals that stick with your audience.",

    "To keep the story straight, we produce whiteboard videos that keep your business’s message sharp and easy to share.",

    "To replace the noise, we help you swap repeated emails and calls with a single, clear video everyone can reference.",

    "To clear things up, our whiteboard explainers break down complicated info into simple visuals so your message lands every time.",

    "To save everyone’s time, we build videos that simplify your story, so your business spends less time explaining and more time doing.",

    "To cut through the clutter, we make whiteboard videos that turn your offer into an easy-to-follow story.",

    "To remove the guesswork, our videos help your business communicate clearly, so prospects get the message without delay.",

    "To speed things up, our whiteboard explainers simplify your offer and make decisions easier.",

    "To reduce the back-and-forth, we build whiteboard explainers that deliver your message quickly and clearly every time.",

    "To fix the confusion, our whiteboard videos cut through the mess with clear, engaging visuals everyone trusts.",

    "To make sure it sticks, we design whiteboard explainers that make your value easy to remember and hard to miss.",

    "To stay aligned, we help your business tell one consistent story with whiteboard videos that drive action.",

    "To stop the rehash, we create whiteboard videos that make sure your message is delivered right the first time.",

    "To avoid do-overs, our whiteboard explainers give you one clear version of your pitch that works every time.",

    "To keep the focus, we build whiteboard videos that turn your core message into something easy to share and hard to ignore."
]

paragraph_4_variants = [
    "I can sketch a 10-second teaser for you; keep it or toss it.\n\nIf it’s not your thing, just reply NO and I’ll quietly step away.",
    "I'd be happy to draft a short sample script or 10 second teaser if you want; no strings, just a gift.\n\nIf you’re not interested, reply NO and I won’t bother you again.",
    "I’d be glad to put together a brief 10-second teaser for you; yours to keep or ignore.\n\nIf it’s not a fit, reply NO and I’ll disappear.",
    "If you’re open to it, I can create a quick script draft; no pressure at all.\n\nIf you’d rather not, reply NO and I’ll back off.",
    "I can send over a short 10-second teaser; whether you use it or not, it’s yours.\n\nIf you don’t want it, reply NO and I won’t follow up.",
    "I enjoy making these; happy to draft a quick teaser for you.\n\nIf you don’t want it, a simple NO will end it.",
    "I can put together a small teaser if you’re curious; no need to reply.\n\nIf it’s not useful, reply NO and I’ll go silent.",
    "If you’re interested later, I can have a 10-second teaser ready for you.\n\nIf not, just say NO and I’ll stop reaching out.",
    "You don’t have to decide now; I can send a 10-second teaser when you want.\n\nIf you don’t want it, reply NO and I’ll step away.",
    "I’d be happy to whip up a quick script for you; useful or not.\n\nIf it’s not your vibe, reply NO and I’ll take the hint.",
    "If you want, I can sketch a sample script; no strings attached.\n\nIf you want no more, just say NO and I’ll disappear.",
    "Just for reading, I can send over a rough 10-second teaser if you like.\n\nIf it’s not a fit, reply NO and I’ll bow out.",
    "I can share a quick script idea; yours to ignore or use.\n\nIf it’s not for you, reply NO and I won’t bother you again.",
    "I’d like to gift you a short teaser; no ask, no pressure.\n\nIf you don’t want it, just say NO and I’ll stop.",
    "I can quietly sketch a 10-second teaser; totally optional for you.\n\nIf it’s not useful, reply NO and I’ll fade away.",
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
    "Sending this again; maybe the timing was wrong.",
    "Thought this might be worth a second look, so here it is again.",
    "Giving this another shot before I set it aside.",
    "Not sure if my earlier note reached you, so I’m trying again.",
    "This might’ve slipped by earlier, so I’m passing it along again.",
    "Thought it’d be worth sending this again.",
    "Trying this again in case the first one didn’t land.",
    "Resending this in case it got lost",
    "Might’ve been a busy day when I first sent this; here’s another try.",
    "This is the same note I sent earlier, just making sure it reached you.",
    "Could be the first email missed you; here it is again.",
    "This might be worth another look, so I’m sending it again.",
    "Sending this one more time in case it’s still on your radar.",
    "Just passing this along again if it got buried.",
]

fu1_paragraph_2_variants = [
    "Like I said, every misread email or misunderstood deck can quietly drain the budget.\n\nThat money might not just disappear; it’s work you’ve already done but may not get paid for.",
    
    "You may not realize it, but re-explaining the same point over calls and threads can do more than burn time; it might chip away at profit, trust, and everyone’s patience.\n\nTighter messaging can stop those leaks before they get worse.",
    
    "When I reached out before, I mentioned how small misunderstandings might derail deals. The lost revenue can add up faster than you think.\n\nIt’s money that may never make it to your bottom line but can weigh on your business.",
    
    "As I said, back-and-forths can eat into billable hours you simply might not be able to charge for. If you’re busy explaining, you may not be delivering.\n\nThat slow drain might cost more than it looks at first glance.",
    
    "Like I noted, the real waste might not just be the emails; it can be ghosted leads, un-booked calls, and meetings that go nowhere.\n\nThat’s money that might be slipping through your fingers, not just wasted time.",
    
    "Here’s the thing: most businesses don’t really track how much they might lose repeating the same ideas in different ways.\n\nBut those unbilled hours can pile up in extra calls, more emails, and meetings that drag on.",
    
    "Just as I said last time, those extra meetings and calls that go in circles might cost more than they ever bring back.\n\nIt’s not just a messaging problem; it can be real money walking out the door.",
    
    "Like I said, inefficiency doesn’t have to be dramatic: it might look like those calls that drag out in circles or another pointless meeting booked.\n\nIt’s annoying, yes, but can also be expensive because that's wasted time you can't really invoice.",
    
    "Like I hinted; extra calls, emails, and meetings can add up fast. It might feel small until you tally how much of your week is gone.\n\nEven losing a couple hours a week can cost thousands annually.",
    
    "As I said, unclear communication might slow everyone down and quietly waste money.\n\nThose extra calls and pointless meetings can be hours you’ll never bill for, no matter how hard you work.",
        
    "As I said, every unanswered question or fuzzy brief may mean more emails, calls, and meetings.\n\nThat’s unbillable time slowly slipping away from your business, day by day.",
    
    "Like I mentioned, unclear messaging can cause extra follow-ups that waste time and money.\n\nThat slow drip of lost hours may eventually bite into your potential profits.",
    
    "You might not notice, but unclear offers might force your business to spend hours explaining instead of closing deals.\n\nThose lost hours can add up, cutting into your potential profits far more than you expect.",
            
    "You know those repeated questions and check-ins? They might cost you more billable time than you think.\n\nThose pointless meetings and calls that drag out in circles can be money that your business may not afford to lose.",

    "Like I said, small misunderstandings can lead to a lot of extra explaining and follow-ups.\n\nThat’s time and money your business might not get back.",
        
    "Like I mentioned, every unclear brief might mean more emails and calls just to get everyone on the same page.\n\nIt’s work you might be doing but won’t ever get paid for.",
    
    "The truth is, those repeated check-ins and follow-ups aren’t just annoying; they can be costly.\n\nIt’s billable time lost that your competitors might be cashing in on instead.",
]

fu1_paragraph_3_variants = [
    "To fix the mess, we create clear whiteboard explainers that lock your story down; no need for endless rehashing.",
    "To plug the leak, we make reusable whiteboard videos; one clean version of your message that lands every time.",
    "To break the cycle, we produce whiteboard videos your business can share again and again; no retelling required.",
    "To keep it straight, we build short whiteboard explainers that become the reliable go-to your business trusts.",
    "To stop the churn, we turn those boring bullet points into a single whiteboard video that’s sharp, clear, and memorable.",
    "To cut the fluff, we create whiteboard videos that condense your pitch so prospects watch once and get it.",
    "To save hours, we make whiteboard explainers that highlight your value instantly; all under two minutes.",
    "To cut the churn, we craft whiteboard videos that keep everyone aligned from the very first call.",
    "To avoid confusion, we build whiteboard explainers that say it clearly once; and make it stick for good.",
    "To speed decisions, we design whiteboard videos that simplify your offer and help prospects move faster.",
    "To plug the churn, we make whiteboard explainers you can drop into any presentation or pitch.",
    "To stop rehashing, we create whiteboard videos that lay out your value so clearly, no follow-up explanations are needed.",
    "To fix mixed messages, we build reusable whiteboard explainers; one crisp story, zero guesswork.",
    "To keep it consistent, we make whiteboard videos that give your business a steady story; no more mixed signals.",
    "To keep key points intact, our whiteboard explainers hit the same notes every time you meet with clients.",
    "To avoid the guesswork, our whiteboard videos make your message crystal clear, so prospects don’t have to fill in blanks.",
    "To cut through the mess, we build whiteboard videos that get everyone on the same page from the start.",
    "To move things forward, our whiteboard explainers help your business spend less time explaining and more time closing.",
    "To keep it smooth, we make whiteboard videos that help your message land every time without the extra effort.",
]

fu1_paragraph_4_variants = [
    "If it still feels relevant, I’ll gift you a short script this week. No strings, use it or toss it.\n\nIf it’s not a fit, reply 'NO' and I’ll scram.",
    "Totally happy to put together a 10-second teaser; whether you use it or not, it’s yours.\n\nIf you’d rather not, reply 'NO' and I’ll take you off my list.",
    "Still glad to draw up a teaser; no strings, no pitch, just a gift.\n\nIf this doesn’t click, reply 'NO' and I’ll disappear.",
    "If you’re open to it, I’ll send over a quick script idea; just something to keep on hand if it clicks later.\n\nIf it’s a no, reply 'NO' and I’ll bow out.",
    "If it’s helpful, I’ll draft a tiny teaser anyway. Yours to keep, no strings.\n\nIf it’s not your cup of tea, reply 'NO' and I’ll leave you be.",
    "Whether or not you’re in the market, I’d still enjoy putting together a short script.\n\nIf you’re not interested, reply 'NO' and I’ll quietly back away.",
    "I can draw up a 10-second teaser or a script. No strings.\n\nIf you’d prefer I didn’t, reply 'NO' and I’ll cross you off.",
    "Happy to create a quick 10-second teaser, whether or not we ever talk again.\n\nIf it’s not relevant, reply 'NO' and I’ll move along.",
    "I can put together a quick script outline this week; no strings attached.\n\nIf this isn’t up your alley, reply 'NO' and I’ll vanish.",
    "If it helps, I’ll make a short teaser for you to keep.\n\nIf it’s a pass, reply 'NO' and I’ll step aside.",
    "I’m happy to send over a quick script idea; use it however you like.\n\nIf you’re not feeling it, reply 'NO' and I’ll go quietly.",
    "If you want, I’ll put together a short teaser just so you have it.\n\nIf it’s not for you, reply 'NO' and I’ll head out.",
    "I could pull together a small script; no charge, no pitch.\n\nIf it’s not the right time, reply 'NO' and I’ll back off.",
    "If it’s useful, I’ll make a quick 10-second teaser to keep on file.\n\nIf it’s not a fit, reply 'NO' and I’ll fade away.",
    "Glad to mock up a short script draft for you; yours either way.\n\nIf you’d rather not, reply 'NO' and I’ll vanish.",
    "I’ll happily whip up a 10-second teaser you can keep, no commitment needed on your end.\n\nIf you’re not interested, reply 'NO' and I’ll get out.",
    "Happy to share a quick script outline that might make things easier.\n\nIf this isn’t your thing, reply 'NO' and I’ll step out.",
    "I can throw together a short 10-second teaser; take it or leave it.\n\nIf you’re not into it, reply 'NO' and I’ll walk away.",
    "I’ll write a short script and send it over, use it or ignore.\n\nIf it’s a no, reply 'NO' and I’ll drop it.",
    "Always happy to make a small 10-second teaser that might help down the road.\n\nIf it’s not for you, reply 'NO' and I’ll bow out."
]

#--------------EMAIL 3 TEMPLATES---------------------------------------------------------------------------

fu2_paragraph_1_variants = [
    "Just sending this one last time in case it slipped through.",
    "Before I close the loop, I wanted to send this one more time.",
    "Last call to see if this might be helpful before I step back.",
    "Sending this final note in case it’s still on your radar.",
    "Wrapping up some projects; wanted to make sure you saw this.",
    "One last quick message before I sign off.",
    "This is my final check-in to see if you want to take a look.",
    "Before I drop off your inbox, here’s a quick reminder.",
    "Final pass on this; let me know if it’s worth a chat.",
    "Just reaching out one last time to keep this top of mind.",
    "Last try to get this on your radar before I bow out.",
    "One last message to make sure you got this.",
    "Sending a final note; just making sure it reaches you.",
    "Before I step away, I wanted to share this one last time.",
    "This is the last time you’ll hear from me on this; unless you want to chat.",
    "Giving this one final attempt before I sign off.",
    "Final message in case it got lost earlier.",
    "Closing out with this quick reminder in case it helps."
]

fu2_paragraph_2_variants = [
    "Like I said earlier, unclear messaging can mean every extra call or email eats away at billable hours; over time, that might add up to thousands lost without you realizing it.",
    
    "As mentioned before, repeated explanations can mean your business spends less time delivering value and more time spinning wheels; quietly draining revenue week after week.",
    
    "As I mentioned, unclear communication can create confusion that might lead to missed deadlines and stalled projects; hitting your bottom line harder than you may expect.",
    
    "Like I pointed out, every no-show, ghosted lead, or wasted meeting isn’t just frustrating; it may be lost income piling up and shrinking your profit margins before you even notice.",
    
    "As I said before, endless back-and-forth emails and calls may seem minor, but they can add up to lost billable hours your business might not recover; quietly eating into growth and profits.",
    
    "Like I said earlier, a single unclear brief can trigger a chain reaction of extra work, calls, and emails that might drag down productivity; costing thousands in lost labor each quarter.",
    
    "You may not notice this, but poor communication can cost more than wasted time; it might frustrate clients, miss opportunities, and steal revenue before it reaches your books.",
    
    "As I mentioned, unclear messaging might slow your business down, forcing repeated explanations and avoidable questions; all potentially taking time away from billable work and cutting revenue.",
    
    "Like I pointed out, when your offer isn’t clearly understood, your business might spend valuable hours putting out fires instead of closing deals; causing a slow but steady revenue drain.",
    
    "As I said before, unclear or vague briefs can create extra work, follow-ups, and revisions.\n\nNone of which you may be able to bill for, yet all can cost real money and wasted effort.",
    
    "Like I said earlier, the real price of miscommunication can go beyond lost hours.\n\nIt might be deals that never close and clients who walk away before you even get started.",
    
    "Actually, when messaging falls short, your business might get stuck in cycles trying to explain; losing actual billable time that could have been spent more productively.",
    
    "As I mentioned, the longer you spend fixing misunderstandings and answering avoidable questions, the more your profits might shrink; quietly eating into your annual revenue.",

    "As I said earlier, when your message isn’t clear, deals may drag out or stall; potentially costing you billable hours and money you might not recover.",
    
    "You might not realize it, but poor communication might force your business into overtime and last-minute fixes; burning valuable billable time and cutting deeply into your profits.",

    "Like I mentioned before, every unclear interaction can lead to more back-and-forth emails and meetings; each one potentially eating away at billable time and quietly shrinking your profits.",

    "Actually, unclear messaging can trap your business in endless explanations instead of productive work; those unpaid hours might pile up fast and cut your revenue growth.",

    "As I said, poor communication doesn’t just slow things down; it can drain billable hours and break everyone's focus, which makes hitting revenue targets harder than it needs to be.",

    "Like I pointed out earlier, repeated explanations can cost far more than just time; they might chip away at your billable hours and put a real dent in your revenue potential.",

    "You might not notice at first, but unclear messaging can cause costly overtime and urgent firefighting that might burn through your billable time and even shrink your profits without warning."
]

fu2_paragraph_3_variants = [
    "To cut the churn, we build whiteboard explainers that capture your core message; so you don’t have to repeat yourself.",
    "To keep it consistent, we make sharp whiteboard videos; one clear story your business can share over and over.",
    "To plug those leaks, we create whiteboard videos that your business can lean on for consistent, clear messaging.",
    "To save time, we produce whiteboard explainers that serve as your go-to explanation; quick, clear, and reliable.",
    "To stop confusion, we turn your key ideas into a single whiteboard video that’s easy to understand and remember.",
    "To avoid blank stares, we make whiteboard videos that break down your pitch so prospects get it on the first watch.",
    "To save time, we develop whiteboard explainers that highlight your value clearly; all in under two minutes.",
    "To keep everyone in sync, we build whiteboard videos that keep your business aligned from day one onward.",
    "To avoid mixed messages, we deliver whiteboard explainers that say it once and make it stick for good.",
    "To speed decisions, we design whiteboard videos that streamline your pitch and help clients make decisions faster.",
    "To plug the leaks, we create whiteboard explainers that fit perfectly into any deck, proposal, or call.",
    "To cut the load, we produce whiteboard videos that explain your value so well, no extra follow-up is needed.",
    "To fix muddled messaging, we build reusable whiteboard explainers; one crisp story, zero confusion.",
    "To keep it clean, we turn your offer into a short whiteboard video that does the talking for you, every time.",
    "To stop guesswork, we create whiteboard videos that give your business a consistent, compelling story; no guessing or mixed signals.",
    "To keep it tight, our whiteboard explainers help your business stay on message every time you engage with prospects.",
    "To cut the mess, our whiteboard videos make your value obvious and easy to understand quickly; so clients don’t have to wonder.",
    "To keep momentum, our whiteboard explainers help your business spend less time explaining and more time closing deals.",
    "To land smoothly, we deliver whiteboard videos that help your message connect effortlessly; every time without the hassle.",
]

fu2_paragraph_4_variants = [
    "I can sketch a 10-second teaser for you; keep it or toss it.\n\nNo pressure, just something to have on hand if it helps.",
    "Happy to draft a short sample script if you want; no strings, just a gift.\n\nTotally up to you whether you use it or not.",
    "I’d be glad to put together a brief 10-second teaser for you; yours to keep or ignore.\n\nJust letting you know it’s available if you want it.",
    "If you’re open to it, I can create a quick script draft; no pressure at all.\n\nYou can decide if and when it’s useful.",
    "I can send over a short 10-second teaser; whether you use it or not, it’s yours.\n\nNo follow-up needed from your side.",
    "I enjoy making these; happy to sketch a quick sample script for you.\n\nUse it however you like.",
    "I can put together a small teaser if you’re curious; no need to reply.\n\nJust something to keep if it’s helpful down the road.",
    "If you’re interested later, I can have a 10-second teaser ready for you.\n\nNo rush or pressure, just here if it helps.",
    "You don’t have to decide now; I can send a 10-second teaser whenever you want.\n\nJust keeping it open if it’s useful.",
    "I’d be happy to whip up a quick script for you; useful or not.\n\nYour call to keep or ignore.",
    "If you want, I can sketch a sample script; no strings attached.\n\nJust a simple gesture to help if you need it.",
    "Just for reading, I can send over a rough 10-second teaser if you like.\n\nNo obligations, just here to assist.",
    "I can share a quick script idea; yours to ignore or use.\n\nNo pressure, just a little something in case it helps.",
    "I’d like to gift you a short teaser; no ask, no pressure.\n\nJust putting it out there if it’s useful to you.",
    "I can quietly sketch a 10-second teaser; totally optional.\n\nOnly if it feels right for you.",
    "I can create a quick teaser for you to keep.\n\nNo pressure, just something ready if you want it.",
    "Happy to put together a quick script idea.\n\nUse it if it works, ignore if it doesn’t.",
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
    "sig": VariantRotator(signatures),

    # Email 2 (follow-up 1)
    "fu1_p1": VariantRotator(fu1_paragraph_1_variants),
    "fu1_p2": VariantRotator(fu1_paragraph_2_variants),
    "fu1_p3": VariantRotator(fu1_paragraph_3_variants),
    "fu1_p4": VariantRotator(fu1_paragraph_4_variants),

    # Email 3 (follow-up 2)
    "fu2_p1": VariantRotator(fu2_paragraph_1_variants),
    "fu2_p2": VariantRotator(fu2_paragraph_2_variants),
    "fu2_p3": VariantRotator(fu2_paragraph_3_variants),
    "fu2_p4": VariantRotator(fu2_paragraph_4_variants),
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
    
    salutation = rotators["sal"].next().format(name=name)
    return (
        f"{salutation},\n\n"
        f"{rotators['p1'].next().format(name=name, company=company)}\n\n"
        f"{rotators['p2'].next().format(company=company)}\n\n"
        f"{rotators['p3'].next()}\n\n"
        f"{rotators['p4'].next().format(company=company)}\n\n"
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
