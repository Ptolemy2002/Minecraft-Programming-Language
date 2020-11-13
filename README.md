# Minecraft-Programming-Language

This is a project that, when finished, will allow for the creation of data packs and data pack tags through a simple programming language syntax that resembles object oriented languages such as Java. This is intended to be much more powerful and user friendly than typing a series of commands like you do in regular development. Here are the planned features (checked features are implemented):

 - [x] Tag Development
	 - [x] [Define a tag](#define-a-tag)
	 - [x] [Add entries to your tag](#add-entries)
	 - [x] [Remove entries from your tag](#remove-entries)
	 - [x] [Add entries from other tags](#specify-other-tags)
	 - [x] [Specify all available entries](#all)
	 - [x] [Filter entries by name](#filter-by-name)
	 - [x] [Filter entries by value](#filter-by-value)
	 - [x] [Sort entries](#sort)
	 - [x] [Limit entry count](#limit-count)
	 - [ ] Data files used for filtering
		 - [x] [entity_types](#entity-data)
			 - [x] [default tags](#default-entity-tags)
		 - [x] [functions](#function-data)
			 - [x] [default tags](#default-function-tags)
		 - [ ] [fluids](#fluid-data)
			 - [ ] [default tags](#default-fluid-tags)
		 - [ ] [blocks](#block-data)
			 - [ ] [default tags](#default-block-tags)
		 - [ ] [items](#item-data)
			 - [ ] [default tags](#default-item-tags)

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

There is an alternate way to define tags that can be used if you have a list of all entries that should be included. You may insert a "txt" file in the directory "./.saved/tags/[type]" that contains either a line separated or comma separated list of the specific entries that should be included (default namespace is "minecraft"). You may not specify other tags or filter entries - This format only accepts literal entry specifications.

Format example:

    minecraft:armor_stand
    minecraft:potion
