from music21 import converter, instrument, note, chord, stream
import numpy as np
from imageio import imwrite
from PIL import Image
import pandas as pd
from mido import MidiFile, MetaMessage, Message, MidiTrack

def extractNote(element):
    return int(element.pitch.ps)

def extractDuration(element):
    return element.duration.quarterLength

def get_notes(notes_to_parse):
    durations = []
    notes = []
    start = []

    for element in notes_to_parse:
        if isinstance(element, note.Note):
            if element.isRest:
                continue

            start.append(element.offset)
            notes.append(extractNote(element))
            durations.append(extractDuration(element))
                
        elif isinstance(element, chord.Chord):
            if element.isRest:
                continue
            for chord_note in element:
                start.append(element.offset)
                durations.append(extractDuration(element))
                notes.append(extractNote(chord_note))

    return {"start":start, "pitch":notes, "dur":durations}


def midi_to_png(midi_path, max_repetitions = float("inf"), resolution = 0.25, lowerBoundNote = 21, upperBoundNote = 127, maxSongLength = 100):
    mid = converter.parse(midi_path)
    instruments = instrument.partitionByInstrument(mid)
    data = {}

    try:
        i=0
        for instrument_i in instruments.parts:
            notes_to_parse = instrument_i.recurse()
            notes_data = get_notes(notes_to_parse)
            
            if len(notes_data["start"]) == 0:
                continue

            if instrument_i.partName is None:
                data["instrument_{}".format(i)] = notes_data
                i+=1
            else:
                data[instrument_i.partName] = notes_data

    except:
        notes_to_parse = mid.flat.notes
        data["instrument_0"] = get_notes(notes_to_parse)

    for instrument_name, values in data.items():
        # https://en.wikipedia.org/wiki/Scientific_pitch_notation#Similar_systems
        pitches = values["pitch"]
        durs = values["dur"]
        starts = values["start"]
        index = 0
        
        while index < max_repetitions:
            matrix = np.zeros((upperBoundNote-lowerBoundNote,maxSongLength))

            for dur, start, pitch in zip(durs, starts, pitches):
                dur = int(dur/resolution)
                start = int(start/resolution)

                if not start > index*(maxSongLength+1) or not dur+start < index*maxSongLength:
                    for j in range(start,start+dur):
                        if j - index*maxSongLength >= 0 and j - index*maxSongLength < maxSongLength:
                            matrix[pitch-lowerBoundNote,j - index*maxSongLength] = 255

            if matrix.any(): # If matrix contains no notes (only zeros) don't save it
                temp_path = f"{midi_path}".replace(".mid",f"_{instrument_name}_{index}.png")
                imwrite(f"{temp_path}", matrix.astype(np.uint8))
                index += 1
            else:
                break

lowerBoundNote = 21
def column2notes(column):
    notes = []
    for i in range(len(column)):
        if column[i] > 255/2:
            notes.append(i+lowerBoundNote)
    return notes

resolution = 0.25
def updateNotes(newNotes,prevNotes): 
    res = {} 
    for note in newNotes:
        if note in prevNotes:
            res[note] = prevNotes[note] + resolution
        else:
            res[note] = resolution
    return res

def png_to_midi(image_path, midi_path):
    with Image.open(image_path) as image:
        im_arr = np.frombuffer(image.tobytes(), dtype=np.uint8)
        try:
            im_arr = im_arr.reshape((image.size[1], image.size[0]))
        except:
            im_arr = im_arr.reshape((image.size[1], image.size[0],3))
            im_arr = np.dot(im_arr, [0.33, 0.33, 0.33])
            
    offset = 0
    output_notes = []

    prev_notes = updateNotes(im_arr.T[0,:],{})
    for column in im_arr.T[1:,:]:
        notes = column2notes(column)
        notes_in_chord = notes
        old_notes = prev_notes.keys()
        for old_note in old_notes:
            if not old_note in notes_in_chord:
                new_note = note.Note(old_note,quarterLength=prev_notes[old_note])
                new_note.storedInstrument = instrument.Piano()
                if offset - prev_notes[old_note] >= 0:
                    new_note.offset = offset - prev_notes[old_note]
                    output_notes.append(new_note)
                elif offset == 0:
                    new_note.offset = offset
                    output_notes.append(new_note)                    
                else:
                    print(offset,prev_notes[old_note],old_note)

        prev_notes = updateNotes(notes_in_chord,prev_notes)
        offset += resolution

    for old_note in prev_notes.keys():
        new_note = note.Note(old_note,quarterLength=prev_notes[old_note])
        new_note.storedInstrument = instrument.Piano()
        new_note.offset = offset - prev_notes[old_note]

        output_notes.append(new_note)

    prev_notes = updateNotes(notes_in_chord,prev_notes)
    midi_stream = stream.Stream(output_notes)
    midi_stream.write('midi', fp=f"{midi_path}".replace(".png",".mid"))

def midi_to_csv(path_in: str, path_out: str) -> None:
    df = pd.DataFrame()
    mid = mid = MidiFile(path_in)

    for n_track, track in enumerate(mid.tracks):
        track_df = pd.DataFrame()
        time = 0

        for msg in track:
            msg_dict = msg.__dict__
            msg_dict["meta"] = int(isinstance(msg, MetaMessage))
            msg_dict["track"] = n_track

            if "time" not in msg_dict:
                continue

            time += int(msg_dict["time"])
            msg_dict["tick"] = time

            for k in ["name", "text"]:
                if k in msg_dict:
                    del msg_dict[k]

            track_df = pd.concat(
                [track_df, pd.DataFrame([msg_dict])], ignore_index=True
            )

        if df.shape[0] > 0:
            df = pd.merge(df, track_df, how="outer")
        else:
            df = track_df

    for col in df.columns:
        if df[col].dtype == "float64":
            df[col] = df[col].astype("Int64")

    df.set_index("tick", inplace=True)
    df.sort_index(inplace=True)
    df.to_csv(path_out)

def si(path_in: str, path_out: str) -> None:
    df = pd.read_csv(path_in)
    n_tracks = max(df["track"])
    mid = MidiFile()
    tracks = {i: MidiTrack() for i in range(n_tracks + 1)}

    for _, row in df.iterrows():
        msg_class = MetaMessage if row["meta"] else Message
        track = int(row["track"])
        row.drop(["meta", "track", "tick"], inplace=True)
        params = dict(row.dropna())

        for k, v in params.items():
            if type(v) is float:
                params[k] = int(v)

        tracks[track].append(msg_class(**params))

    for track in tracks.values():
        if len(track):
            mid.tracks.append(track)

    mid.save(path_out)
