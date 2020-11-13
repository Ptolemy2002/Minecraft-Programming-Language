# Minecraft-Programming-Language

This is a project that, when finished, will allow for the creation of data packs and data pack tags through a simple programming language syntax that resembles object oriented languages such as Java. This is intended to be much more powerful and user friendly than typing a series of commands like you do in regular development. Here are the planned features (checked features are implemented):

 - [x] Tag Development
	 - [x] [Define a tag](#define-a-tag)
	 - [x] [Add entries to your tag](#add-entries)
	 - [x] [Remove entries from your tag](#remove-entries)
	 - [x] [Specify all available entries](#all)
	 - [x] [Filter entries by name](#filter-by-name)
	 - [x] [Filter entries by value](#filter-by-value)
	 - [x] [Sort entries](#sort)
	 - [x] [Limit entry count](#limit-count)

# Define a Tag
You may define a tag by creating a file with the "mctag" extension in the directory "./tags" relative to the main directory (the directory where you put "main.py" and "tags.py"). All subdirectories of "./tags" will be checked for files, and the resulting data pack will preserve subdirectories (so if you put a file in the "internal" folder, the tag name will be "#internal/[tag_name]").

On the first line of your file, you should specify the type of tag you are creating. Offically, you can create these tag types in data packs:

 - blocks
 - items
 - entity_types
 - fluids
 - functions

Defining the type ensures that the correct data file is used for filtering and that the tag is put in the correct directory of the data pack.

Each subsequent line of the file defines the entries you are placing in your tag and must be prefixed by either "+" or "-" unless it's a comment.

Comment lines are ignored by the generator and may be prefixed by "#". You may also add a comment to the end of a line using the same character.

Format example:

    type: entity_types
    #This is a comment.
    + minecraft:armor_stand #This is also a comment.
