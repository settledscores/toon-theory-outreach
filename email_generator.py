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
    "Good day", "Greetings", "Howdy"
]

signatures = [
    "Warm regards,\nTrent — Founder, Toon Theory\nwww.toontheory.com",
    "All the best,\nTrent — Founder, Toon Theory\nwww.toontheory.com",
    "Cheers,\nTrent — Founder, Toon Theory\nwww.toontheory.com",
    "Take care,\nTrent — Founder, Toon Theory\nwww.toontheory.com",
    "Sincerely,\nTrent — Founder, Toon Theory\nwww.toontheory.com",
    "Best wishes,\nTrent — Founder, Toon Theory\nwww.toontheory.com",
    "Kind regards,\nTrent — Founder, Toon Theory\nwww.toontheory.com",
    "With appreciation,\nTrent — Founder, Toon Theory\nwww.toontheory.com",
    "Respectfully,\nTrent — Founder, Toon Theory\nwww.toontheory.com"
]

# --- Paragraph Templates for Email 1 ---------------------------------------

paragraph1_templates = [
    "Hi {name},\n\nI came across {company} recently and wanted to reach out directly.",
    "Hello {name},\n\nI just saw {company} and thought you might be the right person to speak with.",
    "Hey {name},\n\nI came across {company} recently and thought I’d drop you a quick note.",
    "Hi {name},\n\nI stumbled on {company} the other day and wanted to get in touch.",
    "Hi {name},\n\nI stumbled across {company} and thought I’d reach out.",
    "Hi {name},\n\nI came across {company} recently and thought there could be an opportunity to collaborate."
]

paragraph2_variants = [
    "I'm Trent, and I run Toon Theory; an animation studio based in the UK. We make whiteboard videos that break down complex ideas with simple, hand-drawn visuals. It’s perfect for B2B, thought leadership, and data-heavy education.",
    "I'm Trent. I run Toon Theory, a whiteboard animation studio in the UK. We make simple, story-driven explainer videos that help people understand dense ideas. They're great for B2B services, thought leadership, and data-rich education.",
    "I'm Trent, and I run Toon Theory; an animation studio based in the UK. We use hand-drawn animations to help businesses get their message across. It's a simple way to cut through noise, especially in B2B, thought leadership, and data-heavy fields."
]

paragraph3_additional_variants = [
    "For {company}, I see a great opportunity to use visual storytelling to help more people “get it” faster. Our animations are fully done-for-you: script, illustrations, voice, and storyboard; and they’re great for:\n",
    "I think {company} could really benefit from using visual storytelling to explain things faster and make them stick. We take care of everything: scripting, illustration, voiceover and storyboarding; so you can use the final video for:\n",
    "{company} has a strong foundation, and a short animated video could be a powerful way to bring your message to life. We’ll take care of the full creative lift: script, voice, and illustrations, so you can use it for:\n"
]

paragraph4b_variants = [
    "These videos often help businesses increase engagement by up to 60%, double conversion rates, and boost message retention by up to 80%.",
    "These animations don’t just explain, they convert; Many of our past clients see a big lift in engagement, trust, and sales.",
    "Clients often tell us these pieces help reduce bloat, increase clarity, and lead to more meaningful conversions.",
    "Whether it’s more signups, better retention, or faster understanding, these animations know how to hit hard and they move the needle where it counts."
]

paragraph5_variants = [
    "If you’re open to it, I’d love to share a quick demo built around something {company} offers. Just a sketch or script; no pressure, no pitch; just curious to see what it might sound like in your voice.",
    "I could pull together a quick sketch or sample script based on one of {company}’s core offerings. Just a lightweight preview, no expectations; just to show what’s possible.",
    "I'd be happy to draft a ten-second demo around something core to your brand. Totally low-lift, just keen to explore what this could look like with {company}'s voice behind it.",
    "Would you be open to seeing a quick script or ten-second sketch built with {company} in mind? No expectations; just interested in showing you what’s possible.",
    "If you're open to a quick preview, I could whip up a ten-second mock or short script tailored to something core at {company}; No pressure, no cost, purely exploratory.",
    "I'd be more than happy to whip up a quick snippet; a short script or sketch; that speaks to what {company} does best. No commitments at all, just a chance to show you what's possible.",
    "I’d be glad to pull together a short demo; maybe a script or quick sketch; based on what {company} does best. No pressure, just a chance to preview what it might look and sound like.",
    "If you're curious, I could draft a ten-second teaser or sketch based on what {company} offers. Nothing formal. Just something you can react to, no strings or expectations.",
    "I’d love to put together a quick concept; maybe a script or a short teaser; around one of your key offerings. No strings, just a preview of what's possible with {company}'s voice behind it.",
    "How about a quick sample built around {company}'s strengths? Ten seconds or so, just a feeler to see what resonates.",
    "Could I sketch something out for you? A short demo or script idea based on what {company} offers. No pitch; just something for you to react to."
]

paragraph6_variants = [
    "Thanks for putting something refreshing out there.",
    "Thanks for leading with both heart and strategy.",
    "Keep doing what you do, it's making an impact."
]

paragraph7_cta_variants = [
    "Feel free to reply if you’d like to explore this a bit more. There’s also a link to our site in my signature if you’d like to take a peek at some past work.",
    "You’ll find a link to our site in the signature if you’d like to see a few examples. And if anything clicks, I’d love to hear your thoughts.",
    "If it feels like a fit, you can reply any time. There’s also a link in my signature in case you want to browse a few previous projects.",
    "If you're open to chatting more, just hit reply. And if you're curious, there’s a site link in the signature with a few past examples.",
    "If you’re curious about what this might look like, just reach out. There’s a link in my signature with a few examples you can check out, too.",
    "I’d be happy to dig in deeper if you’re interested. Just reply anytime, and feel free to check out some of our work through the link in my signature.",
    "Let me know if you'd like to take this further. You can check out some of our work through the link in my signature as well.",
    "Always open to a quick chat if this feels worth exploring. In the meantime, you can view a few past projects via the link in my signature.",
    "Reply anytime if you'd like to talk more about this. There’s also a link below with some samples of what we’ve done before.",
    "Just reach out if you’d like to continue the conversation. You’ll find a few previous projects linked in the signature below."
]

# --- Email 2 Templates ------------------------------------------------------

email2_templates = [
    """{salutation} {name},

Just looping back in case this got lost in your inbox. I mentioned how whiteboard animation could support {company}’s messaging ;  and I still believe there’s a great fit here.

These videos are especially helpful when you’re trying to explain something technical, strategic, or new in a way that sticks.

If it helps, I’d be happy to put together a short script or quick teaser to show what this could look like.

Feel free to reply if you’d like to explore it. You’ll find examples of our work in my signature.

{signature}""",

    """{salutation} {name},

Wanted to follow up in case this timing works better for you. Whiteboard animation can be a surprisingly simple way to make your message clearer and more memorable ;  especially in B2B settings.

For {company}, this could mean increased understanding and stronger engagement, both internally and externally.

If you're still open to that quick sketch or demo, I’d be happy to create one based on something you’re working on.

There’s a link to our past projects in my signature if you’d like to browse.

{signature}""",

    """{salutation} {name},

Just circling back. I realize it can be tricky to see how something like whiteboard animation fits into a business like {company}, which is why I’d love to show rather than tell.

If you’d be open to a 10-second snippet or a short script tailored to one of your core offerings, I’d be glad to share.

It’s no obligation, just a way to explore what this could look like in your context.

You’ll find some of our past work linked in my signature.

{signature}""",

    """{salutation} {name},

Following up briefly in case you’re still open to exploring how animated storytelling could help simplify {company}’s messaging.

It’s something that’s worked well for businesses trying to explain detailed services, product workflows, or thought leadership content in a more digestible way.

Happy to create a short, customized sample if you’d like a clearer sense of how this could look.

Reply anytime;  there’s also a link to our previous work below.

{signature}""",

    """{salutation} {name},

I didn’t want to leave things hanging without checking in. I mentioned how whiteboard animation can be a strong complement to what {company} is already doing, especially when you’re communicating ideas that needs a touch of personalization.

If it’s helpful, I can pull together a short visual sketch or sample script based on one of your key offerings.

No pressure;  just a creative starting point for you to consider.

You’ll find some of our work linked in my signature.

{signature}""",

    """{salutation} {name},

Reaching out again in case the idea of using whiteboard animation is still on your radar.

It’s often a great fit for simplifying dense content, making internal updates more engaging, or curating educational content that feel less overwhelming and more human.

For {company}, I’d be glad to sketch a quick visual or draft a short script so you can see what this might look like in practice.

Reply when you can, or check out some examples in the signature below.

{signature}""",

    """{salutation} {name},

Quick follow-up in case now’s a better time. My last email was about how visual storytelling could help {company} make certain messages clearer and more engaging.

If you're curious, I could create a ten-second teaser or a rough script so you can get a sense of what’s possible.

Just reply if you’d like to explore. There’s a link to some of our previous work in the signature below.

{signature}""",

    """{salutation} {name},

I wanted to briefly follow up to see if the idea of a quick, low-lift demo might interest you.

These kinds of animations are used to clarify big-picture strategies, improve training content, or explain services in a more human way.

If {company} has something complex or critical to explain, I’d love to put together a sample to show what it might look like.

Reply when ready, and check out some past examples linked below.

{signature}""",

    """{salutation} {name},

I know inboxes get full fast, so here's a quick follow up.

Whiteboard storytelling might be a surprisingly effective way for {company} to simplify something your audience or team needs to grasp quickly.

If you’re still open to it, I can send a short demo ;  a sample script or 10-second sketch; to give you a feel.

Let me know, or feel free to check out some of our past work in the signature.

{signature}""",

    """{salutation} {name},

Just checking in one more time.

I understand if now’s not ideal, but I still think there’s value in exploring how a short whiteboard video could help {company} communicate more clearly.

It could be a great fit for onboarding, product overviews, or thought leadership; and I’d be happy to show you a no-cost sample.

You can reply any time, or check out some of our past work linked in my signature.

{signature}""",

    """{salutation} {name},

I wanted to circle back following my last email about using whiteboard animation at {company}. These videos can really simplify complex ideas and help you connect with your audience in a memorable way.

If you’re open to it, I’d love to put together that quick sketch or script I mentioned earlier; something tailored specifically to your key offerings or a new product launch, perhaps.

Feel free to reply anytime. And just in case you missed it, some of our past projects are linked in my signature.

{signature}""",

    """{salutation} {name},

Just circling back as I didn’t want you to miss out on the chance to explore whiteboard animation for {company}.

Our animations are designed to help businesses like yours increase engagement, boost clarity, and convert more customers; all with story-driven illustrations.

If you'd like, I can create a short demo or script as a no-pressure way to see how this could work for your team.

You’ll find examples of our work linked in my signature. Let me know if you’d like to see something specific.

{signature}""",

    """{salutation} {name},

Following up on my previous note about whiteboard animation at {company}.

Many of our clients find these videos help explain their offerings faster and more clearly, which often leads to more meaningful conversations and better results.

If it’s helpful, I’d be happy to draft a quick concept or short sample that fits your brand voice and messaging.

You can reply anytime, and our portfolio is linked below if you want to get a feel for what we do.

{signature}""",

    """{salutation} {name},

Hope you’re well. I wanted to check back in and remind you about the offer I shared; a quick, tailored script or visual teaser that could spark some ideas.

It’s a simple, no-strings way to explore how animation can support your {company}'s messaging and help your audience understand your value more clearly.

Feel free to reply if you want to see this, or browse some of our previous projects linked in my signature.

{signature}""",

    """{salutation} {name},

Just wanted to reconnect after my last email about how {company} could benefit from whiteboard animation.

This type of video storytelling often boosts engagement and helps simplify complicated topics; making your message easier to remember.

If you’re curious, I’d be glad to draft a short teaser or script for you to review.

Please reply anytime, and there’s a link to our work in my signature if you want to take a look.

{signature}""",

    """{salutation} {name},

Reaching out again about the opportunity for {company} to stand out using whiteboard animation.

Whether it’s for pitching, explaining products, or internal training, these videos hit the nail on the head.

If you’re open to it, I can prepare a quick demo or script sample tailored to your brand; no pressure at all.

You’ll find examples of our previous work linked below. Let me know if you’d like to explore the fit.

{signature}""",

    """{salutation} {name},

Hope this finds you well. I’m following up on my previous email offering a quick, no-commitment demo to show how whiteboard animation might work for {company}.

These animations are a great way to explain services or products in an engaging, easy-to-understand format.

If you’d like me to put something together, just let me know. You’ll find some past examples linked below too.

{signature}""",

    """{salutation} {name},

Just reaching out again about the possibility of using whiteboard animation to enhance {company}’s messaging.

This approach often helps businesses increase engagement, simplify communication, and improve conversion rates.

If you’re curious, I’d be happy to draft a quick demo or script for you to review at your convenience.

You can reply any time, and there’s a link to our previous work in my signature.

{signature}""",

    """{salutation} {name},

Checking in one more time to see if you’d like to explore whiteboard animation for {company}.

We help clients bring their ideas to life through story-driven visuals that capture attention and make messages stick.

If you’d like, I can prepare a short sample or script tailored to your needs, no strings attached.

Please feel free to reply, and you can browse some of our past projects linked below.

{signature}"""
]

# --- Email 3 Templates ------------------------------------------------------

email3_templates = [
    """{salutation} {name},

Just circling back in case the timing makes more sense now. I still believe whiteboard animation could amplify something {company} is working on, whether that is a pitch, process, or product.

If you would like to test the waters, I am happy to sketch something out to show what it might look like.

You will find past examples linked in my signature. Feel free to reply if you would like to explore this.

{signature}""",

    """{salutation} {name},

I am still happy to share a quick sketch or demo if it is helpful. Many of our clients use animation to break down services, explain strategy, or walk users through dashboards and pages.

If {company} has anything you are trying to simplify, I would love to help you explore it. Just reply if you want me to send something over.

You will find past examples in the signature below.

{signature}""",

    """{salutation} {name},

Thought I would check in one last time.

If you are still curious what an animated whiteboard explainer might look like for {company}, I would be glad to share something rough, a short teaser, or a script to get the ball rolling.

You can find our work in the link below. Reply anytime if you are interested.

{signature}""",

    """{salutation} {name},

Just reaching out again before I close this thread. If you think animated storytelling could be of value to {company}, I would love to put something together.

Even a 10-second sketch can be a useful way to explore what is possible.

Feel free to reply at your convenience.

{signature}""",

    """{salutation} {name},

If you are still considering creative ways to showcase {company}'s value offerings, animated storytelling could be the missing piece of the puzzle to accelerate those conversions.

I would be happy to send over a short visual teaser to get the ideas flowing.

No pressure, just a creative option to keep in mind. Reply anytime or take a peek at some of our previous work. The link is in my signature.

{signature}""",
    
    """{salutation} {name},

Circling back once more before I close the loop.

If there is anything at {company} you have been meaning to simplify, such as those boring quarterly reports your team never reads, whiteboard animation could help bring that to life.

I would be happy to draft something visual if you want to see what that might look like. You can reply anytime or check out some of our previous work on our website, linked in my signature.

{signature}""",

    """{salutation} {name},

Reaching out one last time before I close the loop. If you are still exploring creative ways to showcase what {company} offers, this could be a great fit.

I would be glad to put together a simple teaser or sketch if you are curious. Reply at your convenience or check out some of our past projects. The link is in my signature.

{signature}""",

    """{salutation} {name},

I hope your week is going well. I am wrapping up some projects and wanted to reach out again before I close things out.

If you would still like to explore using whiteboard videos to support {company}'s messaging, I would love to help. Simply reply or take a peek at some of our previous work on our website, which is linked in my signature.

{signature}""",

    """{salutation} {name},

A quick follow-up before I close out my list. If now is not the right time, no worries at all.

But if you are curious about how whiteboard animation might help {company}, I am still open to sharing a quick demo. No pressure. You can reply anytime or skim through some of our previous projects to see what we have done for other businesses. The link is in my signature.

{signature}""",

    """{salutation} {name},

Just one last follow-up in case you missed my previous notes. I would still be happy to sketch a teaser for {company} if you are curious to see what whiteboard animation can do.

It could help simplify one of your key offerings or assist with your latest project launch. If you are a little curious, just hit reply or check out some of our past work, which is already linked in my signature.

{signature}""",

    """{salutation} {name},

I just wanted to check in again and see if the idea of using whiteboard animation for {company} has sparked any interest. Animation can be a great way to highlight key messages and bring stories to life in a memorable way.

If you'd like, I can put together a simple draft or a short sample video to show how this could work for you.

You can also find examples of our previous work linked in my signature. Please don’t hesitate to reply if you want to explore this.

{signature}""",

    """{salutation} {name},

Following up once more because I think animation could really help {company} communicate ideas in a clear and compelling way. Many of our clients have seen great results from adding this creative approach to their messaging.

I’d be happy to sketch out a quick visual or script that suits your brand and goals.

Feel free to reply if you’d like to see what this might look like. You’ll find links to our past projects in my signature.

{signature}""",

    """{salutation} {name},

I hope this note finds you well. I’m reaching out again to offer a creative way for {company} to stand out using animated whiteboard videos.

Even a short, simple animation can make complex ideas easier to understand and more engaging for your audience.

If that sounds interesting, I’d be glad to prepare a brief demo or script to share with you.

Please reply anytime. Past examples are linked in my signature.

{signature}""",

    """{salutation} {name},

Just wanted to reconnect in case my previous notes got buried. If you have any questions or thoughts about using whiteboard animation at {company}, I'd be more than happy to answer them..

It’s a creative way to explain your value offerings, and it can really help with marketing, training, or internal communications.

If you’d like, I can send over a quick teaser or script sample.

You’ll find some of our past work in my signature. I’m here if you want to chat.

{signature}""",

    """{salutation} {name},

Checking in again to share how whiteboard animation could help {company} communicate clearly and creatively with your audience.

Animation can make even the most complicated topics accessible and engaging, which often leads to better engagement.

If you’re open to it, I’d love to draft a short visual concept for you to review.

Feel free to reply anytime, and you can see examples of our work linked below.

{signature}""",

    """{salutation} {name},

I wanted to reach out once more to highlight the potential benefits of whiteboard animation for {company}.

Whether it’s for sales, marketing, onboarding, or internal messaging, animation can be a great tool to simplify ideas and keep people interested.

If you’re curious, I’d be happy to create a short sample or script that fits your goals.

Please reply whenever you’re ready. Past projects are linked in my signature.

{signature}""",

    """{salutation} {name},

Just following up again because I think animation could add real value to {company}’s messaging.

It’s an engaging way to capture attention and explain what makes your business stand out.

If it sounds useful, I’d be glad to prepare a quick teaser or script to show you what’s possible.

You can reply anytime, and a link to our portfolio is in my signature.

{signature}""",

    """{salutation} {name},

I’m checking in one last time about the opportunity to use whiteboard animation at {company}.

Many teams find that even short animations help simplify their message and make content more digestible.

If you’d like, I can put together a brief teaser or script to help you explore this option.

Please feel free to reply at any time. Examples of our work are linked in my signature.

{signature}""",

    """{salutation} {name},

Just wanted to follow up to see if you’ve had a chance to consider adopting whiteboard animation at {company}.

It’s a creative way to bring your ideas to life and connect with your audience more effectively.

If you’re interested, I’d be happy to share a quick demo or script tailored to your needs.

You’ll find past examples linked in my signature. Reply whenever you’re ready.

{signature}""",

    """{salutation} {name},

I wanted to check in one last time to offer support if you’re thinking about how {company} could benefit from whiteboard animation.

We’ve helped many businesses explain their offerings clearly and creatively through short, engaging videos.

If you’d like, I can draft a quick sample to show how this might work for you.

Please don’t hesitate to reply. Our past projects are linked below.

{signature}""",
]

# --- Rotators --------------------------------------------------------------

rotators = {
    "p1": VariantRotator(paragraph1_templates),
    "p2": VariantRotator(paragraph2_variants),
    "p3": VariantRotator(paragraph3_additional_variants),
    "p4": VariantRotator(paragraph4b_variants),
    "p5": VariantRotator(paragraph5_variants),
    "p6": VariantRotator(paragraph6_variants),
    "p7": VariantRotator(paragraph7_cta_variants),
    "sig": VariantRotator(signatures),
    "e2": VariantRotator(email2_templates),
    "e3": VariantRotator(email3_templates),
}

# --- Utilities -------------------------------------------------------------

def parse_use_cases(raw):
    items = [item.strip() for item in str(raw or "").split("|") if item.strip()]
    return random.sample(items, min(3, len(items)))

def build_email1(lead):
    name = lead.get("first name", "there")
    company = lead.get("business name", "your company")
    use_cases = "\n".join(f"• {uc}" for uc in parse_use_cases(lead.get("use cases", "")))
    return (
        f"{rotators['p1'].next().format(name=name, company=company)}\n\n"
        f"{rotators['p2'].next()}\n\n"
        f"{rotators['p3'].next().format(company=company)}{use_cases}\n\n"
        f"{rotators['p4'].next()}\n\n"
        f"{rotators['p5'].next().format(company=company)}\n\n"
        f"{rotators['p7'].next()}\n\n"
        f"{rotators['p6'].next()}\n\n"
        f"{rotators['sig'].next()}"
    )

def build_email2(lead):
    name = lead.get("first name", "there")
    company = lead.get("business name", "your company")
    salutation = random.choice(salutations)
    signature = rotators["sig"].next()
    return rotators["e2"].next().format(salutation=salutation, name=name, company=company, signature=signature)

def build_email3(lead):
    name = lead.get("first name", "there")
    company = lead.get("business name", "your company")
    salutation = random.choice(salutations)
    signature = rotators["sig"].next()
    return rotators["e3"].next().format(salutation=salutation, name=name, company=company, signature=signature)

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
        if buffer:  # handle last block if no trailing newline
            try:
                records.append(json.loads(buffer))
            except json.JSONDecodeError as e:
                print(f"❌ JSON decode error at EOF:\n{buffer}\n→ {e}")
    return records

def save_ndjson(filepath, records):
    with open(filepath, "w", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False, indent=2) + "\n")

# --- Main ------------------------------------------------------------------

def main():
    leads = load_ndjson(LEADS_FILE)
    updated1 = updated2 = updated3 = 0

    for lead in leads:
        use_cases = lead.get("use cases", "").strip()
        if not use_cases:
            continue  # ❌ Skip this lead if no use cases

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
