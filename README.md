What is this?
=============

Frotz activity is a wrapper for the classic interactive fiction
interpreter Frotz.

Frotz activity is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or any
later version.

Frotz interprets Z-code story-files, which are usually text adventure
games (although a few arcade-style Z-code games have been written).

Examples of such story files include the adventure games published by
Infocom, as well as any games produced by compilers to this format, such
as Inform.

Frotz is free software; you can redistribute it and/or modify it under
the terms of the GNU General Public License version 2 or any later
version.  You can obtain the source from:
https://davidgriffith.gitlab.io/frotz/

Frotz activity is not part of the Sugar desktop, but can be added.
Please refer to;

* [How to Get Sugar on sugarlabs.org](https://sugarlabs.org/),
* [How to use Sugar](https://help.sugarlabs.org/),

Frotz activity depends on Python, [Sugar
Toolkit](https://github.com/sugarlabs/sugar-toolkit-gtk3), GTK+ 3, Pango, Vte and frotz.


How to install dependencies?
============================

Frotz activity will try to install Frotz if it is not yet installed.
Or you can install by hand;

* Update the package index,
   - On Ubuntu/Debian systems, run
   ```sudo apt update```
   - On Fedora systems, run
   ```sudo dnf update```
* Install `frotz`,
   - On Ubuntu/Debian systems, run
    ```sudo apt install frotz```
   - On Fedora systems, run
    ```sudo dnf install frotz```
