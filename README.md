# Tempesta-RedSTED
The Tempesta (www.github.com/TestaLab/Tempesta) version used for the RedSTED, in the TestaLab @SciLifeLab.

This version of Tempesta is used to control the STED microscope built in the Testa Lab (www.testalab.org) at SciLifeLab in Stockholm, Sweden. It was adapted from the Tempesta used to control the MoNaLISA microscope developed in the lab, which in turn was adapted from the  custom-written microscope-control software Tormenta (www.github.com/fedebarabas/tormenta).

It is modularly based, with custom-written drivers and code implementation for control of lasers, SLM, scanning stage, z-piezo, focus lock, widefield camera, tiling, AOMs, AOTFs, and the synchronization of all these parts. 
A communication channel with microscope software Imspector (https://imspectordocs.readthedocs.io/) is also implemented. 

Adaptation by:
Jonatan Alvelid

Do not hesitate to contact me (@jonatanalvelid) for any questions regarding the code, for your own implementation or curiosity. 

Used in the following publications:
Alvelid et al., Stable STED imaging of Extended Sample Regions, J. Phys. D: Appl. Phys. (2019), in press https://doi.org/10.1088/1361-6463/ab4c13
