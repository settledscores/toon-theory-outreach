from midiutil import MIDIFile

mf = MIDIFile(1)
mf.addTempo(0, 0, 95)

chords = [
    ['E3', 'G3', 'B3'], ['A3', 'C4', 'E4'],
    ['E3', 'G3', 'B3'], ['A3', 'C4', 'E4'],
    ['E3', 'G3', 'B3'], ['A3', 'C4', 'E4'],
    ['E3', 'G3', 'B3'], ['A3', 'C4', 'E4']
]

time = 0
for triad in chords:
    for note in triad:
        pitch = MIDIFile().noteNameToNumber(note)
        mf.addNote(0, 0, pitch, time, 4, 100)
    time += 4

with open("bring_me_to_life_verse.mid", "wb") as f:
    mf.writeFile(f)
