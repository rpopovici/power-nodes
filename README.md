<p align="center">
<img src="assets/img/logo.png" width="500px">
</p>
<br/>

Power Nodes is a node based 3D modeling solution with focus on UI/UX, interactive nodes and highly efficient operators accelerated with CUDA cores.

Official page: https://www.power-nodes.com/

Patreon: https://www.patreon.com/radupopovici

Twitter: https://twitter.com/radu_popovic

Blender artists forum: https://blenderartists.org/t/power-nodes-project/1237749

### Goals of this project:
* user friendly node based modeling, animation and simulation solution, with focus on UI/UX
* interactive operators with automatic node sensing and activation
* performant operators, accelereated with GPU/CUDA cores
* declarative style operators and nodes
* uncluttered nodes interface
* node parametrization and data binding
* reusable digital assets
* fewer connection as possible
* pass-through state
* automatic conversion to and from mesh/object/curve/collection/etc when required
* generic operators based on standard ops, modifiers and bmesh already working
* live node previews
* custom python operators
* independent/autonomous operators from blender internal

### Long term goals:
* integration with geometry nodes
* complete workflows for game development
* batched processing and optimizations
* multi user support
* Unity/Unreal exchange
* animation/simulation integration
* relase as stand-alone app with other packages integration

### Installation and requirements
* Blender v2.92+ is required
* numba 0.52+ is automatically installed.
* CUDA Toolkit v10.x+ is required for CUDA accelerated operators. Manual installation is required.

Clone or download the zip file to install the plugin in blender. :exclamation: The installation process might take up to a minute due to the fact that numba needs to be installed and CSG boolean library needs to be compiled ahead of time. Sorry for the inconvenience :exclamation:

#### Manual numba installation
If you are running on Windows, go to Blender's install folder and from subfolder python/bin run `./python.exe -m pip install --upgrade --target ../lib/site-packages numba`

### Expression engine(experimental)
Power Nodes allows the use of python expressions in nodes for element selection and more complex calculations which cannot be performed exclusively by nodes.
By default, the expression engine will inject most builtin python functions, math module and blender mathutils. Special variables can be injected if they are 
prefixed by the $ sign.

#### Global scope variables:
* $CTX - blender context
* $FRAME - current frame
* $FSTART - start frame
* $FEND - end frame
* $FPS - frames per second
* $FPS_BASE - base fps
* $LEN - if executed in LOOP/VERTEX/EDGE/FACE context it will inject the total number of elements
* $LOC - the location of the current object being processed in the data stream
* $ROT - object rotation of the current object being processed in the data stream
* $SCA - object scale of the current object being processed in the data stream

#### Local scope variables:
* $self - reference to the current LOOP/VERTEX/EDGE/FACE element being processed
* $IDX - index of the current element being processed

#### Blender builtin data fields
* $area - face area
* $co - vertex coords
* $index - element index(can be different from $IDX)
* $normal - vertex/edge/face normal
* $tangent - loop tangent
* $select - vertex/edge/face selection status
* $center - face center
* most BMesh data fields can be accessed in this manner

#### Custom attributes
Any custom attribute(data layer) can be accessed/injected by prefixing the name with $ sign. E.g $Col can be used to access the vertex color map named Col

In select expression field, if you want to invert selection just replace the default "$select" expression with "not $select" or if you want to select everything then use "True" or empty expression.

#### Node links(not implemented yet)
$(/path/to/node/input/field) can be used to inject/reference input fields from other nodes. 

#### Backtick selection range(not implemented yet)
Backtick string can be used to specify selection series and and ranges. `index1, index2, [start:end:step]` E.g `0, 1, 2, 7:15:2, 25`

### Recommendations 
* Turn off autosave in Blender
* Lock interface in Render menu in order to prevent crashes during rendering

### License
Power Nodes is licensed under Apache v2 license with the exception of CSG boolean(https://evanw.github.io/csg.js) library which is licensed under MIT.
Be warned, If you are using Power Nodes in combination with Blender(https://www.blender.org) the less attractive licensing model applies, which is GPL v3 in this case.

 :exclamation: This project is in early BETA state. Bugs are to be expected  :exclamation:


Created by Radu-Marius Popovici<br/>
Copyright © 2020 Radu-Marius Popovici
