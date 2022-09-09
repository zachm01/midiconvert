from midiconvert import midi_to_png
import sys, os

def midi_to_png(midi_path):
    if len(sys.argv) >= 3:
        max_repetitions = int(sys.argv[2])
        midi_to_png(midi_path, max_repetitions)
    else:
        midi_to_png(midi_path)

if __name__ == '__main__':
    in_dir = 'ragtime_midi'
    files = os.listdir(in_dir)

    for i in range(len(files)):
        midi_to_png(f'{in_dir}/{files[i]}')
        print(f'Converted {i + 1} of {len(files)} files')
    
    print('\nComplete!\n')
