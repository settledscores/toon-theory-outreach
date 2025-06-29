import os
import json
import random

INPUT_FILE = "leads/scraped_leads.json"

with open(INPUT_FILE, "r", encoding="utf-8") as f:
    leads = json.load(f)

class VariantRotator:
    def __init__(self, items):
        self.original = items[:]
        self.pool = []
        self._reshuffle()

    def _reshuffle(self):
        self.pool = self.original[:]
        random.shuffle(self.pool)

    def next(self):
        if not self.pool:
            self._reshuffle()
        return self.pool.pop()

# === EMAIL 1 VARIANTS ===

paragraph1_templates = [
    "Hi {name},\n\nI came across {company} recently and wanted to reach out directly.",
    "Hello {name},\n\nI just saw {company} and thought you might be the right person to speak with.",
    "Hey {name},\n\nI came across {company} recently and thought I’d drop you a quick note.",
    "Hi {name},\n\nI stumbled on {company} the other day and wanted to get in touch.",
    "Hi {name},\n\nI stumbled across {company} and thought I’d reach out.",
    "Hi {name},\n\nI just spotted {company} and thought there could be an opportunity to collaborate.",
    "Hi {name},\n\nHope you don't mind me reaching out; I came across {company} recently and thought we could collaborate."
]

paragraph2_variants = [
    "I'm Trent. I run Toon Theory, a whiteboard animation studio based in the UK. We create strategic, story-driven explainer videos that simplify complex ideas and boost engagement, especially for B2B services, thought leadership, and data-driven education.",
    "I'm Trent, founder of Toon Theory – a UK-based animation studio that creates story-driven whiteboard animations to help businesses like yours explain ideas with clarity and speed, especially for B2B services, thought leadership, and data-driven education.",
    "I'm Trent, I lead a creative studio called Toon Theory. We work with businesses like yours to turn abstract ideas into short, powerful videos that actually stick, especially for B2B services, thought leadership, and data-driven education.",
    "I'm Trent, I run Toon Theory, an animation studio based in the UK. We focus on helping businesses cut through the noise using clean, hand-drawn storytelling, especially for B2B services, thought leadership, and data-driven education."
]

paragraph3_additional_variants = [
    "For {company}, I think there’s real potential to add a layer of visual storytelling that helps even more people 'get it' faster.\n\nOur animations are fully done-for-you: illustrations, scripting, voiceover, storyboard; and are often used for:\n",
    "I see a clear opportunity for {company} to use visual storytelling as a way to explain things faster and more memorably.\n\nWe handle everything end-to-end; illustration, scripting, voice, and storyboarding; and they’re often used for:\n",
    "Visual storytelling could be a strong lever for {company}, especially when clarity and connection are vital.\n\nWe take care of the entire process; from script to storyboard to final voiceover; and they’re typically applied in:\n",
    "{company} has a solid foundation, and a short animated piece could be a powerful way to bring your message to life quickly.\n\nWe handle the full creative lift; script, visuals, voice; and these are often created for:\n",
    "For {company}, a short explainer could help communicate key ideas more clearly and quickly.\n\nWe take care of everything; writing, illustrating, voicing, and producing; so you can focus on results. These typically support:\n"
]

paragraph4b_variants = [
    "These videos often help businesses increase engagement by up to 60%, double conversion rates, and boost message retention by up to 80%.",
    "These animations don’t just explain, they convert; Many clients see a big lift in engagement, trust, and sales.",
    "Clients often tell us these pieces help cut through the noise, increase clarity, and lead to more meaningful conversions.",
    "Whether it’s more signups, better retention, or faster understanding, these animations tend to move the needle where it counts.",
    "People use these to clarify complex ideas, but they often notice the real impact in engagement and conversion metrics too."
]

paragraph5_variants = [
    "If you'd be open to it, I’d love to share a brief demo tailored to one of your core offerings. This could be a sample script or a ten second sketch. No strings attached; just curious to explore how it might sound with {company}'s voice.",
    "If you’re open to it, I’d love to share a quick sketch or sample script tailored to one of your key offerings. No pressure at all; just interested in how this could come to life in {company}'s tone.",
    "I'd be happy to draft a ten-second demo around something core to your brand. Totally low-lift, just keen to explore what this could look like with {company}'s voice behind it.",
    "Would you be open to seeing a quick script or ten-second sketch built with {company} in mind? No expectations; just interested in showing you what’s possible.",
    "Open to a quick preview? I could whip up a ten-second mock or short script tailored to something core at {company}; purely exploratory.",
    "Happy to create a no-commitment snippet; a short script or sketch; that speaks to what {company} does best. Just a chance to show you what I mean.",
    "If you're curious, I can pull together a short sketch or script draft focused on something {company} offers. Just to give you a sense of what it might sound like.",
    "I’d love to put together a quick concept; maybe a script or a short visual; around one of your offerings. No strings, just a glimpse of the potential in {company}'s tone.",
    "How about a quick sample built around {company}'s strengths? Ten seconds or so, just a feeler to see what resonates.",
    "Could I sketch something out for you? A short demo or script idea based on what {company} does. No pitch; just something for you to react to."
]

paragraph6_variants = [
    "Thanks for putting something refreshing out there.",
    "Thanks for leading with both heart and strategy.",
    "Keep doing what you do, it's making an impact."
]

paragraph7_cta_variants = [
    "Feel free to reply if you’d like to explore what this could look like. There’s also a link to our site in my signature if you’d like to take a peek at some of our previous work.",
    "You’ll find a link to our site in the signature if you’d like to check out our past work. I’d love to hear your thoughts if anything stands out.",
    "If it feels like a fit, you can reply any time. There’s also a link in my signature in case you want to browse a few previous projects.",
    "If you're open to chatting more, just hit reply. And if you're curious, there’s a site link in the signature with a few past examples.",
    "Curious what this might look like for you? I'm around if you want to explore. You’ll find some previous work in the signature link too.",
    "Happy to dive deeper if you're interested. You can reply anytime, and there’s a portfolio link in my signature if you’d like to have a look.",
    "Let me know if you'd like to take this further. You can check out some of our work through the link in my signature as well.",
    "Always open to a quick chat if this feels worth exploring. In the meantime, you can view a few past pieces via the link in my signature.",
    "Reply anytime if you'd like to talk more about this. There’s also a link below with some samples of what we’ve done before.",
    "Just reach out if you’d like to continue the conversation. You’ll find a few previous projects linked in the signature below."
]

signature_variants = [
    "Warm regards,\nTrent — Founder, Toon Theory\nwww.toontheory.com",
    "All the best,\nTrent — Founder, Toon Theory\nwww.toontheory.com",
    "Cheers,\nTrent — Founder, Toon Theory\nwww.toontheory.com",
    "Take care,\nTrent — Founder, Toon Theory\nwww.toontheory.com",
    "Sincerely,\nTrent — Founder, Toon Theory\nwww.toontheory.com"
]

followup2_templates = [
    "{salutation} {name},\n\nJust circling back in case my note got buried.\n\nStill happy to mock something up if a sketch or script sample sounds helpful.\n\n{signature}",
    "{salutation} {name},\n\nWanted to follow up briefly — no pressure at all.\n\nIf a 10-second sample would be useful for {company}, I’d be happy to mock something up.\n\n{signature}",
    "{salutation} {name},\n\nLet me know if it’s worth drafting a short demo around what {company} offers. Always happy to show, not just tell.\n\n{signature}",
    "{salutation} {name},\n\nAppreciate you taking a moment if you’ve had a chance to read the earlier note.\n\nStill open to sketching something up if you’d like to explore further.\n\n{signature}",
    "{salutation} {name},\n\nJust nudging this up in your inbox.\n\nIf there’s even a sliver of curiosity, I can draft something short and sharp for {company}.\n\n{signature}"
]

followup3_templates = [
    "{salutation} {name},\n\nHope this isn’t intrusive — just giving this one last try.\n\nStill happy to put together a short visual idea or script if that’s useful for {company}.\n\nIf not now, maybe down the line!\n\n{signature}",
    "{salutation} {name},\n\nNo worries if the timing's off. Just wanted to close the loop here.\n\nOffer’s still open for a short sample if you’re ever curious.\n\nAll the best in the meantime.\n\n{signature}",
    "{salutation} {name},\n\nFinal ping on this — appreciate your time either way.\n\nStill happy to draft a quick visual or script idea around something core to {company}.\n\nThanks again for doing great work.\n\n{signature}",
    "{salutation} {name},\n\nThis’ll be my last note — just offering one last shot at a sample sketch if that could help.\n\nReally admire what {company} is building.\n\n{signature}",
    "{salutation} {name},\n\nJust wrapping up the thread here. If you're curious later on, I'm always happy to mock something up.\n\nKeep building great things at {company}.\n\n{signature}"
]

salutation_choices = ["Hi", "Hey", "Hello", "Hi there", "Hey there", "Hello there"]

rotators = {
    "p1": VariantRotator(paragraph1_templates),
    "p2": VariantRotator(paragraph2_variants),
    "p3": VariantRotator(paragraph3_additional_variants),
    "p4b": VariantRotator(paragraph4b_variants),
    "p5": VariantRotator(paragraph5_variants),
    "p6": VariantRotator(paragraph6_variants),
    "p7": VariantRotator(paragraph7_cta_variants),
    "sig": VariantRotator(signature_variants)
}

def parse_use_cases(raw):
    return [x.strip() for x in (raw or "").split("|") if x.strip()][:3]

def build_email1(lead):
    name = lead.get("first name", "there")
    company = lead.get("business name", "your company")
    bullets = "\n".join([f"• {uc}" for uc in parse_use_cases(lead.get("use case", ""))])
    return f"""{rotators["p1"].next().format(name=name, company=company)}

{rotators["p2"].next()}

{rotators["p3"].next().format(company=company)}{bullets}

{rotators["p4b"].next()}

{rotators["p5"].next().format(company=company)}

{rotators["p7"].next()}

{rotators["p6"].next()}

{rotators["sig"].next()}"""

def build_followup(template_pool, lead):
    name = lead.get("first name", "there")
    company = lead.get("business name", "your company")
    template = random.choice(template_pool)
    salutation = random.choice(salutation_choices)
    signature = random.choice(signature_variants)
    return template.format(name=name, company=company, salutation=salutation, signature=signature)

updated = 0
for lead in leads:
    if lead.get("email 1", "").strip() == "":
        lead["email 1"] = build_email1(lead)
        updated += 1
    if lead.get("email 2", "").strip() == "":
        lead["email 2"] = build_followup(followup2_templates, lead)
        updated += 1
    if lead.get("email 3", "").strip() == "":
        lead["email 3"] = build_followup(followup3_templates, lead)
        updated += 1

with open(INPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(leads, f, indent=2, ensure_ascii=False)

print(f"✅ Done. {updated} emails populated.")
