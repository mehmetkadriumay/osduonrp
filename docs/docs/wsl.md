# Windows - WSL
The Windows Subsystem for Linux operates as a virtual machine that can dynamically grow the amount of RAM to a maximum set at startup time.  Microsoft sets a default maximum RAM available to 50% of the physical memory and a swap-space that is 1/4 of the maximum WSL RAM.  

You may wish to allow WSL to use more RAM to run OSDU.
To do this add or change you .wslconfig, located in your windows home directory.
```
# Settings apply across all Linux distros running on WSL 2
[wsl2]
# Limits VM memory to use no more than 48 GB, this can be set as whole numbers using GB or MB
memory=48GB
# Sets amount of swap storage space to 8GB, default is 25% of available RAM
swap=8GB
```