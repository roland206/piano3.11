# piano3.11
Installation and system notes:
I used python 3.11 (tested also with 3.10) on Ubuntu and Windows 11
There were problems with PyQt5 on Ubuntu Linux. If you get some Qt5 error messages install "qtdesigner". This sets some system settings for Qt5.
There were Ubuntu/Linux problems with rtmidi2 and ALSA library reporting missing libraries. The problem was that ALSA searches libraies in /usr/lib64/alsa-lib......
while Ubuntu stores these libraries in /usr/lib/x86_64-linux-gnu/alsa-lib. I used a link to repair the problem "ln -s /usr/lib/x86_64-linux-gnu/alsa-lib /usr/lib64/alsa-lib"
There may be smarter ways to solve the problem.

What is it good for:

This is a kind of piano teacher:
The SW can read/import music partitures for pianos. It uses the MusicXML format and is intended to be used in combination with MuseScore (3 or 4).
The "Export" or "Save as" option in musescore can generate these files. It migth also work with other sources of .musicXML files, but hasn't been tested.

If a partuture is importet (using the Import Partiture Button) it is displayed in a different way as usual.
Measures have graphical length strongly related to the time for it. Scores within a measure are rectangles with a "timewise correct" length and position.
Scores with signs have a "#" in the rectangles.

The SW should also be connected to an E-piano via a Midi interface using an USB port.
The Python package "rtmidi2" is used for the communication. If the SW finds a suitable E-Piano Midi IF it connects to it and shows the used port on the screen.

The partiture can now be send to the piano with the play button. It can be stopped with the same button.
This may sound very cold and mechanically since it strictly follows the scores without any human feeling or art.

With the "first measure" input one can set the first measure used for the teaching/controlling part.

One can now play the partiture on the piano. The piano sends the playing data to the SW. When you want to stop playing press the left pedal or play the left most "A" on the keyboard.
The "Repeat" button can be used to send the received piano input back. You can hear again what you just played.

The SW analyes the piano input and displays it on top of the partiture data. One can now compare the playing with the target.
Usually it is very difficult to play exactly with the desired speed. After some measures there is hardly a good match anymore.
The SW performs a time stretching to the input data for a best fit. However it does not match individual score, just complete measures.
For every measure there is an individual stretch for a best (linear) fit.

The violine and the bass clefs have different color coding (green and blue).
The partiture scores are displayed with higher rectangles and may have 2 colors. Grey indicates that a correspondig key hit have been found. Gray-red indicates no match have been found.
The played scores are green or blue if a match to the target song has been found. They are red in case of no match.
One can also use and display the right pedal. Play it and set the "show pedal" button.
Two things happen:
  The diplay has now white or grey background to indicate the status of the pedal while playing.
  Played tones may be extended with smaller rectangles to indicate how long the tone has been extended with the pedal.

Beside the main display of the timing, some addional info is available.
There are 3 tacho meters:
  The "Rubato" meter indicates temporal differences (ignoring the measure based stretch). It shows the mean difference in units of 64 scores. The "red zone" shows the minimal and maximal difference.
  The green zone indicated the mean variation.

  The tempo tacho shows the played speed.

  The legato tacho shows how well legato has been played. It uses units of milliseconds.
  If two tones are played with perfect legato, a 0 is shown.
  If in a sequence of two scores the first key is released before the second key is pressed, a negative value is shown. If there is a temporal overlap a positiv legato is shown.

  All three tachos show the mean, the min/max range (red) and the mean variation (gree) or standdard deviation.

  The "show" selector can be used to dispaly additional infos below the scores.
  Pedal: shows the use of the right pedal.
  Level: Show the dynamic of the played music using the same colors as the scores.
  Tempo: shows the speed. Green is the traget speed in bpm (beats per minutes). Blue is the mean value of the record and red shows how the speed varies in the song.
  Legato: Show the legato as explained above

  The buttons "Simulation" and "Relaod" are just for debugging and can be ignored.
  
  
  



