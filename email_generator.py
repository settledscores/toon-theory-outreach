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

# --- Salutations & Signatures ----------------------------------------------

salutations = [
    "Hi", "Hey", "Hello", "Hi there", "Hey there", "Hello there",
    "Good day"
]

openers = [
    "Hi {name}, I read about {company} a couple days back, so I figured I’d finally say hi.",
    "Hello {name}, I know inboxes are crowded so I’ll cut to the chase.",
    "Hi there {name}, Reaching out with a quick idea that might be up your alley.",
    "Hey there {name}, You might be the wrong person for this, but maybe not.",
    "Hi {name}, Dropping in with something that might be useful (or at least mildly interesting.)",
    "Hello {name}, Noticed some of the work you’re doing and thought it was worth getting in touch.",
    "Hi {name}, No fluff here, just a small idea I wanted to toss your way.",
    "Hi {name}, You can ignore this if it’s way off, but it might be a fit.",
    "Hey there {name}, I’ll keep this super quick; had an idea for {company}.",
    "Hey {name}, If this email is one of 200 you've gotten today, I’ll make mine short.",
    "Hi there {name}, I’ve got a weird idea that might actually help.",
    "Hey {name}, I’ve been in your shoes before, and this might save you some time.",
    "Hi {name}, Not pitching anything, just wanted to throw an idea your way.",
    "Hey there {name}, This might sound random, but it’s relevant; promise.",
    "Hello there {name}, Totally okay if this isn’t your thing, just sharing an idea.",
    "Hey {name}, If you hate cold emails, I’m with you; I’ll be brief.",
    "Hi {name}, Hoping to trade a tiny bit of your attention for a quick sketch of an idea.",
    "Hey {name}, I don’t send these often, just when I think it’s worth it."
]

paragraph_1_variants = [
    "I’m Trent. I run a small studio called Toon Theory. We draw videos by hand; it’s a fun way to show people what you do.",
    "I’m Trent. I started Toon Theory because sometimes words don’t cut it, a quick sketch can go a long way.",
    "I’m Trent and I run an animation studio called Toon Theory, we make short, hand-drawn videos. Not flashy, just clear and kind of charming.",
    "I’m Trent and Toon Theory is a tiny animation studio I run. We use doodles and voiceover to help teams share what they’re putting out there.",
    "I’m Trent. I run Toon Theory, it’s just a few of us drawing stories for people who don’t love PowerPoints.",
    "I’m Trent. I make short videos at a studio called Toon Theory. Think whiteboard sketches with a background voice, simple and watchable.",
    "I’m Trent and I’m the guy behind Toon Theory. We help people show what they mean without making it a whole production snag.",
    "I’m Trent. Toon Theory is my animation shop, mostly whiteboard videos with a human feel. Not too polished, not too stiff.",
    "I’m Trent and I started Toon Theory to make videos that feel like they were drawn by someone real, because they are.",
    "I’m Trent and I run Toon Theory. We sketch short videos for people who want to say big things without writing an essay.",
    "I’m Trent. Toon Theory is my little animation outfit. We work with voice, sketch, and story; that’s it.",
    "I’m Trent. I make videos at Toon Theory, mostly hand-drawn stuff that people don’t mind watching.",
    "I’m Trent. I started Toon Theory a while back. We draw things for people who need to explain what they’re up to.",
    "I’m Trent and I run an animation studio called Toon Theory. We don’t do fancy, just videos that feel real and personal.",
    "I’m Trent. Toon Theory is my studio, we draw little stories for people with big things to say.",
    "I’m Trent. Toon Theory is a small studio I run. We turn people’s thoughts into moving doodles."
]

paragraph_2_variants = [
    "If {company}'s services branch into different areas, a whiteboard video can help show how it all ties together. We handle script, voice, and visuals; all in-house.",
    "If {company} has multi-layered service offerings, a video can help connect the dots faster than words alone. We write, draw, and narrate the whole thing so you don't even have to move a muscle.",
    "{company} probably wears a few hats. A short explainer can help show how they all fit under one roof. We do the heavy lifting; script, voice, and illustration so you don't have to lift a finger.",
    "When {company}'s offer spans multiple areas, people sometimes need a guide to see how it all fits. These videos do that. You approve; we handle the rest.",
    "It’s hard to write copy for bundled or multi-layered service offerings; and we get that. At {company}, these videos can let you *show* people instead. No scriptwriting or heavy lifting needed on your end.",
    "We’ve worked with teams like {company} who offer multiple services that work best together. A short whiteboard-style video can show that without making people think too hard.",
    "When business like {company} offer more than one service, clarity gets tricky. A whiteboard video can walk people through it; kind of like a mini tour.",
    "If it ever feels like the work at {company} is easier to show than tell, that’s where we come in. We make short explainer videos that do the talking for you.",
    "Services like those at {company} don’t always click in a single headline. We build short videos to walk people through the ‘why it matters’ part; full creative done for you.",
    "{company} probably has a lot going on behind the scenes. A quick video can pull it all together in a way that feels approachable, not overwhelming.",
    "We’ve helped other multi-layered service businesses show how everything connects. Same could work for {company}; all we’d need is a bit of your input upfront, while we do the rest of the heavy lifting.",
    "If there’s a lot to explain at {company} but you don’t want to overload folks with text, video might be a lighter way to go. We’ll draw it out; fully done-for-you.",
    "Trying to explain too much at once is tough. If that ever happens at {company}, this kind of explainer helps lay it out clearly without losing people. We handle all production in-house so all you have to do is hit play.",
    "When it’s hard to describe what {company} does without going on a tangent, a short video can anchor the message. That’s what we build; and I think it could help.",
    "{company} sounds like one of those teams with a lot of valuable offerings. A short video could help people see the whole picture at once. We take care of it all; illustrations, voice, script; and it's fully in-house."
]

paragraph_3_variants = [
    "These videos are pretty low-lift; most folks use them across their homepage, email, or even onboarding.",
    "They’re short, hand-drawn, and easy to reuse anywhere you need to explain what you do.",
    "They’re not fancy or high-budget; just a simple way to say something once and use it everywhere.",
    "Clients end up dropping these into proposals, landing pages, even training. Super versatile.",
    "They’re quick to watch and easy to share; kind of like a visual elevator pitch you can repurpose.",
    "Most teams keep reusing them; on websites, in follow-ups, or even onboarding flows.",
    "It’s not studio-glossy stuff; just helpful and reusable in lots of spots.",
    "People usually end up using these in more places than they expected; website, email, intros, that kind of thing.",
    "They tend to stick around; folks re-use them in demos, sales decks, or even hiring.",
    "Nothing flashy; just something that helps people catch on faster, and reuse again and again.",
    "Teams often plug them into their homepage, newsletters, or even client onboarding kits.",
    "They’re built once, but tend to get reused in all kinds of conversations.",
    "It’s not the kind of video you watch once and forget; most clients use them on repeat.",
    "They slot in wherever you need a quick ‘here’s what we do’; homepage, sales call, whatever.",
    "Most folks use them as evergreen explainers; handy whenever someone asks ‘so what do you do?’",
    "They’re simple enough to live on your homepage but clear enough for email intros and decks too.",
    "It’s a single piece of content, but it usually earns its keep across different touchpoints.",
    "Once you’ve got one, you can drop it into all sorts of places where words fall short.",
    "They’re short, visual, and surprisingly sticky; people keep watching and rewatching.",
    "These things tend to travel well; from landing pages to pitches and everything in between."
]

paragraph_4_variants = [
    "If you’re open to it, I could put together a quick sketch or sample script; just something to see if the tone feels right.",
    "Happy to mock up a small piece; maybe a 10-second snippet; to give you a sense of how this could sound.",
    "Could sketch something out if you’re curious; nothing polished, just a rough idea to react to.",
    "If you want to see what this might look like in your world, I could draft a short example.",
    "No pressure at all; I can put together a tiny demo if it helps spark ideas.",
    "Totally optional, but I’d be glad to send over a first-pass sketch. Just to play around with.",
    "If you’re game, I could draft a tiny voice-over or outline to show how this might work for you.",
    "Always happy to put pen to paper. I could sketch something simple out; no strings.",
    "Let me know if you’d like to see how this could sound for {company}; happy to whip up a short draft.",
    "I could mock something up if you want to see how it might land in your tone of voice.",
    "If it helps to see it in action, I can send over a tiny preview; even just a first line or two.",
    "Just say the word if you’d like a tiny prototype; I keep things super scrappy at first.",
    "I could take a stab at a quick draft; no expectations, just to get a sense of the vibe.",
    "Happy to play with a short version if you want to see what it might feel like in practice.",
    "If you're even a little curious, I can sketch a 10-second version just to test the waters.",
    "I’d be happy to map out a quick intro or 10 second snippet if you want to see what it could look like.",
    "Let me know if you want a quick visual mock; no deck, no pitch, just a sketch.",
    "This might be easier to show than tell; happy to put a sample together if you’re up for it.",
    "If it sounds halfway interesting, I’d be glad to draw something up; just a loose draft to react to."
]

paragraph_5_variants = [
    "Reply anytime if you're even a little interested; and feel free to check out some previous work in my signature. Just reply 'NO' if you'd prefer not to hear from me again.",
    "If this sparks even a bit of curiosity, you can reply whenever. I also added a few past projects in my signature. Totally fine to reply 'NO' if you'd rather not get future emails.",
    "You can reply whenever if this seems worth exploring. There’s some past work in my signature below. Or just send 'NO' if this isn’t your thing.",
    "No rush; reply if you're even slightly interested. You can take a peek at what we’ve done before in my signature. Also say 'NO' if you don't want me to reach out again.",
    "If you're curious at all, feel free to reply. There’s some previous work listed in my signature. And if this isn’t for you, just reply 'NO'.",
    "You’re welcome to reach out if this interests you. A few examples are included in my signature; and if not your thing, a simple 'NO' will take you off my list.",
    "Reply anytime if it feels like something you’d want to chat more about. You’ll see some past examples of our work in my signature. Totally fine to reply 'NO' if not.",
    "If any part of this felt interesting, you can always reply. Some previous projects are listed in the signature. Or reply 'NO' and I won’t send anything else.",
    "Happy to hear from you if this caught your eye. You’ll find some examples down below if you’d like to browse; or just reply 'NO' if you’d rather not get follow-ups.",
    "You’re free to ignore this, but if you're at all interested, reply anytime. A few past projects are mentioned below in my signature. Just say 'NO' if you'd prefer no future messages."
]

signatures = [
    "Warmly,\nTrent — Toon Theory\ntoontheory.com\nWhiteboard videos your customers will actually remember.",
    "All the best,\nTrent — Founder, Toon Theory\nwww.toontheory.com\nTrusted by consultants, coaches, and businesses who care about clarity.",
    "Cheers,\nTrent — Toon Theory\nhttps://toontheory.com\nExplainer videos made to convert, not just impress.",
    "Take care,\nTrent — Toon Theory\nwww.toontheory.com\nThe explainer video partner for thoughtful, service-based brands.",
    "Sincerely,\nTrent — Founder, Toon Theory\ntoontheory.com\nHelping you teach, pitch, and persuade in under two minutes.",
    "Best wishes,\nTrent — Toon Theory\nwww.toontheory.com\nAnimation for experts who need to sound less 'expert-y'.",
    "Kind regards,\nTrent — Founder, Toon Theory\nhttps://www.toontheory.com\nExplainers that turn confusion into conversion.",
    "With appreciation,\nTrent — Toon Theory\ntoontheory.com\nWhiteboard videos your customers will actually remember.",
    "Respectfully,\nTrent — Toon Theory\nhttps://toontheory.com\nTrusted by consultants, coaches, and businesses who care about clarity.",
    "Warm regards,\nTrent — Founder @ Toon Theory\nwww.toontheory.com\nExplainer videos made to convert, not just impress.",
    "Regards,\nTrent — Toon Theory\nhttps://www.toontheory.com\nThe explainer video partner for thoughtful, service-based brands.",
    "With gratitude,\nTrent — Toon Theory\nwww.toontheory.com\nHelping you teach, pitch, and persuade in under two minutes.",
    "Yours truly,\nTrent — Founder, Toon Theory\ntoontheory.com\nAnimation for experts who need to sound less 'expert-y'.",
    "Faithfully,\nTrent — Toon Theory\nwww.toontheory.com\nExplainers that turn confusion into conversion.",
    "Thanks again,\nTrent — Toon Theory\nhttps://www.toontheory.com\nExplainer videos made to convert, not just impress."
]

# --- Email 2 Templates ------------------------------------------------------

email2_templates = [
    """{salutation} {name},

Just looping back in case this got lost in your inbox. I mentioned how whiteboard animation could support {company}’s messaging ; and I still believe there’s a great fit here.

These videos are especially helpful when you’re trying to explain something technical, strategic, or new in a way that sticks.

If it helps, I’d be happy to put together a short script or quick teaser to show what this could look like.

Feel free to reply if you’d like to explore it. You’ll find examples of our work in my signature. If it’s not a fit, feel free to reply with a quick “NO” and I won’t reach out again.

{signature}""",

    """{salutation} {name},

Wanted to follow up in case this timing works better for you. Whiteboard animation can be a surprisingly simple way to make your message clearer and more memorable; especially in B2B settings.

For {company}, this could mean increased understanding and stronger engagement, both internally and externally.

If you're still open to that quick sketch or demo, I’d be happy to create one based on something you’re working on.

There are some past projects in my signature if you’d like to browse. And of course, just reply “NO” if you’d rather not hear from me again.

{signature}""",

    """{salutation} {name},

Just circling back. I realize it can be tricky to see how something like whiteboard animation fits into a business like {company}, which is why I’d love to show rather than tell.

If you’d be open to a 10-second snippet or a short script tailored to one of your core offerings, I’d be glad to share.

It’s no obligation, just a way to explore what this could look like in your context.

You’ll find some of our past work in my signature. If this isn't something you're interested in, replying with “NO” will do the trick.

{signature}""",

    """{salutation} {name},

Following up briefly in case you’re still open to exploring how animated storytelling could help simplify {company}’s messaging.

It’s something that’s worked well for businesses trying to explain detailed services, product workflows, or industry insights in a more digestible way.

Happy to create a short, customized sample if you’d like a clearer sense of how this could look.

Reply anytime; there’s also some of our previous work mentioned below. Or just reply “NO” if you'd prefer not to receive future messages.

{signature}""",

    """{salutation} {name},

I didn’t want to leave things hanging without checking in. I mentioned how whiteboard animation can be a strong complement to what {company} is already doing, especially when you’re communicating ideas that needs a touch of individuality.

If it’s helpful, I can pull together a short visual sketch or sample script based on one of your key offerings.

No pressure; just a creative starting point for you to consider.

You’ll find some of our work in my signature. If it’s not for you, feel free to just reply “NO” and I’ll close the loop here.

{signature}""",

    """{salutation} {name},

Reaching out again in case the idea of using whiteboard animation is still on your radar.

It’s often a great fit for simplifying dense content, making internal updates more engaging, or curating educational content that feel less overwhelming and more human.

For {company}, I’d be glad to sketch a quick visual or draft a short script so you can see what this might look like in practice.

Reply when you can, or check out some examples in the signature below. If you’re not interested, a quick “NO” will ensure no follow-ups.

{signature}""",

    """{salutation} {name},

Quick follow-up in case now’s a better time. My last note was about how visual storytelling could support {company}'s messaging for doubled impact.

If you're curious, I could create a ten-second teaser or a rough script so you can get a sense of what’s possible.

Just reply if you’d like to explore. There are some previous work samples in the signature below. If not, no worries at all — just send “NO”.

{signature}""",

    """{salutation} {name},

I wanted to briefly follow up to see if the idea of a quick, low-lift sketch might interest you.

These kinds of animations are used to clarify big-picture strategies, improve training content, or explain services in a more human way.

If {company} has something complex or critical to explain, I’d love to put together a sample to show what it might look like.

Reply when ready, and check out some past examples mentioned below. Or simply reply “NO” if you'd like to opt out.

{signature}""",

    """{salutation} {name},

I know inboxes get full fast, so here's a quick follow up.

Whiteboard storytelling might be a surprisingly effective way for {company} to simplify something your audience or team needs to grasp quickly.

If you’re still open to it, I can send a short demo such as a sample script or 10-second sketch, just to give you a feel.

Let me know, or feel free to check out some of our past work in the signature. And if you’re not interested, just reply “NO”.

{signature}""",

    """{salutation} {name},

Just checking in one more time.

I understand if now’s not ideal, but I still think there’s value in exploring how a short whiteboard video could help {company} communicate more clearly.

It could be a great fit for onboarding, product overviews, or thought leadership; and I’d be happy to show you a no-cost sample.

You can reply any time, or check out some of our past work in my signature. Or just send a quick “NO” if you’re not looking to explore this.

{signature}""",

    """{salutation} {name},

I wanted to circle back following my last email about using whiteboard animation at {company}. These videos can really simplify complex ideas and help you connect with your audience in a memorable way.

If you’re open to it, I’d love to put together that quick sketch or script I mentioned earlier; something tailored specifically to one of your key offerings or a new product launch, perhaps.

Feel free to reply anytime. And just in case you missed it, some of our past projects are in my signature. If this isn’t your thing, replying “NO” is all it takes.

{signature}""",

    """{salutation} {name},

Just circling back as I didn’t want you to miss out on the chance to explore whiteboard animation for {company}.

Our videos are designed to help businesses like yours increase engagement, boost clarity, and convert more customers; all with animated storytelling.

If you'd like, I can create a short demo or script as a no-pressure way to see how this could work for your team.

You’ll find examples of our work in my signature. Let me know if you’d like to see something specific, or just reply “NO” if not.

{signature}""",

    """{salutation} {name},

Following up on my previous note about whiteboard animation at {company}.

Many of our clients find these videos help explain their offerings faster and more clearly, which often leads to more meaningful conversations and better results.

If it’s helpful, I’d be happy to draft a quick concept or short sample that fits your brand voice and messaging.

You can reply anytime, and our portfolio is in the signature if you want to get a feel for what we do. If not interested, replying “NO” will stop future messages.

{signature}""",

    """{salutation} {name},

I wanted to check back in and remind you about the offer I shared earlier; a 10 second sketch that could spark some ideas.

It’s a simple, no-strings way to explore how animation can support your {company}'s messaging and help your audience understand your value offerings more clearly.

Feel free to reply if you want to see this, or browse some of our previous projects in my signature. Just reply “NO” if you’d rather I not follow up again.

{signature}""",

    """{salutation} {name},

Just wanted to touch base after my last email about how {company} could benefit from whiteboard animation.

This type of video storytelling often boosts engagement and helps simplify complicated topics; making your message more human and easier to remember.

If you’re curious, I’d be glad to draft a short teaser or script for you to review.

Please reply anytime. Not interested? A quick “NO” is fine.

{signature}""",

    """{salutation} {name},

Reaching out again about the opportunity for {company} to stand out using whiteboard animation.

Whether it’s for pitching, explaining products, or internal training, these videos really hit the nail on the head.

If you’re open to it, I can prepare a quick sketch or script sample tailored to your brand; no pressure at all.

You’ll find examples of our previous work mentioned below. Let me know if you’d like to explore the fit, or reply “NO” if you’d rather pass.

{signature}""",

    """{salutation} {name},

Hope this finds you well. I’m following up on my previous note offering a quick, no-commitment demo to show how whiteboard animation might work for {company}.

These animations are a great way to explain services or products in an engaging, easy-to-understand format.

If you’d like me to put something together, just let me know. Some past examples are listed below too. Otherwise, feel free to reply “NO” if you’re not interested.

{signature}""",

    """{salutation} {name},

Just reaching out again about the possibility of using whiteboard animation to enhance {company}’s messaging.

This approach often helps businesses increase engagement, simplify communication, and improve conversion rates.

If you’re curious, I’d be happy to draft a quick demo or script for you to review at your convenience.

You can reply any time. If it’s not something you want to pursue, replying “NO” is totally fine.

{signature}"""
]

# ---EMAIL 3 TEMPLATES---------------------------------------------------------------------------

email3_templates = [
    """{salutation} {name},

Just circling back in case the timing makes more sense now. I still believe whiteboard animation could support something {company} is working on, whether that is a pitch, process, or product.

If you would like to test the waters, I am happy to sketch something out to show what it might look like.

You will find past examples in my signature. Feel free to reply if you would like to explore this.

{signature}""",

    """{salutation} {name},

I am still happy to share a quick sketch or demo if it is helpful. Many of our clients use animation to break down services, explain strategy, or walk users through dashboards and pages.

If {company} has anything you are trying to simplify, I would love to help you explore it. Just reply if you want me to send something over.

You will also find examples of past work in my signature below.

{signature}""",

    """{salutation} {name},

Thought I would check in one last time.

If you are still curious what an animated whiteboard explainer might look like for {company}, I would be glad to share something rough, a short teaser, or a script to get the ball rolling.

You can find our work in my signature. Reply anytime if you are interested.

{signature}""",

    """{salutation} {name},

Just reaching out again before I close this thread. If you think animated storytelling could be of value to {company}, I would love to put something together.

Even a 10-second sketch can be a useful way to explore what is possible.

Feel free to reply at your convenience.

{signature}""",

    """{salutation} {name},

If you are still considering creative ways to showcase {company}'s value offerings, animated storytelling could be the missing piece of the puzzle to accelerate those conversions.

I would be happy to send over a short visual teaser to get the ideas flowing.

No pressure, just a creative option to keep in mind. Reply anytime or take a peek at some of our previous work. It is in my signature.

{signature}""",

    """{salutation} {name},

Circling back once more before I close the loop.

If there is anything at {company} you have been meaning to simplify, such as those boring quarterly reports your team never reads, then whiteboard animation could help bring that to life.

I would be happy to sketch something if you want to see what that might look like. You can reply anytime or check out some of our previous work in my signature.

{signature}""",

    """{salutation} {name},

Reaching out one last time before I close the loop. If you are still exploring creative ways to showcase what {company} offers, this could be a great fit.

I would be glad to put together a simple teaser or sketch if you are curious. Reply at your convenience or check out some of our past projects. You will find them in my signature.

{signature}""",

    """{salutation} {name},

I hope your week is going well. I am wrapping up some projects and wanted to reach out again before I close things out.

If you would still like to explore using whiteboard videos to support {company}'s messaging, I would love to help. Simply reply or take a peek at some of our previous work. It is in my signature.

{signature}""",

    """{salutation} {name},

A quick follow-up before I close out my list. If now is not the right time, no worries at all.

But if you are a little curious about how whiteboard animation might help {company}, I am still open to sharing a quick demo. No pressure. You can reply anytime or skim through some of our previous projects to see what we have done for other businesses. They are in my signature.

{signature}""",

    """{salutation} {name},

Just one last follow-up in case you missed my previous notes. I would still be happy to sketch a teaser for {company} if you are curious to see what whiteboard animation can do.

It could help simplify one of your key offerings or assist with your latest project launch. If you are a little curious, just hit reply or check out some of our past work in my signature.

{signature}""",

    """{salutation} {name},

I just wanted to check in again and see if the idea of using whiteboard animation for {company} has sparked any interest. Animation can be a great way to highlight key messages and bring stories to life in a memorable way.

If you'd like, I can put together a simple draft or a short sample video to show how this could work for you.

You can also find examples of our previous work in my signature. Please don’t hesitate to reply if you want to explore this.

{signature}""",

    """{salutation} {name},

Following up once more because I think animation could really help {company} communicate ideas in a clear and compelling way. Many of our clients have seen great results from adding this creative touch to their messaging.

I’d be happy to sketch out a quick teaser or draft a script that suits your brand and goals.

Feel free to reply if you’d like to see what this might look like. You’ll find our past projects in my signature.

{signature}""",

    """{salutation} {name},

I hope this note finds you well. I’m reaching out again to offer a creative way for {company} to stand out using animated whiteboard videos.

Even a short, simple animation can make complex ideas easier to understand and more engaging for your audience.

If that sounds interesting, I’d be glad to prepare a brief sketch or a script to share with you.

Please reply anytime. Past examples are in my signature.

{signature}""",

    """{salutation} {name},

Just wanted to reconnect in case my previous notes got buried. If you have any questions or thoughts about using whiteboard animation at {company}, I'd be more than happy to answer them.

It’s a creative way to explain your value offerings, and it can really help with marketing, training, or internal communications.

If you’d like, I can send over a quick teaser or script sample.

You’ll find some of our past work in my signature. I’m here if you want to chat.

{signature}""",

    """{salutation} {name},

Checking in again to share how whiteboard animation could help {company} communicate clearly and creatively with your audience.

Animation can make even the most complicated topics accessible and engaging, which often leads to better engagement.

If you’re open to it, I’d love to draft a short visual concept for you to review.

Feel free to reply anytime, and you can see examples of our work in my signature.

{signature}""",

    """{salutation} {name},

I wanted to reach out once more to highlight the potential benefits of whiteboard animation for {company}.

Whether it’s for sales, marketing, onboarding, or internal messaging, animation can be a great tool to simplify ideas and keep people interested.

If you’re curious, I’d be happy to create a short sample or script that fits your goals.

Please reply whenever you’re ready. Past projects are in my signature.

{signature}""",

    """{salutation} {name},

Just following up again because I think animation could add real value to {company}’s messaging.

It’s an engaging way to capture attention and explain what makes your business stand out.

If it sounds useful, I’d be glad to prepare a quick teaser or script to show you what’s possible.

You can reply anytime, and our portfolio is in my signature.

{signature}""",

    """{salutation} {name},

I’m checking in one last time about the opportunity to use whiteboard animation at {company}.

Many teams find that even short animations help simplify their message and make content more digestible.

If you’d like, I can put together a brief teaser or script to help you explore this option.

Please feel free to reply at any time. Examples of our work are in my signature.

{signature}""",

    """{salutation} {name},

Just wanted to follow up to see if you’ve had a chance to consider using whiteboard animation at {company}.

It’s a creative way to bring your ideas to life and connect with your audience more effectively.

If you’re interested, I’d be happy to share a quick demo or script tailored to your needs.

You’ll find past examples in my signature. Reply whenever you’re ready.

{signature}""",

    """{salutation} {name},

I wanted to check in one last time to offer support if you’re thinking about how {company} could benefit from whiteboard animation.

We’ve helped many businesses explain their offerings clearly and creatively through short, engaging videos.

If you’d like, I can draft a quick sample to show how this might work for you.

Please don’t hesitate to reply. Our past projects are in my signature.

{signature}"""
]

# --- Rotators --------------------------------------------------------------

rotators = {
    "o": VariantRotator(openers),
    "p1": VariantRotator(paragraph_1_variants),
    "p2": VariantRotator(paragraph_2_variants),
    "p3": VariantRotator(paragraph_3_variants),
    "p4": VariantRotator(paragraph_4_variants),
    "p5": VariantRotator(paragraph_5_variants),
    "sig": VariantRotator(signatures),
    "e2": VariantRotator(email2_templates),
    "e3": VariantRotator(email3_templates),
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
    salutation = random.choice(["Hey", "Hi", "Hello"])
    signature = rotators["sig"].next()
    return rotators["e2"].next().format(salutation=salutation, name=name, company=company, signature=signature)

def build_email3(lead):
    name = lead.get("first name", "there")
    company = lead.get("business name", "your company")
    salutation = random.choice(["Hey", "Hi", "Hello"])
    signature = rotators["sig"].next()
    return rotators["e3"].next().format(salutation=salutation, name=name, company=company, signature=signature)

# --- Main ------------------------------------------------------------------

def main():
    leads = load_ndjson(LEADS_FILE)
    updated1 = updated2 = updated3 = 0

    for lead in leads:
        if not lead.get("email 1", "").strip():
            lead["email 1"] = build_email1(lead)
            updated1 += 1
        if not lead.get("email 2", "").strip():
            lead["email 2"] = build_email2(lead)
            updated2 += 1
        if not lead.get("email 3", "").strip():
            lead["email 3"] = build_email3(lead)
            updated3 += 1

    save_ndjson(LEADS_FILE, leads)
    print(f"✅ Done: {updated1} email 1s, {updated2} email 2s, {updated3} email 3s generated.")

if __name__ == "__main__":
    main()
