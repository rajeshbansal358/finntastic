# finntastic
App for full stack course at LUT


App functionality summary: ( May still get adjusted due to time constraints )

1) A random 5-10 word English sentence is displayed to user ( allow user to select difficulty level ) ( in future versions user may type their own sentence )

2) Each word in the above sentence is clickable. Upon clicking - user can type to change the word to its Finnish equivalent. They can also tap a button that gives hints as multiple choice. ( first for the stem, then the inflections ) ( difficulty level governs how helpful the hints are ) ( must also accomodate consonant gradation somehow )

3) User should also be able to move the words around and merge words ( as Finnish is agglutinative )

4) Until the sentence is fully correct the user should be made aware that a certain word is wrong/untranslated/mispositioned/unnecessary

5) Future version also allows reverse translation


Other technical details:
=========================
- As required by the course rules - the app needs to have a frontend, a backend and a database
- The intended frontend here is React ( not native ) as the app needs to be a mobile friendly web app
- The intended backend here is FastAPI (Python)
- The intended DB here is SQLite
- The frontend needs to be minimalistic but also not clunky, and definitely good performance is non-negotiable