from midiutil import MIDIFile
from midiutil.MidiFile import noteNameToNumber  # ✅ Correct way

mf = MIDIFile(4)
for i in range(4):
    mf.addTempo(i, 0, 95)

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
        pitch = noteNameToNumber(note)
        mf.addNote(0, 0, pitch, time, 4, 80)
    time += 4

# === Strings (Track 1) - Em pad ===
for t in range(0, 32, 4):
    for n in ['E4', 'G4', 'B4']:
        mf.addNote(1, 1, noteNameToNumber(n), t, 4, 40)

# === Synth (Track 2) - root only ===
roots = ['E3', 'A3'] * 4
time = 0
for r in roots:
    mf.addNote(2, 2, noteNameToNumber(r), time, 4, 30)
    time += 4

# === Ambient Guitar (Track 3) ===
dyads = [
    ['G4', 'B4'], ['C5', 'E5'],
    ['G4', 'B4'], ['C5', 'E5'],
    ['G4', 'B4'], ['C5', 'E5'],
    ['G4', 'B4'], ['C5', 'E5']
]
time = 0
for dyad in dyads:
    for note in dyad:
        mf.addNote(3, 3, noteNameToNumber(note), time, 4, 35)
    time += 4

with open("bring_me_to_life_first_verse_full.mid", "wb") as f:
    mf.writeFile(f)

print("✅ MIDI generated successfully.")
