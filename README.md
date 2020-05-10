# Cross-Seed-AutoDL
Crappily finds cross-seedable torrents for Movies and TV via Jackett. Parses existing files/folders in order to download matching torrents

Requires [Jackett](https://github.com/Jackett/Jackett)

Copy exact string for the tracker that appears in the torznab feed URL in Jackett to use for the script

This script was created to be used in a Windows environment

![example img](https://i.ibb.co/8YdNh5v/image.png)


# Setup

edit the .py file and change the values of variables at the top of the python file enclosed by the hash symbol `#`. Since this script is meant for windows, you'll want to add your Windows paths with the backslashes escaped (meaning, for every backslash `\`, you need to prepend it with another backslash. If you copy a path that looks like this: `D:\downloads\downloadspot`, you should input it into the python file as `D:\\downloads\\downloadspot`
