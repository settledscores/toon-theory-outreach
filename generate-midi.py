from midiutil import MIDIFile

mf = MIDIFile(4)  # 4 tracks: Piano, Strings, Synth, Guitar
mf.addTempo(0, 0, 95)
mf.addTempo(1, 0, 95)
mf.addTempo(2, 0, 95)
mf.addTempo(3, 0, 95)

chords = [
    ['E3', 'G3', 'B3'], ['A3', 'C4', 'E4'],
    ['E3', 'G3', 'B3'], ['A3', 'C4', 'E4'],
    ['E3', 'G3', 'B3'], ['A3', 'C4', 'E4'],
    ['E3', 'G3', 'B3'], ['A3', 'C4', 'E4'],
]

# === Piano (Track 0) ===
time = 0
for triad in chords:
    for note in triad:
        pitch = MIDIFile().noteNameToNumber(note)
        mf.addNote(0, 0, pitch, time, 4, 80)
    time += 4

# === Strings (Track 1) - sustained Em pad ===
for t in range(0, 32, 4):
    for pitch in [MIDIFile().noteNameToNumber(n) for n in ['E4', 'G4', 'B4']]:
        mf.addNote(1, 1, pitch, t, 4, 40)

# === Synth Pad (Track 2) - roots only ===
roots = ['E3', 'A3'] * 4
time = 0
for root in roots:
    pitch = MIDIFile().noteNameToNumber(root)
    mf.addNote(2, 2, pitch, time, 4, 30)
    time += 4

# === Ambient Guitar Swells (Track 3) ===
dyads = [
    ['G4', 'B4'], ['C5', 'E5'],
    ['G4', 'B4'], ['C5', 'E5'],
    ['G4', 'B4'], ['C5', 'E5'],
    ['G4', 'B4'], ['C5', 'E5']
]
time = 0
for dyad in dyads:
    for note in dyad:
        pitch = MIDIFile().noteNameToNumber(note)
        mf.addNote(3, 3, pitch, time, 4, 35)
    time += 4

with open("bring_me_to_life_first_verse_full.mid", "wb") as f:
    mf.writeFile(f)

print("✅ MIDI saved: bring_me_to_life_first_verse_full.mid")
