# OWWvisualScripting
Visual Scripting Engine for the Overwatch Workshop

# What is this?
This is a visual scripting engine for the Overwatch Workshop.
You write scripts by combining different building blocks in a graph, rather than writing code or menuing for 2 hours every time you want to change something.

# Is it useful?
No.

# Installation
You will need pygame in order for this program to work. You can install it with
`pip install -U pygame`
*Note: Command name may differ on operating systems other than windows. You may need to invoke pip with a version number if you have multiple Python versions on your PATH.*

# Credits
Overwatch, the Overwatch Workshop, and the small hammer icon I used for the window header are property of Blizzard Entertainment.
The code is mine tho, so get your hands off it!

This application uses Workshop.JSON, a project by arxenix that lists all available actions/values on the workshop in an easy to parse format.
You can visit the projects repo here: https://github.com/arxenix/owws-documentation/blob/master/workshop.json

# Known Problems

-Can't delete connections between nodes
-Deleting nodes will probably crash the application
-Text is spilling out of frames everywhere
-No saving/loading
-Can't navigate viewport
-Colors will probably make your eyes bleed
-Search is slow
-Some parameters currently require manual typing
-No string building (yet)
-No array building (yet)
-No taskbar icon
-Probably looks ass on anything not full HD
-Can't see lines while dragging
-Not actually useful for any serious project