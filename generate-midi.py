from midiutil import MIDIFile

def note_name_to_number(name):
    note_base = {'C': 0, 'C#': 1, 'D': 2, 'D#': 3, 'E': 4, 'F': 5,
                 'F#': 6, 'G': 7, 'G#': 8, 'A': 9, 'A#': 10, 'B': 11}
    if len(name) == 2:
        key, octave = name[0], int(name[1])
        accidental = ''
    elif len(name) == 3:
        key, accidental, octave = name[0], name[1], int(name[2])
        key += accidental
    else:
        raise ValueError(f"Invalid note format: {name}")
    return 12 + note_base[key.upper()] + (12 * octave)

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
        pitch = note_name_to_number(note)
        mf.addNote(0, 0, pitch, time, 4, 80)
    time += 4

# === Strings (Track 1) - Em pad ===
for t in range(0, 32, 4):
    for n in ['E4', 'G4', 'B4']:
        mf.addNote(1, 1, note_name_to_number(n), t, 4, 40)

# === Synth (Track 2) - root only ===
roots = ['E3', 'A3'] * 4
time = 0
for r in roots:
    mf.addNote(2, 2, note_name_to_number(r), time, 4, 30)
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
        mf.addNote(3, 3, note_name_to_number(note), time, 4, 35)
    time += 4

with open("bring_me_to_life_first_verse_full.mid", "wb") as f:
    mf.writeFile(f)

print("✅ MIDI file generated.")
